"""Archivos procesados con respuestas fijas para sugerir una versión nueva (RF-06, RF-07),
compartidos por las pruebas y los escenarios BDD EVD-A y EVD-B.
Valores sintéticos del oráculo de la cadena de evidencia."""

from typing import Any

import httpx

from atlas.dominio.enumeraciones import TipoDocumental
from atlas.procesamiento import esquemas
from tests import archivos
from tests.flujo_api import Contexto, cargar
from tests.flujo_procesamiento import recorrer, trabajo_de
from tests.procesamiento_fijo import ModeloFijo, dato


def procesado(
    aplicacion: Any, ctx: Contexto, tramite_id: int, tipo: str, campos: dict[str, str]
) -> dict[str, Any]:
    """Carga un DOCX sintético con los valores citados y lo procesa: queda pendiente."""
    lineas = [f"{campo} | {valor}" for campo, valor in campos.items()]
    contenido = archivos.docx(" · ".join([f"Documento sintético {tipo}", *lineas]))
    archivo = cargar(ctx, tramite_id, contenido, formato="docx")
    modelo = ModeloFijo(
        {
            esquemas.HERRAMIENTA_CLASIFICACION: {"tipo": tipo},
            # El esquema exige todos los campos del tipo; los ausentes vuelven sin valor.
            esquemas.HERRAMIENTA_EXTRACCION: {
                c.nombre: (
                    dato(campos[c.nombre], f"{c.nombre} | {campos[c.nombre]}")
                    if c.nombre in campos
                    else dato(None)
                )
                for c in esquemas.CAMPOS[TipoDocumental(tipo)]
            },
        }
    )
    salidas = recorrer(aplicacion, trabajo_de(ctx.motor, archivo["id"]), modelo)
    assert salidas[-1] == {"resultado": "persistido"}, salidas[-1]
    return archivo


def archivo(ctx: Contexto, tramite_id: int, archivo_id: int) -> dict[str, Any]:
    respuesta = ctx.cliente.get(f"/tramites/{tramite_id}/archivos", headers=ctx.encabezados)
    assert respuesta.status_code == 200, respuesta.text
    return next(a for a in respuesta.json() if a["id"] == archivo_id)


def como_version(ctx: Contexto, tramite_id: int, archivo_id: int) -> httpx.Response:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/archivos/{archivo_id}/version", headers=ctx.encabezados
    )


def descartar(ctx: Contexto, tramite_id: int, archivo_id: int) -> httpx.Response:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/archivos/{archivo_id}/descarte", headers=ctx.encabezados
    )
