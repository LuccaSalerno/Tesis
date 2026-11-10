"""Lambda privada de operaciones (RC-P10-15, V-DB, V-MT, DO-2026-10-22-OPS P3).

Sin AWS: Secrets Manager y Step Functions simulados con moto, PostgreSQL real. La
inicialización privilegiada se prueba contra un superusuario solo si la CI lo ofrece
(`ATLAS_PRUEBAS_PG_SUPERUSUARIO`); en RDS se verifica en la sesión autorizada (V-DB).
"""

import json
import os
import uuid
from typing import Any

import psycopg
import pytest
from alembic.script import ScriptDirectory
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from atlas.configuracion import Configuracion, ErrorConfiguracion
from atlas.integraciones.aws import crear_cliente
from atlas.operacion import lambda_operaciones as ops
from atlas.persistencia.motor import crear_motor
from tests import datos
from tests.conftest import configuracion_sin_base, lineas_registro

SUPERUSUARIO = os.environ.get("ATLAS_PRUEBAS_PG_SUPERUSUARIO")


def test_v_db_sentencias_sin_delete_y_con_rds_iam() -> None:
    n = ops.Nombres(base="pfi_demo", app="atlas_demo_app", migracion="atlas_demo_migracion")
    servidor = [s.as_string() for s in ops.sentencias_servidor(n)]
    base = [s.as_string() for s in ops.sentencias_base(n)]
    assert 'REVOKE ALL ON DATABASE "pfi_demo" FROM PUBLIC' in servidor
    # DIF-95: rds_iam al final, cuando ya no se abre otra conexión maestra.
    assert not any("rds_iam" in s for s in servidor)
    assert base[-2:] == [
        'REVOKE "atlas_demo_migracion" FROM CURRENT_USER',
        'GRANT rds_iam TO "atlas_demo_migracion", "atlas_demo_app"',
    ]
    assert any("GRANT SELECT, INSERT, UPDATE ON TABLES" in s for s in base)
    assert not any("DELETE" in s or "TRUNCATE" in s for s in servidor + base)


class ConexionFalsa:
    def __init__(self, existe: bool, ejecutadas: list[tuple[str, Any]]) -> None:
        self.existe = existe
        self.ejecutadas = ejecutadas

    def __enter__(self) -> "ConexionFalsa":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sentencia: Any, parametros: Any = None) -> Any:
        self.ejecutadas.append((str(sentencia), parametros))
        existe = self.existe

        class Resultado:
            def fetchone(self) -> tuple[int] | None:
                return (1,) if existe else None

        return Resultado()


def _configuracion_ops(**campos: Any) -> Configuracion:
    return configuracion_sin_base(bd_usuario_migracion="atlas_demo_migracion", **campos)


def test_v_db_inicializar_se_niega_si_la_base_existe() -> None:
    ejecutadas: list[tuple[str, Any]] = []
    with pytest.raises(ops.ErrorOperacion, match="base_ya_inicializada"):
        ops.inicializar_base(_configuracion_ops(), lambda _: ConexionFalsa(True, ejecutadas))
    assert len(ejecutadas) == 1  # solo la comprobación


def test_v_db_inicializar_ejecuta_servidor_y_base_en_orden() -> None:
    ejecutadas: list[tuple[str, Any]] = []
    bases: list[str] = []

    def conectar(base: str) -> ConexionFalsa:
        bases.append(base)
        return ConexionFalsa(False, ejecutadas)

    resultado = ops.inicializar_base(_configuracion_ops(), conectar)
    assert bases == ["postgres", "sin_base"]
    # DIF-95: después de rds_iam no hay más sentencias ni conexiones con el maestro.
    assert "rds_iam" in ejecutadas[-1][0]
    assert sum("rds_iam" in sentencia for sentencia, _ in ejecutadas) == 1
    assert resultado == {"base": "sin_base", "usuarios": ["atlas_demo_migracion", "nadie"]}
    n = ops.nombres(_configuracion_ops())
    assert len(ejecutadas) == 1 + len(ops.sentencias_servidor(n)) + len(ops.sentencias_base(n))


def test_v_db_nombres_exigen_usuario_de_migracion() -> None:
    with pytest.raises(ErrorConfiguracion):
        ops.nombres(configuracion_sin_base())


def test_rc_p10_15_credencial_maestra_desde_secrets_manager(
    moto_local: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    configuracion = _configuracion_ops(
        aws_endpoint_url=moto_local, bd_host_migracion="instancia.ejemplo.local"
    )
    with pytest.raises(ErrorConfiguracion, match="SECRETO_MAESTRO"):
        ops.conector_maestro(configuracion)
    secreto = crear_cliente(configuracion, "secretsmanager").create_secret(
        Name=f"rds-maestro-{uuid.uuid4()}",
        SecretString=json.dumps({"username": "maestro", "password": "ficticia"}),
    )
    capturadas: list[str] = []
    monkeypatch.setattr(ops.psycopg, "connect", lambda info, **_: capturadas.append(info))
    conectar = ops.conector_maestro(
        configuracion.model_copy(update={"ops_secreto_maestro_arn": secreto["ARN"]})
    )
    conectar("postgres")
    assert "host=instancia.ejemplo.local" in capturadas[0]
    assert "user=maestro" in capturadas[0] and "dbname=postgres" in capturadas[0]


@pytest.mark.integracion
@pytest.mark.skipif(SUPERUSUARIO is None, reason="Requiere un superusuario de PostgreSQL (CI)")
def test_v_db_inicializacion_real_en_postgresql_16() -> None:
    nombre = f"ops_{uuid.uuid4().hex[:8]}"
    n = ops.Nombres(base=nombre, app=f"{nombre}_app", migracion=f"{nombre}_migracion")
    configuracion = configuracion_sin_base(
        bd_nombre=n.base, bd_usuario=n.app, bd_usuario_migracion=n.migracion
    )

    def conectar(base: str) -> Any:
        return psycopg.connect(f"{SUPERUSUARIO} dbname={base}", autocommit=True)

    with conectar("postgres") as conexion:
        conexion.execute(
            "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rds_iam')"
            " THEN CREATE ROLE rds_iam; END IF; END $$"
        )
    try:
        ops.inicializar_base(configuracion, conectar)
        with conectar(n.base) as conexion:
            dueno = conexion.execute(
                "SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname = 'atlas'"
            ).fetchone()
            vector = conexion.execute(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
            publico = conexion.execute(
                "SELECT has_database_privilege('public', %s, 'CONNECT')", (n.base,)
            ).fetchone()
            # DIF-95: el maestro no conserva la pertenencia explícita al usuario de migración.
            pertenece = conexion.execute(
                "SELECT count(*) FROM pg_auth_members WHERE roleid = %s::regrole"
                " AND member = current_user::regrole",
                (n.migracion,),
            ).fetchone()
            iam = conexion.execute(
                "SELECT count(*) FROM pg_auth_members WHERE roleid = 'rds_iam'::regrole"
                " AND member IN (%s::regrole, %s::regrole)",
                (n.migracion, n.app),
            ).fetchone()
        assert dueno == (n.migracion,) and vector == (1,) and publico == (False,)
        assert pertenece == (0,) and iam == (2,)
        with pytest.raises(ops.ErrorOperacion, match="base_ya_inicializada"):
            ops.inicializar_base(configuracion, conectar)
    finally:
        with conectar("postgres") as conexion:
            conexion.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(n.base)))
            for rol in (n.app, n.migracion):
                conexion.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(rol)))


# --- Migraciones, administrador y drenaje contra la base de pruebas ---------------------


@pytest.mark.integracion
def test_rc_p10_15_estado_y_migracion_idempotente(base_migrada: Configuracion) -> None:
    cabeza = ScriptDirectory.from_config(ops.configuracion_alembic(base_migrada)).get_current_head()
    estado = ops.estado_migraciones(base_migrada)
    assert estado["al_dia"] is True and estado["revision_actual"] == cabeza
    resultado = ops.migrar(base_migrada)
    assert resultado["revision_anterior"] == resultado["revision_actual"] == cabeza


@pytest.mark.integracion
def test_dt_aut_02_crear_administrador_una_sola_vez(base_reiniciada: Configuracion) -> None:
    sub = f"sub-{uuid.uuid4()}"
    primero = ops.ejecutar(
        {"accion": "crear_administrador", "identificador_externo": sub}, base_reiniciada
    )
    assert isinstance(primero["usuario_id"], int)
    with pytest.raises(ops.ErrorOperacion, match="administrador_ya_existe"):
        ops.ejecutar(
            {"accion": "crear_administrador", "identificador_externo": "otro"}, base_reiniciada
        )
    with pytest.raises(ops.ErrorOperacion, match="falta_identificador"):
        ops.ejecutar({"accion": "crear_administrador"}, base_reiniciada)


@pytest.mark.integracion
def test_v_mt_verificar_drenaje_cuenta_lo_pendiente(base_migrada: Configuracion) -> None:
    resultado = ops.ejecutar({"accion": "verificar_drenaje"}, base_migrada)
    claves = ("urls_vigentes", "cargas_pendientes", "trabajos_abiertos", "ejecuciones_activas")
    assert all(isinstance(resultado[c], int) for c in claves)
    assert resultado["drenado"] is (not any(resultado[c] for c in claves))


@pytest.mark.integracion
def test_rc_p10_15_ejecutar_despacha_las_acciones(base_migrada: Configuracion) -> None:
    assert ops.ejecutar({"accion": "estado_migraciones"}, base_migrada)["al_dia"] is True
    assert ops.ejecutar({"accion": "migrar"}, base_migrada)["al_dia"] is True
    with pytest.raises(ops.ErrorOperacion, match="base_ya_inicializada"):
        ops.ejecutar(
            {"accion": "inicializar_base"},
            base_migrada,
            conectar_maestro=lambda _: lambda __: ConexionFalsa(True, []),
        )


def test_rnf_09_manejar_no_filtra_mensajes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(ops, "obtener_configuracion", configuracion_sin_base)
    assert ops.manejar({"accion": "borrar_todo"}, None) == {
        "accion": "borrar_todo",
        "resultado": "rechazada",
        "codigo": "accion_desconocida",
    }

    def explotar(*_: Any, **__: Any) -> Any:
        raise RuntimeError("password=secreta host=instancia")

    monkeypatch.setattr(ops, "ejecutar", explotar)
    respuesta = ops.manejar({"accion": "migrar"}, None)
    assert respuesta == {"accion": "migrar", "resultado": "fallida", "codigo": "RuntimeError"}
    monkeypatch.setattr(ops, "ejecutar", lambda *_: {"al_dia": True})
    assert ops.manejar({"accion": "estado_migraciones"}, None)["resultado"] == "completada"
    salida = capsys.readouterr().out
    assert "secreta" not in salida
    eventos = {r["evento"] for r in lineas_registro(salida)}
    assert {"operacion_rechazada", "operacion_fallida", "operacion_completada"} <= eventos


# --- Fotos de la base para la demo (DO-2026-11-09-ESTADOS-DEMO, temporal) -------------------


def _offline(_: Configuracion) -> ops.EstadoOperativo:
    return ops.EstadoOperativo.OFFLINE


DRENADO = {
    "urls_vigentes": 0,
    "cargas_pendientes": 0,
    "trabajos_abiertos": 0,
    "ejecuciones_activas": 0,
    "drenado": True,
}


@pytest.fixture
def drenado(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Moto conserva ejecuciones de otras pruebas: el drenaje se simula por prueba."""
    estado = dict(DRENADO)
    monkeypatch.setattr(ops, "verificar_drenaje", lambda _: estado)
    return estado


def _foto(configuracion: Configuracion, accion: str, nombre: str = "semilla", **extra: Any) -> Any:
    evento = {"accion": accion, "nombre": nombre, "confirmar": configuracion.bd_nombre, **extra}
    return ops.ejecutar(evento, configuracion, leer_estado=_offline)


def _conteo(motor: Any, tabla: str) -> int:
    with motor.connect() as conexion:
        consulta = text(f"SELECT count(*) FROM atlas.{tabla}")  # noqa: S608 (tabla fija)
        return int(conexion.execute(consulta).scalar_one())


@pytest.mark.integracion
def test_demo_restablecer_vuelve_a_la_foto_y_reactiva_las_protecciones(
    base_reiniciada: Configuracion, drenado: dict[str, Any]
) -> None:
    motor = crear_motor(base_reiniciada, migracion=True, poolclass=NullPool)
    _foto(base_reiniciada, "guardar_estado", nombre="vacia")
    try:
        with motor.begin() as conexion:
            escenario = datos.escenario_documento(conexion)
        guardada = _foto(base_reiniciada, "guardar_estado")
        assert guardada["filas"] >= 4 and guardada["estado"] == "semilla"

        # La demo agrega un trámite; restablecer lo quita y conserva el documento con su
        # versión vigente (clave foránea circular y diferible).
        with motor.begin() as conexion:
            extra = datos.crear_tramite(conexion, escenario["usuario"], "Intento de grabación")
        assert _conteo(motor, "tramite") == 2
        assert _foto(base_reiniciada, "restablecer_estado")["filas"] == guardada["filas"]
        assert _conteo(motor, "tramite") == 1 and _conteo(motor, "documento") == 1

        with motor.begin() as conexion:
            # Las identidades no retroceden: el próximo trámite no repite el del intento.
            assert datos.crear_tramite(conexion, escenario["usuario"]) > extra
            # Las protecciones de RNF-04 vuelven a regir después de restablecer.
            deshabilitados = conexion.execute(
                text(
                    "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid"
                    " JOIN pg_namespace n ON n.oid = c.relnamespace"
                    " WHERE n.nspname = 'atlas' AND NOT t.tgisinternal AND t.tgenabled = 'D'"
                )
            ).scalar_one()
            assert deshabilitados == 0
        with pytest.raises(Exception, match="es inmutable: TRUNCATE"), motor.begin() as conexion:
            conexion.execute(text("TRUNCATE atlas.validacion_humana CASCADE"))
    finally:
        # La base de pruebas queda como la dejó `base_reiniciada`.
        _foto(base_reiniciada, "restablecer_estado", nombre="vacia")
        with motor.begin() as conexion:
            conexion.execute(text("DROP SCHEMA IF EXISTS atlas_estado_semilla CASCADE"))
            conexion.execute(text("DROP SCHEMA IF EXISTS atlas_estado_vacia CASCADE"))
        motor.dispose()


@pytest.mark.integracion
def test_demo_fotos_rechazan_sin_resguardos(
    base_reiniciada: Configuracion, drenado: dict[str, Any]
) -> None:
    def rechaza(
        codigo: str,
        evento: dict[str, Any],
        configuracion: Configuracion = base_reiniciada,
        leer_estado: Any = _offline,
    ) -> None:
        with pytest.raises(ops.ErrorOperacion, match=codigo):
            ops.ejecutar(evento, configuracion, leer_estado=leer_estado)

    base = {
        "accion": "restablecer_estado",
        "nombre": "semilla",
        "confirmar": base_reiniciada.bd_nombre,
    }
    rechaza("confirmacion_invalida", {**base, "confirmar": "otra_base"})
    rechaza("falta_nombre", {**base, "nombre": None})
    rechaza("operacion_no_offline", base, leer_estado=lambda _: ops.EstadoOperativo.ACTIVE)
    # Un despliegue AWS (sin endpoint local) que no es demo nunca admite fotos.
    rechaza("solo_en_demo", base, base_reiniciada.model_copy(update={"aws_endpoint_url": None}))
    rechaza("nombre_de_estado_invalido", {**base, "nombre": "Semilla; DROP"})
    rechaza("estado_inexistente", {**base, "nombre": "nunca_guardado"})
    # Con un procesamiento en curso no se restablece; para guardar, la base tiene que estar
    # drenada del todo.
    drenado.update(ejecuciones_activas=1, drenado=False)
    rechaza("operacion_no_drenada", base)
    drenado.update(ejecuciones_activas=0, cargas_pendientes=1)
    rechaza("operacion_no_drenada", {**base, "accion": "guardar_estado"})
    drenado.update(DRENADO)

    motor = crear_motor(base_reiniciada, migracion=True, poolclass=NullPool)
    try:
        _foto(base_reiniciada, "guardar_estado", nombre="vieja")
        with motor.begin() as conexion:
            conexion.execute(text("ALTER TABLE atlas_estado_vieja.tramite DROP COLUMN titulo"))
        rechaza("estado_incompatible_con_el_esquema", {**base, "nombre": "vieja"})
    finally:
        with motor.begin() as conexion:
            conexion.execute(text("DROP SCHEMA IF EXISTS atlas_estado_vieja CASCADE"))
        motor.dispose()
