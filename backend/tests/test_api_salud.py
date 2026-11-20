"""API: estado del proceso y registro de solicitudes (RNF-09)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from atlas.api.middleware import CABECERA_SOLICITUD
from atlas.principal import crear_aplicacion
from tests.conftest import configuracion_sin_base, lineas_registro

VALOR_DOCUMENTAL = "CUIT 30-71234567-8"


def nueva_aplicacion() -> FastAPI:
    return crear_aplicacion(configuracion_sin_base())


def test_salud_responde_sin_base() -> None:
    aplicacion = nueva_aplicacion()
    respuesta = TestClient(aplicacion).get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "entorno": "tests", "operacion": "active"}
    assert respuesta.headers[CABECERA_SOLICITUD]


def test_entorno_no_se_elige_por_peticion() -> None:
    aplicacion = nueva_aplicacion()
    respuesta = TestClient(aplicacion).get(
        "/salud", params={"entorno": "demo"}, headers={"x-atlas-entorno": "demo"}
    )
    assert respuesta.json()["entorno"] == "tests"


def test_rnf_09_registro_usa_plantilla_de_ruta_sin_valores(
    capsys: pytest.CaptureFixture[str],
) -> None:
    aplicacion = nueva_aplicacion()

    @aplicacion.get("/eco/{dato}")
    def eco(dato: str) -> dict[str, str]:
        return {"dato": dato}

    TestClient(aplicacion).get(f"/eco/{VALOR_DOCUMENTAL}", params={"q": VALOR_DOCUMENTAL})
    (linea,) = [
        r for r in lineas_registro(capsys.readouterr().out) if r["evento"] == "solicitud_atendida"
    ]
    assert linea["ruta"] == "/eco/{dato}"
    assert linea["estado_http"] == 200
    assert VALOR_DOCUMENTAL not in str(linea)


def test_error_no_controlado_responde_generico_sin_filtrar_valores(
    capsys: pytest.CaptureFixture[str],
) -> None:
    aplicacion = nueva_aplicacion()

    @aplicacion.get("/falla")
    def falla() -> None:
        raise ValueError(VALOR_DOCUMENTAL)

    respuesta = TestClient(aplicacion).get("/falla")
    assert respuesta.status_code == 500
    assert respuesta.json() == {
        "detalle": "Error interno",
        "solicitud_id": respuesta.headers[CABECERA_SOLICITUD],
    }
    registros = [
        r for r in lineas_registro(capsys.readouterr().out) if r["registrador"] == "atlas.api"
    ]
    assert {r["evento"] for r in registros} == {"error_no_controlado", "solicitud_atendida"}
    assert any(r.get("codigo_error") == "ValueError" for r in registros)
    assert VALOR_DOCUMENTAL not in str(registros)


def test_verificacion_previa_de_cors_responde_204_sin_token() -> None:
    """La ruta OPTIONS sin autorizador de API Gateway llega aquí (sesión e90-ensayo-2)."""
    cliente = TestClient(nueva_aplicacion())
    previa = cliente.options(
        "/usuarios/yo",
        headers={"Origin": "http://localhost:4173", "Access-Control-Request-Method": "GET"},
    )
    assert previa.status_code == 204 and previa.content == b""
    # Un OPTIONS que no es verificación previa sigue el camino normal.
    assert cliente.options("/usuarios/yo").status_code in (401, 405)
