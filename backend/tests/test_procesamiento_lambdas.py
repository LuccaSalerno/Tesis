"""Funciones Lambda del procesamiento contra PostgreSQL real y S3 simulado (sin AWS).

Se reemplaza solo la configuración del proceso; Textract y el modelo no se invocan
(P1). Cubre el despacho de cada función, la transacción de la de persistencia y la
salida de errores sin contenido (regla 5 de AGENTS.md).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from atlas.procesamiento import lambdas
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from tests import archivos
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, cargar, crear_tramite

pytestmark = pytest.mark.integracion


@pytest.fixture
def entorno(
    base_migrada: Configuracion, motor_aplicacion: Engine, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Contexto]:
    monkeypatch.setattr(lambdas, "obtener_configuracion", lambda: base_migrada)
    lambdas._dependencias.cache_clear()
    lambdas._fabrica_sesiones.cache_clear()
    aplicacion = crear_aplicacion(base_migrada)
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
    aplicacion.state.motor.dispose()
    lambdas._fabrica_sesiones().kw["bind"].dispose()
    lambdas._dependencias.cache_clear()
    lambdas._fabrica_sesiones.cache_clear()


def trabajo(ctx: Contexto, formato: str = "docx") -> tuple[int, dict[str, Any]]:
    tramite = crear_tramite(ctx)
    datos = archivos.CONTRATO_DOCX.read_bytes() if formato == "docx" else archivos.pdf()
    archivo = cargar(ctx, tramite["id"], datos, formato=formato)
    with ctx.motor.connect() as conexion:
        trabajo_id = conexion.execute(
            text("SELECT id FROM atlas.trabajo_procesamiento WHERE archivo_id = :a"),
            {"a": archivo["id"]},
        ).scalar_one()
    return int(trabajo_id), archivo


def estado_trabajo(ctx: Contexto, trabajo_id: int) -> tuple[str, str | None]:
    with ctx.motor.connect() as conexion:
        fila = conexion.execute(
            text("SELECT estado, codigo_error FROM atlas.trabajo_procesamiento WHERE id = :t"),
            {"t": trabajo_id},
        ).one()
    return fila.estado, fila.codigo_error


def test_dt_proc_lambdas_preparar_y_normalizar_docx(entorno: Contexto) -> None:
    trabajo_id, _ = trabajo(entorno)
    base = {"trabajo_id": trabajo_id, "intento": 1}
    preparado = lambdas.manejar_persistencia({"etapa": "preparar", **base}, None)
    assert preparado["formato"] == "docx"
    assert preparado["clave_objeto"].startswith("cargas-temporales/")
    normalizado = lambdas.manejar_procesamiento(
        {"etapa": "normalizar_docx", "clave_objeto": preparado["clave_objeto"], **base}, None
    )
    assert normalizado == {"contenido": f"resultados/{trabajo_id}/1/contenido.json"}


def test_dt_proc_lambda_de_persistencia_registra_el_fallo_con_su_codigo(entorno: Contexto) -> None:
    trabajo_id, _ = trabajo(entorno, "pdf")
    respuesta = lambdas.manejar_persistencia(
        {
            "etapa": "registrar_fallo",
            "trabajo_id": trabajo_id,
            "intento": 1,
            "error": "ErrorPermanente",
            "causa": '{"errorMessage": "textract_fallido", "errorType": "ErrorPermanente"}',
        },
        None,
    )
    assert respuesta == {"registrado": True}
    assert estado_trabajo(entorno, trabajo_id) == ("fallido", "textract_fallido")


def test_dt_proc_lambda_de_persistencia_revierte_ante_error(entorno: Contexto) -> None:
    """Si faltan los resultados en S3, la transacción se revierte y el error es reintentable."""
    trabajo_id, _ = trabajo(entorno)
    with pytest.raises(ErrorTransitorio, match="s3_lectura_fallida"):
        lambdas.manejar_persistencia(
            {
                "etapa": "persistir",
                "trabajo_id": trabajo_id,
                "intento": 1,
                "clasificacion": f"resultados/{trabajo_id}/1/no-existe.json",
                "extraccion": f"resultados/{trabajo_id}/1/no-existe.json",
            },
            None,
        )
    assert estado_trabajo(entorno, trabajo_id) == ("en_ejecucion", None)


def test_dt_proc_lambda_de_procesamiento_rechaza_etapas_de_persistencia(entorno: Contexto) -> None:
    trabajo_id, _ = trabajo(entorno)
    with pytest.raises(ErrorPermanente, match="evento_invalido"):
        lambdas.manejar_procesamiento(
            {"etapa": "persistir", "trabajo_id": trabajo_id, "intento": 1}, None
        )
    with pytest.raises(ErrorPermanente, match="evento_invalido"):
        lambdas.manejar_persistencia(
            {"etapa": "clasificar", "trabajo_id": trabajo_id, "intento": 1}, None
        )


def test_dt_proc_despacho_coincide_con_las_etapas_declaradas(
    entorno: Contexto, monkeypatch: pytest.MonkeyPatch
) -> None:
    vistas: dict[str, set[str]] = {}

    def capturar(_: dict[str, Any], disponibles: dict[str, Any]) -> None:
        vistas.setdefault("ultima", set()).clear()
        vistas["ultima"].update(disponibles)

    monkeypatch.setattr(lambdas, "ejecutar", capturar)
    lambdas.manejar_procesamiento({}, None)
    assert vistas["ultima"] == lambdas.ETAPAS_PROCESAMIENTO
    lambdas.manejar_persistencia({}, None)
    assert vistas["ultima"] == lambdas.ETAPAS_PERSISTENCIA


def test_dt_proc_consultar_textract_no_recibe_mas_que_el_identificador(
    entorno: Contexto, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Analizador:
        def estado(self, job_id: str) -> str:
            assert job_id == "job-1"
            return "en_curso"

    dependencias = lambdas._dependencias()
    monkeypatch.setitem(dependencias, "analizador", Analizador())
    respuesta = lambdas.manejar_procesamiento(
        {"etapa": "consultar_textract", "trabajo_id": 1, "intento": 1, "job_id": "job-1"}, None
    )
    assert respuesta == {"estado": "en_curso"}
