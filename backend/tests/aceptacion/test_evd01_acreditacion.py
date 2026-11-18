"""Acreditación de EVD-01: los criterios V1 a V11 contra el oráculo PD-07 congelado.

Requisito de aceptación de la reconstrucción («automatización de EVD-01», EVD-01 §1): los
cuatro recorridos EVD-A, EVD-B, EVD-C y EVD-N12 por la API autenticada, con datos y
resultados esperados fijados **antes** de ejecutar en `demo/cadena_evidencia/oraculo_PD07_v2.json`
(congelado, DO-2026-10-23-DIF). Cada comprobación registra esperado y observado; un criterio
cumple solo si cumplen todas las suyas. Con `ATLAS_EVIDENCIA_EVD01=<carpeta>` se escribe el
paquete probatorio (EVD-01 §2): resultado por caso y criterio, versión del código, entorno,
fecha, huella del oráculo e identificadores correlacionables.

Alcance declarado (EVD-01 §1, condición 6): Textract y Bedrock se sustituyen por dobles
controlados que devuelven los valores del oráculo; las cuentas ficticias se crean como
precondición. No reemplaza las mediciones de §6.3.1.
"""

import hashlib
import json
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
from atlas.evaluacion import campana as cmp
from atlas.herramientas import sembrar_demo
from atlas.principal import crear_aplicacion
from atlas.servicios.tareas import TAREA_DESACTUALIZADA
from tests.flujo_api import Contexto, crear_tramite, incorporar
from tests.flujo_revision import (
    Equipo,
    ciclos,
    contexto,
    decidir,
    equipo,
    evidencia,
    iniciar_ciclo,
    obtener,
    plantilla_de_contratos,
    tramite,
)
from tests.flujo_versiones import archivo, como_version, procesado
from tests.flujo_vinculos import resolver, vincular, vinculos

pytestmark = pytest.mark.integracion

ORACULO = json.loads(sembrar_demo.ORACULO.read_text(encoding="utf-8"))
HUELLA_ORACULO = hashlib.sha256(sembrar_demo.ORACULO.read_bytes()).hexdigest()
CRITERIOS = ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11")
ESENCIALES = ("V1", "V2", "V3", "V4", "V7", "V9")


def _valores() -> dict[str, dict[str, str]]:
    """Valores esperados por documento del oráculo, con los nombres del esquema (PD-07)."""
    valores = sembrar_demo.escenario(ORACULO)
    f1 = ORACULO["documentos"]["F-v1"]
    valores["F-v1"] = {
        **valores["F-v2"],
        "numero": f1["numero"],
        "fecha_emision": f1["fecha_emision"],
        "cuit_emisor": f1["cuit_emisor"],
        "importe_total": f1["total"],
        "moneda": f1["moneda"],
    }
    return valores


VALORES = _valores()
TIPO = {"C": "contrato", "O": "orden_compra", "F": "factura"}
# Conjuntos y resultados de R1 a R4 fijados por el oráculo (conjuntos_esperados).
ESPERADO = {
    tuple(sorted(c["versiones"])): {r: c[r] for r in ("R1", "R2", "R3", "R4")}
    for c in ORACULO["conjuntos_esperados"]
}
RESULTADO_API = {"cumple": "cumplimiento", "advertencia": "advertencia"}
MOTIVO = "La fecha de emisión de la orden está fuera de la vigencia del contrato."
# Valor que no debe aparecer en una denegación (V10): CUIT de los documentos del caso.
SENSIBLE = ORACULO["registro_cuit"]["numero"]


# --- Registro de comprobaciones ----------------------------------------------------------


@dataclass
class Comprobacion:
    criterio: str
    caso: str
    descripcion: str
    esperado: Any
    observado: Any
    cumple: bool
    ids: dict[str, Any] = field(default_factory=dict)


@dataclass
class Registro:
    comprobaciones: list[Comprobacion] = field(default_factory=list)

    def verificar(
        self,
        criterio: str,
        caso: str,
        descripcion: str,
        esperado: Any,
        observado: Any,
        **ids: Any,
    ) -> bool:
        cumple = esperado == observado
        self.comprobaciones.append(
            Comprobacion(criterio, caso, descripcion, esperado, observado, cumple, ids)
        )
        return cumple

    def estado(self, criterio: str) -> str:
        propias = [c for c in self.comprobaciones if c.criterio == criterio]
        if not propias:
            return "No ejecutado"
        return "Cumple" if all(c.cumple for c in propias) else "No cumple"


# --- Fixtures y pasos comunes ------------------------------------------------------------


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


def _por_campo(ctx: Contexto, tramite_id: int, documento_id: int) -> dict[str, Any]:
    datos = obtener(ctx, f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones")
    return {"tipo_documental": datos["clasificacion"], **{d["campo"]: d for d in datos["campos"]}}


def _campos(ctx: Contexto, tramite_id: int, documento_id: int) -> list[tuple[str, Any]]:
    return [
        (c, d)
        for c, d in _por_campo(ctx, tramite_id, documento_id).items()
        if c != "tipo_documental"
    ]


def _validar(
    ctx: Contexto, tramite_id: int, documento_id: int, codigo: str
) -> dict[str, dict[str, Any]]:
    """Valida como una persona: confirma la sugerencia que coincide con el oráculo y corrige
    la que no. La clasificación primero: los campos del esquema dependen del tipo
    (DO-2026-10-22-VAL P3). Devuelve las validaciones registradas por campo."""
    registradas: dict[str, dict[str, Any]] = {}

    def registrar(campo: str, dato: dict[str, Any]) -> None:
        sugerencia, vigente = dato.get("sugerencia"), dato.get("vigente")
        respuesta = ctx.cliente.post(
            f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones",
            json={
                "campo": dato["campo"],
                "valor_validado": VALORES[codigo][campo],
                "valor_sugerido_id": sugerencia["id"] if sugerencia else None,
                "reemplaza_a_id": vigente["id"] if vigente else None,
            },
            headers=ctx.encabezados,
        )
        assert respuesta.status_code == 201, respuesta.text
        registradas[campo] = respuesta.json()

    registrar("tipo_documental", _por_campo(ctx, tramite_id, documento_id)["tipo_documental"])
    for campo, dato in _campos(ctx, tramite_id, documento_id):
        registrar(campo, dato)
    return registradas


def _procesar(
    aplicacion: Any, e: Equipo, tramite_id: int, codigo: str, errores: dict[str, str] | None = None
) -> dict[str, Any]:
    """Archivo sintético procesado con los valores del oráculo (dobles controlados); los de
    `errores` se sugieren distintos para que la persona los corrija (V2)."""
    sugeridos = {k: v for k, v in VALORES[codigo].items() if k != "tipo_documental"}
    sugeridos |= errores or {}
    return procesado(aplicacion, e.responsable, tramite_id, TIPO[codigo[0]], sugeridos)


def _documento(
    aplicacion: Any, e: Equipo, tramite_id: int, codigo: str, errores: dict[str, str] | None = None
) -> tuple[int, dict[str, Any]]:
    cargado = _procesar(aplicacion, e, tramite_id, codigo, errores)
    respuesta = incorporar(e.responsable, tramite_id, cargado["id"], nombre=codigo[0])
    assert respuesta.status_code == 201, respuesta.text
    documento_id = int(respuesta.json()["id"])
    return documento_id, _validar(e.responsable, tramite_id, documento_id, codigo)


def _conjunto(
    aplicacion: Any, e: Equipo, codigos: tuple[str, str, str], errores: dict[str, str] | None = None
) -> dict[str, Any]:
    """Trámite con contrato, orden y factura validados y vinculados (R1 a R4 ejecutadas)."""
    tramite_id = crear_tramite(e.responsable, f"EVD-01 {'+'.join(codigos)}")["id"]
    ids: dict[str, Any] = {"tramite": tramite_id}
    validaciones = {}
    for codigo in codigos:
        documento_id, validaciones[codigo] = _documento(
            aplicacion, e, tramite_id, codigo, errores if codigo.startswith("F") else None
        )
        ids[codigo[0]] = documento_id
    r = e.responsable
    for origen, destino in (("O", "C"), ("F", "O")):
        par = {ids[origen], ids[destino]}
        sugeridos = [
            v
            for v in vinculos(r, tramite_id)["sugeridos"]
            if {v["documento_origen_id"], v["documento_destino_id"]} == par
        ]
        if sugeridos:
            assert resolver(r, tramite_id, sugeridos[0]["id"], "confirmacion").status_code == 200
        else:
            assert vincular(r, tramite_id, ids[origen], ids[destino]).status_code == 201
    return {"ids": ids, "codigos": codigos, "validaciones": validaciones}


def _vigentes(e: Equipo, tramite_id: int) -> set[int]:
    return {d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]}


def _controles(datos: dict[str, Any]) -> dict[str, str]:
    return {c["codigo_regla"][:2]: c["resultado"] for c in datos["controles"]}


def _esperados(codigos: tuple[str, ...]) -> dict[str, str]:
    return {r: RESULTADO_API[v] for r, v in ESPERADO[tuple(sorted(codigos))].items()}


def _nueva_version(
    aplicacion: Any, e: Equipo, caso: dict[str, Any], codigo: str, reg: Registro, nombre: str
) -> int:
    """V7: una carga pendiente no altera el conjunto; al confirmarla como versión nueva el
    trámite vuelve a Borrador. Devuelve la versión nueva, ya validada."""
    tramite_id = caso["ids"]["tramite"]
    antes, estado_antes = _vigentes(e, tramite_id), tramite(e.responsable, tramite_id)["estado"]
    cargado = _procesar(aplicacion, e, tramite_id, codigo)
    reg.verificar(
        "V7",
        nombre,
        "Una carga pendiente no cambia el conjunto ni el estado",
        (antes, estado_antes),
        (_vigentes(e, tramite_id), tramite(e.responsable, tramite_id)["estado"]),
    )
    sugerencia = archivo(e.responsable, tramite_id, cargado["id"])["sugerencia_version"]
    documento_id = caso["ids"][codigo[0]]
    reg.verificar(
        "V7",
        nombre,
        f"RF-06 sugiere {codigo} como versión nueva del documento vigente",
        documento_id,
        (sugerencia or {}).get("documento_id"),
    )
    respuesta = como_version(e.responsable, tramite_id, cargado["id"])
    assert respuesta.status_code == 201, respuesta.text
    nueva = int(respuesta.json()["version_vigente"]["id"])
    reg.verificar(
        "V7",
        nombre,
        "Al confirmar la versión nueva el trámite vuelve a Borrador (RN-12)",
        "borrador",
        tramite(e.responsable, tramite_id)["estado"],
        version=nueva,
    )
    # V8: la versión nueva no hereda validaciones: exige confirmación propia.
    pendientes = _por_campo(e.responsable, tramite_id, documento_id)
    reg.verificar(
        "V8",
        nombre,
        f"{codigo} empieza sin validaciones heredadas",
        [],
        sorted(c for c, d in pendientes.items() if d.get("vigente")),
    )
    caso["validaciones"][codigo] = _validar(e.responsable, tramite_id, documento_id, codigo)
    return nueva


def _ids_validaciones(datos: dict[str, Any], documento_id: int) -> set[int]:
    return {v["validacion_id"] for v in datos["validaciones"] if v["documento_id"] == documento_id}


# --- Verificaciones transversales ----------------------------------------------------------


def _v1(
    reg: Registro, caso: str, datos: dict[str, Any], ciclo: dict[str, Any], esperadas: set[int]
) -> None:
    reg.verificar(
        "V1",
        caso,
        "La decisión recupera su tarea, su ciclo y el conjunto exacto de versiones de ese ciclo",
        (ciclo["id"], esperadas),
        (datos["ciclo"]["id"], {v["version_id"] for v in datos["versiones"]}),
        decision=datos["decision"]["id"],
        tarea=datos["tarea"]["id"],
    )


def _v3(reg: Registro, caso: str, datos: dict[str, Any], codigos: tuple[str, ...]) -> None:
    reg.verificar(
        "V3",
        caso,
        f"Resultados de R1 a R4 para {'+'.join(sorted(codigos))} según el oráculo",
        _esperados(codigos),
        _controles(datos),
        controles=[c["id"] for c in datos["controles"]],
    )
    validaciones = {v["validacion_id"] for v in datos["validaciones"]}
    entradas = [
        (c["codigo_regla"][:2], bool(c["version_regla"]), v["validacion_id"] in validaciones)
        for c in datos["controles"]
        for v in c["valores"]
    ]
    reg.verificar(
        "V3",
        caso,
        "Cada ejecución tiene versión de regla y entradas que son validaciones humanas del ciclo",
        [],
        [x for x in entradas if not (x[1] and x[2])],
    )
    reg.verificar(
        "V3",
        caso,
        "Ninguna entrada de regla es una sugerencia sin confirmar",
        set(),
        {v["tipo"] for c in datos["controles"] for v in c["valores"]}
        - {"confirmacion", "correccion", "registro", "ausencia"},
    )


def _v4(reg: Registro, caso: str, decision: dict[str, Any], datos: dict[str, Any]) -> None:
    reg.verificar(
        "V4",
        caso,
        "Los controles considerados al decidir se recuperan desde la decisión",
        sorted(decision.get("controles_considerados") or []),
        sorted(c["id"] for c in datos["controles"]),
        decision=decision["id"],
    )
    reg.verificar(
        "V4",
        caso,
        "La decisión registró controles considerados (no una lista vacía)",
        True,
        bool(datos["controles"]),
    )


def _v5(reg: Registro, caso: str, e: Equipo, tramite_id: int, requeridas: set[str]) -> None:
    linea = obtener(e.responsable, f"/tramites/{tramite_id}/linea-tiempo")
    acciones = {h["accion"] for h in linea}
    reg.verificar(
        "V5",
        caso,
        "La línea de tiempo registra las acciones del recorrido",
        set(),
        requeridas - acciones,
    )
    completos = all(
        h.get("ocurrido_en") and h.get("accion") and h.get("entidad_tipo") and h.get("resultado")
        for h in linea
    )
    reg.verificar(
        "V5", caso, "Cada evento tiene instante, acción, entidad y resultado", True, completos
    )


# --- Recorridos ------------------------------------------------------------------------------


def _evd_a(aplicacion: Any, e: Equipo, reg: Registro) -> None:
    """EVD-A: {C-v1,O-v2,F-v1} aprobado → F-v2 confirmada → CR-2 {C-v1,O-v2,F-v2} (RN-12)."""
    nombre = "EVD-A"
    # F-v1 llega con el importe mal sugerido: la persona lo corrige (V2).
    caso = _conjunto(
        aplicacion, e, ("C-v1", "O-v2", "F-v1"), errores={"importe_total": "1312000.00"}
    )
    tramite_id, ids = caso["ids"]["tramite"], caso["ids"]
    _v2(reg, nombre, e, caso)
    ciclo_1 = iniciar_ciclo(e.responsable, tramite_id)
    legal, final = (t["id"] for t in ciclo_1["tareas"])
    _v6(reg, nombre, e, ciclo_1, ("C-v1", "O-v2", "F-v1"))
    d1a = decidir(e.revisor, legal).json()
    d1 = decidir(e.aprobador, final).json()
    reg.verificar(
        "V9",
        nombre,
        "CR-1 aprobado deja el trámite Aprobado",
        "aprobado",
        tramite(e.responsable, tramite_id)["estado"],
    )
    versiones_1 = _vigentes(e, tramite_id)
    ev1 = evidencia(e.responsable, d1["id"])
    _v1(reg, nombre, ev1, ciclo_1, versiones_1)
    _v3(reg, nombre, ev1, ("C-v1", "O-v2", "F-v1"))
    _v4(reg, nombre, d1, ev1)
    f2 = _nueva_version(aplicacion, e, caso, "F-v2", reg, nombre)
    despues = evidencia(e.responsable, d1["id"])
    reg.verificar(
        "V7",
        nombre,
        "DEC-1 conserva ciclo, versiones, validaciones y controles tras confirmar F-v2",
        (ev1["ciclo"]["id"], ev1["versiones"], ev1["validaciones"], ev1["controles"]),
        (
            despues["ciclo"]["id"],
            despues["versiones"],
            despues["validaciones"],
            despues["controles"],
        ),
        decision=d1["id"],
    )
    reg.verificar(
        "V4",
        nombre,
        "DEC-1 sigue ligada a sus controles originales tras recalcular",
        sorted(c["id"] for c in ev1["controles"]),
        sorted(c["id"] for c in despues["controles"]),
    )
    ciclo_2 = iniciar_ciclo(e.responsable, tramite_id)
    esperadas_2 = (
        versiones_1 - {v["version_id"] for v in ev1["versiones"] if v["documento_id"] == ids["F"]}
    ) | {f2}
    reg.verificar(
        "V9",
        nombre,
        "CR-2 considera exactamente {C-v1,O-v2,F-v2}",
        esperadas_2,
        {v["version_id"] for v in ciclo_2["versiones"]},
        ciclo=ciclo_2["id"],
    )
    reg.verificar(
        "V9",
        nombre,
        "Ninguna tarea de CR-2 hereda una decisión de CR-1",
        [None, None],
        [t["decision_id"] for t in ciclo_2["tareas"]],
    )
    d2 = decidir(e.revisor, ciclo_2["tareas"][0]["id"]).json()
    ev2 = evidencia(e.responsable, d2["id"])
    _v1(reg, nombre, ev2, ciclo_2, esperadas_2)
    _v3(reg, nombre, ev2, ("C-v1", "O-v2", "F-v2"))
    _v4(reg, nombre, d2, ev2)
    # V4 (EVD-01 §3): los controles de DEC-2 corresponden a CR-2. Los que comparte con DEC-1
    # solo pueden ser ejecuciones cuyas versiones siguen en CR-2 (R2 y R3: contrato y orden
    # no cambiaron); los que involucran la factura son nuevos.
    versiones_2 = {v["version_id"] for v in ev2["versiones"]}
    reg.verificar(
        "V4",
        nombre,
        "Los controles de DEC-2 solo consideran versiones de CR-2",
        [],
        [
            c["id"]
            for c in ev2["controles"]
            if not {v["version_id"] for v in c["versiones"]} <= versiones_2
        ],
    )
    compartidos = {c["id"] for c in ev1["controles"]} & {c["id"] for c in ev2["controles"]}
    reg.verificar(
        "V4",
        nombre,
        "Los controles compartidos con DEC-1 no involucran la factura reemplazada",
        [],
        [
            c["codigo_regla"][:2]
            for c in ev2["controles"]
            if c["id"] in compartidos and ids["F"] in {v["documento_id"] for v in c["versiones"]}
        ],
    )
    previa = ev1
    reg.verificar(
        "V8",
        nombre,
        "C-v1 y O-v2 conservan sus validaciones en CR-2",
        (_ids_validaciones(previa, ids["C"]), _ids_validaciones(previa, ids["O"])),
        (_ids_validaciones(ev2, ids["C"]), _ids_validaciones(ev2, ids["O"])),
    )
    reg.verificar(
        "V8",
        nombre,
        "Las validaciones de F-v2 son nuevas (no las de F-v1)",
        set(),
        _ids_validaciones(ev2, ids["F"]) & _ids_validaciones(previa, ids["F"]),
    )
    reg.verificar(
        "V8",
        nombre,
        "Las reglas se volvieron a ejecutar con F-v2",
        True,
        all(
            f2 in {v["version_id"] for v in c["versiones"]}
            for c in ev2["controles"]
            if c["codigo_regla"][:2] in ("R1", "R4")
        ),
    )
    _v5(
        reg,
        nombre,
        e,
        tramite_id,
        {
            "carga_confirmada",
            "documento_incorporado",
            "campo_confirmado",
            "campo_corregido",
            "regla_ejecutada",
            "flujo_confirmado",
            "tarea_asignada",
            "tarea_aprobada",
            "tramite_aprobado",
            "version_incorporada",
            "tramite_vuelve_a_borrador",
        },
    )
    _v10(reg, nombre, e, tramite_id, d1["id"], ids["F"], asignado=e.revisor)
    reg.verificar(
        "V7",
        nombre,
        "La decisión de la tarea legal de CR-1 no se transfiere a CR-2",
        False,
        d1a["id"] in {t["decision_id"] for t in ciclo_2["tareas"]},
    )


def _evd_b(aplicacion: Any, e: Equipo, reg: Registro) -> None:
    """EVD-B (demo): {C-v1,O-v1,F-v2} observado → O-v2 → CR-2 aprobado → firma simulada."""
    nombre = "EVD-B"
    codigos = ("C-v1", "O-v1", "F-v2")
    caso = _conjunto(aplicacion, e, codigos)
    tramite_id, ids = caso["ids"]["tramite"], caso["ids"]
    ciclo_1 = iniciar_ciclo(e.responsable, tramite_id)
    d1 = decidir(e.revisor, ciclo_1["tareas"][0]["id"], "observacion", MOTIVO).json()
    reg.verificar(
        "V9",
        nombre,
        "La observación deja el trámite Observado",
        "observado",
        tramite(e.responsable, tramite_id)["estado"],
    )
    versiones_1 = _vigentes(e, tramite_id)
    ev1 = evidencia(e.responsable, d1["id"])
    _v1(reg, nombre, ev1, ciclo_1, versiones_1)
    _v3(reg, nombre, ev1, codigos)
    _v4(reg, nombre, d1, ev1)
    o2 = _nueva_version(aplicacion, e, caso, "O-v2", reg, nombre)
    despues = evidencia(e.responsable, d1["id"])
    reg.verificar(
        "V7",
        nombre,
        "La observación conserva motivo, ciclo, versiones y controles",
        (MOTIVO, ev1["ciclo"]["id"], ev1["versiones"], ev1["controles"]),
        (
            despues["decision"]["motivo"],
            despues["ciclo"]["id"],
            despues["versiones"],
            despues["controles"],
        ),
        decision=d1["id"],
    )
    ciclo_2 = iniciar_ciclo(e.responsable, tramite_id)
    esperadas_2 = {
        v
        for v in versiones_1
        if v not in {x["version_id"] for x in ev1["versiones"] if x["documento_id"] == ids["O"]}
    } | {o2}
    reg.verificar(
        "V9",
        nombre,
        "CR-2 considera exactamente {C-v1,O-v2,F-v2}",
        esperadas_2,
        {v["version_id"] for v in ciclo_2["versiones"]},
        ciclo=ciclo_2["id"],
    )
    legal, final = (t["id"] for t in ciclo_2["tareas"])
    decidir(e.revisor, legal)
    d2 = decidir(e.aprobador, final).json()
    ev2 = evidencia(e.responsable, d2["id"])
    _v1(reg, nombre, ev2, ciclo_2, esperadas_2)
    _v3(reg, nombre, ev2, ("C-v1", "O-v2", "F-v2"))
    _v4(reg, nombre, d2, ev2)
    _v11(reg, nombre, e, caso, ciclo_2, d2["id"], versiones_1 - esperadas_2)


def _evd_c(aplicacion: Any, e: Equipo, reg: Registro) -> None:
    """EVD-C: subsanación sin archivo nuevo (RN-13): misma versión, Pendiente de validación."""
    nombre = "EVD-C"
    caso = _conjunto(aplicacion, e, ("C-v1", "O-v1", "F-v2"))
    tramite_id, ids = caso["ids"]["tramite"], caso["ids"]
    ciclo_1 = iniciar_ciclo(e.responsable, tramite_id)
    primera, segunda = (t["id"] for t in ciclo_1["tareas"])
    aprobacion = decidir(e.revisor, primera).json()
    observacion = decidir(e.aprobador, segunda, "observacion", MOTIVO).json()
    versiones = _vigentes(e, tramite_id)
    previa = evidencia(e.responsable, observacion["id"])
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/subsanacion", headers=e.responsable.encabezados
    )
    assert respuesta.status_code == 200, respuesta.text
    # Se corrige un dato (la fecha de la orden) sin cargar un archivo nuevo.
    fecha = _por_campo(e.responsable, tramite_id, ids["O"])["fecha"]
    e.cliente.post(
        f"/tramites/{tramite_id}/documentos/{ids['O']}/validaciones",
        json={
            "campo": "fecha",
            "valor_validado": VALORES["O-v2"]["fecha"],
            "reemplaza_a_id": fecha["vigente"]["id"],
        },
        headers=e.responsable.encabezados,
    )
    reg.verificar(
        "V7",
        nombre,
        "La subsanación no fabrica una versión documental",
        versiones,
        _vigentes(e, tramite_id),
    )
    reg.verificar(
        "V9",
        nombre,
        "El trámite pasa a Pendiente de validación (RN-13), no a Borrador",
        "pendiente_validacion",
        tramite(e.responsable, tramite_id)["estado"],
    )
    ciclo_2 = iniciar_ciclo(e.responsable, tramite_id)
    reg.verificar(
        "V9",
        nombre,
        "La nueva revisión no hereda las decisiones anteriores",
        [None, None],
        [t["decision_id"] for t in ciclo_2["tareas"]],
    )
    for decision in (aprobacion, observacion):
        datos = evidencia(e.responsable, decision["id"])
        reg.verificar(
            "V1",
            nombre,
            "Las decisiones de CR-1 siguen ligadas a CR-1 y a sus versiones",
            (ciclo_1["id"], versiones),
            (datos["ciclo"]["id"], {v["version_id"] for v in datos["versiones"]}),
            decision=decision["id"],
        )
    reg.verificar(
        "V2",
        nombre,
        "La observación conserva el valor validado que se observó",
        [v["valor_validado"] for v in previa["validaciones"] if v["campo"] == "fecha"],
        [
            v["valor_validado"]
            for v in evidencia(e.responsable, observacion["id"])["validaciones"]
            if v["campo"] == "fecha"
        ],
    )


def _evd_n12(aplicacion: Any, e: Equipo, reg: Registro) -> None:
    """EVD-N12: una tarea abierta de un ciclo desplazado no admite decisión."""
    nombre = "EVD-N12"
    caso = _conjunto(aplicacion, e, ("C-v1", "O-v2", "F-v1"))
    tramite_id = caso["ids"]["tramite"]
    ciclo_1 = iniciar_ciclo(e.responsable, tramite_id)
    primera, pendiente = (t["id"] for t in ciclo_1["tareas"])
    aprobacion = decidir(e.revisor, primera).json()
    previa = evidencia(e.responsable, aprobacion["id"])
    _nueva_version(aplicacion, e, caso, "F-v2", reg, nombre)
    respuesta = decidir(e.aprobador, pendiente)
    reg.verificar(
        "V7",
        nombre,
        "La tarea abierta del ciclo desplazado rechaza la decisión",
        (409, TAREA_DESACTUALIZADA),
        (respuesta.status_code, respuesta.json().get("detalle")),
        tarea=pendiente,
    )
    (ciclo,) = ciclos(e.responsable, tramite_id)
    reg.verificar(
        "V7",
        nombre,
        "El ciclo queda desplazado y la tarea anulada, sin decisión",
        ("desplazado", [("aprobada", True), ("anulada", False)]),
        (ciclo["estado"], [(t["estado"], t["decision_id"] is not None) for t in ciclo["tareas"]]),
    )
    actual = evidencia(e.responsable, aprobacion["id"])
    reg.verificar(
        "V7",
        nombre,
        "La evidencia de la decisión previa no se altera retroactivamente",
        (previa["versiones"], previa["validaciones"], previa["controles"]),
        (actual["versiones"], actual["validaciones"], actual["controles"]),
    )


# --- V2, V6, V10 y V11 -----------------------------------------------------------------------


def _v2(reg: Registro, caso: str, e: Equipo, datos: dict[str, Any]) -> None:
    tramite_id, factura = datos["ids"]["tramite"], datos["ids"]["F"]
    validaciones = datos["validaciones"]["F-v1"]
    importe, numero = validaciones["importe_total"], validaciones["numero"]
    vigente = tramite(e.responsable, tramite_id)["documentos"]
    version_f = next(d["version_vigente"]["id"] for d in vigente if d["id"] == factura)
    reg.verificar(
        "V2",
        caso,
        "Un dato corregido conserva la sugerencia y registra el valor validado",
        ("correccion", VALORES["F-v1"]["importe_total"], version_f, e.responsable.usuario_id),
        (
            importe["tipo"],
            importe["valor_validado"],
            importe["version_id"],
            importe["validador_id"],
        ),
        validacion=importe["id"],
        sugerencia=importe["valor_sugerido_id"],
    )
    reg.verificar(
        "V2",
        caso,
        "Un dato confirmado referencia su sugerencia",
        ("confirmacion", True),
        (numero["tipo"], numero["valor_sugerido_id"] is not None),
        validacion=numero["id"],
    )
    campos = _por_campo(e.responsable, tramite_id, factura)
    sugerida = campos["importe_total"]["sugerencia"]
    reg.verificar(
        "V2",
        caso,
        "La sugerencia corregida sigue recuperable con su procedencia",
        ("1312000.00", True),
        (sugerida["valor"], bool(sugerida.get("fuente") or sugerida.get("localizador"))),
        sugerencia=sugerida["id"],
    )
    reg.verificar(
        "V2",
        caso,
        "La validación registra el instante de la intervención",
        True,
        bool(importe.get("validado_en")),
    )


def _v6(
    reg: Registro, caso: str, e: Equipo, ciclo: dict[str, Any], codigos: tuple[str, ...]
) -> None:
    tramite_id = ciclo["tramite_id"]
    hay_advertencia = "advertencia" in _esperados(codigos).values()
    estados = [t["estado"] for t in ciclos(e.responsable, tramite_id)[-1]["tareas"]]
    reg.verificar(
        "V6",
        caso,
        "Con una advertencia, ninguna tarea se resuelve sola",
        (True, ["pendiente", "en_espera"]),
        (hay_advertencia, estados),
    )
    tarea = ciclo["tareas"][0]["id"]
    sin_motivo = decidir(e.revisor, tarea, "observacion", None)
    reg.verificar("V6", caso, "Observar sin motivo se rechaza", 422, sin_motivo.status_code)
    admin = decidir(e.administrador, tarea)
    reg.verificar(
        "V6",
        caso,
        "El administrador operativo no puede resolver la tarea",
        True,
        admin.status_code in (403, 404),
    )
    otro = contexto(e.cliente, e.responsable.motor, "revisor_aprobador")
    ajeno = decidir(otro, tarea)
    reg.verificar(
        "V6",
        caso,
        "Un revisor no asignado no puede resolver la tarea",
        True,
        ajeno.status_code in (403, 404),
    )


def _v10(
    reg: Registro,
    caso: str,
    e: Equipo,
    tramite_id: int,
    decision_id: int,
    documento_id: int,
    asignado: Contexto,
) -> None:
    rutas = {
        "tramite": f"/tramites/{tramite_id}",
        "evidencia": f"/decisiones/{decision_id}/evidencia",
        "validaciones": f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones",
        "linea_tiempo": f"/tramites/{tramite_id}/linea-tiempo",
        "archivos": f"/tramites/{tramite_id}/archivos",
    }
    m = e.responsable.motor
    actores = {
        "responsable_ajeno": contexto(e.cliente, m, "responsable_tramite"),
        "revisor_sin_tarea": contexto(e.cliente, m, "revisor_aprobador"),
        "administrador": e.administrador,
    }
    observado, filtraciones = {}, []
    for actor, ctx in actores.items():
        for operacion, ruta in rutas.items():
            r = ctx.cliente.get(ruta, headers=ctx.encabezados)
            observado[f"{actor}:{operacion}"] = r.status_code in (403, 404)
            if SENSIBLE in r.text or VALORES["F-v1"]["importe_total"] in r.text:
                filtraciones.append(f"{actor}:{operacion}")
    reg.verificar(
        "V10",
        caso,
        "Actores sin acceso no recuperan trámite, evidencia, datos ni historia",
        dict.fromkeys(observado, True),
        observado,
    )
    reg.verificar("V10", caso, "Las denegaciones no filtran datos del trámite", [], filtraciones)
    permitidos = {
        "responsable": e.responsable.cliente.get(
            rutas["evidencia"], headers=e.responsable.encabezados
        ).status_code,
        "revisor_asignado": asignado.cliente.get(
            rutas["evidencia"], headers=asignado.encabezados
        ).status_code,
    }
    reg.verificar(
        "V10",
        caso,
        "El responsable y el revisor asignado sí reconstruyen la evidencia",
        {"responsable": 200, "revisor_asignado": 200},
        permitidos,
    )


def _v11(
    reg: Registro,
    caso: str,
    e: Equipo,
    datos: dict[str, Any],
    ciclo: dict[str, Any],
    decision_id: int,
    ajenas: set[int],
) -> None:
    tramite_id = datos["ids"]["tramite"]
    contrato = next(v for v in ciclo["versiones"] if v["documento_id"] == datos["ids"]["C"])
    if ajenas:
        fuera = e.cliente.post(
            f"/tramites/{tramite_id}/firma",
            json={"version_id": min(ajenas)},
            headers=e.aprobador.encabezados,
        )
        reg.verificar(
            "V11",
            caso,
            "No se firma una versión ajena al ciclo aprobado",
            True,
            fuera.status_code in (409, 422),
        )
    sin_autorizacion = e.cliente.post(
        f"/tramites/{tramite_id}/firma",
        json={"version_id": contrato["version_id"]},
        headers=e.revisor.encabezados,
    )
    reg.verificar(
        "V11",
        caso,
        "Sin autorización específica no se firma",
        True,
        sin_autorizacion.status_code in (403, 409),
    )
    r = e.cliente.post(
        f"/tramites/{tramite_id}/firma",
        json={"version_id": contrato["version_id"]},
        headers=e.aprobador.encabezados,
    )
    assert r.status_code == 201, r.text
    firma = r.json()
    reg.verificar(
        "V11",
        caso,
        "La firma es simulada, de la versión del ciclo, con firmante y huella",
        (True, contrato["version_id"], ciclo["id"], e.aprobador.usuario_id, True, True),
        (
            firma["simulada"],
            firma["version_id"],
            firma["ciclo_revision_id"],
            firma["firmante_id"],
            firma["leyenda"].startswith("Firma digital simulada"),
            len(firma.get("referencia_integridad") or "") == 64,
        ),
        firma=firma["id"],
    )
    reg.verificar(
        "V11",
        caso,
        "El trámite queda Cerrado",
        "cerrado",
        tramite(e.responsable, tramite_id)["estado"],
    )
    carga = e.cliente.post(
        f"/tramites/{tramite_id}/cargas",
        json={"nombre": "O-v3.pdf", "formato": "pdf", "tamano_bytes": 1000},
        headers=e.responsable.encabezados,
    )
    reg.verificar(
        "V11", caso, "Desde Cerrado no se aceptan documentos nuevos", 409, carga.status_code
    )
    historia = evidencia(e.responsable, decision_id)
    reg.verificar(
        "V11",
        caso,
        "La historia sigue consultable y muestra la firma",
        firma["id"],
        (historia.get("firma") or {}).get("id"),
    )


# --- Ejecución y paquete probatorio ----------------------------------------------------------


def _paquete(reg: Registro, inicio: datetime) -> dict[str, Any]:
    return {
        "verificacion": "EVD-01 — cadena de evidencia documental",
        "ejecutada_en": inicio.isoformat(),
        **cmp._commit(cmp.RAIZ_REPOSITORIO),
        "entorno": "local: API FastAPI (TestClient) + PostgreSQL 16 con pgvector; "
        "procesamiento con dobles controlados (EVD-01 §1, condición 6)",
        "oraculo": {
            "archivo": "demo/cadena_evidencia/oraculo_PD07_v2.json",
            "id": ORACULO["id"],
            "estado": ORACULO["estado"],
            "sha256": HUELLA_ORACULO,
        },
        "criterios": {
            v: {
                "estado": reg.estado(v),
                "prioridad": "esencial"
                if v in ESENCIALES
                else ("complementario" if v in ("V5", "V6", "V8") else "ampliación"),
                "comprobaciones": sum(c.criterio == v for c in reg.comprobaciones),
            }
            for v in CRITERIOS
        },
        "comprobaciones": [c.__dict__ for c in reg.comprobaciones],
    }


def _json(valor: Any) -> Any:
    if isinstance(valor, set):
        return sorted(valor)
    if isinstance(valor, tuple):
        return list(valor)
    return str(valor)


def test_evd01_v1_a_v11_contra_el_oraculo_pd07(aplicacion: Any, e: Equipo) -> None:
    inicio = datetime.now(UTC)
    reg = Registro()
    for recorrido in (_evd_a, _evd_b, _evd_c, _evd_n12):
        recorrido(aplicacion, e, reg)
    paquete = _paquete(reg, inicio)
    destino = os.environ.get("ATLAS_EVIDENCIA_EVD01")
    if destino:
        carpeta = Path(destino)
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "evd01.json").write_text(
            json.dumps(paquete, ensure_ascii=False, indent=2, default=_json) + "\n", "utf-8"
        )
    fallidas = [
        f"{c.criterio} {c.caso}: {c.descripcion} "
        f"(esperado {c.esperado!r}, observado {c.observado!r})"
        for c in reg.comprobaciones
        if not c.cumple
    ]
    assert not fallidas, "\n".join(fallidas)
    assert all(v["estado"] == "Cumple" for v in paquete["criterios"].values())
