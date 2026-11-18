"""Pasos de `incorporacion_documental.feature`.

Cada paso opera por la API autenticada y autorizada, con PostgreSQL real y S3 y
Step Functions simulados con moto. RF-04, RF-05, RF-07, RNF-01.
"""

import hashlib
from typing import Any

import httpx
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests import archivos
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, cargar, eventos_del_tramite, incorporar

pytestmark = pytest.mark.integracion

scenarios("incorporacion_documental.feature")


@given("un trámite en Borrador a su cargo")
def tramite_en_borrador(ctx: Contexto, estado: dict[str, Any]) -> None:
    respuesta = ctx.cliente.post(
        "/tramites", json={"titulo": "Escenario BDD ficticio"}, headers=ctx.encabezados
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "borrador"
    estado["tramite"] = respuesta.json()


@given(parsers.parse('que cargó el documento sintético "{nombre}"'))
@when(parsers.parse('carga el documento sintético "{nombre}"'))
def carga_documento(ctx: Contexto, estado: dict[str, Any], nombre: str) -> None:
    datos = (archivos.CORPUS / nombre).read_bytes()
    estado["datos"] = datos
    estado["archivo"] = cargar(ctx, estado["tramite"]["id"], datos)


@given("pasaron más de 24 horas sin incorporarlo")
def pasaron_24_horas(aplicacion: Any) -> None:
    # Reloj determinista: una vigencia nula equivale a haber superado las 24 h.
    aplicacion.state.vigencia_carga_pendiente_s = 0


@when("confirma su incorporación como documento nuevo")
def confirma_incorporacion(ctx: Contexto, estado: dict[str, Any]) -> None:
    estado["respuesta"] = incorporar(ctx, estado["tramite"]["id"], estado["archivo"]["id"])


@when("otro responsable intenta incorporarlo")
def otro_responsable_incorpora(ctx: Contexto, estado: dict[str, Any]) -> None:
    _, sub = crear_cuenta(ctx.motor, "responsable_tramite")
    estado["respuesta"] = ctx.cliente.post(
        f"/tramites/{estado['tramite']['id']}/archivos/{estado['archivo']['id']}/incorporacion",
        headers=portador(sub),
    )


@then("el archivo queda pendiente de incorporación con su huella SHA-256")
def archivo_pendiente(estado: dict[str, Any]) -> None:
    archivo = estado["archivo"]
    assert archivo["estado_incorporacion"] == "pendiente"
    assert archivo["huella"] == hashlib.sha256(estado["datos"]).hexdigest()


@then("el trámite sigue en Borrador sin documentos")
def tramite_sin_documentos(ctx: Contexto, estado: dict[str, Any]) -> None:
    abierto = ctx.cliente.get(f"/tramites/{estado['tramite']['id']}", headers=ctx.encabezados)
    assert abierto.json()["estado"] == "borrador"
    assert abierto.json()["documentos"] == []


@then("el trámite tiene un documento cuya versión vigente es la número 1")
def documento_con_version_inicial(ctx: Contexto, estado: dict[str, Any]) -> None:
    respuesta: httpx.Response = estado["respuesta"]
    assert respuesta.status_code == 201
    abierto = ctx.cliente.get(f"/tramites/{estado['tramite']['id']}", headers=ctx.encabezados)
    (documento,) = abierto.json()["documentos"]
    assert documento["version_vigente"]["numero"] == 1
    assert documento["version_vigente"]["archivo_id"] == estado["archivo"]["id"]


@then("la incorporación queda registrada en la auditoría con su versión")
def incorporacion_auditada(ctx: Contexto, estado: dict[str, Any]) -> None:
    documento = estado["respuesta"].json()
    (evento,) = [
        e
        for e in eventos_del_tramite(ctx.motor, estado["tramite"]["id"])
        if e["accion"] == "documento_incorporado"
    ]
    assert evento["version_id"] == documento["version_vigente"]["id"]
    assert evento["actor_id"] == ctx.usuario_id


@then("la incorporación se rechaza por vencimiento")
def rechazo_por_vencimiento(estado: dict[str, Any]) -> None:
    respuesta: httpx.Response = estado["respuesta"]
    assert respuesta.status_code == 409
    assert "venció" in respuesta.json()["detalle"]


@then("la operación se rechaza sin revelar el trámite")
def rechazo_sin_revelar(estado: dict[str, Any]) -> None:
    assert estado["respuesta"].status_code == 404
