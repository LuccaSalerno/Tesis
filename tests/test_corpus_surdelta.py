"""DO-2026-11-09-DEMO-SURDELTA: integridad de los documentos de demostración, sin regenerar.

Huellas del oráculo, CUIT ya consultados por el equipo (nunca los de medición de E90), datos
visibles en cada PDF, sin texto de control, y los conflictos que la historia necesita.
"""

import hashlib
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

from herramientas.corpus_e90.comun import cuit_valido

RAIZ = Path(__file__).resolve().parents[1]
ORACULO = json.loads((RAIZ / "oraculos/oraculo_surdelta_v1.json").read_text(encoding="utf-8"))
CORPUS = RAIZ / "corpus/surdelta"


def texto(archivo: str) -> str:
    return " ".join(p.extract_text() for p in PdfReader(CORPUS / archivo).pages)


def pesos(valor: str) -> str:
    entero, decimales = f"{Decimal(valor):.2f}".split(".")
    return f"{int(entero):,}".replace(",", ".") + "," + decimales


def fecha(iso: str) -> str:
    anio, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{anio}"


class CorpusSurDeltaTests(unittest.TestCase):
    def campos(self, codigo: str) -> dict[str, str]:
        return ORACULO["documentos"][codigo]["campos"]

    def test_huellas_del_oraculo(self) -> None:
        self.assertEqual(
            {d["archivo"] for d in ORACULO["documentos"].values()},
            {p.name for p in CORPUS.iterdir()},
        )
        for doc in ORACULO["documentos"].values():
            huella = hashlib.sha256((CORPUS / doc["archivo"]).read_bytes()).hexdigest()
            self.assertEqual(huella, doc["sha256"], doc["archivo"])

    def test_solo_cuit_consultados_en_arca_y_ninguno_de_medicion(self) -> None:
        pd07 = json.loads((RAIZ / "oraculos/oraculo_PD07_v2.json").read_text(encoding="utf-8"))
        candidatos = json.loads((RAIZ / "oraculos/e90/cuit_candidatos.json").read_text())
        ajuste = {
            c["cuit"]
            for c in candidatos["candidatos"]
            if c["particion"] == "ajuste" and c["consulta_arca"]["resultado"] == "No existe"
        }
        consultados = ajuste | {pd07["registro_cuit"]["numero"]}
        for codigo, doc in ORACULO["documentos"].items():
            for campo, valor in doc["campos"].items():
                if campo.startswith("cuit"):
                    self.assertTrue(cuit_valido(valor), codigo)
                    self.assertIn(valor, consultados, codigo)
        self.assertEqual(
            set(ORACULO["consultas_cuit"]),
            {
                v
                for d in ORACULO["documentos"].values()
                for k, v in d["campos"].items()
                if k.startswith("cuit")
            },
        )

    def test_cada_dato_figura_en_su_documento_y_sin_texto_de_control(self) -> None:
        for codigo, doc in ORACULO["documentos"].items():
            contenido = re.sub(r"\s+", " ", texto(doc["archivo"]))
            for campo, valor in doc["campos"].items():
                if campo in ("monto_total", "importe_total"):
                    valor = pesos(valor)
                elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
                    valor = fecha(valor)
                elif campo == "moneda":
                    valor = "(ARS)"
                self.assertIn(valor, contenido, f"{codigo}.{campo}")
            for prohibido in ("regla", "R3", "R4", "se espera", "advertencia", "oráculo"):
                self.assertNotIn(prohibido, contenido, codigo)

    def test_conflictos_de_la_historia(self) -> None:
        contrato, orden = self.campos("SD-C1"), self.campos("SD-O1")
        v1, v2 = self.campos("SD-F1"), self.campos("SD-F2")
        # R4: la v1 supera la orden y la v2 no; R3: la orden es anterior a la vigencia.
        self.assertGreater(Decimal(v1["importe_total"]), Decimal(orden["importe_total"]))
        self.assertEqual(Decimal(v2["importe_total"]), Decimal(orden["importe_total"]))
        self.assertLess(orden["fecha"], contrato["vigencia_desde"])
        # RF-06: la v2 tiene otro número y el mismo CUIT del emisor que la v1.
        self.assertNotEqual(v1["numero"], v2["numero"])
        self.assertEqual(v1["cuit_emisor"], v2["cuit_emisor"])
        self.assertEqual(v1["cuit_emisor"], orden["cuit_proveedor"])
        self.assertEqual(orden["cuit_proveedor"], contrato["cuit_contraparte"])
        # Compra: la factura llega con el CUIT de otra empresa (R1).
        self.assertNotEqual(
            self.campos("SD-F3")["cuit_emisor"], self.campos("SD-O2")["cuit_proveedor"]
        )


if __name__ == "__main__":
    unittest.main()
