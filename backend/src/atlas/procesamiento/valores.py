"""Normalización determinista de valores extraídos (§5.3.2: fechas, importes, CUIT).

Si un valor no puede normalizarse con certeza se devuelve tal como vino (sin
espacios sobrantes): la sugerencia conserva su forma original y la valida una
persona. Nunca se inventa un valor.
"""

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Final


class ClaseValor(StrEnum):
    TEXTO = "texto"
    CUIT = "cuit"
    FECHA = "fecha"
    IMPORTE = "importe"
    MONEDA = "moneda"


_MESES: Final = {
    m: i
    for i, m in enumerate(
        (
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ),
        start=1,
    )
} | {"setiembre": 9}
_MONEDAS: Final = {
    "ARS": ("ars", "$", "pesos", "peso", "pesos argentinos", "peso argentino"),
    "USD": ("usd", "u$s", "us$", "dólares", "dolares", "dólar", "dolar", "dólares estadounidenses"),
    "EUR": ("eur", "€", "euros", "euro"),
}
_PESOS_CUIT: Final = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def normalizar(valor: str, clase: ClaseValor) -> str:
    limpio = re.sub(r"\s+", " ", valor).strip()
    normalizador = {
        ClaseValor.CUIT: _cuit,
        ClaseValor.FECHA: _fecha,
        ClaseValor.IMPORTE: _importe,
        ClaseValor.MONEDA: _moneda,
    }.get(clase)
    if normalizador is None:
        return limpio
    return normalizador(limpio) or limpio


def cuit_valido(digitos: str) -> bool:
    if not re.fullmatch(r"\d{11}", digitos):
        return False
    resto = sum(int(d) * p for d, p in zip(digitos[:10], _PESOS_CUIT, strict=True)) % 11
    verificador = 0 if resto == 0 else 11 - resto
    return verificador != 10 and verificador == int(digitos[10])


def _cuit(valor: str) -> str | None:
    digitos = re.sub(r"\D", "", valor)
    if not cuit_valido(digitos):
        return None
    return f"{digitos[:2]}-{digitos[2:10]}-{digitos[10]}"


def _fecha(valor: str) -> str | None:
    texto = valor.casefold()
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", texto):
        anio, mes, dia = (int(x) for x in m.groups())
    elif m := re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", texto):
        dia, mes, anio = (int(x) for x in m.groups())
    elif m := re.fullmatch(r"(\d{1,2})(?:º|°)? de ([a-záéíóú]+) de(?:l)? (\d{4})", texto):
        if m.group(2) not in _MESES:
            return None
        dia, mes, anio = int(m.group(1)), _MESES[m.group(2)], int(m.group(3))
    else:
        return None
    try:
        return date(anio, mes, dia).isoformat()
    except ValueError:
        return None


def _importe(valor: str) -> str | None:
    # Las variantes largas van primero: «euros» no debe dejar «os» al quitar «eur».
    texto = re.sub(r"(?i)(euros?|ars|usd|eur|u\$s|us\$|\$|€|pesos?|d[oó]lares?)", "", valor).strip()
    texto = texto.replace(" ", "")
    if not re.fullmatch(r"-?[\d.,]+", texto):
        return None
    decimal: str | None
    if "," in texto and "." in texto:
        # El separador que aparece último es el decimal: 1.234,56 o 1,234.56.
        decimal = "," if texto.rfind(",") > texto.rfind(".") else "."
    elif "," in texto:
        decimal = "," if re.search(r",\d{1,2}$", texto) else None
    elif "." in texto:
        decimal = "." if re.search(r"\.\d{1,2}$", texto) and texto.count(".") == 1 else None
    else:
        decimal = None
    miles = {",": ".", ".": ","}.get(decimal or "", ",.")
    for separador in miles:
        texto = texto.replace(separador, "")
    if decimal:
        texto = texto.replace(decimal, ".")
    try:
        return f"{Decimal(texto):.2f}"
    except InvalidOperation:
        return None


def _moneda(valor: str) -> str | None:
    texto = valor.casefold().strip(" .")
    for codigo, variantes in _MONEDAS.items():
        if texto in variantes:
            return codigo
    return None
