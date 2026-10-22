"""Validación del archivo por su contenido (RC-P04, RF-04)."""

import pytest

from atlas.dominio.enumeraciones import FormatoArchivo
from atlas.dominio.validacion_archivo import (
    ArchivoRechazado,
    LimitesCarga,
    validar_contenido,
    validar_tamano,
)
from tests import archivos

LIMITES = LimitesCarga(
    tamano_maximo_bytes=20 * 1024 * 1024, paginas_maximas_pdf=50, caracteres_maximos_docx=150_000
)
PDF, DOCX = FormatoArchivo.PDF, FormatoArchivo.DOCX


@pytest.mark.parametrize(
    ("datos", "formato"),
    [
        (archivos.CONTRATO_PDF.read_bytes(), PDF),
        (archivos.CONTRATO_DOCX.read_bytes(), DOCX),
        (archivos.pdf(paginas=50), PDF),
        (archivos.docx("x" * 150_000), DOCX),
    ],
    ids=["contrato_pdf_corpus", "contrato_docx_corpus", "pdf_50_paginas", "docx_150000"],
)
def test_rc_p04_archivos_admitidos(datos: bytes, formato: FormatoArchivo) -> None:
    validar_contenido(datos, formato, LIMITES)


@pytest.mark.parametrize(
    ("datos", "formato", "codigo"),
    [
        (b"", PDF, "formato_no_admitido"),
        (b"texto plano renombrado como .pdf", PDF, "formato_no_admitido"),
        (b"\x89PNG\r\n\x1a\n", DOCX, "formato_no_admitido"),
        (archivos.docx(), PDF, "formato_no_coincide"),
        (archivos.pdf(), DOCX, "formato_no_coincide"),
        (archivos.pdf(clave="secreta"), PDF, "pdf_protegido"),
        (archivos.pdf(paginas=51), PDF, "pdf_demasiadas_paginas"),
        (b"%PDF-1.7\nesto no es un PDF valido", PDF, "pdf_danado"),
        (archivos.pdf()[:200], PDF, "pdf_danado"),
        (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 64, DOCX, "docx_protegido"),
        (archivos.zip_sin_documento(), DOCX, "docx_danado"),
        (archivos.docx(documento_xml="<w:document"), DOCX, "docx_danado"),
        (b"PK\x03\x04truncado", DOCX, "docx_danado"),
        (archivos.docx("x" * 150_001), DOCX, "docx_demasiado_texto"),
    ],
    ids=[
        "vacio",
        "texto",
        "imagen",
        "docx_declarado_pdf",
        "pdf_declarado_docx",
        "pdf_con_clave",
        "pdf_51_paginas",
        "pdf_corrupto",
        "pdf_truncado",
        "office_protegido",
        "zip_sin_documento",
        "xml_malformado",
        "zip_truncado",
        "docx_150001",
    ],
)
def test_rc_p04_archivos_rechazados_con_causa_y_accion(
    datos: bytes, formato: FormatoArchivo, codigo: str
) -> None:
    with pytest.raises(ArchivoRechazado) as rechazo:
        validar_contenido(datos, formato, LIMITES)
    assert rechazo.value.codigo == codigo
    assert "volvé" in rechazo.value.mensaje.lower() or "dividilo" in rechazo.value.mensaje.lower()


def test_rc_p04_limites_configurables() -> None:
    estrictos = LimitesCarga(
        tamano_maximo_bytes=10, paginas_maximas_pdf=1, caracteres_maximos_docx=3
    )
    with pytest.raises(ArchivoRechazado, match="pdf_demasiadas_paginas"):
        validar_contenido(archivos.pdf(paginas=2), PDF, estrictos)
    with pytest.raises(ArchivoRechazado, match="docx_demasiado_texto"):
        validar_contenido(archivos.docx("abcd"), DOCX, estrictos)
    with pytest.raises(ArchivoRechazado, match="archivo_demasiado_grande"):
        validar_tamano(11, 11, estrictos)


def test_rc_p04_tamano_recibido_debe_coincidir_con_el_autorizado() -> None:
    with pytest.raises(ArchivoRechazado, match="tamano_no_coincide"):
        validar_tamano(1000, 999, LIMITES)
    validar_tamano(1000, 1000, LIMITES)


def test_rnf_03_el_rechazo_no_incluye_contenido_del_archivo() -> None:
    with pytest.raises(ArchivoRechazado) as rechazo:
        validar_contenido(b"CUIT 30-71234567-8 importe 10500", PDF, LIMITES)
    assert "30-71234567-8" not in rechazo.value.mensaje
