"""Documentos validados, vínculos y controles por la API, compartidos por las pruebas y los
escenarios BDD del hito 1.7. Valores sintéticos del oráculo de la cadena de evidencia."""

from typing import Any

import httpx

from tests import archivos
from tests.flujo_api import Contexto, cargar, incorporar

CUIT = "30-96472518-3"
OTRO_CUIT = "30-71234567-1"

C_V1 = {
    "cuit_contraparte": CUIT,
    "vigencia_desde": "2026-03-01",
    "vigencia_hasta": "2027-02-28",
    "monto_total": "1250000.00",
    "moneda": "ARS",
}
O_V1 = {
    "cuit_proveedor": CUIT,
    "fecha": "2027-03-15",
    "importe_total": "1250000.00",
    "moneda": "ARS",
}
O_V2 = {**O_V1, "fecha": "2026-09-15"}
F_V1 = {"cuit_emisor": CUIT, "importe_total": "1312500.00", "moneda": "ARS"}
F_V2 = {**F_V1, "importe_total": "1250000.00"}


def validar(
    ctx: Contexto,
    tramite_id: int,
    documento_id: int,
    campo: str,
    valor: str,
    reemplaza_a_id: int | None = None,
) -> dict[str, Any]:
    """Valor registrado por el responsable sin sugerencia previa (RF-12)."""
    respuesta = ctx.cliente.post(
        f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones",
        json={"campo": campo, "valor_validado": valor, "reemplaza_a_id": reemplaza_a_id},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 201, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def documento(
    ctx: Contexto,
    tramite_id: int,
    nombre: str,
    tipo: str | None = None,
    campos: dict[str, str] | None = None,
) -> int:
    """Incorpora un PDF sintético y valida su clasificación y los campos indicados."""
    archivo = cargar(ctx, tramite_id, archivos.pdf())
    respuesta = incorporar(ctx, tramite_id, archivo["id"], nombre=nombre)
    assert respuesta.status_code == 201, respuesta.text
    documento_id = int(respuesta.json()["id"])
    if tipo is not None:
        validar(ctx, tramite_id, documento_id, "tipo_documental", tipo)
    for campo, valor in (campos or {}).items():
        validar(ctx, tramite_id, documento_id, campo, valor)
    return documento_id


def vincular(
    ctx: Contexto,
    tramite_id: int,
    origen: int,
    destino: int,
    tipo: str = "campos",
    justificacion: str = "Comparten el CUIT del proveedor",
    encabezados: dict[str, str] | None = None,
    **extra: Any,
) -> httpx.Response:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/vinculos",
        json={
            "documento_origen_id": origen,
            "documento_destino_id": destino,
            "tipo": tipo,
            "justificacion": justificacion,
            **extra,
        },
        headers=encabezados or ctx.encabezados,
    )


def vinculos(ctx: Contexto, tramite_id: int, historial: bool = False) -> dict[str, Any]:
    respuesta = ctx.cliente.get(
        f"/tramites/{tramite_id}/vinculos",
        params={"historial": historial},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 200, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def resolver(ctx: Contexto, tramite_id: int, vinculo_id: int, accion: str) -> httpx.Response:
    """`accion`: confirmacion, rechazo o eliminacion (DELETE)."""
    ruta = f"/tramites/{tramite_id}/vinculos/{vinculo_id}"
    if accion == "eliminacion":
        return ctx.cliente.delete(ruta, headers=ctx.encabezados)
    return ctx.cliente.post(f"{ruta}/{accion}", headers=ctx.encabezados)


def controles(ctx: Contexto, tramite_id: int, historial: bool = False) -> dict[str, Any]:
    respuesta = ctx.cliente.get(
        f"/tramites/{tramite_id}/controles",
        params={"historial": historial},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 200, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def resultados(ctx: Contexto, tramite_id: int) -> dict[str, str]:
    """Resultado vigente por regla (R1…R4) del trámite."""
    return {c["codigo_regla"][:2]: c["resultado"] for c in controles(ctx, tramite_id)["vigentes"]}


def control(ctx: Contexto, tramite_id: int, prefijo: str) -> dict[str, Any]:
    return next(
        c for c in controles(ctx, tramite_id)["vigentes"] if c["codigo_regla"].startswith(prefijo)
    )


def conjunto(
    ctx: Contexto, tramite_id: int, orden: dict[str, str], factura: dict[str, str]
) -> dict[str, int]:
    """Contrato C-v1 + orden + factura validados y vinculados: se confirma la sugerencia del
    sistema (RF-15) o, si no la hay, se vincula a mano (RF-14)."""
    ids = {
        "contrato": documento(ctx, tramite_id, "Contrato C-v1", "contrato", C_V1),
        "orden": documento(ctx, tramite_id, "Orden de compra", "orden_compra", orden),
        "factura": documento(ctx, tramite_id, "Factura", "factura", factura),
    }
    for origen, destino in (("orden", "contrato"), ("factura", "orden")):
        pendiente = next(
            (
                v
                for v in vinculos(ctx, tramite_id)["sugeridos"]
                if {v["documento_origen_id"], v["documento_destino_id"]}
                == {ids[origen], ids[destino]}
            ),
            None,
        )
        if pendiente is not None:
            respuesta = resolver(ctx, tramite_id, pendiente["id"], "confirmacion")
            assert respuesta.status_code == 200, respuesta.text
        else:
            respuesta = vincular(ctx, tramite_id, ids[origen], ids[destino])
            assert respuesta.status_code == 201, respuesta.text
    return ids
