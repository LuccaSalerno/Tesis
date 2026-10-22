"""Vencimiento de cargas pendientes, traslado al prefijo definitivo y limpieza en S3.

DO-2026-10-22-CARGAS (DT-CARGA-01), RF-04, RF-05, RF-07, RF-21. Contra PostgreSQL
real y S3 versionado simulado con moto; sin AWS.
"""

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from atlas.configuracion import Configuracion
from atlas.integraciones.aws import AlmacenS3, crear_cliente
from atlas.integraciones.ciclo_vida_s3 import (
    PREFIJO_CARGAS_TEMPORALES,
    PREFIJO_DOCUMENTOS,
    REGLAS_CICLO_VIDA,
)
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.principal import crear_aplicacion
from atlas.servicios import cargas
from tests import archivos
from tests.conftest import BUCKET_PRUEBA
from tests.datos import crear_cuenta, portador
from tests.flujo_api import (
    Contexto,
    autorizar,
    cargar,
    contar,
    crear_tramite,
    eventos_del_tramite,
    incorporar,
    transferir,
)

pytestmark = pytest.mark.integracion

VIGENCIA = 24 * 60 * 60


@pytest.fixture
def entorno(base_reiniciada: Configuracion) -> Iterator[tuple[Any, Contexto, Any]]:
    """Base recreada desde cero: la limpieza recorre todas las cargas, así sus conteos son
    exactos. Devuelve la aplicación, el contexto del responsable y el cliente S3."""
    aplicacion = crear_aplicacion(base_reiniciada)
    motor = aplicacion.state.motor
    usuario_id, sub = crear_cuenta(motor, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield (
            aplicacion,
            Contexto(cliente, motor, usuario_id, portador(sub)),
            crear_cliente(base_reiniciada, "s3"),
        )
    motor.dispose()


def versiones(s3: Any, clave: str) -> int:
    respuesta = s3.list_object_versions(Bucket=BUCKET_PRUEBA, Prefix=clave)
    return sum(
        1
        for v in respuesta.get("Versions", []) + respuesta.get("DeleteMarkers", [])
        if v["Key"] == clave
    )


def fila(motor: Engine, consulta: str, **parametros: Any) -> Any:
    with motor.connect() as conexion:
        return conexion.execute(text(consulta), parametros).one()


def limpiar(configuracion: Configuracion, ahora: datetime) -> cargas.ResumenLimpieza:
    motor = crear_motor(configuracion)
    try:
        with crear_fabrica_sesiones(motor)() as sesion:
            return cargas.limpiar_cargas_vencidas(
                sesion,
                AlmacenS3(crear_cliente(configuracion, "s3"), BUCKET_PRUEBA),
                vigencia_pendiente_s=VIGENCIA,
                ahora=ahora,
            )
    finally:
        motor.dispose()


# --- URL de 5 minutos y vigencia de 24 horas -----------------------------------------


def test_do_2026_10_22_url_prefirmada_vence_a_los_5_minutos(entorno: Any) -> None:
    _, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    carga = autorizar(ctx, tramite["id"], archivos.pdf())
    assert parse_qs(urlparse(carga["url"]).query)["X-Amz-Expires"] == ["300"]
    assert urlparse(carga["url"]).path.split("/", 2)[2].startswith(PREFIJO_CARGAS_TEMPORALES)


def test_do_2026_10_22_carga_pendiente_informa_su_vencimiento(entorno: Any) -> None:
    _, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    vence = datetime.fromisoformat(archivo["vence_en"]) - datetime.fromisoformat(
        archivo["cargado_en"]
    )
    assert vence == timedelta(hours=24)


def test_do_2026_10_22_carga_vencida_no_se_incorpora(entorno: Any) -> None:
    aplicacion, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    aplicacion.state.vigencia_carga_pendiente_s = 0  # equivale a haber superado las 24 h
    respuesta = incorporar(ctx, tramite["id"], archivo["id"])
    assert respuesta.status_code == 409
    assert "venció" in respuesta.json()["detalle"]
    assert contar(ctx.motor, "documento", tramite["id"]) == 0


# --- Traslado al prefijo definitivo ---------------------------------------------------


def test_do_2026_10_22_incorporacion_traslada_el_original_con_su_huella(entorno: Any) -> None:
    _, ctx, s3 = entorno
    tramite = crear_tramite(ctx)
    datos = archivos.CONTRATO_PDF.read_bytes()
    archivo = cargar(ctx, tramite["id"], datos)
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 201

    clave = fila(
        ctx.motor, "SELECT clave_objeto FROM atlas.archivo WHERE id = :a", a=archivo["id"]
    )[0]
    assert clave.startswith(PREFIJO_DOCUMENTOS)
    copia = s3.get_object(Bucket=BUCKET_PRUEBA, Key=clave)["Body"].read()
    assert hashlib.sha256(copia).hexdigest() == archivo["huella"]
    (listado,) = ctx.cliente.get(
        f"/tramites/{tramite['id']}/archivos", headers=ctx.encabezados
    ).json()
    assert listado["estado_incorporacion"] == "incorporado"
    assert listado["vence_en"] is None


def test_do_2026_10_22_copia_inconsistente_no_incorpora(entorno: Any) -> None:
    aplicacion, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())

    real = aplicacion.state.almacen

    class AlmacenAlterado:
        def __getattr__(self, nombre: str) -> Any:
            return getattr(real, nombre)

        def leer(self, clave: str) -> bytes:
            return b"%PDF-1.7 contenido distinto"

    aplicacion.state.almacen = AlmacenAlterado()
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 503
    estado, clave = fila(
        ctx.motor,
        "SELECT estado_incorporacion, clave_objeto FROM atlas.archivo WHERE id = :a",
        a=archivo["id"],
    )
    assert (estado, clave.startswith(PREFIJO_CARGAS_TEMPORALES)) == ("pendiente", True)
    assert contar(ctx.motor, "documento", tramite["id"]) == 0


@pytest.mark.parametrize(
    ("sentencia", "mensaje"),
    [
        (
            "UPDATE atlas.archivo SET clave_objeto = 'documentos/x' WHERE id = :a",
            "clave del objeto",
        ),
        (
            "UPDATE atlas.archivo SET estado_incorporacion = 'incorporado',"
            " clave_objeto = 'otro-prefijo/x' WHERE id = :a",
            "clave del objeto",
        ),
        ("UPDATE atlas.archivo SET huella = repeat('0', 64) WHERE id = :a", "huella"),
        ("UPDATE atlas.archivo SET cargado_en = now() - interval '2 days' WHERE id = :a", "huella"),
    ],
    ids=["clave_sin_incorporar", "prefijo_no_definitivo", "huella", "fecha_de_carga"],
)
def test_do_2026_10_22_archivo_protegido_incluso_para_el_propietario(
    entorno: Any, motor_migracion: Engine, sentencia: str, mensaje: str
) -> None:
    _, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    with pytest.raises(IntegrityError, match=mensaje), motor_migracion.begin() as conexion:
        conexion.execute(text(sentencia), {"a": archivo["id"]})


def test_do_2026_10_22_estado_final_no_cambia(entorno: Any) -> None:
    _, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 201
    with pytest.raises(IntegrityError, match="estado es final"), ctx.motor.begin() as conexion:
        conexion.execute(
            text("UPDATE atlas.archivo SET estado_incorporacion = 'vencido' WHERE id = :a"),
            {"a": archivo["id"]},
        )


# --- Limpieza segura e idempotente ----------------------------------------------------


def test_do_2026_10_22_limpieza_de_los_tres_casos_y_versiones_residuales(
    entorno: Any, base_reiniciada: Configuracion
) -> None:
    _, ctx, s3 = entorno
    tramite = crear_tramite(ctx)

    sin_confirmar = autorizar(ctx, tramite["id"], archivos.pdf())
    transferir(sin_confirmar, archivos.pdf())
    transferir(sin_confirmar, archivos.pdf())  # versión residual del mismo objeto
    pendiente = cargar(ctx, tramite["id"], archivos.pdf())
    incorporado = cargar(ctx, tramite["id"], archivos.CONTRATO_PDF.read_bytes())
    assert incorporar(ctx, tramite["id"], incorporado["id"]).status_code == 201

    claves = {
        nombre: fila(
            ctx.motor,
            "SELECT clave_objeto FROM atlas.autorizacion_carga WHERE id = :c",
            c=carga_id,
        )[0]
        for nombre, carga_id in (
            ("sin_confirmar", sin_confirmar["id"]),
            ("pendiente", _carga_de(ctx.motor, pendiente["id"])),
            ("incorporado", _carga_de(ctx.motor, incorporado["id"])),
        )
    }
    definitiva = fila(
        ctx.motor, "SELECT clave_objeto FROM atlas.archivo WHERE id = :a", a=incorporado["id"]
    )[0]
    assert versiones(s3, claves["sin_confirmar"]) == 2

    # Antes de las 24 h no se toca nada.
    assert limpiar(base_reiniciada, datetime.now(UTC)).revisadas == 0

    resumen = limpiar(base_reiniciada, datetime.now(UTC) + timedelta(hours=25))
    assert (resumen.revisadas, resumen.vencidas, resumen.objetos_limpiados) == (3, 1, 3)
    assert resumen.versiones_eliminadas == 4
    assert resumen.errores == []
    assert all(versiones(s3, clave) == 0 for clave in claves.values())

    # El documento confirmado queda intacto en el prefijo definitivo.
    copia = s3.get_object(Bucket=BUCKET_PRUEBA, Key=definitiva)["Body"].read()
    assert hashlib.sha256(copia).hexdigest() == incorporado["huella"]
    estados = {
        a["id"]: a["estado_incorporacion"]
        for a in ctx.cliente.get(
            f"/tramites/{tramite['id']}/archivos", headers=ctx.encabezados
        ).json()
    }
    assert estados == {pendiente["id"]: "vencido", incorporado["id"]: "incorporado"}
    assert incorporar(ctx, tramite["id"], pendiente["id"]).status_code == 409

    (vencimiento,) = [
        e for e in eventos_del_tramite(ctx.motor, tramite["id"]) if e["accion"] == "carga_vencida"
    ]
    assert (vencimiento["entidad_id"], vencimiento["actor_id"]) == (pendiente["id"], None)

    # Idempotente: una segunda ejecución no encuentra nada pendiente.
    segunda = limpiar(base_reiniciada, datetime.now(UTC) + timedelta(hours=26))
    assert (segunda.revisadas, segunda.vencidas, segunda.versiones_eliminadas) == (0, 0, 0)


def test_do_2026_10_22_confirmacion_tardia_se_difiere_hasta_su_vencimiento(
    entorno: Any, base_reiniciada: Configuracion, motor_migracion: Engine
) -> None:
    """Una carga confirmada cerca del límite de su autorización conserva sus 24 h
    para incorporarse: la limpieza no la marca vencida antes de tiempo."""
    _, ctx, s3 = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    carga_id = _carga_de(ctx.motor, archivo["id"])
    with motor_migracion.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE atlas.autorizacion_carga SET creada_en = now() - interval '23 hours'"
                " WHERE id = :c"
            ),
            {"c": carga_id},
        )
    resumen = limpiar(base_reiniciada, datetime.now(UTC) + timedelta(hours=2))
    assert (resumen.revisadas, resumen.diferidas, resumen.vencidas) == (1, 1, 0)
    clave = fila(
        ctx.motor, "SELECT clave_objeto FROM atlas.autorizacion_carga WHERE id = :c", c=carga_id
    )[0]
    assert versiones(s3, clave) == 1
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 201


def test_do_2026_10_22_multipartes_incompletas_solo_del_prefijo_temporal(
    entorno: Any, base_reiniciada: Configuracion
) -> None:
    _, _, s3 = entorno
    temporal = s3.create_multipart_upload(
        Bucket=BUCKET_PRUEBA, Key=f"{PREFIJO_CARGAS_TEMPORALES}tramites/0/incompleta"
    )
    definitiva = s3.create_multipart_upload(
        Bucket=BUCKET_PRUEBA, Key=f"{PREFIJO_DOCUMENTOS}tramites/0/ajena"
    )
    resumen = limpiar(base_reiniciada, datetime.now(UTC) + timedelta(hours=25))
    assert resumen.multipartes_abortadas == 1
    restantes = {
        u["UploadId"] for u in s3.list_multipart_uploads(Bucket=BUCKET_PRUEBA).get("Uploads", [])
    }
    assert temporal["UploadId"] not in restantes
    assert definitiva["UploadId"] in restantes
    s3.abort_multipart_upload(
        Bucket=BUCKET_PRUEBA, Key=definitiva["Key"], UploadId=definitiva["UploadId"]
    )


def test_do_2026_10_22_solo_se_liberan_claves_temporales(entorno: Any) -> None:
    aplicacion, _, _ = entorno
    with aplicacion.state.fabrica_sesiones() as sesion:
        assert cargas._clave_temporal_liberada(sesion, f"{PREFIJO_DOCUMENTOS}tramites/1/x") is False
        assert cargas._clave_temporal_liberada(sesion, "otra/clave") is False
        assert cargas._clave_temporal_liberada(sesion, f"{PREFIJO_CARGAS_TEMPORALES}libre") is True


# --- Regla S3 Lifecycle de respaldo ---------------------------------------------------


def test_do_2026_10_22_regla_lifecycle_de_2_dias_solo_sobre_cargas_temporales(
    entorno: Any,
) -> None:
    _, _, s3 = entorno
    reglas = s3.get_bucket_lifecycle_configuration(Bucket=BUCKET_PRUEBA)["Rules"]
    assert {r["ID"] for r in reglas} == {r["ID"] for r in REGLAS_CICLO_VIDA}
    assert all(r["Filter"]["Prefix"] == PREFIJO_CARGAS_TEMPORALES for r in reglas)
    (respaldo,) = [r for r in reglas if r["ID"] == "atlas-cargas-temporales-respaldo"]
    assert respaldo["Expiration"]["Days"] == 2
    assert respaldo["NoncurrentVersionExpiration"]["NoncurrentDays"] == 2
    assert respaldo["AbortIncompleteMultipartUpload"]["DaysAfterInitiation"] == 2
    assert not PREFIJO_DOCUMENTOS.startswith(PREFIJO_CARGAS_TEMPORALES)
    assert not PREFIJO_CARGAS_TEMPORALES.startswith(PREFIJO_DOCUMENTOS)


def _carga_de(motor: Engine, archivo_id: int) -> int:
    return int(
        fila(motor, "SELECT id FROM atlas.autorizacion_carga WHERE archivo_id = :a", a=archivo_id)[
            0
        ]
    )


def test_do_2026_10_22_herramienta_de_limpieza_es_idempotente(
    entorno: Any,
    base_reiniciada: Configuracion,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from atlas.herramientas import limpiar_cargas_vencidas

    _, ctx, _ = entorno
    tramite = crear_tramite(ctx)
    cargar(ctx, tramite["id"], archivos.pdf())
    # Vigencia nula: la carga recién registrada ya superó su plazo.
    configuracion = base_reiniciada.model_copy(update={"carga_vigencia_pendiente_s": 0})
    monkeypatch.setattr(limpiar_cargas_vencidas, "obtener_configuracion", lambda: configuracion)
    assert limpiar_cargas_vencidas.main([]) == 0
    assert "vencidas 1" in capsys.readouterr().out
    assert limpiar_cargas_vencidas.main([]) == 0
    assert "Revisadas 0" in capsys.readouterr().out
