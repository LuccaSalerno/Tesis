"""Pasos de `vinculos_y_reglas.feature`: punto de demo C (DO-2026-10-22-BDD, DO-2026-10-22-REG).

Contra la API autenticada y PostgreSQL real, con los valores del oráculo PD-07 validados
por el responsable (las reglas nunca usan sugerencias, RN-02).
"""

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from tests.flujo_api import Contexto, crear_tramite
from tests.flujo_vinculos import (
    C_V1,
    F_V2,
    O_V1,
    control,
    controles,
    documento,
    resolver,
    resultados,
    validar,
    vinculos,
)

pytestmark = pytest.mark.integracion

scenarios("vinculos_y_reglas.feature")

ORACULO = {"O-v1": O_V1, "F-v2": F_V2}


@given("un trámite con el contrato C-v1 validado")
def tramite_con_contrato(ctx: Contexto, estado: dict[str, Any]) -> None:
    estado["tramite"] = crear_tramite(ctx)["id"]
    estado["contrato"] = documento(ctx, estado["tramite"], "Contrato C-v1", "contrato", C_V1)


@when(parsers.parse('incorpora y valida la orden de compra "{nombre}"'))
def incorpora_orden(ctx: Contexto, estado: dict[str, Any], nombre: str) -> None:
    estado["orden"] = documento(ctx, estado["tramite"], nombre, "orden_compra", ORACULO[nombre])


def _confirmar_sugerencia(ctx: Contexto, estado: dict[str, Any]) -> dict[str, Any]:
    (sugerido,) = vinculos(ctx, estado["tramite"])["sugeridos"]
    respuesta = resolver(ctx, estado["tramite"], sugerido["id"], "confirmacion")
    assert respuesta.status_code == 200, respuesta.text
    confirmado: dict[str, Any] = respuesta.json()
    return confirmado


@when(
    parsers.parse(
        'incorpora, valida y vincula la orden de compra "{orden}" y la factura "{factura}"'
    )
)
def incorpora_y_vincula(ctx: Contexto, estado: dict[str, Any], orden: str, factura: str) -> None:
    incorpora_orden(ctx, estado, orden)
    _confirmar_sugerencia(ctx, estado)
    estado["factura"] = documento(ctx, estado["tramite"], factura, "factura", ORACULO[factura])
    _confirmar_sugerencia(ctx, estado)


@then("se sugiere un vínculo pendiente entre la orden y el contrato")
def vinculo_sugerido(ctx: Contexto, estado: dict[str, Any]) -> None:
    lista = vinculos(ctx, estado["tramite"])
    assert lista["confirmados"] == []
    (sugerido,) = lista["sugeridos"]
    assert (sugerido["documento_origen_id"], sugerido["documento_destino_id"]) == (
        estado["orden"],
        estado["contrato"],
    )
    assert sugerido["estado"] == "pendiente" and sugerido["origen"] == "automatico"


@then("no hay controles ejecutados")
def sin_controles(ctx: Contexto, estado: dict[str, Any]) -> None:
    assert controles(ctx, estado["tramite"], historial=True)["historial"] == []


@when("confirma el vínculo sugerido")
def confirma_sugerido(ctx: Contexto, estado: dict[str, Any]) -> None:
    estado["vinculo"] = _confirmar_sugerencia(ctx, estado)


@then("el vínculo rige y los controles se ejecutan")
def vinculo_rige(ctx: Contexto, estado: dict[str, Any]) -> None:
    assert vinculos(ctx, estado["tramite"])["confirmados"] == [estado["vinculo"]]
    assert {
        e["codigo_regla"][:2] for e in controles(ctx, estado["tramite"], True)["historial"]
    } == {
        "R2",
        "R3",
    }


@then(parsers.parse("R3 advierte que la fecha de la orden {fecha} está fuera de la vigencia"))
def r3_advierte(ctx: Contexto, estado: dict[str, Any], fecha: str) -> None:
    r3 = control(ctx, estado["tramite"], "R3")
    assert r3["resultado"] == "advertencia"
    assert f"({fecha}) está fuera de la vigencia del contrato" in r3["explicacion"]


@then("R1, R2 y R4 se cumplen")
def otras_cumplen(ctx: Contexto, estado: dict[str, Any]) -> None:
    obtenidos = resultados(ctx, estado["tramite"])
    assert [obtenidos[r] for r in ("R1", "R2", "R4")] == ["cumplimiento"] * 3


@then("el control R3 muestra la regla, las versiones y los valores validados comparados")
def r3_detalle(ctx: Contexto, estado: dict[str, Any]) -> None:
    ejecucion = control(ctx, estado["tramite"], "R3")["ejecucion"]
    assert (ejecucion["codigo_regla"], ejecucion["version_regla"]) == (
        "R3-VIGENCIA-OC-CONTRATO",
        "v1",
    )
    assert {v["documento_id"] for v in ejecucion["versiones"]} == {
        estado["contrato"],
        estado["orden"],
    }
    assert {v["campo"]: v["valor_validado"] for v in ejecucion["valores"]} == {
        "vigencia_desde": "2026-03-01",
        "vigencia_hasta": "2027-02-28",
        "fecha": "2027-03-15",
    }
    estado["advertencia"] = ejecucion


@then("el trámite sigue en Borrador")
def sigue_en_borrador(ctx: Contexto, estado: dict[str, Any]) -> None:
    with ctx.motor.connect() as conexion:
        valor = conexion.execute(
            text("SELECT estado FROM atlas.tramite WHERE id = :t"), {"t": estado["tramite"]}
        ).scalar_one()
    assert valor == "borrador"  # RN-06: la advertencia no decide nada


@when(parsers.parse('corrige la fecha validada de la orden a "{fecha}"'))
def corrige_fecha(ctx: Contexto, estado: dict[str, Any], fecha: str) -> None:
    estado["advertencia"] = control(ctx, estado["tramite"], "R3")["ejecucion"]
    datos = ctx.cliente.get(
        f"/tramites/{estado['tramite']}/documentos/{estado['orden']}/validaciones",
        headers=ctx.encabezados,
    ).json()
    vigente = next(c for c in datos["campos"] if c["campo"] == "fecha")["vigente"]
    validar(ctx, estado["tramite"], estado["orden"], "fecha", fecha, reemplaza_a_id=vigente["id"])


@then("R3 se cumple con una ejecución nueva")
def r3_cumple(ctx: Contexto, estado: dict[str, Any]) -> None:
    r3 = control(ctx, estado["tramite"], "R3")
    assert r3["resultado"] == "cumplimiento"
    assert r3["ejecucion"]["id"] != estado["advertencia"]["id"]


@then("la ejecución con la advertencia sigue en el historial sin cambios")
def advertencia_conservada(ctx: Contexto, estado: dict[str, Any]) -> None:
    historial = controles(ctx, estado["tramite"], historial=True)["historial"]
    assert estado["advertencia"] in historial
