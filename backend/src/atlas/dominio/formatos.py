"""Formato canónico de los valores validados (DO-2026-10-22-VAL, P4).

Los valores validados alimentan las reglas de consistencia (R1 a R4, PD-01), así que
se exige una forma única. Un CUIT con dígito verificador inválido se acepta con una
advertencia: la validación debe reflejar lo que dice el documento.
"""

import re
from datetime import date
from typing import Final

from atlas.procesamiento.valores import ClaseValor, cuit_valido
from atlas.servicios.errores import ErrorDominio

ADVERTENCIA_CUIT: Final = "cuit_digito_verificador_invalido"
_LARGO_MAXIMO_TEXTO: Final = 500


def canonico(valor: str, clase: ClaseValor) -> tuple[str, list[str]]:
    """Devuelve (valor, advertencias) o rechaza con un mensaje que indica el formato."""
    limpio = valor.strip()
    if not limpio:
        raise ErrorDominio("El valor validado no puede estar vacío")
    if clase is ClaseValor.TEXTO:
        if len(limpio) > _LARGO_MAXIMO_TEXTO:
            raise ErrorDominio(f"El valor no puede superar {_LARGO_MAXIMO_TEXTO} caracteres")
        return re.sub(r"\s+", " ", limpio), []
    if clase is ClaseValor.FECHA:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", limpio):
            raise ErrorDominio("La fecha debe tener el formato AAAA-MM-DD")
        try:
            date.fromisoformat(limpio)
        except ValueError as error:
            raise ErrorDominio("La fecha no existe en el calendario") from error
        return limpio, []
    if clase is ClaseValor.IMPORTE:
        if not re.fullmatch(r"\d+\.\d{2}", limpio):
            raise ErrorDominio("El importe debe tener el formato 1234567.89, con dos decimales")
        return limpio, []
    if clase is ClaseValor.CUIT:
        if not re.fullmatch(r"\d{2}-\d{8}-\d", limpio):
            raise ErrorDominio("El CUIT debe tener el formato 30-12345678-9")
        advertencias = [] if cuit_valido(limpio.replace("-", "")) else [ADVERTENCIA_CUIT]
        return limpio, advertencias
    if not re.fullmatch(r"[A-Z]{3}", limpio):
        raise ErrorDominio("La moneda debe indicarse con su código ISO 4217, por ejemplo ARS")
    return limpio, []
