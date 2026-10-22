"""Escenarios EVD-01 de `cadena_evidencia.feature` (DO-2026-10-22-BDD, DO-2026-10-22-TAR).

EVD-C (RN-13) y EVD-N12 (RN-12) se ejecutan contra la API autenticada y PostgreSQL real.
En EVD-N12 el cambio del conjunto documental es la incorporación de un documento nuevo,
que RN-12 también contempla. EVD-A y EVD-B requieren confirmar una **versión nueva**
(RF-06, Etapa 2) y se **omiten con motivo explícito**: pytest los informa como omitidos,
nunca como aprobados. Ejecutar un escenario no acredita por sí solo el cumplimiento de
EVD-01: eso exige el oráculo congelado y la evidencia conservada (AGENTS.md §7).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from atlas.servicios.tareas import TAREA_DESACTUALIZADA
from tests import archivos
from tests.flujo_api import cargar, incorporar
from tests.flujo_revision import (
    Equipo,
    ciclos,
    decidida,
    decidir,
    equipo,
    evidencia,
    iniciar_ciclo,
    obtener,
    plantilla_de_contratos,
    tramite,
    tramite_con_conjunto,
)
from tests.flujo_vinculos import validar

pytestmark = pytest.mark.integracion

scenarios("cadena_evidencia.feature")

PENDIENTE_RF_06 = (
    "EVD-01 pendiente: requiere confirmar una versión nueva (RF-06, Etapa 2); "
    "no acredita cumplimiento"
)


@pytest.fixture
def aplicacion(base_migrada: Configuracion) -> Iterator[Any]:
    aplicacion = crear_aplicacion(base_migrada)
    yield aplicacion
    aplicacion.state.motor.dispose()


@pytest.fixture
def e(aplicacion: Any, motor_aplicacion: Engine) -> Iterator[Equipo]:
    with TestClient(aplicacion) as cliente:
        actual = equipo(cliente, motor_aplicacion)
        plantilla_de_contratos(actual)
        yield actual


@pytest.fixture
def estado() -> dict[str, Any]:
    return {}


def _versiones(e: Equipo, tramite_id: int) -> set[int]:
    return {d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]}


@given("un trámite con un conjunto documental validado y un primer ciclo aprobado")
@given("un primer ciclo con una observación motivada")
def requiere_version_nueva() -> None:
    pytest.skip(PENDIENTE_RF_06)


# --- EVD-C: subsanación sin nuevo archivo (RN-13) ---------------------------------------


@given("un ciclo observado con el documento vigente identificado")
def ciclo_observado(e: Equipo, estado: dict[str, Any]) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    primera, segunda = (t["id"] for t in ciclo["tareas"])
    # Más de una tarea: una aprobación previa en CR-1 que debe quedar en el historial.
    aprobacion = decidida(e.revisor, primera)
    observacion = decidida(e.aprobador, segunda, "observacion", "Corregir el importe validado")
    estado.update(
        ids=ids,
        ciclo_1=ciclo,
        aprobacion=aprobacion,
        observacion=observacion,
        versiones=_versiones(e, ids["tramite"]),
    )
    assert tramite(e.responsable, ids["tramite"])["estado"] == "observado"


@when("se subsanan datos o metadatos sin reemplazar el contenido del archivo")
def subsanar_datos(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id, factura = estado["ids"]["tramite"], estado["ids"]["factura"]
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/subsanacion", headers=e.responsable.encabezados
    )
    assert respuesta.status_code == 200, respuesta.text
    datos = obtener(e.responsable, f"/tramites/{tramite_id}/documentos/{factura}/validaciones")
    importe = next(c for c in datos["campos"] if c["campo"] == "importe_total")
    validar(
        e.responsable,
        tramite_id,
        factura,
        "importe_total",
        "1250000.00",
        importe["vigente"]["id"],
    )


@then("se conserva la versión documental existente")
def version_conservada(e: Equipo, estado: dict[str, Any]) -> None:
    assert _versiones(e, estado["ids"]["tramite"]) == estado["versiones"]
    linea = obtener(e.responsable, f"/tramites/{estado['ids']['tramite']}/linea-tiempo")
    assert sum(h["accion"] == "documento_incorporado" for h in linea) == 3


@then("el trámite regresa al estado de validación exigido por RN-13")
def regresa_a_validacion(e: Equipo, estado: dict[str, Any]) -> None:
    assert tramite(e.responsable, estado["ids"]["tramite"])["estado"] == "pendiente_validacion"


@then("la nueva revisión no hereda automáticamente la decisión anterior")
def no_hereda(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id = estado["ids"]["tramite"]
    ciclo_2 = iniciar_ciclo(e.responsable, tramite_id)
    assert ciclo_2["numero"] == 2
    assert {v["version_id"] for v in ciclo_2["versiones"]} == estado["versiones"]
    assert [(t["estado"], t["decision_id"]) for t in ciclo_2["tareas"]] == [
        ("pendiente", None),
        ("en_espera", None),
    ]
    assert tramite(e.responsable, tramite_id)["estado"] == "pendiente_aprobacion"
    # Las decisiones de CR-1 siguen en el historial, ligadas a su ciclo y versiones.
    ciclo_1 = ciclos(e.responsable, tramite_id)[0]
    assert ciclo_1["estado"] == "observado"
    for decision in (estado["aprobacion"], estado["observacion"]):
        datos = evidencia(e.responsable, decision["id"])
        assert datos["ciclo"]["id"] == estado["ciclo_1"]["id"]
        assert {v["version_id"] for v in datos["versiones"]} == estado["versiones"]
    importes = {
        v["valor_validado"]
        for v in evidencia(e.responsable, estado["observacion"]["id"])["validaciones"]
        if v["campo"] == "importe_total" and v["documento_id"] == estado["ids"]["factura"]
    }
    assert importes == {"1312500.00"}  # el valor que se observó, no la corrección posterior


# --- EVD-N12: decisión tardía sobre un ciclo desplazado (RN-12) -------------------------


@given("un ciclo de revisión con una tarea pendiente")
def ciclo_con_tarea_pendiente(e: Equipo, estado: dict[str, Any]) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    primera, segunda = (t["id"] for t in ciclo["tareas"])
    aprobacion = decidida(e.revisor, primera)
    estado.update(
        ids=ids,
        ciclo=ciclo,
        pendiente=segunda,
        aprobacion=aprobacion,
        evidencia_previa=evidencia(e.responsable, aprobacion["id"]),
    )


@when("se confirma un cambio del conjunto documental que desplaza ese ciclo")
def cambio_documental(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id = estado["ids"]["tramite"]
    archivo = cargar(e.responsable, tramite_id, archivos.pdf())
    respuesta = incorporar(e.responsable, tramite_id, archivo["id"], nombre="Anexo de precios")
    assert respuesta.status_code == 201, respuesta.text


@when("se intenta resolver la tarea pendiente del ciclo anterior")
def decision_tardia(e: Equipo, estado: dict[str, Any]) -> None:
    estado["respuesta"] = decidir(e.aprobador, estado["pendiente"])


@then("la operación es rechazada por estar desactualizada")
def rechazada(estado: dict[str, Any]) -> None:
    assert estado["respuesta"].status_code == 409
    assert estado["respuesta"].json()["detalle"] == TAREA_DESACTUALIZADA


@then("no se crea una decisión válida ni se altera retroactivamente la evidencia anterior")
def sin_efectos(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id = estado["ids"]["tramite"]
    (ciclo,) = ciclos(e.responsable, tramite_id)
    assert ciclo["estado"] == "desplazado"
    assert [(t["estado"], t["decision_id"] is None) for t in ciclo["tareas"]] == [
        ("aprobada", False),
        ("anulada", True),
    ]
    assert tramite(e.responsable, tramite_id)["estado"] == "borrador"
    # La cadena de la decisión anterior no cambia; solo se agregan los eventos posteriores
    # del ciclo (desplazamiento y anulación), sin alterar los ya registrados.
    actual = evidencia(e.responsable, estado["aprobacion"]["id"])
    previa = estado["evidencia_previa"]
    eventos_previos = previa.pop("eventos")
    eventos = actual.pop("eventos")
    assert actual["tareas_del_ciclo"][1]["estado"] == "anulada"
    actual["tareas_del_ciclo"][1] = previa["tareas_del_ciclo"][1] = None
    assert actual["ciclo"]["estado"] == "desplazado"
    # Estados actuales del ciclo, la tarea anulada y el trámite: contexto, no evidencia.
    for clave in ("ciclo", "tramite"):
        actual[clave]["estado"] = previa[clave]["estado"] = None
    assert actual == previa
    assert eventos[: len(eventos_previos)] == eventos_previos
    assert [ev["accion"] for ev in eventos[len(eventos_previos) :]] == [
        "ciclo_desplazado",
        "tarea_anulada",
    ]
