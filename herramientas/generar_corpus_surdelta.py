#!/usr/bin/env python3
"""Generador reproducible de los documentos sintéticos del escenario SurDelta.

DO-2026-11-09-DEMO-SURDELTA: demostración (videos y defensa), separada de PD-07 y del corpus
E90 de §6.3. Todos los sujetos son ficticios; los CUIT son solo los ya consultados por el
equipo en ARCA (el de PD-07 y los de la partición de ajuste de E90, nunca los de medición).

Uso, en el entorno de `herramientas/corpus_e90/requisitos.txt` y con LibreOffice local:

    python herramientas/generar_corpus_surdelta.py [--libreoffice soffice]

Escribe los PDF en `corpus/surdelta/` y el oráculo `oraculos/oraculo_surdelta_v1.json`, con
la huella SHA-256 de cada PDF. Se niega a sobrescribir: para regenerar, borrar ambos antes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from pypdf import PdfReader, PdfWriter

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "corpus" / "surdelta"
ORACULO = RAIZ / "oraculos" / "oraculo_surdelta_v1.json"
PIE = "Documento ficticio para demostración académica · sin validez comercial ni fiscal"

COMPRADOR = "SurDelta Componentes S.R.L."
# Proveedores ficticios. CUIT con consulta ARCA informada por el equipo («No existe»).
ANDES = ("Andes Sistemas S.A.", "30-96472518-3")  # PD-07, consulta del 23/10/2026
EQUIPAR = ("Distribuidora Equipar S.A.", "30-98641015-1")  # E90 ajuste, 23/10/2026
HORIZONTE = ("Horizonte Servicios S.R.L.", "30-98641014-3")  # E90 ajuste, 23/10/2026
NUBE = ("Nube Austral Tecnología S.R.L.", "30-98641017-8")  # E90 ajuste, 23/10/2026
CONSULTAS_CUIT = {
    ANDES[1]: "oraculos/oraculo_PD07_v2.json (registro_cuit)",
    EQUIPAR[
        1
    ]: "docs/evaluacion/corpus_e90/Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md",
    HORIZONTE[
        1
    ]: "docs/evaluacion/corpus_e90/Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md",
    NUBE[
        1
    ]: "docs/evaluacion/corpus_e90/Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md",
}


def pesos(valor: str) -> str:
    """'9200000.00' → '9.200.000,00'."""
    entero, decimales = f"{Decimal(valor):.2f}".split(".")
    return f"{int(entero):,}".replace(",", ".") + "," + decimales


def fecha(iso: str) -> str:
    """'2026-09-25' → '25/09/2026'."""
    anio, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{anio}"


class Redactor:
    """Documento DOCX con el formato común del escenario."""

    def __init__(self, membrete: str) -> None:
        self.d = Document()
        seccion = self.d.sections[0]
        seccion.top_margin, seccion.bottom_margin = Cm(2.2), Cm(2.2)
        seccion.left_margin, seccion.right_margin = Cm(2.4), Cm(2.4)
        normal = self.d.styles["Normal"]
        normal.font.name, normal.font.size = "Liberation Sans", Pt(10.5)
        normal.paragraph_format.space_after = Pt(6)
        for estilo, tamano in (("Title", 17), ("Heading 1", 12.5), ("Heading 2", 11)):
            s = self.d.styles[estilo]
            s.font.name, s.font.size, s.font.bold = "Liberation Sans", Pt(tamano), True
            s.font.color.rgb = RGBColor(28, 52, 84)
        encabezado = seccion.header.paragraphs[0]
        encabezado.text = membrete
        encabezado.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        encabezado.runs[0].font.size = Pt(8)
        pie = seccion.footer.paragraphs[0]
        pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
        texto = pie.add_run(PIE)
        texto.font.size, texto.font.color.rgb = Pt(7), RGBColor(120, 120, 120)

    def titulo(self, texto: str) -> None:
        self.d.add_heading(texto, 0)

    def h(self, texto: str) -> None:
        self.d.add_heading(texto, level=1)

    def p(self, texto: str) -> None:
        self.d.add_paragraph(texto)

    def item(self, texto: str) -> None:
        self.d.add_paragraph(texto, style="List Bullet")

    def tabla(self, filas: list[tuple[str, ...]], encabezado: bool = False) -> None:
        tabla = self.d.add_table(rows=0, cols=len(filas[0]))
        tabla.style, tabla.alignment = "Table Grid", WD_TABLE_ALIGNMENT.CENTER
        for i, fila in enumerate(filas):
            celdas = tabla.add_row().cells
            for celda, valor in zip(celdas, fila, strict=True):
                celda.text = valor
                if encabezado and i == 0:
                    celda.paragraphs[0].runs[0].font.bold = True
        self.d.add_paragraph()

    def pagina(self) -> None:
        self.d.add_page_break()

    def guardar(self, ruta: Path) -> None:
        self.d.save(ruta)


@dataclass(frozen=True)
class Pieza:
    codigo: str
    archivo: str
    tipo: str
    campos: dict[str, str]
    redactor: Redactor


# --- Contratos ----------------------------------------------------------------------------


def contrato_mantenimiento() -> Pieza:
    proveedor, cuit = ANDES
    r = Redactor("SurDelta Componentes S.R.L. · Contrato C-2026-014")
    r.titulo("Contrato de servicio de mantenimiento integral de planta")
    r.p(
        "En la localidad de Avellaneda, provincia de Buenos Aires, a los 15 días del mes de"
        " septiembre de 2026, se celebra el presente contrato de servicios entre las partes"
        " que se identifican a continuación."
    )
    r.tabla(
        [
            ("Contrato N.º", "C-2026-014"),
            ("Comitente", COMPRADOR),
            ("Prestadora / contraparte", proveedor),
            ("CUIT de la prestadora", cuit),
            ("Fecha de celebración", "15/09/2026"),
        ]
    )
    r.h("1. Objeto")
    r.p(
        "La prestadora realizará el mantenimiento preventivo y correctivo de la infraestructura"
        " tecnológica de la planta de la comitente: equipos de red, servidores de respaldo,"
        " estaciones de control de la línea de montaje y su cableado estructurado."
    )
    for texto in (
        "Una visita preventiva mensual con informe técnico.",
        "Atención de incidentes críticos en un plazo máximo de 4 horas hábiles.",
        "Hasta 20 horas mensuales de soporte correctivo incluidas en el abono.",
        "Informe trimestral de estado de la infraestructura con recomendaciones.",
    ):
        r.item(texto)
    r.h("2. Obligaciones de la prestadora")
    r.p(
        "La prestadora designará un responsable técnico, registrará cada intervención con su"
        " fecha, alcance y resultado, y entregará la documentación de respaldo junto con cada"
        " factura mensual. No podrá modificar órdenes de compra ni aprobar gastos en nombre"
        " de la comitente."
    )
    r.pagina()
    r.h("3. Vigencia")
    r.p(
        "El contrato rige desde el 01/10/2026 hasta el 30/09/2027, ambas fechas inclusive. Su"
        " renovación requiere un nuevo instrumento firmado por ambas partes."
    )
    r.tabla([("Inicio de vigencia", "01/10/2026"), ("Fin de vigencia", "30/09/2027")])
    r.h("4. Precio y forma de pago")
    r.p(
        "El precio total del contrato asciende a PESOS NOVENTA Y SEIS MILLONES"
        " (ARS 96.000.000,00), IVA incluido, pagadero en doce abonos mensuales de"
        " ARS 8.000.000,00. Cada abono se factura a mes vencido contra la orden de compra"
        " mensual emitida por la comitente."
    )
    r.tabla(
        [
            ("Monto total del contrato", "ARS 96.000.000,00"),
            ("Moneda", "Pesos argentinos (ARS)"),
            ("Abono mensual", "ARS 8.000.000,00"),
        ]
    )
    r.h("5. Trabajos adicionales")
    r.p(
        "Las horas de soporte que excedan las incluidas en el abono, y cualquier trabajo fuera"
        " del objeto, se consideran trabajos adicionales. Los trabajos adicionales requieren"
        " autorización previa y por escrito de la comitente, mediante una orden de compra"
        " específica. Sin esa autorización no serán reconocidos ni podrán facturarse."
    )
    r.pagina()
    r.h("6. Facturación y conformidad")
    r.p(
        "La prestadora emitirá una factura por cada abono mensual, con referencia a la orden"
        " de compra correspondiente. La comitente revisará cada factura contra el contrato y"
        " la orden de compra antes de prestar conformidad. Una factura con importes no"
        " autorizados será observada y deberá ser reemplazada."
    )
    r.h("7. Confidencialidad")
    r.p(
        "Las partes mantendrán reserva sobre la información técnica y comercial a la que"
        " accedan con motivo del contrato y la utilizarán solo para su ejecución."
    )
    r.h("8. Rescisión")
    r.p(
        "Cualquiera de las partes podrá rescindir el contrato con un preaviso de 60 días."
        " La rescisión no afecta las obligaciones devengadas hasta esa fecha."
    )
    return Pieza(
        "SD-C1",
        "SD-C1_Contrato_Mantenimiento_Planta.pdf",
        "contrato",
        {
            "contraparte": proveedor,
            "cuit_contraparte": cuit,
            "fecha_celebracion": "2026-09-15",
            "vigencia_desde": "2026-10-01",
            "vigencia_hasta": "2027-09-30",
            "monto_total": "96000000.00",
            "moneda": "ARS",
        },
        r,
    )


def contrato_soporte() -> Pieza:
    proveedor, cuit = NUBE
    r = Redactor("SurDelta Componentes S.R.L. · Contrato C-2026-021")
    r.titulo("Contrato de soporte informático")
    r.p(
        "En la localidad de Avellaneda, provincia de Buenos Aires, a los 30 días del mes de"
        " octubre de 2026, se celebra el presente contrato de soporte informático."
    )
    r.tabla(
        [
            ("Contrato N.º", "C-2026-021"),
            ("Comitente", COMPRADOR),
            ("Prestadora / contraparte", proveedor),
            ("CUIT de la prestadora", cuit),
            ("Fecha de celebración", "30/10/2026"),
        ]
    )
    r.h("1. Objeto")
    r.p(
        "Mesa de ayuda para las áreas administrativa y comercial, administración de cuentas"
        " de correo y licencias, y mantenimiento de 40 puestos de trabajo."
    )
    r.h("2. Vigencia")
    r.p("El contrato rige desde el 01/12/2026 hasta el 30/11/2027, ambas fechas inclusive.")
    r.h("3. Precio")
    r.p(
        "El precio total asciende a ARS 18.000.000,00, IVA incluido, en pesos argentinos,"
        " pagadero en doce cuotas mensuales iguales."
    )
    r.tabla(
        [
            ("Monto total del contrato", "ARS 18.000.000,00"),
            ("Moneda", "Pesos argentinos (ARS)"),
            ("Inicio de vigencia", "01/12/2026"),
            ("Fin de vigencia", "30/11/2027"),
        ]
    )
    return Pieza(
        "SD-C3",
        "SD-C3_Contrato_Soporte_Informatico.pdf",
        "contrato",
        {
            "contraparte": proveedor,
            "cuit_contraparte": cuit,
            "fecha_celebracion": "2026-10-30",
            "vigencia_desde": "2026-12-01",
            "vigencia_hasta": "2027-11-30",
            "monto_total": "18000000.00",
            "moneda": "ARS",
        },
        r,
    )


# --- Órdenes, presupuestos y facturas -----------------------------------------------------


def orden(
    codigo: str,
    numero: str,
    iso: str,
    sujeto: tuple[str, str],
    total: str,
    items: list[tuple[str, str]],
    referencia: str,
) -> Pieza:
    proveedor, cuit = sujeto
    r = Redactor(f"SurDelta Componentes S.R.L. · Orden de compra {numero}")
    r.titulo("Orden de compra")
    r.tabla(
        [
            ("Orden de compra N.º", numero),
            ("Fecha", fecha(iso)),
            ("Emitida por", COMPRADOR),
            ("Proveedor", proveedor),
            ("CUIT del proveedor", cuit),
            ("Referencia", referencia),
        ]
    )
    r.h("Detalle")
    r.tabla(
        [("Concepto", "Importe (IVA incluido)"), *[(c, f"ARS {pesos(i)}") for c, i in items]],
        encabezado=True,
    )
    r.tabla([("Importe total", f"ARS {pesos(total)}"), ("Moneda", "Pesos argentinos (ARS)")])
    r.p("Autoriza: Gerencia de Administración. Facturar a mes vencido con referencia a esta orden.")
    return Pieza(
        codigo,
        f"{codigo}_Orden_Compra_{numero}.pdf",
        "orden_compra",
        {
            "numero": numero,
            "fecha": iso,
            "proveedor": proveedor,
            "cuit_proveedor": cuit,
            "importe_total": total,
            "moneda": "ARS",
        },
        r,
    )


def presupuesto(
    codigo: str,
    numero: str,
    iso: str,
    sujeto: tuple[str, str],
    total: str,
    items: list[tuple[str, str]],
) -> Pieza:
    proveedor, cuit = sujeto
    r = Redactor(f"{proveedor} · Presupuesto {numero}")
    r.titulo("Presupuesto")
    r.tabla(
        [
            ("Presupuesto N.º", numero),
            ("Fecha", fecha(iso)),
            ("Proveedor", proveedor),
            ("CUIT del proveedor", cuit),
            ("Cliente", COMPRADOR),
            ("Validez de la oferta", "30 días"),
        ]
    )
    r.h("Detalle")
    r.tabla(
        [("Concepto", "Importe (IVA incluido)"), *[(c, f"ARS {pesos(i)}") for c, i in items]],
        encabezado=True,
    )
    r.tabla([("Importe total", f"ARS {pesos(total)}"), ("Moneda", "Pesos argentinos (ARS)")])
    return Pieza(
        codigo,
        f"{codigo}_Presupuesto_{numero}.pdf",
        "presupuesto",
        {
            "numero": numero,
            "fecha": iso,
            "proveedor": proveedor,
            "cuit_proveedor": cuit,
            "importe_total": total,
            "moneda": "ARS",
        },
        r,
    )


def factura(
    codigo: str,
    numero: str,
    iso: str,
    sujeto: tuple[str, str],
    total: str,
    items: list[tuple[str, str]],
    referencia: str,
    nota: str | None = None,
) -> Pieza:
    emisor, cuit = sujeto
    r = Redactor(f"{emisor} · Factura A {numero}")
    r.titulo("Factura A")
    r.tabla(
        [
            ("Factura N.º", numero),
            ("Fecha de emisión", fecha(iso)),
            ("Emisor", emisor),
            ("CUIT del emisor", cuit),
            ("Cliente", COMPRADOR),
            ("Referencia", referencia),
        ]
    )
    r.h("Detalle")
    r.tabla(
        [("Concepto", "Importe (IVA incluido)"), *[(c, f"ARS {pesos(i)}") for c, i in items]],
        encabezado=True,
    )
    neto = (Decimal(total) / Decimal("1.21")).quantize(Decimal("0.01"))
    r.tabla(
        [
            ("Subtotal neto", f"ARS {pesos(str(neto))}"),
            ("IVA 21 %", f"ARS {pesos(str(Decimal(total) - neto))}"),
            ("Importe total", f"ARS {pesos(total)}"),
            ("Moneda", "Pesos argentinos (ARS)"),
        ]
    )
    if nota:
        r.p(nota)
    r.p("Comprobante ficticio: sin CAE ni código QR fiscal.")
    return Pieza(
        codigo,
        f"{codigo}_Factura_{numero}.pdf",
        "factura",
        {
            "numero": numero,
            "fecha_emision": iso,
            "emisor": emisor,
            "cuit_emisor": cuit,
            "importe_total": total,
            "moneda": "ARS",
        },
        r,
    )


def piezas() -> list[Pieza]:
    abono = [("Abono mensual de mantenimiento integral, octubre de 2026", "8000000.00")]
    return [
        # Historia principal: R4 en la factura v1, R3 aceptada en la OC.
        contrato_mantenimiento(),
        orden(
            "SD-O1", "OC-2026-118", "2026-09-25", ANDES, "8000000.00", abono, "Contrato C-2026-014"
        ),
        factura(
            "SD-F1",
            "0004-00001248",
            "2026-10-31",
            ANDES,
            "9200000.00",
            [*abono, ("Horas adicionales de soporte correctivo (40 h)", "1200000.00")],
            "Orden de compra OC-2026-118",
        ),
        factura(
            "SD-F2",
            "0004-00001263",
            "2026-11-05",
            ANDES,
            "8000000.00",
            abono,
            "Orden de compra OC-2026-118",
            "Reemplaza a la factura 0004-00001248, anulada mediante la nota de crédito"
            " 0004-00000087.",
        ),
        # Compra de equipos: la factura llega con el CUIT de otra empresa (R1).
        presupuesto(
            "SD-P2",
            "PRE-0457",
            "2026-10-12",
            EQUIPAR,
            "14500000.00",
            [
                ("6 notebooks de 14 pulgadas", "10800000.00"),
                ("6 monitores de 24 pulgadas", "3700000.00"),
            ],
        ),
        orden(
            "SD-O2",
            "OC-2026-131",
            "2026-10-20",
            EQUIPAR,
            "14500000.00",
            [("6 notebooks y 6 monitores según presupuesto PRE-0457", "14500000.00")],
            "Presupuesto PRE-0457",
        ),
        factura(
            "SD-F3",
            "0002-00000519",
            "2026-10-28",
            HORIZONTE,
            "14500000.00",
            [("6 notebooks y 6 monitores", "14500000.00")],
            "Orden de compra OC-2026-131",
        ),
        # Renovación de soporte: otro tipo de gestión, sin advertencias.
        contrato_soporte(),
        presupuesto(
            "SD-P3",
            "PRE-NA-0112",
            "2026-10-20",
            NUBE,
            "18000000.00",
            [("Soporte informático anual, 40 puestos", "18000000.00")],
        ),
    ]


def a_pdf(libreoffice: str, docx: Path, destino: Path, titulo: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                libreoffice,
                f"-env:UserInstallation={Path(tmp, 'perfil').as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                tmp,
                str(docx),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        escritor = PdfWriter()
        escritor.clone_document_from_reader(PdfReader(Path(tmp, docx.stem + ".pdf")))
        escritor.add_metadata(
            {
                "/Title": titulo,
                "/Author": "ATLAS · escenario de demostración SurDelta",
                "/CreationDate": "D:20261109000000Z",
                "/ModDate": "D:20261109000000Z",
            }
        )
        with destino.open("wb") as salida:
            escritor.write(salida)


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--libreoffice", default="soffice")
    opciones = analizador.parse_args(argumentos)
    if ORACULO.exists() or (SALIDA.exists() and any(SALIDA.iterdir())):
        print("El corpus SurDelta ya existe: no se sobrescribe", flush=True)
        return 1
    SALIDA.mkdir(parents=True, exist_ok=True)
    documentos = {}
    with tempfile.TemporaryDirectory() as tmp:
        for pieza in piezas():
            docx = Path(tmp, pieza.archivo.removesuffix(".pdf") + ".docx")
            pieza.redactor.guardar(docx)
            destino = SALIDA / pieza.archivo
            a_pdf(opciones.libreoffice, docx, destino, pieza.archivo.removesuffix(".pdf"))
            documentos[pieza.codigo] = {
                "archivo": pieza.archivo,
                "tipo_documental": pieza.tipo,
                "paginas": len(PdfReader(destino).pages),
                "sha256": hashlib.sha256(destino.read_bytes()).hexdigest(),
                "campos": pieza.campos,
            }
    oraculo = {
        "id": "oraculo_surdelta_v1",
        "estado": "demostracion",
        "decision": "DO-2026-11-09-DEMO-SURDELTA",
        "uso": "Demostración (videos y defensa). No acredita EVD-01 ni métricas de §6.3.",
        "consultas_cuit": CONSULTAS_CUIT,
        "documentos": documentos,
    }
    ORACULO.write_text(json.dumps(oraculo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"{len(documentos)} PDF en {SALIDA.relative_to(RAIZ)}; oráculo en {ORACULO.relative_to(RAIZ)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
