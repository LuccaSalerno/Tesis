"""Flujo de revisión por la API, compartido por las pruebas y los escenarios BDD del hito 1.8.

Cuentas, documentos y valores sintéticos (PD-07, AGENTS.md §2.4). DO-2026-10-22-TAR.
"""

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, crear_tramite
from tests.flujo_vinculos import C_V1, F_V1, O_V1, documento, resolver, vincular, vinculos

# Todos los campos del esquema de cada tipo (RC-P04): los exige la confirmación del flujo.
C_COMPLETO = {"contraparte": "Servicios Ficticios SA", "fecha_celebracion": "2026-02-20", **C_V1}
O_COMPLETO = {"numero": "OC-0001", "proveedor": "Servicios Ficticios SA", **O_V1}
F_COMPLETO = {
    "numero": "F-0001-00000001",
    "fecha_emision": "2027-03-20",
    "emisor": "Servicios Ficticios SA",
    **F_V1,
}


@dataclass
class Equipo:
    """Responsable, revisor legal, aprobador con autorización de cierre y administrador."""

    responsable: Contexto
    revisor: Contexto
    aprobador: Contexto
    administrador: Contexto

    @property
    def cliente(self) -> TestClient:
        return self.responsable.cliente


def contexto(
    cliente: TestClient, motor: Engine, *roles: str, autorizacion_cierre: bool = False
) -> Contexto:
    usuario_id, sub = crear_cuenta(motor, *roles, autorizacion_cierre=autorizacion_cierre)
    return Contexto(cliente, motor, usuario_id, portador(sub))


def equipo(cliente: TestClient, motor: Engine) -> Equipo:
    return Equipo(
        responsable=contexto(cliente, motor, "responsable_tramite"),
        revisor=contexto(cliente, motor, "revisor_aprobador"),
        aprobador=contexto(cliente, motor, "revisor_aprobador", autorizacion_cierre=True),
        administrador=contexto(cliente, motor, "administrador_operativo"),
    )


def crear_plantilla(
    admin: Contexto, alcance: str, revisores: list[int], nombre: str = "Revisión de contratos"
) -> httpx.Response:
    return admin.cliente.post(
        "/plantillas-flujo",
        json={
            "nombre": nombre,
            "alcance": alcance,
            "pasos": [
                {"nombre": f"Paso {i}", "revisor_por_defecto_id": r}
                for i, r in enumerate(revisores, start=1)
            ],
        },
        headers=admin.encabezados,
    )


def plantilla(admin: Contexto, alcance: str, revisores: list[int]) -> dict[str, Any]:
    """Plantilla nueva y activa del alcance (reemplaza a la anterior)."""
    respuesta = crear_plantilla(admin, alcance, revisores)
    assert respuesta.status_code == 201, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def plantilla_de_contratos(e: Equipo) -> dict[str, Any]:
    """RC-P03.1: «revisión legal» y luego «aprobación final» por quien puede cerrar."""
    return plantilla(e.administrador, "contrato", [e.revisor.usuario_id, e.aprobador.usuario_id])


def tramite_con_contrato(e: Equipo) -> dict[str, int]:
    """Trámite con el contrato C-v1 validado por completo."""
    tramite = crear_tramite(e.responsable)["id"]
    contrato = documento(e.responsable, tramite, "Contrato C-v1", "contrato", C_COMPLETO)
    return {"tramite": tramite, "contrato": contrato}


def tramite_con_conjunto(e: Equipo) -> dict[str, int]:
    """Contrato, orden y factura validados y vinculados (R1 a R4 con ejecuciones)."""
    ids = tramite_con_contrato(e)
    r = e.responsable
    ids["orden"] = documento(r, ids["tramite"], "Orden de compra", "orden_compra", O_COMPLETO)
    ids["factura"] = documento(r, ids["tramite"], "Factura", "factura", F_COMPLETO)
    for origen, destino in (("orden", "contrato"), ("factura", "orden")):
        sugeridos = [
            v
            for v in vinculos(r, ids["tramite"])["sugeridos"]
            if {v["documento_origen_id"], v["documento_destino_id"]} == {ids[origen], ids[destino]}
        ]
        if sugeridos:
            assert (
                resolver(r, ids["tramite"], sugeridos[0]["id"], "confirmacion").status_code == 200
            )
        else:
            assert vincular(r, ids["tramite"], ids[origen], ids[destino]).status_code == 201
    return ids


def enviar_a_validacion(ctx: Contexto, tramite_id: int) -> httpx.Response:
    return ctx.cliente.post(f"/tramites/{tramite_id}/envio-a-validacion", headers=ctx.encabezados)


def flujo_sugerido(ctx: Contexto, tramite_id: int) -> dict[str, Any]:
    respuesta = ctx.cliente.get(f"/tramites/{tramite_id}/flujo-sugerido", headers=ctx.encabezados)
    assert respuesta.status_code == 200, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def confirmar_flujo(
    ctx: Contexto, tramite_id: int, plantilla_id: int | None = None, version: int | None = None
) -> httpx.Response:
    if plantilla_id is None:
        sugerido = flujo_sugerido(ctx, tramite_id)
        plantilla_id, version = sugerido["plantilla_id"], sugerido["version_plantilla"]
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/ciclos",
        json={"plantilla_id": plantilla_id, "version_plantilla": version},
        headers=ctx.encabezados,
    )


def iniciar_ciclo(ctx: Contexto, tramite_id: int) -> dict[str, Any]:
    """Envía a validación (si está en Borrador) y confirma el flujo sugerido."""
    respuesta = enviar_a_validacion(ctx, tramite_id)
    assert respuesta.status_code in (200, 409), respuesta.text
    respuesta = confirmar_flujo(ctx, tramite_id)
    assert respuesta.status_code == 201, respuesta.text
    ciclo: dict[str, Any] = respuesta.json()
    return ciclo


def decidir(
    ctx: Contexto, tarea_id: int, tipo: str = "aprobacion", motivo: str | None = None
) -> httpx.Response:
    return ctx.cliente.post(
        f"/tareas/{tarea_id}/decision",
        json={"tipo": tipo, "motivo": motivo},
        headers=ctx.encabezados,
    )


def decidida(
    ctx: Contexto, tarea_id: int, tipo: str = "aprobacion", motivo: str | None = None
) -> dict[str, Any]:
    respuesta = decidir(ctx, tarea_id, tipo, motivo)
    assert respuesta.status_code == 201, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def obtener(ctx: Contexto, ruta: str, esperado: int = 200) -> Any:
    respuesta = ctx.cliente.get(ruta, headers=ctx.encabezados)
    assert respuesta.status_code == esperado, respuesta.text
    return respuesta.json()


def tramite(ctx: Contexto, tramite_id: int) -> dict[str, Any]:
    datos: dict[str, Any] = obtener(ctx, f"/tramites/{tramite_id}")
    return datos


def ciclos(ctx: Contexto, tramite_id: int) -> list[dict[str, Any]]:
    datos: list[dict[str, Any]] = obtener(ctx, f"/tramites/{tramite_id}/ciclos")
    return datos


def evidencia(ctx: Contexto, decision_id: int) -> dict[str, Any]:
    datos: dict[str, Any] = obtener(ctx, f"/decisiones/{decision_id}/evidencia")
    return datos
