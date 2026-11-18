"""Catálogo R1 a R4 sin base de datos (RF-16, RN-06 P5-P6)."""

import pytest

from atlas.dominio import reglas
from atlas.dominio.enumeraciones import ResultadoRegla, TipoDocumental

C, OC, F = TipoDocumental.CONTRATO, TipoDocumental.ORDEN_COMPRA, TipoDocumental.FACTURA
CUIT = "30-96472518-3"
OTRO_CUIT = "30-71234567-1"

# Oráculo de la cadena de evidencia: contrato C-v1, órdenes OC-v1/OC-v2 y facturas F-v1/F-v2
# (importes con IVA, ARS).
C_V1 = {"cuit_contraparte": CUIT, "vigencia_desde": "2026-03-01", "vigencia_hasta": "2027-02-28"}
O_V1 = {
    "cuit_proveedor": CUIT,
    "fecha": "2027-03-15",
    "importe_total": "1250000.00",
    "moneda": "ARS",
}
O_V2 = {**O_V1, "fecha": "2026-09-15"}
F_V1 = {"cuit_emisor": CUIT, "importe_total": "1312500.00", "moneda": "ARS"}
F_V2 = {**F_V1, "importe_total": "1250000.00"}


def regla(codigo: str) -> reglas.Regla:
    return next(r for r in reglas.CATALOGO if r.codigo.startswith(codigo))


def resultados(
    contrato: dict[str, str], orden: dict[str, str], factura: dict[str, str]
) -> dict[str, ResultadoRegla]:
    valores = {C: contrato, OC: orden, F: factura}
    return {r.codigo[:2]: r.evaluar(valores).resultado for r in reglas.CATALOGO}


CUMPLE = ResultadoRegla.CUMPLIMIENTO
ADVIERTE = ResultadoRegla.ADVERTENCIA


@pytest.mark.parametrize(
    ("orden", "factura", "esperado"),
    [
        (O_V1, F_V2, {"R1": CUMPLE, "R2": CUMPLE, "R3": ADVIERTE, "R4": CUMPLE}),
        (O_V2, F_V1, {"R1": CUMPLE, "R2": CUMPLE, "R3": CUMPLE, "R4": ADVIERTE}),
        (O_V2, F_V2, {"R1": CUMPLE, "R2": CUMPLE, "R3": CUMPLE, "R4": CUMPLE}),
    ],
    ids=["C-v1+OC-v1+F-v2", "C-v1+OC-v2+F-v1", "C-v1+OC-v2+F-v2"],
)
def test_resultados_esperados_del_oraculo(
    orden: dict[str, str], factura: dict[str, str], esperado: dict[str, ResultadoRegla]
) -> None:
    assert resultados(C_V1, orden, factura) == esperado


def test_catalogo_con_codigo_y_version() -> None:
    assert [(r.codigo, r.version) for r in reglas.CATALOGO] == [
        ("R1-CUIT-FACTURA-OC", "v1"),
        ("R2-CUIT-OC-CONTRATO", "v1"),
        ("R3-VIGENCIA-OC-CONTRATO", "v1"),
        ("R4-IMPORTE-FACTURA-OC", "v1"),
    ]
    assert [r.tipos for r in reglas.CATALOGO] == [{F, OC}, {OC, C}, {OC, C}, {F, OC}]


def test_escenario_r4_diez_mil_contra_diez_mil_quinientos() -> None:
    evaluacion = regla("R4").evaluar(
        {
            F: {"importe_total": "10500.00", "moneda": "ARS"},
            OC: {"importe_total": "10000.00", "moneda": "ARS"},
        }
    )
    assert evaluacion.resultado is ADVIERTE
    assert "supera" in evaluacion.explicacion and "500.00 ARS" in evaluacion.explicacion


def test_r4_detecta_la_diferencia_de_f_v1() -> None:
    explicacion = regla("R4").evaluar({F: F_V1, OC: O_V2}).explicacion
    assert "62500.00 ARS" in explicacion


@pytest.mark.parametrize(
    ("fecha", "esperado"),
    [
        ("2026-03-01", CUMPLE),  # extremos incluidos
        ("2027-02-28", CUMPLE),
        ("2026-02-28", ADVIERTE),
        ("2027-03-01", ADVIERTE),
    ],
)
def test_r3_incluye_los_extremos_de_la_vigencia(fecha: str, esperado: ResultadoRegla) -> None:
    assert regla("R3").evaluar({OC: {**O_V1, "fecha": fecha}, C: C_V1}).resultado is esperado


def test_r3_explica_la_advertencia_con_los_valores_comparados() -> None:
    explicacion = regla("R3").evaluar({OC: O_V1, C: C_V1}).explicacion
    assert explicacion == (
        "La fecha de la orden de compra (2027-03-15) está fuera de la vigencia del contrato"
        " (del 2026-03-01 al 2027-02-28)."
    )


@pytest.mark.parametrize(
    ("codigo", "valores"),
    [
        ("R1", {F: {**F_V1, "cuit_emisor": OTRO_CUIT}, OC: O_V1}),
        ("R2", {OC: {**O_V1, "cuit_proveedor": OTRO_CUIT}, C: C_V1}),
    ],
)
def test_cuits_distintos_advierten(
    codigo: str, valores: dict[TipoDocumental, dict[str, str]]
) -> None:
    evaluacion = regla(codigo).evaluar(valores)
    assert evaluacion.resultado is ADVIERTE
    assert "difiere" in evaluacion.explicacion and OTRO_CUIT in evaluacion.explicacion


@pytest.mark.parametrize("codigo", ["R1", "R2", "R3", "R4"])
def test_sin_validar_es_falta_de_datos(codigo: str) -> None:
    """RN-02: un dato sin validar no se reemplaza por nada; la regla informa qué falta."""
    evaluacion = regla(codigo).evaluar({})
    assert evaluacion.resultado is ResultadoRegla.FALTA_DE_DATOS
    assert evaluacion.explicacion.startswith("Falta validar: ")


def test_falta_de_datos_lista_solo_lo_que_falta() -> None:
    evaluacion = regla("R3").evaluar({OC: O_V1, C: {"vigencia_desde": "2026-03-01"}})
    assert evaluacion.explicacion == "Falta validar: vigencia hasta (contrato)."


def test_r4_monedas_distintas_no_aplica() -> None:
    evaluacion = regla("R4").evaluar({F: {**F_V1, "moneda": "USD"}, OC: O_V1})
    assert evaluacion.resultado is ResultadoRegla.NO_APLICABLE
    assert "USD" in evaluacion.explicacion and "ARS" in evaluacion.explicacion


def test_r4_moneda_sin_validar_es_falta_de_datos_aunque_haya_importes() -> None:
    sin_moneda = {"importe_total": "1.00"}
    assert regla("R4").evaluar({F: sin_moneda, OC: O_V1}).resultado is ResultadoRegla.FALTA_DE_DATOS


def test_r4_monedas_distintas_prevalecen_sobre_importes_sin_validar() -> None:
    resultado = regla("R4").evaluar({F: {"moneda": "USD"}, OC: {"moneda": "ARS"}}).resultado
    assert resultado is ResultadoRegla.NO_APLICABLE


def test_r4_misma_moneda_sin_importe_es_falta_de_datos() -> None:
    evaluacion = regla("R4").evaluar({F: {"moneda": "ARS"}, OC: O_V1})
    assert evaluacion.resultado is ResultadoRegla.FALTA_DE_DATOS
    assert evaluacion.explicacion == "Falta validar: importe total (factura)."


@pytest.mark.parametrize(
    ("a", "b", "esperado"),
    [
        (F, OC, ["R1-CUIT-FACTURA-OC", "R4-IMPORTE-FACTURA-OC"]),
        (OC, F, ["R1-CUIT-FACTURA-OC", "R4-IMPORTE-FACTURA-OC"]),  # en cualquier dirección
        (C, OC, ["R2-CUIT-OC-CONTRATO", "R3-VIGENCIA-OC-CONTRATO"]),
        (F, C, []),  # par sin regla
        (F, F, []),
        (F, None, []),  # sin clasificación validada
    ],
)
def test_reglas_pertinentes_segun_los_tipos_validados(
    a: TipoDocumental, b: TipoDocumental | None, esperado: list[str]
) -> None:
    assert [r.codigo for r in reglas.pertinentes(a, b)] == esperado
