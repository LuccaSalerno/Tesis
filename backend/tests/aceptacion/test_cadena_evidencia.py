"""Escenarios EVD-01 de `cadena_evidencia.feature`.

Los cuatro recorridos se ejecutan contra la API autenticada y PostgreSQL real. En EVD-A y
EVD-B el cambio es una **versión nueva** sugerida por el sistema y confirmada por el
responsable (RF-06, RF-07); el procesamiento usa respuestas fijas. En
EVD-N12 es la incorporación de un documento nuevo, que RN-12 también contempla. Ejecutar
un escenario no acredita por sí solo el cumplimiento de EVD-01: eso exige el oráculo
congelado y la evidencia conservada (AGENTS.md §7).
"""

from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from atlas.servicios.tareas import TAREA_DESACTUALIZADA
from tests import archivos
from tests.flujo_api import cargar, incorporar
from tests.flujo_revision import (
    F_COMPLETO,
    O_COMPLETO,
    Equipo,
    ciclos,
    decidida,
    decidir,
    evidencia,
    iniciar_ciclo,
    obtener,
    tramite,
    tramite_con_conjunto,
)
from tests.flujo_versiones import archivo, como_version, procesado
from tests.flujo_vinculos import validar

pytestmark = pytest.mark.integracion

scenarios("cadena_evidencia.feature")


def _versiones(e: Equipo, tramite_id: int) -> set[int]:
    return {d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]}


# --- EVD-A y EVD-B: versión nueva confirmada (RN-12) -----------------

F_V2 = {**F_COMPLETO, "importe_total": "1250000.00"}
O_V2 = {**O_COMPLETO, "fecha": "2026-09-15"}
MOTIVO = "La fecha de la orden de compra está fuera de la vigencia del contrato"


def _validaciones(datos: dict[str, Any], documento_id: int) -> set[int]:
    return {v["validacion_id"] for v in datos["validaciones"] if v["documento_id"] == documento_id}


def _version_nueva(
    aplicacion: Any,
    e: Equipo,
    estado: dict[str, Any],
    tipo: str,
    documento: str,
    valores: dict[str, str],
) -> None:
    """Carga el archivo corregido, confirma la versión sugerida (RF-06, RF-07) y la valida."""
    tramite_id = estado["ids"]["tramite"]
    previo = tramite(e.responsable, tramite_id)["estado"]
    sugeridos = {
        k: v for k, v in valores.items() if k in ("numero", "cuit_proveedor", "cuit_emisor")
    }
    nuevo = procesado(aplicacion, e.responsable, tramite_id, tipo, sugeridos)
    # Pendiente: todavía no altera el conjunto ni el estado (RF-04).
    assert tramite(e.responsable, tramite_id)["estado"] == previo
    assert _versiones(e, tramite_id) == estado["versiones"]
    sugerencia = archivo(e.responsable, tramite_id, nuevo["id"])["sugerencia_version"]
    assert sugerencia["documento_id"] == estado["ids"][documento]
    respuesta = como_version(e.responsable, tramite_id, nuevo["id"])
    assert respuesta.status_code == 201, respuesta.text
    estado["version_nueva"] = respuesta.json()["version_vigente"]["id"]
    assert tramite(e.responsable, tramite_id)["estado"] == "borrador"
    documento_id = estado["ids"][documento]
    validar(e.responsable, tramite_id, documento_id, "tipo_documental", tipo)
    for campo, valor in valores.items():
        validar(e.responsable, tramite_id, documento_id, campo, valor)


@given("un trámite con un conjunto documental validado y un primer ciclo aprobado")
def primer_ciclo_aprobado(e: Equipo, estado: dict[str, Any]) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    legal, final = (t["id"] for t in ciclo["tareas"])
    decidida(e.revisor, legal)
    aprobacion = decidida(e.aprobador, final)
    assert tramite(e.responsable, ids["tramite"])["estado"] == "aprobado"
    estado.update(
        ids=ids,
        ciclo_1=ciclo,
        decision_1=aprobacion,
        versiones=_versiones(e, ids["tramite"]),
        evidencia_1=evidencia(e.responsable, aprobacion["id"]),
    )


@when("se confirma la incorporación de una nueva versión antes del cierre")
def version_antes_del_cierre(aplicacion: Any, e: Equipo, estado: dict[str, Any]) -> None:
    _version_nueva(aplicacion, e, estado, "factura", "factura", F_V2)


@then("la decisión del primer ciclo sigue asociada a las versiones que consideró")
def decision_1_intacta(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id = estado["ids"]["tramite"]
    actual = evidencia(e.responsable, estado["decision_1"]["id"])
    assert actual["ciclo"]["id"] == estado["ciclo_1"]["id"]
    assert actual["ciclo"]["estado"] == "aprobado"  # RN-12: un ciclo concluido no cambia
    assert {v["version_id"] for v in actual["versiones"]} == estado["versiones"]
    assert estado["version_nueva"] not in {v["version_id"] for v in actual["versiones"]}
    assert actual["validaciones"] == estado["evidencia_1"]["validaciones"]
    assert actual["controles"] == estado["evidencia_1"]["controles"]
    assert ciclos(e.responsable, tramite_id)[0]["estado"] == "aprobado"


@then("el nuevo conjunto documental requiere la revisión y decisión que correspondan")
def nuevo_ciclo_con_decision(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id, ids = estado["ids"]["tramite"], estado["ids"]
    ciclo_2 = iniciar_ciclo(e.responsable, tramite_id)
    assert ciclo_2["numero"] == 2
    vigentes = _versiones(e, tramite_id)
    assert {v["version_id"] for v in ciclo_2["versiones"]} == vigentes
    assert estado["version_nueva"] in vigentes and len(vigentes - estado["versiones"]) == 1
    decision_2 = decidida(e.revisor, ciclo_2["tareas"][0]["id"])
    datos = evidencia(e.responsable, decision_2["id"])
    assert datos["ciclo"]["id"] == ciclo_2["id"]
    previa = estado["evidencia_1"]
    # V8: C-v1 y O-v1 conservan sus validaciones; F-v2 no hereda las de F-v1.
    for documento in ("contrato", "orden"):
        assert _validaciones(datos, ids[documento]) == _validaciones(previa, ids[documento])
    assert _validaciones(datos, ids["factura"]).isdisjoint(_validaciones(previa, ids["factura"]))
    importes = {
        v["valor_validado"]
        for v in datos["validaciones"]
        if v["documento_id"] == ids["factura"] and v["campo"] == "importe_total"
    }
    assert importes == {"1250000.00"}
    # Los controles de la factura se ejecutaron de nuevo con F-v2.
    con_factura = [
        c
        for c in datos["controles"]
        if estado["version_nueva"] in {v["version_id"] for v in c["versiones"]}
    ]
    assert con_factura and {c["id"] for c in con_factura}.isdisjoint(
        {c["id"] for c in previa["controles"]}
    )
    estado.update(ciclo_2=ciclo_2, decision_2=decision_2)


@then("la aprobación anterior no se transfiere automáticamente al nuevo ciclo")
def sin_transferencia(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id = estado["ids"]["tramite"]
    _, ciclo_2 = ciclos(e.responsable, tramite_id)
    assert [(t["estado"], t["decision_id"]) for t in ciclo_2["tareas"]] == [
        ("aprobada", estado["decision_2"]["id"]),
        ("pendiente", None),
    ]
    assert estado["decision_1"]["id"] not in {t["decision_id"] for t in ciclo_2["tareas"]}
    assert tramite(e.responsable, tramite_id)["estado"] == "pendiente_aprobacion"
    # Sin el nuevo ciclo aprobado no hay firma posible (RF-23).
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/firma",
        json={"version_id": estado["version_nueva"]},
        headers=e.aprobador.encabezados,
    )
    assert respuesta.status_code == 409


@given("un primer ciclo con una observación motivada")
def primer_ciclo_observado(e: Equipo, estado: dict[str, Any]) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    observacion = decidida(e.revisor, ciclo["tareas"][0]["id"], "observacion", MOTIVO)
    assert tramite(e.responsable, ids["tramite"])["estado"] == "observado"
    estado.update(
        ids=ids,
        ciclo_1=ciclo,
        decision_1=observacion,
        versiones=_versiones(e, ids["tramite"]),
        evidencia_1=evidencia(e.responsable, observacion["id"]),
    )


@when("se confirma una versión corregida del documento observado")
def version_corregida(aplicacion: Any, e: Equipo, estado: dict[str, Any]) -> None:
    _version_nueva(aplicacion, e, estado, "orden_compra", "orden", O_V2)


@then("la observación anterior conserva su contexto documental")
def observacion_intacta(e: Equipo, estado: dict[str, Any]) -> None:
    actual = evidencia(e.responsable, estado["decision_1"]["id"])
    assert actual["decision"]["motivo"] == MOTIVO
    assert actual["ciclo"]["id"] == estado["ciclo_1"]["id"]
    assert actual["ciclo"]["estado"] == "observado"
    assert {v["version_id"] for v in actual["versiones"]} == estado["versiones"]
    assert actual["validaciones"] == estado["evidencia_1"]["validaciones"]
    assert actual["controles"] == estado["evidencia_1"]["controles"]
    r3 = next(c for c in actual["controles"] if c["codigo_regla"].startswith("R3"))
    assert r3["resultado"] == "advertencia"


@then("se crea el ciclo correspondiente al conjunto documental actualizado")
def ciclo_actualizado(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id = estado["ids"]["tramite"]
    ciclo_2 = iniciar_ciclo(e.responsable, tramite_id)
    assert ciclo_2["numero"] == 2
    versiones = {v["version_id"] for v in ciclo_2["versiones"]}
    assert estado["version_nueva"] in versiones
    assert versiones - {estado["version_nueva"]} < estado["versiones"]
    assert [(t["estado"], t["decision_id"]) for t in ciclo_2["tareas"]] == [
        ("pendiente", None),
        ("en_espera", None),
    ]
    estado["ciclo_2"] = ciclo_2


@then("el resultado de la revisión posterior queda ligado a ese nuevo ciclo")
def revision_posterior(e: Equipo, estado: dict[str, Any]) -> None:
    tramite_id, ciclo_2 = estado["ids"]["tramite"], estado["ciclo_2"]
    legal, final = (t["id"] for t in ciclo_2["tareas"])
    decidida(e.revisor, legal)
    decision_2 = decidida(e.aprobador, final)
    datos = evidencia(e.responsable, decision_2["id"])
    assert datos["ciclo"]["id"] == ciclo_2["id"] and datos["ciclo"]["estado"] == "aprobado"
    r3 = next(c for c in datos["controles"] if c["codigo_regla"].startswith("R3"))
    assert r3["resultado"] == "cumplimiento"
    assert estado["version_nueva"] in {v["version_id"] for v in r3["versiones"]}
    # V11: la firma simulada cierra la historia; después no se admiten versiones nuevas.
    contrato = next(
        v for v in ciclo_2["versiones"] if v["documento_id"] == estado["ids"]["contrato"]
    )
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/firma",
        json={"version_id": contrato["version_id"]},
        headers=e.aprobador.encabezados,
    )
    assert respuesta.status_code == 201, respuesta.text
    assert tramite(e.responsable, tramite_id)["estado"] == "cerrado"
    assert evidencia(e.responsable, decision_2["id"])["firma"]["id"] == respuesta.json()["id"]
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/cargas",
        json={"nombre": "O-v3.pdf", "formato": "pdf", "tamano_bytes": 1000},
        headers=e.responsable.encabezados,
    )
    assert respuesta.status_code == 409


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
