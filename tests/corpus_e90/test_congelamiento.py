"""DO-2026-10-23-E90-CONGELACION: congelación de la candidata y modo congelado del validador.

Las pruebas trabajan sobre una copia temporal: si el repositorio ya está congelado, la copia
vuelve primero a su forma candidata (los documentos y registros no cambian al congelar).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from herramientas.corpus_e90.comun import (
    ESTADO,
    ESTADO_CONGELADO,
    escribir_json,
    leer_json,
)
from herramientas.corpus_e90.congelar import ARCHIVOS, DOCUMENTOS_REVISADOS, congelar
from herramientas.corpus_e90.validar import leer_conjunto, validar, validar_estructura

RAIZ = Path(__file__).resolve().parents[2]
COPIAR = (
    "corpus/e90",
    "oraculos/e90",
    "herramientas/corpus_e90/plantillas",
    "docs/evaluacion/corpus_e90/fuentes",
    "docs/evaluacion/plan_diseno_corpus_e90.csv",
)


def copia_candidata(destino: Path) -> None:
    for relativa in COPIAR:
        origen, final = RAIZ / relativa, destino / relativa
        if origen.is_dir():
            shutil.copytree(origen, final)
        else:
            final.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen, final)
    registro = destino / "oraculos/e90/congelamiento.json"
    if registro.exists():
        registro.unlink()
        for nombre, archivo in ARCHIVOS.items():
            ruta = destino / "oraculos/e90" / archivo
            oraculo = leer_json(ruta)
            oraculo["estado"], oraculo["revisado_por_autores"] = ESTADO, False
            oraculo.pop("revision_autores", None)
            for elemento in oraculo[nombre]:
                elemento["estado"], elemento["revisado_por_autores"] = ESTADO, False
            escribir_json(ruta, oraculo)


class CongelamientoE90Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.raiz = Path(cls.tmp.name)
        copia_candidata(cls.raiz)
        cls.candidata_valida = validar(cls.raiz) == []
        cls.registro = congelar(
            cls.raiz, fecha="2026-10-23", autores=["Autor uno", "Autor dos"], commit_datos="abc"
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_p4_la_candidata_valida_y_queda_congelada(self):
        self.assertTrue(self.candidata_valida)
        self.assertEqual(validar(self.raiz), [])
        datos = leer_conjunto(self.raiz)
        for nombre in ARCHIVOS:
            self.assertEqual(datos[nombre]["estado"], ESTADO_CONGELADO)
            self.assertTrue(datos[nombre]["revisado_por_autores"])
            self.assertEqual(datos[nombre]["revision_autores"]["modalidad"], "muestreo")
        # P3: documentos, registros e inventario no cambian.
        for nombre in ("registros", "artefactos", "cuit"):
            self.assertEqual(datos[nombre]["estado"], ESTADO)

    def test_p2_solo_lo_revisado_queda_marcado(self):
        datos = leer_conjunto(self.raiz)
        campos = datos["campos"]["campos"]
        marcados = {c["doc_id"] for c in campos if c["revisado_por_autores"]}
        self.assertEqual(marcados, set(DOCUMENTOS_REVISADOS))
        self.assertTrue(all(q["revisado_por_autores"] for q in datos["consultas"]["consultas"]))
        self.assertFalse(any(f["revisado_por_autores"] for f in datos["fragmentos"]["fragmentos"]))

    def test_p1_el_registro_fija_las_huellas(self):
        rutas = self.registro["sha256"]
        self.assertIn("corpus/e90/registros_fuente.json", rutas)
        self.assertIn("oraculos/e90/consultas_candidatas.json", rutas)
        self.assertNotIn("oraculos/e90/congelamiento.json", rutas)
        self.assertEqual(len([r for r in rutas if r.startswith("corpus/e90/medicion/")]), 50)

    def test_p4_no_se_congela_dos_veces(self):
        with self.assertRaisesRegex(ValueError, "e90_ya_congelado"):
            congelar(self.raiz, fecha="2026-10-24", autores=["a", "b"], commit_datos="x")

    def test_p4_un_cambio_posterior_se_detecta(self):
        ruta = self.raiz / "oraculos/e90/inventario_candidato.csv"
        original = ruta.read_bytes()
        try:
            ruta.write_bytes(original + b"\n")
            self.assertEqual(validar(self.raiz), ["E90_HUELLAS_CONGELADAS:corpus"])
        finally:
            ruta.write_bytes(original)

    def test_p2_marcar_como_revisado_lo_no_revisado_es_un_error(self):
        datos = leer_conjunto(self.raiz)
        campo = next(c for c in datos["campos"]["campos"] if not c["revisado_por_autores"])
        campo["revisado_por_autores"] = True
        self.assertIn(
            "E90_REVISION_NO_AUTORIZADA:" + campo["doc_id"], validar_estructura(datos)
        )
        datos = leer_conjunto(self.raiz)
        datos["consultas"]["revision_autores"] = {}
        self.assertIn("E90_CONGELAMIENTO_INCOHERENTE:consultas", validar_estructura(datos))

    def test_p4_exige_ambos_autores_y_una_candidata_valida(self):
        with tempfile.TemporaryDirectory() as otro:
            raiz = Path(otro)
            copia_candidata(raiz)
            with self.assertRaisesRegex(ValueError, "ambos_autores"):
                congelar(raiz, fecha="2026-10-23", autores=["solo"], commit_datos="x")
            (raiz / "corpus/e90/registros_fuente.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "candidata_con_errores"):
                congelar(raiz, fecha="2026-10-23", autores=["a", "b"], commit_datos="x")


if __name__ == "__main__":
    unittest.main()
