"""Segmentación para la indexación (§5.3.4)."""

from atlas.procesamiento.contenido import desde_docx, desde_textract
from atlas.procesamiento.segmentacion import VERSION_SEGMENTACION, segmentar
from tests import archivos
from tests.flujo_procesamiento import PAGINAS_C_V1
from tests.procesamiento_fijo import textract_fijo


def test_fragmentos_respetan_pagina_y_seccion() -> None:
    fragmentos = segmentar(desde_textract(textract_fijo(PAGINAS_C_V1)))
    assert [f.pagina for f in fragmentos] == [1, 2, 3, 4, 5, 6]
    vigencia = fragmentos[-1]
    assert vigencia.seccion == "5. Plazo de ejecución y vigencia"
    assert "28/02/2027" in vigencia.texto
    assert vigencia.localizador == "página 6"
    assert [f.orden for f in fragmentos] == list(range(1, 7))
    assert VERSION_SEGMENTACION == "segmentacion-v1"


def test_ningun_fragmento_supera_el_maximo() -> None:
    largo = "Cláusula de prueba con texto sintético. " * 120  # ~4800 caracteres
    contenido = desde_textract(textract_fijo([[("titulo", "1. Larga"), ("linea", largo)]]))
    fragmentos = segmentar(contenido, maximo=1200)
    assert len(fragmentos) >= 4
    assert all(len(f.texto) <= 1200 for f in fragmentos)
    assert {f.seccion for f in fragmentos} == {"1. Larga"}


def test_palabras_sin_puntuacion_tambien_se_dividen() -> None:
    contenido = desde_textract(textract_fijo([[("linea", "palabra " * 400)]]))
    assert all(len(f.texto) <= 300 for f in segmentar(contenido, maximo=300))


def test_docx_con_localizador_de_parrafos() -> None:
    fragmentos = segmentar(desde_docx(archivos.CONTRATO_DOCX.read_bytes()))
    assert all(f.pagina is None for f in fragmentos)
    assert all(len(f.texto) <= 1200 for f in fragmentos)
    assert any(" a " in f.localizador for f in fragmentos)  # grupo de varios párrafos
    assert any("28/02/2027" in f.texto for f in fragmentos)
