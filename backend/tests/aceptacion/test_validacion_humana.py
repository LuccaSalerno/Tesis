"""Pasos de `validacion_humana.feature`: punto de demo A (DO-2026-10-22-BDD, DO-2026-10-22-VAL).

Contra la API autenticada y PostgreSQL real; el procesamiento usa respuestas fijas con
las páginas del oráculo preliminar PD-07 (P1 de DO-2026-10-22-PROC).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto
from tests.flujo_procesamiento import contrato_procesado_e_incorporado

pytestmark = pytest.mark.integracion

scenarios("validacion_humana.feature")


@pytest.fixture
def aplicacion(base_migrada: Configuracion) -> Iterator[Any]:
    aplicacion = crear_aplicacion(base_migrada)
    yield aplicacion
    aplicacion.state.motor.dispose()


@pytest.fixture
def estado() -> dict[str, Any]:
    return {}


@given("un responsable del trámite autenticado", target_fixture="ctx")
def responsable_autenticado(aplicacion: Any, motor_aplicacion: Engine) -> Iterator[Contexto]:
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))


@given("el contrato sintético C-v1 procesado e incorporado a su trámite")
def contrato_incorporado(aplicacion: Any, ctx: Contexto, estado: dict[str, Any]) -> None:
    estado.update(contrato_procesado_e_incorporado(aplicacion, ctx))
    estado["ruta"] = (
        f"/tramites/{estado['tramite']['id']}/documentos/{estado['documento']['id']}/validaciones"
    )


def _consultar(ctx: Contexto, estado: dict[str, Any]) -> dict[str, Any]:
    respuesta = ctx.cliente.get(estado["ruta"], headers=ctx.encabezados)
    assert respuesta.status_code == 200
    datos: dict[str, Any] = respuesta.json()
    return datos


def _campo(ctx: Contexto, estado: dict[str, Any], campo: str) -> dict[str, Any]:
    return next(c for c in _consultar(ctx, estado)["campos"] if c["campo"] == campo)


def _validar(ctx: Contexto, estado: dict[str, Any], **cuerpo: Any) -> Any:
    return ctx.cliente.post(estado["ruta"], json=cuerpo, headers=ctx.encabezados)


@when("confirma la clasificación sugerida")
def confirma_clasificacion(ctx: Contexto, estado: dict[str, Any]) -> None:
    sugerida = _consultar(ctx, estado)["clasificacion"]["sugerencia"]
    respuesta = _validar(
        ctx,
        estado,
        campo="tipo_documental",
        valor_validado=sugerida["valor"],
        valor_sugerido_id=sugerida["id"],
    )
    assert respuesta.status_code == 201


@when("confirma el monto total sugerido")
def confirma_monto(ctx: Contexto, estado: dict[str, Any]) -> None:
    sugerida = _campo(ctx, estado, "monto_total")["sugerencia"]
    respuesta = _validar(
        ctx,
        estado,
        campo="monto_total",
        valor_validado=sugerida["valor"],
        valor_sugerido_id=sugerida["id"],
    )
    assert respuesta.status_code == 201
    estado["sugerencia_monto"] = sugerida


@when(parsers.parse('corrige la moneda a "{valor}"'))
def corrige_moneda(ctx: Contexto, estado: dict[str, Any], valor: str) -> None:
    sugerida = _campo(ctx, estado, "moneda")["sugerencia"]
    respuesta = _validar(
        ctx, estado, campo="moneda", valor_validado=valor, valor_sugerido_id=sugerida["id"]
    )
    assert respuesta.status_code == 201


@when("intenta validar el monto total sin validar la clasificación")
def valida_sin_clasificacion(ctx: Contexto, estado: dict[str, Any]) -> None:
    estado["respuesta"] = _validar(ctx, estado, campo="monto_total", valor_validado="1250000.00")


@then(parsers.parse('la clasificación sugerida es "{tipo}" y no está validada'))
def clasificacion_sugerida(ctx: Contexto, estado: dict[str, Any], tipo: str) -> None:
    clasificacion = _consultar(ctx, estado)["clasificacion"]
    assert clasificacion["sugerencia"]["valor"] == tipo
    assert clasificacion["vigente"] is None


@then(parsers.parse('el monto total sugerido es "{valor}" en la página {pagina:d}'))
def monto_sugerido(ctx: Contexto, estado: dict[str, Any], valor: str, pagina: int) -> None:
    respuesta = ctx.cliente.get(
        f"/tramites/{estado['tramite']['id']}/archivos/{estado['archivo']['id']}/sugerencias",
        headers=ctx.encabezados,
    ).json()
    monto = next(c for c in respuesta["campos"] if c["campo"] == "monto_total")
    assert monto["valor"] == valor
    assert monto["localizador"]["pagina"] == pagina


@then(parsers.parse('el documento queda clasificado como "{tipo}"'))
def documento_clasificado(ctx: Contexto, estado: dict[str, Any], tipo: str) -> None:
    detalle = ctx.cliente.get(
        f"/tramites/{estado['tramite']['id']}", headers=ctx.encabezados
    ).json()
    assert detalle["documentos"][0]["tipo"] == tipo


@then(
    parsers.parse(
        "el monto total validado conserva la sugerencia, el actor, la fecha, la versión "
        "y la página {pagina:d}"
    )
)
def monto_validado(ctx: Contexto, estado: dict[str, Any], pagina: int) -> None:
    vigente = _campo(ctx, estado, "monto_total")["vigente"]
    assert vigente["tipo"] == "confirmacion"
    assert vigente["valor_sugerido_id"] == estado["sugerencia_monto"]["id"]
    assert vigente["validador_id"] == ctx.usuario_id
    assert vigente["validado_en"]
    assert vigente["version_id"] == estado["documento"]["version_vigente"]["id"]
    assert vigente["localizador"]["pagina"] == pagina


@then(parsers.parse('la moneda vigente es "{valor}" como corrección'))
def moneda_vigente(ctx: Contexto, estado: dict[str, Any], valor: str) -> None:
    vigente = _campo(ctx, estado, "moneda")["vigente"]
    assert (vigente["valor_validado"], vigente["tipo"]) == (valor, "correccion")


@then(parsers.parse('la sugerencia original de la moneda sigue siendo "{valor}"'))
def sugerencia_original(ctx: Contexto, estado: dict[str, Any], valor: str) -> None:
    assert _campo(ctx, estado, "moneda")["sugerencia"]["valor"] == valor


@then("la validación se rechaza pidiendo validar primero la clasificación")
def rechazo_sin_clasificacion(estado: dict[str, Any]) -> None:
    assert estado["respuesta"].status_code == 409
    assert "clasificación" in estado["respuesta"].json()["detalle"]
