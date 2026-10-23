"""Modo mantenimiento (RC-P10-09, V-MT) y despliegue en Lambda (DO-2026-10-22-OPS P2, P4, P5).

Sin AWS: el objeto de control vive en el S3 simulado por moto (DT-AWS-01).
"""

import asyncio
import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from atlas.configuracion import ErrorConfiguracion
from atlas.integraciones.aws import crear_cliente
from atlas.lambda_api import crear_manejador
from atlas.operacion.mantenimiento import (
    CLAVE_CONTROL,
    EstadoOperativo,
    LectorMantenimiento,
    admite,
)
from atlas.persistencia.motor import crear_motor
from atlas.principal import crear_aplicacion
from atlas.registro import configurar_registro
from tests.conftest import BUCKET_PRUEBA, configuracion_sin_base, lineas_registro


class Reloj:
    def __init__(self) -> None:
        self.ahora = 0.0

    def __call__(self) -> float:
        return self.ahora


def test_rc_p10_09_lector_usa_cache_y_deniega_lo_ilegible() -> None:
    contenido = {"valor": b'{"estado": "draining"}'}
    lecturas: list[int] = []

    def leer() -> bytes:
        lecturas.append(1)
        return contenido["valor"]

    reloj = Reloj()
    lector = LectorMantenimiento(leer, cache_s=15, reloj=reloj)
    assert lector.estado() == EstadoOperativo.DRAINING
    contenido["valor"] = b'{"estado": "desconocido"}'
    reloj.ahora = 10
    assert lector.estado() == EstadoOperativo.DRAINING  # todavía en caché
    reloj.ahora = 16
    assert lector.estado() is None  # inválido: se deniega
    assert len(lecturas) == 2


def test_rc_p10_09_objeto_ausente_se_deniega(capsys: pytest.CaptureFixture[str]) -> None:
    def leer() -> bytes:
        raise KeyError("NoSuchKey")

    configurar_registro("INFO")
    assert LectorMantenimiento(leer).estado() is None
    (linea,) = [r for r in lineas_registro(capsys.readouterr().out) if r["evento"]]
    assert linea["evento"] == "mantenimiento_ilegible" and linea["codigo_error"] == "KeyError"


@pytest.mark.parametrize(
    ("estado", "metodo", "ruta", "esperado"),
    [
        (EstadoOperativo.ACTIVE, "POST", "/tramites", True),
        (EstadoOperativo.DRAINING, "GET", "/tramites/1", True),
        (EstadoOperativo.DRAINING, "POST", "/tramites/1/cargas", False),
        (EstadoOperativo.DRAINING, "PUT", "/tareas/1/asignacion", False),
        (EstadoOperativo.OFFLINE, "GET", "/tramites", False),
        (EstadoOperativo.OFFLINE, "GET", "/salud", True),
        (None, "GET", "/tramites", False),
        (None, "GET", "/salud", True),
    ],
)
def test_rc_p10_09_matriz_de_admision(
    estado: EstadoOperativo | None, metodo: str, ruta: str, esperado: bool
) -> None:
    assert admite(estado, metodo, ruta) is esperado


@pytest.fixture
def control_s3(moto_local: str) -> Iterator[Any]:
    configuracion = configuracion_sin_base(
        aws_endpoint_url=moto_local, mantenimiento_fuente="s3", mantenimiento_cache_s=0
    )
    s3 = crear_cliente(configuracion, "s3")

    def fijar(estado: str | None) -> TestClient:
        if estado is None:
            s3.delete_object(Bucket=BUCKET_PRUEBA, Key=CLAVE_CONTROL)
        else:
            s3.put_object(
                Bucket=BUCKET_PRUEBA, Key=CLAVE_CONTROL, Body=json.dumps({"estado": estado})
            )
        return TestClient(crear_aplicacion(configuracion))

    yield fijar
    s3.delete_object(Bucket=BUCKET_PRUEBA, Key=CLAVE_CONTROL)


def test_v_mt_draining_admite_consultas_y_rechaza_cambios(control_s3: Any) -> None:
    cliente = control_s3("draining")
    salud = cliente.get("/salud")
    assert salud.json()["estado"] == "mantenimiento" and salud.json()["operacion"] == "draining"
    assert cliente.get("/tramites").status_code == 401  # pasa al dominio: falta el token
    rechazo = cliente.post("/tramites", json={"titulo": "x"})
    assert rechazo.status_code == 503
    assert rechazo.headers["retry-after"] == "300"
    assert rechazo.json()["detalle"].startswith("ATLAS está en mantenimiento")


def test_v_mt_offline_y_control_ausente_responden_503(control_s3: Any) -> None:
    for estado in ("offline", None):
        cliente = control_s3(estado)
        assert cliente.get("/tramites").status_code == 503
        salud = cliente.get("/salud").json()
        assert salud["estado"] == "mantenimiento"
        assert salud["operacion"] == ("offline" if estado else "desconocido")


def test_v_mt_active_opera_normalmente(control_s3: Any) -> None:
    cliente = control_s3("active")
    assert cliente.get("/salud").json() == {
        "estado": "ok",
        "entorno": "tests",
        "operacion": "active",
    }
    assert cliente.post("/tramites", json={"titulo": "x"}).status_code == 401


# --- Despliegue: validación, conexión IAM y Lambda ---------------------------------------


@pytest.mark.parametrize(
    ("campos", "mensaje"),
    [
        ({"bd_autenticacion": "iam"}, "BD_CA_CERTIFICADOS"),
        ({"entorno": "demo"}, "autenticación IAM"),
        (
            {"entorno": "demo", "bd_autenticacion": "iam", "bd_ca_certificados": "/ca.pem"},
            "mantenimiento",
        ),
    ],
)
def test_rc_p10_demo_exige_iam_tls_y_mantenimiento(campos: dict[str, Any], mensaje: str) -> None:
    with pytest.raises(ErrorConfiguracion, match=mensaje):
        configuracion_sin_base(**campos).validar_despliegue()


def test_rc_p10_04_cada_conexion_usa_un_token_iam_y_tls_verificado() -> None:
    configuracion = configuracion_sin_base(
        bd_autenticacion="iam",
        bd_ca_certificados="/opt/rds/global-bundle.pem",
        bd_host="proxy.ejemplo.local",
        bd_host_migracion="instancia.ejemplo.local",
        bd_usuario_migracion="atlas_demo_migracion",
    )
    firmados: list[tuple[str, str, int]] = []

    def generador(host: str, usuario: str, puerto: int) -> str:
        firmados.append((host, usuario, puerto))
        return "token-firmado"

    motor = crear_motor(configuracion, generador=generador)
    parametros: dict[str, Any] = {"host": "proxy.ejemplo.local", "user": "nadie", "port": 5432}
    motor.dialect.dispatch.do_connect(motor.dialect, None, [], parametros)
    assert parametros["password"] == "token-firmado"
    assert firmados == [("proxy.ejemplo.local", "nadie", 5432)]
    assert configuracion.argumentos_conexion() == {
        "sslmode": "verify-full",
        "sslrootcert": "/opt/rds/global-bundle.pem",
    }
    migracion = crear_motor(configuracion, migracion=True, generador=generador)
    assert migracion.url.host == "instancia.ejemplo.local"
    assert migracion.url.username == "atlas_demo_migracion"
    motor.dispose()
    migracion.dispose()


def test_rc_p10_04_el_generador_firma_sin_contactar_aws(monkeypatch: pytest.MonkeyPatch) -> None:
    from atlas.persistencia.motor import generador_token_iam

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    token = generador_token_iam(configuracion_sin_base())("proxy.ejemplo.local", "app", 5432)
    assert token.startswith("proxy.ejemplo.local:5432/?Action=connect")
    assert "DBUser=app" in token


def evento_http_api(metodo: str, ruta: str) -> dict[str, Any]:
    """Evento de API Gateway HTTP API (payload 2.0) mínimo."""
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": ruta,
        "rawQueryString": "",
        "headers": {"host": "api.ejemplo.local"},
        "requestContext": {
            "http": {
                "method": metodo,
                "path": ruta,
                "protocol": "HTTP/1.1",
                "sourceIp": "192.0.2.1",
                "userAgent": "pruebas",
            },
            "stage": "$default",
        },
        "isBase64Encoded": False,
    }


def test_do_ops_p5_la_api_responde_eventos_de_api_gateway(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from atlas import lambda_api

    lambda_api._manejador.cache_clear()
    monkeypatch.setattr(
        lambda_api, "crear_manejador", lambda: crear_manejador(configuracion_sin_base())
    )
    asyncio.set_event_loop(None)  # como tras cerrarse un bucle anterior
    from atlas.api import arranque

    monkeypatch.setattr(arranque, "_invocaciones", 0)
    respuesta = lambda_api.manejar(evento_http_api("GET", "/salud"), None)
    assert arranque.estado() == "frio"  # IA-M08: primera invocación del contenedor
    assert respuesta["statusCode"] == 200
    assert json.loads(respuesta["body"])["entorno"] == "tests"
    no_autenticado = lambda_api.manejar(evento_http_api("GET", "/tramites"), None)
    assert no_autenticado["statusCode"] == 401 and arranque.estado() == "caliente"
    lambda_api._manejador.cache_clear()


def test_dif_98_verificacion_previa_antes_del_mantenimiento(control_s3: Any) -> None:
    cliente = control_s3("offline")
    previa = cliente.options("/tramites", headers={"Access-Control-Request-Method": "POST"})
    assert previa.status_code == 204
    assert cliente.post("/tramites", json={"titulo": "x"}).status_code == 503
