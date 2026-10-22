"""Pasos de `revision_y_evidencia.feature`: punto de demo D (DO-2026-10-22-BDD, -TAR).

Contra la API autenticada y PostgreSQL real, con documentos y valores sintéticos (PD-07).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from tests.flujo_revision import (
    Equipo,
    ciclos,
    confirmar_flujo,
    decidida,
    enviar_a_validacion,
    equipo,
    evidencia,
    flujo_sugerido,
    obtener,
    plantilla_de_contratos,
    tramite,
    tramite_con_conjunto,
)

pytestmark = pytest.mark.integracion

scenarios("revision_y_evidencia.feature")


@pytest.fixture
def aplicacion(base_migrada: Configuracion) -> Iterator[Any]:
    aplicacion = crear_aplicacion(base_migrada)
    yield aplicacion
    aplicacion.state.motor.dispose()


@pytest.fixture
def estado() -> dict[str, Any]:
    return {}


@given("una plantilla de contratos con revisión legal y aprobación final", target_fixture="e")
def plantilla_contratos(
    aplicacion: Any, motor_aplicacion: Engine, estado: dict[str, Any]
) -> Iterator[Equipo]:
    with TestClient(aplicacion) as cliente:
        actual = equipo(cliente, motor_aplicacion)
        estado["plantilla"] = plantilla_de_contratos(actual)
        yield actual


@given("un trámite con el contrato C-v1, la orden O-v1 y la factura F-v1 validados y vinculados")
def conjunto(e: Equipo, estado: dict[str, Any]) -> None:
    estado["ids"] = tramite_con_conjunto(e)


def _tramite(estado: dict[str, Any]) -> int:
    return int(estado["ids"]["tramite"])


@when("el responsable envía el trámite a validación")
def envia(e: Equipo, estado: dict[str, Any]) -> None:
    assert enviar_a_validacion(e.responsable, _tramite(estado)).status_code == 200


@then("se sugiere la plantilla de contratos sin crear tareas")
def sugerencia(e: Equipo, estado: dict[str, Any]) -> None:
    sugerido = flujo_sugerido(e.responsable, _tramite(estado))
    assert (sugerido["alcance"], sugerido["plantilla_id"]) == (
        "contrato",
        estado["plantilla"]["id"],
    )
    assert ciclos(e.responsable, _tramite(estado)) == []
    assert obtener(e.revisor, "/tareas") == []


@when("el responsable confirma el flujo sugerido")
def confirma(e: Equipo, estado: dict[str, Any]) -> None:
    respuesta = confirmar_flujo(e.responsable, _tramite(estado))
    assert respuesta.status_code == 201, respuesta.text
    estado["ciclo"] = respuesta.json()


@when("el responsable envía el trámite a validación y confirma el flujo sugerido")
def envia_y_confirma(e: Equipo, estado: dict[str, Any]) -> None:
    envia(e, estado)
    confirma(e, estado)


@then("el trámite queda Pendiente de aprobación con la revisión legal habilitada")
def pendiente_aprobacion(e: Equipo, estado: dict[str, Any]) -> None:
    assert tramite(e.responsable, _tramite(estado))["estado"] == "pendiente_aprobacion"
    (mia,) = obtener(e.revisor, "/tareas")
    assert (mia["orden"], mia["estado"]) == (1, "pendiente")


@then("el ciclo 1 considera las versiones vigentes de los tres documentos")
def versiones_del_ciclo(e: Equipo, estado: dict[str, Any]) -> None:
    vigentes = {
        d["version_vigente"]["id"] for d in tramite(e.responsable, _tramite(estado))["documentos"]
    }
    assert estado["ciclo"]["numero"] == 1
    assert {v["version_id"] for v in estado["ciclo"]["versiones"]} == vigentes
    assert len(vigentes) == 3


@when("el revisor legal aprueba su tarea con las advertencias a la vista")
def aprueba_legal(e: Equipo, estado: dict[str, Any]) -> None:
    tarea_id = estado["ciclo"]["tareas"][0]["id"]
    vista = obtener(e.revisor, f"/tareas/{tarea_id}")
    resultados = {c["codigo_regla"][:2]: c["resultado"] for c in vista["controles"]}
    assert resultados["R3"] == "advertencia" and resultados["R4"] == "advertencia"
    estado["aprobacion"] = decidida(e.revisor, tarea_id)


@when(parsers.parse('el aprobador final observa su tarea con el motivo "{motivo}"'))
def observa(e: Equipo, estado: dict[str, Any], motivo: str) -> None:
    tarea_id = estado["ciclo"]["tareas"][1]["id"]
    estado["observacion"] = decidida(e.aprobador, tarea_id, "observacion", motivo)
    estado["motivo"] = motivo


@then("el trámite queda Observado")
def observado(e: Equipo, estado: dict[str, Any]) -> None:
    assert tramite(e.responsable, _tramite(estado))["estado"] == "observado"


@then(
    "la evidencia de la observación muestra el ciclo, las versiones, los valores validados y "
    "los controles considerados"
)
def evidencia_completa(e: Equipo, estado: dict[str, Any]) -> None:
    datos = evidencia(e.responsable, estado["observacion"]["id"])
    assert datos["decision"]["motivo"] == estado["motivo"]
    assert datos["decision"]["actor_id"] == e.aprobador.usuario_id
    assert datos["ciclo"]["numero"] == 1
    assert {v["version_id"] for v in datos["versiones"]} == {
        v["version_id"] for v in estado["ciclo"]["versiones"]
    }
    assert {v["documento_id"] for v in datos["validaciones"]} == {
        estado["ids"][clave] for clave in ("contrato", "orden", "factura")
    }
    assert {c["codigo_regla"][:2] for c in datos["controles"]} == {"R1", "R2", "R3", "R4"}
    assert {c["id"] for c in datos["controles"]} == set(
        estado["observacion"]["controles_considerados"]
    )
    # La misma evidencia la ve el revisor que aprobó la tarea anterior del ciclo.
    assert evidencia(e.revisor, estado["observacion"]["id"])["decision"] == datos["decision"]


@then("la línea de tiempo registra la confirmación del flujo, las decisiones y el cambio de estado")
def linea_de_tiempo(e: Equipo, estado: dict[str, Any]) -> None:
    linea = obtener(e.responsable, f"/tramites/{_tramite(estado)}/linea-tiempo")
    acciones = [h["accion"] for h in linea]
    posiciones = [
        acciones.index(a)
        for a in ("flujo_confirmado", "tarea_aprobada", "tarea_observada", "tramite_observado")
    ]
    assert posiciones == sorted(posiciones)
