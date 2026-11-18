"""Modelo físico del núcleo de la Figura 5.4 contra PostgreSQL real (migración 0002)."""

import re
import threading
from enum import StrEnum
from typing import Any

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.pool import NullPool

from atlas.dominio.enumeraciones import (
    ClaseSugerencia,
    EstadoIncorporacion,
    EstadoTrabajo,
    EstadoTramite,
    EstadoUsuario,
    FormatoArchivo,
    MotivoSinFuente,
    ResultadoAuditoria,
    Rol,
    TipoActor,
    TipoDocumental,
)
from atlas.persistencia.base import ESQUEMA, Base
from atlas.persistencia.modelos import Usuario  # noqa: F401  (registra los modelos)
from tests import datos

pytestmark = pytest.mark.integracion

TABLAS_DEL_NUCLEO = (
    "usuario",
    "usuario_rol",
    "tramite",
    "archivo",
    "documento",
    "version_documental",
    "evento_auditoria",
)


def rechaza(
    conexion: Connection,
    sentencia: str,
    parametros: dict[str, Any] | None = None,
    error: type[Exception] = IntegrityError,
    coincide: str | None = None,
) -> None:
    """La sentencia falla; un savepoint conserva utilizable la transacción de la prueba."""
    with pytest.raises(error, match=coincide), conexion.begin_nested():
        conexion.execute(text(sentencia), parametros or {})


def verificar_diferidas(conexion: Connection) -> None:
    conexion.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


# --- Coherencia entre el modelo Python y la migración ------------------------------


def test_modelos_coinciden_con_la_migracion(configuracion_tests: Any, base_migrada: Any) -> None:
    # Con `atlas` fuera del search_path, la reflexión informa el esquema de todas las FK.
    motor = create_engine(
        configuracion_tests.url_migracion(),
        poolclass=NullPool,
        connect_args={"options": "-c search_path=public"},
    )
    with motor.connect() as conexion:
        contexto = MigrationContext.configure(
            conexion, opts={"include_schemas": True, "version_table_schema": ESQUEMA}
        )
        diferencias = [
            d for d in compare_metadata(contexto, Base.metadata) if "alembic_version" not in str(d)
        ]
    motor.dispose()
    assert diferencias == []


@pytest.mark.parametrize(
    ("restriccion", "enumeracion"),
    [
        ("ck_usuario_estado", EstadoUsuario),
        ("ck_usuario_rol_rol", Rol),
        ("ck_tramite_estado", EstadoTramite),
        ("ck_archivo_estado_incorporacion", EstadoIncorporacion),
        ("ck_archivo_formato", FormatoArchivo),
        ("ck_documento_tipo", TipoDocumental),
        ("ck_evento_auditoria_actor_tipo", TipoActor),
        ("ck_evento_auditoria_resultado", ResultadoAuditoria),
        ("ck_trabajo_procesamiento_estado", EstadoTrabajo),
        ("ck_valor_sugerido_clase", ClaseSugerencia),
        ("ck_valor_sugerido_motivo_sin_fuente", MotivoSinFuente),
    ],
)
def test_catalogos_de_la_base_coinciden_con_las_enumeraciones(
    conexion_migracion: Connection, restriccion: str, enumeracion: type[StrEnum]
) -> None:
    definicion = conexion_migracion.execute(
        text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :nombre"),
        {"nombre": restriccion},
    ).scalar_one()
    assert set(re.findall(r"'([a-z_]+)'", definicion)) == {m.value for m in enumeracion}


def test_rf_03_tramite_tiene_los_siete_estados_de_la_tesis() -> None:
    assert len(EstadoTramite) == 7


# --- RF-05: documento, versión vigente e historial ---------------------------------


def test_rf_05_documento_y_version_inicial_se_crean_juntos(conexion_aplicacion: Connection) -> None:
    escenario = datos.escenario_documento(conexion_aplicacion)
    verificar_diferidas(conexion_aplicacion)
    vigente = conexion_aplicacion.execute(
        text("SELECT version_vigente_id, tipo FROM atlas.documento WHERE id = :id"),
        {"id": escenario["documento"]},
    ).one()
    assert vigente.version_vigente_id == escenario["version"]
    assert vigente.tipo is None  # Sin tipo hasta validar la clasificación


def test_rf_05_documento_sin_version_vigente_rechazado(conexion_aplicacion: Connection) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    tramite = datos.crear_tramite(conexion_aplicacion, usuario)
    conexion_aplicacion.execute(
        text(
            "INSERT INTO atlas.documento (tramite_id, nombre, version_vigente_id) "
            "VALUES (:tramite, 'Sin versión', :version)"
        ),
        {"tramite": tramite, "version": datos.proximo_id_version(conexion_aplicacion)},
    )
    with pytest.raises(IntegrityError, match="fk_documento_version_vigente"):
        verificar_diferidas(conexion_aplicacion)


def test_rf_05_version_vigente_debe_pertenecer_al_documento(
    conexion_aplicacion: Connection,
) -> None:
    uno = datos.escenario_documento(conexion_aplicacion)
    otro = datos.escenario_documento(conexion_aplicacion)
    archivo = datos.crear_archivo(conexion_aplicacion, otro["tramite"], otro["usuario"])
    version_ajena = datos.insertar_version(
        conexion_aplicacion, None, otro["documento"], archivo, otro["usuario"], 2, otro["version"]
    )
    verificar_diferidas(conexion_aplicacion)
    conexion_aplicacion.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    conexion_aplicacion.execute(
        text("UPDATE atlas.documento SET version_vigente_id = :v WHERE id = :d"),
        {"v": version_ajena, "d": uno["documento"]},
    )
    with pytest.raises(IntegrityError, match="fk_documento_version_vigente"):
        verificar_diferidas(conexion_aplicacion)


def test_rf_05_nueva_version_actualiza_solo_la_vigencia(conexion_aplicacion: Connection) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    archivo = datos.crear_archivo(conexion_aplicacion, e["tramite"], e["usuario"])
    nueva = datos.insertar_version(
        conexion_aplicacion, None, e["documento"], archivo, e["usuario"], 2, e["version"]
    )
    conexion_aplicacion.execute(
        text("UPDATE atlas.documento SET version_vigente_id = :v WHERE id = :d"),
        {"v": nueva, "d": e["documento"]},
    )
    verificar_diferidas(conexion_aplicacion)
    historial = conexion_aplicacion.execute(
        text(
            "SELECT numero, version_previa_id FROM atlas.version_documental "
            "WHERE documento_id = :d ORDER BY numero"
        ),
        {"d": e["documento"]},
    ).all()
    assert [tuple(f) for f in historial] == [(1, None), (2, e["version"])]


def test_rf_05_dos_reemplazos_de_la_misma_version_rechazados(
    conexion_aplicacion: Connection,
) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    primero = datos.crear_archivo(conexion_aplicacion, e["tramite"], e["usuario"])
    segundo = datos.crear_archivo(conexion_aplicacion, e["tramite"], e["usuario"])
    datos.insertar_version(
        conexion_aplicacion, None, e["documento"], primero, e["usuario"], 2, e["version"]
    )
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.version_documental (documento_id, archivo_id, creado_por_id, numero,"
        " version_previa_id) VALUES (:d, :a, :u, 3, :p)",
        {"d": e["documento"], "a": segundo, "u": e["usuario"], "p": e["version"]},
        coincide="uq_version_documental_version_previa_id",
    )


def test_rf_05_reemplazos_concurrentes_solo_uno_se_completa(
    base_migrada: Any, motor_aplicacion: Engine
) -> None:
    """§5.2: si dos confirmaciones reemplazan a la vez la misma versión vigente, solo una
    se completa. Usa transacciones reales confirmadas (la aplicación no puede borrar)."""
    with motor_aplicacion.begin() as conexion:
        e = datos.escenario_documento(conexion)
        archivos = [datos.crear_archivo(conexion, e["tramite"], e["usuario"]) for _ in range(2)]

    sentencia = text(
        "INSERT INTO atlas.version_documental (documento_id, archivo_id, creado_por_id, numero,"
        " version_previa_id) VALUES (:d, :a, :u, 2, :p)"
    )
    errores: list[Exception] = []

    def segunda_confirmacion() -> None:
        try:
            with motor_aplicacion.begin() as conexion:
                conexion.execute(
                    sentencia,
                    {"d": e["documento"], "a": archivos[1], "u": e["usuario"], "p": e["version"]},
                )
        except IntegrityError as error:
            errores.append(error)

    with motor_aplicacion.connect() as primera:
        transaccion = primera.begin()
        primera.execute(
            sentencia, {"d": e["documento"], "a": archivos[0], "u": e["usuario"], "p": e["version"]}
        )
        hilo = threading.Thread(target=segunda_confirmacion)
        hilo.start()
        hilo.join(timeout=1)
        assert hilo.is_alive(), "la segunda confirmación debe esperar a la primera"
        transaccion.commit()
        hilo.join(timeout=10)

    assert len(errores) == 1
    with motor_aplicacion.connect() as conexion:
        versiones = conexion.execute(
            text("SELECT count(*) FROM atlas.version_documental WHERE documento_id = :d"),
            {"d": e["documento"]},
        ).scalar_one()
    assert versiones == 2


@pytest.mark.parametrize(("numero", "con_previa"), [(2, False), (1, True), (0, False)])
def test_rf_05_numero_y_predecesora_coherentes(
    conexion_aplicacion: Connection, numero: int, con_previa: bool
) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    archivo = datos.crear_archivo(conexion_aplicacion, e["tramite"], e["usuario"])
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.version_documental (documento_id, archivo_id, creado_por_id, numero,"
        " version_previa_id) VALUES (:d, :a, :u, :n, :p)",
        {
            "d": e["documento"],
            "a": archivo,
            "u": e["usuario"],
            "n": numero,
            "p": e["version"] if con_previa else None,
        },
        coincide="ck_version_documental",
    )


def test_rf_05_predecesora_de_otro_documento_rechazada(conexion_aplicacion: Connection) -> None:
    uno = datos.escenario_documento(conexion_aplicacion)
    otro = datos.escenario_documento(conexion_aplicacion)
    archivo = datos.crear_archivo(conexion_aplicacion, uno["tramite"], uno["usuario"])
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.version_documental (documento_id, archivo_id, creado_por_id, numero,"
        " version_previa_id) VALUES (:d, :a, :u, 2, :p)",
        {"d": uno["documento"], "a": archivo, "u": uno["usuario"], "p": otro["version"]},
        coincide="fk_version_documental_version_previa",
    )


@pytest.mark.parametrize("caso", ["pendiente", "descartado", "otro_tramite"])
def test_rf_07_version_exige_archivo_incorporado_del_mismo_tramite(
    conexion_aplicacion: Connection, caso: str
) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    if caso == "otro_tramite":
        ajeno = datos.crear_tramite(conexion_aplicacion, e["usuario"])
        archivo = datos.crear_archivo(conexion_aplicacion, ajeno, e["usuario"])
    else:
        archivo = datos.crear_archivo(conexion_aplicacion, e["tramite"], e["usuario"], estado=caso)
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.version_documental (documento_id, archivo_id, creado_por_id, numero,"
        " version_previa_id) VALUES (:d, :a, :u, 2, :p)",
        {"d": e["documento"], "a": archivo, "u": e["usuario"], "p": e["version"]},
        coincide="otro trámite" if caso == "otro_tramite" else "archivo incorporado",
    )


def test_rf_05_un_archivo_origina_una_sola_version(conexion_aplicacion: Connection) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.version_documental (documento_id, archivo_id, creado_por_id, numero,"
        " version_previa_id) VALUES (:d, :a, :u, 2, :p)",
        {"d": e["documento"], "a": e["archivo"], "u": e["usuario"], "p": e["version"]},
        coincide="uq_version_documental_archivo_id",
    )


# --- RF-05, RN-10, RNF-04: inmutabilidad y ausencia de borrado ----------------------


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE atlas.version_documental SET numero = numero WHERE id = :v",
        "DELETE FROM atlas.version_documental WHERE id = :v",
        "UPDATE atlas.evento_auditoria SET accion = accion WHERE id = :ev",
        "DELETE FROM atlas.evento_auditoria WHERE id = :ev",
        "DELETE FROM atlas.tramite WHERE id = :t",
        "DELETE FROM atlas.documento WHERE id = :d",
        "DELETE FROM atlas.archivo WHERE id = :a",
        "UPDATE atlas.archivo SET huella = repeat('0', 64) WHERE id = :a",
        "UPDATE atlas.documento SET tramite_id = tramite_id WHERE id = :d",
        "UPDATE atlas.alembic_version SET version_num = version_num",
    ],
)
def test_rnf_04_rn_10_aplicacion_no_altera_historia(
    conexion_aplicacion: Connection, sentencia: str
) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    evento = datos.registrar_evento(conexion_aplicacion, e["tramite"], e["usuario"])
    rechaza(
        conexion_aplicacion,
        sentencia,
        {
            "v": e["version"],
            "ev": evento,
            "t": e["tramite"],
            "d": e["documento"],
            "a": e["archivo"],
        },
        error=DBAPIError,
        coincide="permission denied",
    )


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE atlas.version_documental SET numero = numero WHERE id = :v",
        "DELETE FROM atlas.version_documental WHERE id = :v",
        "TRUNCATE atlas.version_documental CASCADE",
        "UPDATE atlas.evento_auditoria SET accion = accion WHERE id = :ev",
        "DELETE FROM atlas.evento_auditoria WHERE id = :ev",
        "TRUNCATE atlas.evento_auditoria",
    ],
)
def test_rf_05_rn_10_inmutables_incluso_para_el_propietario(
    conexion_migracion: Connection, sentencia: str
) -> None:
    e = datos.escenario_documento(conexion_migracion)
    evento = datos.registrar_evento(conexion_migracion, e["tramite"], e["usuario"])
    verificar_diferidas(conexion_migracion)  # TRUNCATE no admite verificaciones pendientes
    rechaza(
        conexion_migracion,
        sentencia,
        {"v": e["version"], "ev": evento},
        coincide="es inmutable",
    )


def test_rnf_04_privilegios_de_borrado_de_la_aplicacion(
    conexion_aplicacion: Connection, configuracion_tests: Any
) -> None:
    privilegios = {
        tabla: conexion_aplicacion.execute(
            text(
                "SELECT has_table_privilege(:app, :tabla, 'DELETE'), "
                "has_table_privilege(:app, :tabla, 'TRUNCATE')"
            ),
            {"app": configuracion_tests.bd_usuario, "tabla": f"atlas.{tabla}"},
        ).one()
        for tabla in TABLAS_DEL_NUCLEO
    }
    # Solo usuario_rol representa la asignación actual de roles.
    assert {t for t, (borra, vacia) in privilegios.items() if borra or vacia} == {"usuario_rol"}
    assert privilegios["usuario_rol"] == (True, False)


def test_rf_07_aplicacion_actualiza_estado_de_incorporacion(
    conexion_aplicacion: Connection,
) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    tramite = datos.crear_tramite(conexion_aplicacion, usuario)
    archivo = datos.crear_archivo(conexion_aplicacion, tramite, usuario, estado="pendiente")
    conexion_aplicacion.execute(
        text("UPDATE atlas.archivo SET estado_incorporacion = 'descartado' WHERE id = :a"),
        {"a": archivo},
    )


# --- RF-03, RF-25, RF-26, RF-21: restricciones de valores ------------------


def test_rf_26_cancelacion_exige_motivo(conexion_aplicacion: Connection) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    tramite = datos.crear_tramite(conexion_aplicacion, usuario)
    rechaza(
        conexion_aplicacion,
        "UPDATE atlas.tramite SET estado = 'cancelado' WHERE id = :t",
        {"t": tramite},
        coincide="ck_tramite_motivo_si_cancelado",
    )
    rechaza(
        conexion_aplicacion,
        "UPDATE atlas.tramite SET motivo_cancelacion = 'sin cancelar' WHERE id = :t",
        {"t": tramite},
        coincide="ck_tramite_motivo_si_cancelado",
    )
    conexion_aplicacion.execute(
        text(
            "UPDATE atlas.tramite SET estado = 'cancelado', "
            "motivo_cancelacion = 'El proceso dejó de corresponder' WHERE id = :t"
        ),
        {"t": tramite},
    )


@pytest.mark.parametrize(
    ("sentencia", "restriccion"),
    [
        ("UPDATE atlas.tramite SET estado = 'archivado' WHERE id = :t", "ck_tramite_estado"),
        ("UPDATE atlas.tramite SET titulo = '   ' WHERE id = :t", "ck_tramite_titulo_no_vacio"),
    ],
)
def test_rf_03_valores_del_tramite(
    conexion_aplicacion: Connection, sentencia: str, restriccion: str
) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    tramite = datos.crear_tramite(conexion_aplicacion, usuario)
    rechaza(conexion_aplicacion, sentencia, {"t": tramite}, coincide=restriccion)


def test_rf_03_tramite_descripcion_opcional_y_fechas(conexion_aplicacion: Connection) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    tramite = datos.crear_tramite(conexion_aplicacion, usuario)
    conexion_aplicacion.execute(
        text("UPDATE atlas.tramite SET actualizado_en = '2000-01-01' WHERE id = :t"),
        {"t": tramite},
    )
    fila = conexion_aplicacion.execute(
        text(
            "SELECT descripcion, estado, actualizado_en = now() AS actualizado "
            "FROM atlas.tramite WHERE id = :t"
        ),
        {"t": tramite},
    ).one()
    assert fila.descripcion is None
    assert fila.estado == EstadoTramite.BORRADOR
    assert fila.actualizado  # el trigger fija la fecha de última actualización (RF-03)


@pytest.mark.parametrize(
    ("estado", "externo"), [("suprimida", "sub-conservado"), ("habilitada", None)]
)
def test_rf_25_supresion_elimina_el_identificador_externo(
    conexion_aplicacion: Connection, estado: str, externo: str | None
) -> None:
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.usuario (identificador_externo, estado) VALUES (:e, :s)",
        {"e": externo, "s": estado},
        coincide="ck_usuario_suprimida_sin_identificador",
    )


def test_rf_25_supresion_conserva_id_interno_y_referencias(conexion_aplicacion: Connection) -> None:
    e = datos.escenario_documento(conexion_aplicacion)
    conexion_aplicacion.execute(
        text(
            "UPDATE atlas.usuario SET estado = 'suprimida', identificador_externo = NULL "
            "WHERE id = :u"
        ),
        {"u": e["usuario"]},
    )
    responsable = conexion_aplicacion.execute(
        text("SELECT responsable_id FROM atlas.tramite WHERE id = :t"), {"t": e["tramite"]}
    ).scalar_one()
    assert responsable == e["usuario"]


def test_autorizacion_de_cierre_por_defecto_ausente(
    conexion_aplicacion: Connection,
) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    autorizado = conexion_aplicacion.execute(
        text("SELECT autorizacion_cierre FROM atlas.usuario WHERE id = :u"), {"u": usuario}
    ).scalar_one()
    assert autorizado is False


def test_rf_25_rol_fuera_del_catalogo_rechazado(conexion_aplicacion: Connection) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.usuario_rol (usuario_id, rol) VALUES (:u, 'firmante')",
        {"u": usuario},
        coincide="ck_usuario_rol_rol",
    )


@pytest.mark.parametrize(
    ("columna", "valor", "restriccion"),
    [
        ("formato", "xlsx", "ck_archivo_formato"),
        ("huella", "NO-ES-SHA256", "ck_archivo_huella_sha256"),
        ("tamano_bytes", 0, "ck_archivo_tamano_positivo"),
    ],
)
def test_valores_del_archivo(
    conexion_aplicacion: Connection, columna: str, valor: object, restriccion: str
) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    tramite = datos.crear_tramite(conexion_aplicacion, usuario)
    valores: dict[str, object] = {
        "formato": "pdf",
        "huella": "a" * 64,
        "tamano_bytes": 10,
        columna: valor,
    }
    rechaza(
        conexion_aplicacion,
        "INSERT INTO atlas.archivo (tramite_id, clave_objeto, huella, nombre, formato,"
        " tamano_bytes, cargado_por_id) VALUES (:t, 'clave-unica-prueba', :huella, 'x.pdf',"
        " :formato, :tamano_bytes, :u)",
        {"t": tramite, "u": usuario, **valores},
        coincide=restriccion,
    )


def test_rf_21_evento_de_sistema_sin_actor_y_de_usuario_con_actor(
    conexion_aplicacion: Connection,
) -> None:
    usuario = datos.crear_usuario(conexion_aplicacion)
    insertar = (
        "INSERT INTO atlas.evento_auditoria (actor_id, actor_tipo, entidad_tipo, entidad_id,"
        " accion, resultado) VALUES (:a, :t, 'usuario', 1, 'rol_otorgado', 'exito')"
    )
    rechaza(conexion_aplicacion, insertar, {"a": None, "t": "usuario"}, coincide="actor_coherente")
    rechaza(
        conexion_aplicacion, insertar, {"a": usuario, "t": "sistema"}, coincide="actor_coherente"
    )
    conexion_aplicacion.execute(text(insertar), {"a": None, "t": "sistema"})
    conexion_aplicacion.execute(text(insertar), {"a": usuario, "t": "usuario"})
