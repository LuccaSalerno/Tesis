"""IA-D01–08, RNF-03/09: integridad del corpus generado, sin regeneración en CI."""

import copy
import importlib.util
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from herramientas.corpus_e90.comun import (
    cuit_valido,
    digito_cuit,
    leer_json,
    ruta_segura,
    sha256,
)
from herramientas.corpus_e90.validar import (
    comprobar_localizador,
    leer_conjunto,
    validar,
    validar_estructura,
)

RAIZ = Path(__file__).resolve().parents[2]


class IntegridadE90Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = leer_conjunto(RAIZ)

    def setUp(self):
        self.data = copy.deepcopy(self.base)

    def assertProblema(self, codigo):
        self.assertTrue(
            any(e.startswith(codigo + ":") for e in validar_estructura(self.data)),
            codigo,
        )

    def test_ia_d01_08_estructura_candidata_completa(self):
        self.assertEqual(validar_estructura(self.data), [])

    @unittest.skipUnless(
        importlib.util.find_spec("pypdf"),
        "IA-D02: falta pypdf para inspeccionar PDF generados; no se regenera",
    )
    def test_ia_d02_08_archivos_localizadores_y_referencias_reales(self):
        self.assertEqual(validar(RAIZ), [])

    def test_ia_d07_falta_documento_no_se_oculta(self):
        self.data["registros"]["registros"].pop()
        self.assertProblema("E90_PARTICIONES")

    def test_ia_d03_documento_ajuste_no_puede_ser_medicion(self):
        next(r for r in self.data["registros"]["registros"] if r["grupo"] == "ajuste")[
            "grupo"
        ] = "medicion"
        self.assertProblema("E90_PARTICIONES")

    def test_ia_d03_med_c_no_permitida_en_ajuste(self):
        next(r for r in self.data["registros"]["registros"] if r["grupo"] == "ajuste")[
            "plantilla_id"
        ] = "CTR-MED_C"
        self.assertProblema("E90_PLANTILLA_AJUSTE")

    def test_ia_d03_no_acepta_solo_una_exclusiva(self):
        for r in self.data["registros"]["registros"]:
            if r["tipo"] == "contrato" and r["plantilla_id"] == "CTR-MED_D":
                r["plantilla_id"] = "CTR-MED_C"
        self.assertProblema("E90_PLANTILLAS_MEDICION")

    def test_ia_d04_exactamente_tres_adversariales(self):
        next(r for r in self.data["registros"]["registros"] if r["prompt_injection"])[
            "prompt_injection"
        ] = False
        self.assertProblema("E90_ADVERSARIALES")

    def test_ia_d01_id_duplicado(self):
        self.data["registros"]["registros"][1]["doc_id"] = self.data["registros"][
            "registros"
        ][0]["doc_id"]
        self.assertProblema("E90_ID_DUPLICADO")

    def test_ia_d01_no_acepta_cuit_invalido(self):
        self.data["cuit"]["candidatos"][0]["cuit"] = "30-00000000-1"
        self.assertProblema("E90_CUIT_DIGITO")

    def test_ia_d01_cuit_fuera_del_grupo(self):
        self.data["registros"]["registros"][0]["cuit_id"] = "CUIT-INEXISTENTE"
        self.assertProblema("E90_CUIT_REFERENCIA")

    def test_ia_d01_no_asume_cuit_verificado(self):
        self.data["cuit"]["candidatos"][0]["estado"] = "verificado"
        self.assertProblema("E90_CUIT_ESTADO")

    def test_ia_d02_simulacion_debe_declararse(self):
        next(r for r in self.data["registros"]["registros"] if r["captura"])["captura"][
            "captura_fisica"
        ] = True
        self.assertProblema("E90_SIMULACION_NO_DECLARADA")

    def test_ia_d01_diferencia_oraculo_y_registro(self):
        self.data["campos"]["campos"][0]["valor_esperado"] = "valor_corrupto"
        self.assertProblema("E90_ORACULO_DISCREPANTE")

    def test_ia_d01_ausencia_no_es_valor_ni_localizador(self):
        next(f for f in self.data["campos"]["campos"] if not f["presente"])[
            "localizador"
        ] = {"tipo": "pagina", "pagina": 1}
        self.assertProblema("E90_AUSENCIA_CON_LOCALIZADOR")

    def test_ia_m12_no_marcar_revisado(self):
        self.data["campos"]["campos"][0]["revisado_por_autores"] = True
        self.assertProblema("E90_REVISION_NO_AUTORIZADA")

    def test_ia_m12_no_congelar_desde_validacion(self):
        self.data["artefactos"]["estado"] = "CONGELADO"
        self.assertProblema("E90_ESTADO_NO_CANDIDATO")

    def test_ia_d01_exige_cinco_fuentes_distintas(self):
        fuentes = self.data["plantillas"]["fuentes"]
        fuentes["MED_D"]["url_archivo"] = fuentes["BASE_A"]["url_archivo"]
        self.assertProblema("E90_DIVERSIDAD_FUENTES")

    def test_ia_d03_arg_a_exclusiva_medicion(self):
        next(r for r in self.data["registros"]["registros"] if r["grupo"] == "ajuste")[
            "plantilla_id"
        ] = "CTR-ARG_A"
        self.assertProblema("E90_PLANTILLA_AJUSTE")

    def test_ia_d03_arg_a_no_se_extiende_a_otro_documento(self):
        next(
            r
            for r in self.data["registros"]["registros"]
            if r["doc_id"] == "E90-M-PRE-03"
        )["plantilla_id"] = "PRE-ARG_A"
        self.assertProblema("E90_ARG_A_ALCANCE")

    def test_ia_d03_arg_a_no_sustituye_caso_extenso(self):
        next(
            r
            for r in self.data["registros"]["registros"]
            if r["doc_id"] == "E90-M-CTR-06"
        )["plantilla_id"] = "CTR-ARG_A"
        self.assertProblema("E90_ARG_A_ALCANCE")

    def test_ia_d01_arg_a_no_pierde_licencia_compartir_igual(self):
        self.data["plantillas"]["fuentes"]["ARG_A"]["licencia_adaptacion"] = "CC-BY-4.0"
        self.assertProblema("E90_ARG_A_LICENCIA")

    def test_ia_d01_arg_a_no_habilita_uso_comercial(self):
        self.data["plantillas"]["fuentes"]["ARG_A"]["uso_no_comercial"] = False
        self.assertProblema("E90_ARG_A_LICENCIA")

    def test_ia_d07_arg_a_preserva_64_entradas_y_128_auxiliares(self):
        revision = leer_json(RAIZ / "docs/evaluacion/corpus_e90/Revision_ARG_A.json")
        self.assertEqual(len(revision["entradas_sin_cambios"]), 64)
        for entry in revision["entradas_sin_cambios"]:
            self.assertNotEqual(entry["doc_id"], "E90-M-CTR-03")
            self.assertEqual(len(entry["archivos_sha256"]), 3)
            for path, expected in entry["archivos_sha256"].items():
                self.assertEqual(sha256(RAIZ / path), expected, entry["doc_id"])

    def test_rc_p04_arg_a_ground_truth_separa_honorarios_y_obra(self):
        record = next(
            r
            for r in self.data["registros"]["registros"]
            if r["doc_id"] == "E90-M-CTR-03"
        )
        self.assertEqual(
            record["valores"],
            {
                "contraparte": "Entidad Sintética ATLAS E90 03 (ficticia)",
                "cuit_contraparte": "30-98641004-6",
                "fecha_celebracion": "2026-01-13",
                "vigencia_desde": "2026-01-13",
                "vigencia_hasta": "2027-01-12",
                "monto_total": "80888.03",
                "moneda": "ARS",
            },
        )
        self.assertEqual(
            record["contexto_contractual"]["monto_total_corresponde_a"],
            "honorarios completos; no presupuesto de construcción",
        )
        fields = [
            f for f in self.data["campos"]["campos"] if f["doc_id"] == record["doc_id"]
        ]
        self.assertEqual(len(fields), 7)
        self.assertTrue(
            all(f["presente"] and f["localizador"]["pagina"] == 1 for f in fields)
        )

    def test_ia_d01_preparar_reproduce_registros_aprobados_con_arg_a(self):
        from herramientas.corpus_e90.preparar import preparar

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            folder = target / "docs/evaluacion"
            folder.mkdir(parents=True)
            shutil.copy2(
                RAIZ / "docs/evaluacion/plan_diseno_corpus_e90.csv",
                folder / "plan_diseno_corpus_e90.csv",
            )
            preparar(target)
            self.assertEqual(
                leer_json(target / "corpus/e90/registros_fuente.json"),
                self.data["registros"],
            )

    def test_ia_d01_no_usar_fuente_sin_aprobar(self):
        self.data["plantillas"]["fuentes"]["BASE_B"]["estado_aprobacion"] = "pendiente"
        self.assertProblema("E90_PROCEDENCIA_CONTRATO")

    def test_ia_d07_hash_binario_duplicado(self):
        arts = self.data["artefactos"]["artefactos"]
        arts[1]["sha256"] = arts[0]["sha256"]
        self.assertProblema("E90_ARCHIVO_DUPLICADO")

    def test_ia_d07_inventario_no_discrepa_manifiesto(self):
        self.data["inventario"][0]["sha256"] = "0" * 64
        self.assertProblema("E90_INVENTARIO_DISCREPANTE")

    def test_ia_d08_rechaza_preguntas_sobre_ajuste(self):
        ident = next(
            r["doc_id"]
            for r in self.data["registros"]["registros"]
            if r["grupo"] == "ajuste"
        )
        self.data["consultas"]["consultas"][0]["documentos_autorizados"] = [ident]
        self.assertProblema("E90_CONSULTA_CONTEXTO")

    def test_ia_d08_rechaza_fragmento_inexistente(self):
        self.data["consultas"]["consultas"][0]["fragmentos_relevantes"] = ["no-existe"]
        self.assertProblema("E90_CITA_FUERA_CONTEXTO")

    def test_ia_d08_rechaza_cita_ajena_al_contexto(self):
        self.data["consultas"]["consultas"][0]["documentos_autorizados"] = [
            self.data["consultas"]["consultas"][2]["documentos_autorizados"][0]
        ]
        self.assertProblema("E90_CITA_FUERA_CONTEXTO")

    def test_ia_d08_multidocumento_necesita_dos_documentos(self):
        q = next(
            q
            for q in self.data["consultas"]["consultas"]
            if q["categoria"] == "multidocumento"
        )
        q["fragmentos_relevantes"] = q["fragmentos_relevantes"][:1]
        self.assertProblema("E90_MULTIDOCUMENTO_INCOMPLETO")

    def test_ia_d08_abstencion_no_tiene_respuesta_inventada(self):
        next(
            q
            for q in self.data["consultas"]["consultas"]
            if q["categoria"] == "sin_evidencia"
        )["respuesta_referencia"] = "inventada"
        self.assertProblema("E90_ABSTENCION_INVALIDA")

    def test_ia_d08_reparto_10_8_6_6(self):
        self.data["consultas"]["consultas"][0]["categoria"] = "condiciones"
        self.assertProblema("E90_CONSULTAS_DISTRIBUCION")

    def test_ia_d08_falta_pregunta(self):
        self.data["consultas"]["consultas"].pop()
        self.assertProblema("E90_CONSULTAS_RECUENTO")

    def test_rnf03_impide_traversal_y_ruta_absoluta(self):
        for p in ("../secreto.pdf", "/tmp/secreto.pdf", "corpus/otro.pdf"):
            with self.assertRaises(ValueError):
                ruta_segura(RAIZ, p, "corpus/e90")

    def test_rnf03_impide_symlink_fuera_del_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "corpus/e90").mkdir(parents=True)
            (root / "fuera").write_text("sintetico")
            (root / "corpus/e90/enlace").symlink_to(root / "fuera")
            with self.assertRaises(ValueError):
                ruta_segura(root, "corpus/e90/enlace", "corpus/e90")

    def test_ia_m03_localizador_fuera_de_pagina(self):
        row = copy.deepcopy(
            next(
                f
                for f in self.data["campos"]["campos"]
                if f["localizador"] and f["localizador"]["tipo"] == "pagina"
            )
        )
        a = next(
            a
            for a in self.data["artefactos"]["artefactos"]
            if a["doc_id"] == row["doc_id"]
        )
        row["localizador"]["pagina"] = a["paginas"] + 1
        self.assertTrue(comprobar_localizador(RAIZ, row, a, {}))

    def test_ia_m04_localizador_fuera_de_parrafo(self):
        row = copy.deepcopy(
            next(
                f
                for f in self.data["campos"]["campos"]
                if f["localizador"] and f["localizador"]["tipo"] == "parrafo"
            )
        )
        a = next(
            a
            for a in self.data["artefactos"]["artefactos"]
            if a["doc_id"] == row["doc_id"]
        )
        row["localizador"]["indice"] = 999999
        self.assertTrue(comprobar_localizador(RAIZ, row, a, {}))

    def test_ia_m04_parrafo_debe_respaldar_valor(self):
        row = copy.deepcopy(
            next(
                f
                for f in self.data["campos"]["campos"]
                if f["localizador"] and f["localizador"]["tipo"] == "parrafo"
            )
        )
        a = next(
            a
            for a in self.data["artefactos"]["artefactos"]
            if a["doc_id"] == row["doc_id"]
        )
        row["localizador"]["indice"] = 1
        self.assertTrue(comprobar_localizador(RAIZ, row, a, {}))

    def test_ia_d01_algoritmo_modulo_11(self):
        for c in self.data["cuit"]["candidatos"]:
            self.assertTrue(cuit_valido(c["cuit"]))
        self.assertIsNone(digito_cuit("invalido"))
        self.assertFalse(cuit_valido("30999999999"))

    def test_ia_m04_mismo_valor_no_equivale_a_mismo_campo(self):
        ident = "E90-M-CTR-02"
        fields = [f for f in self.data["campos"]["campos"] if f["doc_id"] == ident]
        celebracion = next(f for f in fields if f["campo"] == "fecha_celebracion")
        vigencia = copy.deepcopy(
            next(f for f in fields if f["campo"] == "vigencia_desde")
        )
        self.assertEqual(celebracion["representacion"], vigencia["representacion"])
        vigencia["localizador"] = celebracion["localizador"]
        artifact = next(
            a for a in self.data["artefactos"]["artefactos"] if a["doc_id"] == ident
        )
        self.assertTrue(comprobar_localizador(RAIZ, vigencia, artifact, {}))

    def test_rnf09_errores_no_revelan_contenido(self):
        marcador = "MARCADOR_PRIVADO_NO_DEBE_SALIR"
        self.data["consultas"]["consultas"][0]["pregunta"] = marcador
        self.data["consultas"]["consultas"][0]["revisado_por_autores"] = True
        self.assertNotIn(marcador, "\n".join(validar_estructura(self.data)))


class RenderLocalE90Tests(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("E90_PRUEBAS_RENDER") == "1"
        and importlib.util.find_spec("docx")
        and importlib.util.find_spec("PIL")
        and shutil.which(os.environ.get("E90_LIBREOFFICE", "libreoffice")),
        "DO-CORPUS P4: render solo local y explícito; CI no regenera; requiere python-docx/Pillow/LibreOffice",
    )
    def test_ia_d02_docx_generado_es_abrible(self):
        from herramientas.corpus_e90.comun import parrafos_docx
        from herramientas.corpus_e90.generar import crear_docx

        data = leer_conjunto(RAIZ)
        with tempfile.TemporaryDirectory() as tmp:
            casos = [
                next(r for r in data["registros"]["registros"] if r["tipo"] == tipo)
                for tipo in (
                    "contrato",
                    "presupuesto",
                    "orden_compra",
                    "factura",
                    "comprobante",
                )
            ]
            casos.append(
                next(
                    r
                    for r in data["registros"]["registros"]
                    if r["doc_id"] == "E90-M-CTR-03"
                )
            )
            for r in casos:
                path = Path(tmp) / (r["doc_id"] + ".docx")
                crear_docx(r, path, data["plantillas"]["fuentes"])
                self.assertTrue(parrafos_docx(path))
                import subprocess

                from pypdf import PdfReader

                binary = os.environ.get("E90_LIBREOFFICE", "libreoffice")
                subprocess.run(
                    [
                        binary,
                        "-env:UserInstallation=" + (Path(tmp) / "perfil").as_uri(),
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        tmp,
                        str(path),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=90,
                )
                self.assertTrue(
                    PdfReader(path.with_suffix(".pdf")).pages[0].extract_text()
                )


if __name__ == "__main__":
    unittest.main()
