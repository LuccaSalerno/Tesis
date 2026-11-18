"""Campos por tipo documental y esquemas de salida del modelo (§5.3.2, §5.4.3).

Los esquemas no admiten propiedades adicionales: la respuesta se valida contra ellos
en el backend antes de registrar cualquier sugerencia.
"""

import hashlib
from dataclasses import dataclass
from importlib import resources
from typing import Any, Final

from atlas.dominio.enumeraciones import TipoDocumental
from atlas.procesamiento.valores import ClaseValor


@dataclass(frozen=True)
class Campo:
    nombre: str
    clase: ClaseValor
    descripcion: str


_T, _C, _F, _I, _M = (
    ClaseValor.TEXTO,
    ClaseValor.CUIT,
    ClaseValor.FECHA,
    ClaseValor.IMPORTE,
    ClaseValor.MONEDA,
)

CAMPOS: Final[dict[TipoDocumental, tuple[Campo, ...]]] = {
    TipoDocumental.CONTRATO: (
        Campo("contraparte", _T, "Razón social de la contraparte del contrato"),
        Campo("cuit_contraparte", _C, "CUIT de la contraparte"),
        Campo("fecha_celebracion", _F, "Fecha de celebración del contrato"),
        Campo("vigencia_desde", _F, "Fecha de inicio de la vigencia"),
        Campo("vigencia_hasta", _F, "Fecha de fin de la vigencia"),
        Campo("monto_total", _I, "Monto total del contrato"),
        Campo("moneda", _M, "Moneda del monto total"),
    ),
    TipoDocumental.ORDEN_COMPRA: (
        Campo("numero", _T, "Número de la orden de compra"),
        Campo("fecha", _F, "Fecha de la orden de compra"),
        Campo("proveedor", _T, "Razón social del proveedor"),
        Campo("cuit_proveedor", _C, "CUIT del proveedor"),
        Campo("importe_total", _I, "Importe total"),
        Campo("moneda", _M, "Moneda del importe total"),
    ),
    TipoDocumental.FACTURA: (
        Campo("numero", _T, "Número de la factura"),
        Campo("fecha_emision", _F, "Fecha de emisión"),
        Campo("emisor", _T, "Razón social del emisor"),
        Campo("cuit_emisor", _C, "CUIT del emisor"),
        Campo("importe_total", _I, "Importe total"),
        Campo("moneda", _M, "Moneda del importe total"),
    ),
    TipoDocumental.PRESUPUESTO: (
        Campo("numero", _T, "Número del presupuesto"),
        Campo("fecha", _F, "Fecha del presupuesto"),
        Campo("proveedor", _T, "Razón social del proveedor"),
        Campo("cuit_proveedor", _C, "CUIT del proveedor"),
        Campo("importe_total", _I, "Importe total"),
        Campo("moneda", _M, "Moneda del importe total"),
    ),
    TipoDocumental.COMPROBANTE: (
        Campo("numero", _T, "Número del comprobante"),
        Campo("fecha", _F, "Fecha del comprobante"),
        Campo("contraparte", _T, "Razón social de la contraparte"),
        Campo("cuit_contraparte", _C, "CUIT de la contraparte"),
        Campo("importe", _I, "Importe del comprobante"),
        Campo("moneda", _M, "Moneda del importe"),
    ),
}

VERSION_INSTRUCCIONES_CLASIFICACION: Final = "clasificacion-v1"
VERSION_INSTRUCCIONES_EXTRACCION: Final = "extraccion-v1"
VERSION_INSTRUCCIONES_CONSULTA: Final = "consulta-v1"
HERRAMIENTA_CONSULTA: Final = "registrar_respuesta"
VERSION_ESQUEMA_CLASIFICACION: Final = "esquema-clasificacion-v1"
HERRAMIENTA_CLASIFICACION: Final = "registrar_clasificacion"
HERRAMIENTA_EXTRACCION: Final = "registrar_campos"
CAMPO_CLASIFICACION: Final = "tipo_documental"

# Huella de cada versión de instrucciones registrada: si el texto cambia, hay que
# registrar una versión nueva (las sugerencias conservan la versión que las produjo).
HUELLAS_INSTRUCCIONES: Final = {
    VERSION_INSTRUCCIONES_CLASIFICACION: (
        "cad807d75ad4d8f3dbdfa623d413d10a7f56622a3c1ec765ba4ae0787f137cc3"
    ),
    VERSION_INSTRUCCIONES_EXTRACCION: (
        "bbfbc7a8d3ac4012f0005ee03d180617a0705eaf36a6fdc6d3fef452f52c65a2"
    ),
    VERSION_INSTRUCCIONES_CONSULTA: (
        "ea3a8f83129b87f8967d6f783e7b7e36412ac8b81856c70385df4f9dab437cd6"
    ),
}


def instrucciones(version: str) -> str:
    nombre = version.replace("-", "_") + ".txt"
    return (resources.files("atlas.procesamiento.instrucciones") / nombre).read_text("utf-8")


def huella(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def version_esquema_extraccion(tipo: TipoDocumental) -> str:
    return f"esquema-extraccion-{tipo.value}-v1"


def herramienta_clasificacion() -> dict[str, Any]:
    return {
        "name": HERRAMIENTA_CLASIFICACION,
        "description": "Registra la categoría del documento.",
        "schema": {
            "type": "object",
            "properties": {"tipo": {"type": "string", "enum": [t.value for t in TipoDocumental]}},
            "required": ["tipo"],
            "additionalProperties": False,
        },
    }


def herramienta_extraccion(tipo: TipoDocumental) -> dict[str, Any]:
    dato = {
        "type": "object",
        "properties": {
            "valor": {"type": ["string", "null"]},
            "pagina": {"type": ["integer", "null"], "minimum": 1},
            "cita": {"type": ["string", "null"], "maxLength": 500},
        },
        "required": ["valor", "pagina", "cita"],
        "additionalProperties": False,
    }
    campos = CAMPOS[tipo]
    return {
        "name": HERRAMIENTA_EXTRACCION,
        "description": "Registra los campos extraídos: "
        + "; ".join(f"{c.nombre}: {c.descripcion}" for c in campos),
        "schema": {
            "type": "object",
            "properties": {c.nombre: dato for c in campos},
            "required": [c.nombre for c in campos],
            "additionalProperties": False,
        },
    }


def herramienta_consulta() -> dict[str, Any]:
    """RF-13: la respuesta son afirmaciones, cada una con los fragmentos que la respaldan."""
    return {
        "name": HERRAMIENTA_CONSULTA,
        "description": "Registra si los fragmentos alcanzan y las afirmaciones con sus citas.",
        "schema": {
            "type": "object",
            "properties": {
                "suficiente": {"type": "boolean"},
                "afirmaciones": {
                    "type": "array",
                    "maxItems": 10,
                    "items": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "maxLength": 1000},
                            "fragmentos": {
                                "type": "array",
                                "items": {"type": "string", "pattern": "^F[0-9]+$"},
                            },
                        },
                        "required": ["texto", "fragmentos"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["suficiente", "afirmaciones"],
            "additionalProperties": False,
        },
    }
