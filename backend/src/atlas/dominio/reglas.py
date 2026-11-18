"""Catálogo de reglas de consistencia R1 a R4 (RF-16, RN-06, §5.3.5).

Reglas explícitas y deterministas sobre valores **validados** y en formato canónico
 de dos documentos vinculados. No acceden a la base ni a
sugerencias: reciben solo lo validado y devuelven resultado y explicación. La explicación
contiene valores del documento: se guarda en la base y nunca va a los registros.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from atlas.dominio.enumeraciones import ResultadoRegla, TipoDocumental

Valores = Mapping[TipoDocumental, Mapping[str, str]]
# Campos que una persona declaró ausentes en la versión.
Ausentes = Mapping[TipoDocumental, frozenset[str]]
SIN_AUSENTES: Ausentes = {}

_NOMBRE_TIPO = {
    TipoDocumental.CONTRATO: "contrato",
    TipoDocumental.ORDEN_COMPRA: "orden de compra",
    TipoDocumental.FACTURA: "factura",
}
_NOMBRE_CAMPO = {
    "cuit_emisor": "CUIT del emisor",
    "cuit_proveedor": "CUIT del proveedor",
    "cuit_contraparte": "CUIT de la contraparte",
    "fecha": "fecha",
    "vigencia_desde": "vigencia desde",
    "vigencia_hasta": "vigencia hasta",
    "importe_total": "importe total",
    "moneda": "moneda",
}


@dataclass(frozen=True)
class Evaluacion:
    resultado: ResultadoRegla
    explicacion: str


@dataclass(frozen=True)
class Regla:
    """Una regla compara campos de dos tipos documentales vinculados."""

    codigo: str
    version: str
    descripcion: str
    campos: Mapping[TipoDocumental, tuple[str, ...]]
    _comparar: Callable[[Valores], Evaluacion]

    @property
    def tipos(self) -> frozenset[TipoDocumental]:
        return frozenset(self.campos)

    def faltantes(self, valores: Valores, ausentes: Ausentes = SIN_AUSENTES) -> list[str]:
        return [
            self._nombre(tipo, campo)
            for tipo, campos in self.campos.items()
            for campo in campos
            if campo not in valores.get(tipo, {}) and campo not in ausentes.get(tipo, frozenset())
        ]

    def ausentes(self, valores: Valores, ausentes: Ausentes) -> list[str]:
        return [
            self._nombre(tipo, campo)
            for tipo, campos in self.campos.items()
            for campo in campos
            if campo not in valores.get(tipo, {}) and campo in ausentes.get(tipo, frozenset())
        ]

    @staticmethod
    def _nombre(tipo: TipoDocumental, campo: str) -> str:
        return f"{_NOMBRE_CAMPO[campo]} ({_NOMBRE_TIPO[tipo]})"

    def evaluar(self, valores: Valores, ausentes: Ausentes = SIN_AUSENTES) -> Evaluacion:
        """Falta de datos si algún campo necesario no tiene valor validado, sea porque
        falta validarlo o porque una persona lo declaró ausente."""
        if self.faltantes(valores, ausentes) or self.ausentes(valores, ausentes):
            return self._falta_de_datos(valores, ausentes)
        return self._comparar(valores)

    def _falta_de_datos(self, valores: Valores, ausentes: Ausentes) -> Evaluacion:
        partes = []
        if faltantes := self.faltantes(valores, ausentes):
            partes.append("Falta validar: " + ", ".join(faltantes) + ".")
        if declarados := self.ausentes(valores, ausentes):
            partes.append("Declarado ausente por una persona: " + ", ".join(declarados) + ".")
        return Evaluacion(ResultadoRegla.FALTA_DE_DATOS, " ".join(partes))


def _cuits(
    tipo_a: TipoDocumental, campo_a: str, tipo_b: TipoDocumental, campo_b: str
) -> Callable[[Valores], Evaluacion]:
    def comparar(valores: Valores) -> Evaluacion:
        a, b = valores[tipo_a][campo_a], valores[tipo_b][campo_b]
        descripcion = f"El {_NOMBRE_CAMPO[campo_a]} {_del(tipo_a)} ({a})"
        destino = f"el {_NOMBRE_CAMPO[campo_b]} {_del(tipo_b)} ({b})"
        if a == b:
            return Evaluacion(ResultadoRegla.CUMPLIMIENTO, f"{descripcion} coincide con {destino}.")
        return Evaluacion(ResultadoRegla.ADVERTENCIA, f"{descripcion} difiere de {destino}.")

    return comparar


def _del(tipo: TipoDocumental) -> str:
    return "del contrato" if tipo is TipoDocumental.CONTRATO else f"de la {_NOMBRE_TIPO[tipo]}"


def _vigencia(valores: Valores) -> Evaluacion:
    """R3: vigencia desde ≤ fecha de la orden ≤ vigencia hasta, extremos incluidos."""
    fecha = date.fromisoformat(valores[TipoDocumental.ORDEN_COMPRA]["fecha"])
    contrato = valores[TipoDocumental.CONTRATO]
    desde = date.fromisoformat(contrato["vigencia_desde"])
    hasta = date.fromisoformat(contrato["vigencia_hasta"])
    intervalo = f"del {desde.isoformat()} al {hasta.isoformat()}"
    if desde <= fecha <= hasta:
        return Evaluacion(
            ResultadoRegla.CUMPLIMIENTO,
            f"La fecha de la orden de compra ({fecha.isoformat()}) está dentro de la vigencia"
            f" del contrato ({intervalo}).",
        )
    return Evaluacion(
        ResultadoRegla.ADVERTENCIA,
        f"La fecha de la orden de compra ({fecha.isoformat()}) está fuera de la vigencia"
        f" del contrato ({intervalo}).",
    )


def _importe(valores: Valores) -> Evaluacion:
    factura = valores[TipoDocumental.FACTURA]
    orden = valores[TipoDocumental.ORDEN_COMPRA]
    moneda = factura["moneda"]
    importe_factura = Decimal(factura["importe_total"])
    importe_orden = Decimal(orden["importe_total"])
    if importe_factura <= importe_orden:
        return Evaluacion(
            ResultadoRegla.CUMPLIMIENTO,
            f"El importe total de la factura ({importe_factura} {moneda}) no supera el de la"
            f" orden de compra ({importe_orden} {moneda}).",
        )
    return Evaluacion(
        ResultadoRegla.ADVERTENCIA,
        f"El importe total de la factura ({importe_factura} {moneda}) supera el de la orden"
        f" de compra ({importe_orden} {moneda}) en {importe_factura - importe_orden} {moneda}.",
    )


@dataclass(frozen=True)
class ReglaImporte(Regla):
    """R4 revisa primero la moneda: sin validar → falta de datos; distinta → no aplicable."""

    def evaluar(self, valores: Valores, ausentes: Ausentes = SIN_AUSENTES) -> Evaluacion:
        monedas = (
            valores.get(TipoDocumental.FACTURA, {}).get("moneda"),
            valores.get(TipoDocumental.ORDEN_COMPRA, {}).get("moneda"),
        )
        if None in monedas:
            return self._falta_de_datos(valores, ausentes)
        if monedas[0] != monedas[1]:
            return Evaluacion(
                ResultadoRegla.NO_APLICABLE,
                f"Las monedas difieren ({monedas[0]} en la factura y {monedas[1]} en la orden"
                " de compra): la regla compara importes en la misma moneda.",
            )
        return super().evaluar(valores, ausentes)


_F, _O, _C = TipoDocumental.FACTURA, TipoDocumental.ORDEN_COMPRA, TipoDocumental.CONTRATO

CATALOGO: tuple[Regla, ...] = (
    Regla(
        "R1-CUIT-FACTURA-OC",
        "v1",
        "CUIT del emisor de la factura = CUIT del proveedor de la orden de compra vinculada",
        {_F: ("cuit_emisor",), _O: ("cuit_proveedor",)},
        _cuits(_F, "cuit_emisor", _O, "cuit_proveedor"),
    ),
    Regla(
        "R2-CUIT-OC-CONTRATO",
        "v1",
        "CUIT del proveedor de la orden de compra = CUIT de la contraparte del contrato vinculado",
        {_O: ("cuit_proveedor",), _C: ("cuit_contraparte",)},
        _cuits(_O, "cuit_proveedor", _C, "cuit_contraparte"),
    ),
    Regla(
        "R3-VIGENCIA-OC-CONTRATO",
        "v1",
        "Fecha de la orden de compra dentro de la vigencia del contrato vinculado",
        {_O: ("fecha",), _C: ("vigencia_desde", "vigencia_hasta")},
        _vigencia,
    ),
    ReglaImporte(
        "R4-IMPORTE-FACTURA-OC",
        "v1",
        "Importe total de la factura ≤ importe total de la orden de compra vinculada,"
        " con la misma moneda",
        {_F: ("importe_total", "moneda"), _O: ("importe_total", "moneda")},
        _importe,
    ),
)


def pertinentes(tipo_a: TipoDocumental | None, tipo_b: TipoDocumental | None) -> tuple[Regla, ...]:
    """Reglas cuyo par de tipos coincide con el de los documentos, en cualquier orden."""
    if tipo_a is None or tipo_b is None:
        return ()
    return tuple(r for r in CATALOGO if r.tipos == {tipo_a, tipo_b})
