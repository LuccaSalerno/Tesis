"""Archivos sintéticos para las pruebas de carga (sin contenido real)."""

import io
import zipfile
from pathlib import Path

from pypdf import PdfWriter

CORPUS = Path(__file__).resolve().parents[2] / "demo" / "cadena_evidencia" / "documentos"
CONTRATO_PDF = CORPUS / "C-v1_Contrato_Mantenimiento_ATLAS.pdf"
CONTRATO_DOCX = CORPUS / "C-v1_Contrato_Mantenimiento_ATLAS.docx"

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
)


def pdf(paginas: int = 1, clave: str | None = None) -> bytes:
    escritor = PdfWriter()
    for _ in range(paginas):
        escritor.add_blank_page(width=595, height=842)
    if clave is not None:
        escritor.encrypt(clave)
    salida = io.BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def docx(texto: str = "Documento ficticio", documento_xml: str | None = None) -> bytes:
    if documento_xml is None:
        documento_xml = (
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{texto}</w:t></w:r></w:p></w:body></w:document>"
        )
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w") as contenedor:
        contenedor.writestr("[Content_Types].xml", _CONTENT_TYPES)
        contenedor.writestr("word/document.xml", documento_xml)
    return salida.getvalue()


def zip_sin_documento() -> bytes:
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w") as contenedor:
        contenedor.writestr("[Content_Types].xml", _CONTENT_TYPES)
    return salida.getvalue()
