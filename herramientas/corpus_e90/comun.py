"""IA-D01/03/04/07: contrato independiente del backend para el corpus E90."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

DECISION = "DO-2026-10-22-CORPUS-CONSTRUCCION"
ESTADO = "CANDIDATO_NO_CONGELADO"
MARCA = "DOCUMENTO FICTICIO - SIN VALIDEZ COMERCIAL NI FISCAL"
CAMPOS = {
    "contrato": (
        "contraparte",
        "cuit_contraparte",
        "fecha_celebracion",
        "vigencia_desde",
        "vigencia_hasta",
        "monto_total",
        "moneda",
    ),
    "presupuesto": (
        "numero",
        "fecha",
        "proveedor",
        "cuit_proveedor",
        "importe_total",
        "moneda",
    ),
    "orden_compra": (
        "numero",
        "fecha",
        "proveedor",
        "cuit_proveedor",
        "importe_total",
        "moneda",
    ),
    "factura": (
        "numero",
        "fecha_emision",
        "emisor",
        "cuit_emisor",
        "importe_total",
        "moneda",
    ),
    "comprobante": (
        "numero",
        "fecha",
        "contraparte",
        "cuit_contraparte",
        "importe",
        "moneda",
    ),
}
ETIQUETAS = {
    "numero": "Número documental",
    "contraparte": "Contraparte",
    "proveedor": "Proveedor",
    "emisor": "Emisor",
    "cuit_contraparte": "CUIT de la contraparte",
    "cuit_proveedor": "CUIT del proveedor",
    "cuit_emisor": "CUIT del emisor",
    "fecha": "Fecha",
    "fecha_emision": "Fecha de emisión",
    "fecha_celebracion": "Fecha de celebración",
    "vigencia_desde": "Vigencia desde",
    "vigencia_hasta": "Vigencia hasta",
    "monto_total": "Monto total",
    "importe_total": "Importe total",
    "importe": "Importe",
    "moneda": "Moneda",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leer_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def escribir_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ruta_segura(root: Path, relative: str, prefijo: str) -> Path:
    """RNF-03: impedir traversal y enlaces que salgan del destino previsto."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("ruta_no_permitida")
    result = (root / path).resolve()
    if not result.is_relative_to((root / prefijo).resolve()):
        raise ValueError("ruta_fuera_de_alcance")
    return result


def digito_cuit(base: str) -> int | None:
    if not re.fullmatch(r"\d{10}", base):
        return None
    residue = (
        11
        - sum(
            int(c) * k
            for c, k in zip(base, (5, 4, 3, 2, 7, 6, 5, 4, 3, 2), strict=True)
        )
        % 11
    )
    return 0 if residue == 11 else None if residue == 10 else residue


def cuit_valido(value: str) -> bool:
    if not re.fullmatch(r"30-\d{8}-\d", value):
        return False
    digits = value.replace("-", "")
    return digito_cuit(digits[:10]) == int(digits[-1])


def normalizar(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold().replace("–", "-").replace("—", "-")


def representacion(campo: str, value: str) -> str:
    if campo.startswith(("fecha", "vigencia")):
        year, month, day = value.split("-")
        return f"{day}/{month}/{year}"
    if campo in {"importe", "importe_total", "monto_total"}:
        from decimal import Decimal

        return (
            f"{Decimal(value):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    return value


def parrafos_docx(path: Path) -> list[str]:
    """RF-11/IA-M04: índice 1-based de todos los párrafos de word/document.xml."""
    from xml.etree import ElementTree as ET
    from zipfile import ZipFile

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        return [
            "".join(n.text or "" for n in p.iter(namespace + "t"))
            for p in root.iter(namespace + "p")
        ]
