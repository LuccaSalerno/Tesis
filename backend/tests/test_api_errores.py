"""Formato de los errores de la API y fallas de servicios externos."""

import asyncio
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from atlas import principal
from atlas.configuracion import Configuracion
from atlas.integraciones.puertos import ErrorIntegracion
from atlas.principal import crear_aplicacion
from atlas.servicios.errores import ErrorDominio
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, crear_tramite


@pytest.mark.parametrize(
    "manejador",
    [principal._responder_http, principal._responder_dominio, principal._responder_integracion],
)
def test_cada_manejador_solo_atiende_su_error(manejador: Any) -> None:
    with pytest.raises(KeyError):
        asyncio.run(manejador(None, KeyError("otro")))


def test_error_de_dominio_generico_responde_422() -> None:
    respuesta = asyncio.run(principal._responder_dominio(None, ErrorDominio("Operación inválida")))
    assert respuesta.status_code == 422


@pytest.fixture
def contexto(
    base_migrada: Configuracion, motor_aplicacion: Engine
) -> Iterator[tuple[Any, Contexto]]:
    aplicacion = crear_aplicacion(base_migrada)
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield aplicacion, Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
    aplicacion.state.motor.dispose()


@pytest.mark.integracion
def test_falla_de_s3_responde_503_sin_efectos(contexto: tuple[Any, Contexto]) -> None:
    aplicacion, ctx = contexto
    tramite = crear_tramite(ctx)

    class AlmacenCaido:
        def url_carga(self, *_: Any) -> str:
            raise ErrorIntegracion("s3_url_no_generada")

    aplicacion.state.almacen = AlmacenCaido()
    respuesta = ctx.cliente.post(
        f"/tramites/{tramite['id']}/cargas",
        json={"nombre": "x.pdf", "formato": "pdf", "tamano_bytes": 10},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 503
    assert respuesta.json() == {
        "detalle": "Servicio no disponible momentáneamente. Reintentá en unos minutos."
    }


@pytest.mark.integracion
def test_la_respuesta_espera_la_confirmacion_de_la_sesion(
    contexto: tuple[Any, Contexto], monkeypatch: pytest.MonkeyPatch
) -> None:
    """La sesión se confirma antes de responder: una confirmación fallida no llega al cliente
    como un 201 y el pedido siguiente siempre ve lo confirmado."""
    from sqlalchemy.orm import Session

    _, ctx = contexto
    original = Session.commit

    def commit_fallido(sesion: Session) -> None:
        raise RuntimeError("commit_fallido")

    monkeypatch.setattr(Session, "commit", commit_fallido)
    with TestClient(ctx.cliente.app, raise_server_exceptions=False) as cliente:
        respuesta = cliente.post(
            "/tramites", json={"titulo": "No confirmado"}, headers=ctx.encabezados
        )
    monkeypatch.setattr(Session, "commit", original)
    assert respuesta.status_code == 500
    assert all(
        t["titulo"] != "No confirmado"
        for t in ctx.cliente.get("/tramites", headers=ctx.encabezados).json()
    )
