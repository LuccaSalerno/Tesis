"""Normalización determinista de valores (§5.3.2)."""

import pytest

from atlas.procesamiento.valores import ClaseValor, cuit_valido, normalizar


@pytest.mark.parametrize(
    ("entrada", "clase", "esperado"),
    [
        ("30-96472518-3", ClaseValor.CUIT, "30-96472518-3"),
        ("30964725183", ClaseValor.CUIT, "30-96472518-3"),
        ("30-96472518-4", ClaseValor.CUIT, "30-96472518-4"),  # dígito inválido: sin normalizar
        ("20 de febrero de 2026", ClaseValor.FECHA, "2026-02-20"),
        ("1º de marzo de 2026", ClaseValor.FECHA, "2026-03-01"),
        ("01/03/2026", ClaseValor.FECHA, "2026-03-01"),
        ("2027-02-28", ClaseValor.FECHA, "2027-02-28"),
        ("31/02/2026", ClaseValor.FECHA, "31/02/2026"),  # fecha imposible: sin normalizar
        # DIF-124: año de dos dígitos, siglo XXI (las 10 fechas críticas de e90-oficial-1).
        ("22/07/26", ClaseValor.FECHA, "2026-07-22"),
        ("01/05/26", ClaseValor.FECHA, "2026-05-01"),
        ("3-9-26", ClaseValor.FECHA, "2026-09-03"),
        ("19.04.26", ClaseValor.FECHA, "2026-04-19"),
        ("31/02/26", ClaseValor.FECHA, "31/02/26"),  # fecha imposible: sin normalizar
        ("22/07/226", ClaseValor.FECHA, "22/07/226"),  # año de tres dígitos: sin normalizar
        ("ARS 1.250.000,00", ClaseValor.IMPORTE, "1250000.00"),
        ("$ 10.500", ClaseValor.IMPORTE, "10500.00"),
        ("1,234.56", ClaseValor.IMPORTE, "1234.56"),
        ("10,5", ClaseValor.IMPORTE, "10.50"),
        ("un millón", ClaseValor.IMPORTE, "un millón"),
        ("pesos argentinos", ClaseValor.MONEDA, "ARS"),
        ("U$S", ClaseValor.MONEDA, "USD"),
        ("euros", ClaseValor.MONEDA, "EUR"),  # ISO 4217 (DIF-109)
        ("€", ClaseValor.MONEDA, "EUR"),
        ("reales", ClaseValor.MONEDA, "reales"),  # moneda no reconocida: sin normalizar
        ("€ 2.242,86", ClaseValor.IMPORTE, "2242.86"),
        ("2.242,86 euros", ClaseValor.IMPORTE, "2242.86"),
        ("  Servicios   Integrales  ", ClaseValor.TEXTO, "Servicios Integrales"),
    ],
)
def test_rf_10_normalizacion(entrada: str, clase: ClaseValor, esperado: str) -> None:
    assert normalizar(entrada, clase) == esperado


def test_rf_10_digito_verificador_de_cuit() -> None:
    assert cuit_valido("30964725183")
    assert not cuit_valido("30964725184")
    assert not cuit_valido("3096472518")
