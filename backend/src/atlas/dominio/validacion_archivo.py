"""Validación del archivo recibido por su contenido, no por su extensión (RC-P04, RF-04).

Los archivos son entradas no confiables (§5.4.3): se acotan tamaños antes de
descomprimir o interpretar y cualquier error de lectura se trata como archivo
dañado. Los rechazos identifican la causa y la acción necesaria, sin incluir
contenido del archivo.
"""

import io
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import Final

from pypdf import PdfReader

from atlas.dominio.enumeraciones import FormatoArchivo

_FIRMA_PDF: Final = b"%PDF-"
_FIRMA_ZIP: Final = b"PK\x03\x04"
# Contenedor OLE: así se guardan los documentos de Office protegidos con contraseña.
_FIRMA_OLE: Final = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_DOCUMENTO_DOCX: Final = "word/document.xml"
_TEXTO_WORD: Final = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
# Tope del XML descomprimido, para no expandir archivos ZIP maliciosos.
_XML_DOCX_MAXIMO_BYTES: Final = 64 * 1024 * 1024


@dataclass(frozen=True)
class LimitesCarga:
    tamano_maximo_bytes: int
    paginas_maximas_pdf: int
    caracteres_maximos_docx: int


class ArchivoRechazado(Exception):
    """`codigo` es técnico y apto para registros; `mensaje` es para la persona que carga."""

    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(codigo)
        self.codigo = codigo
        self.mensaje = mensaje


def validar_tamano(tamano_bytes: int, declarado: int, limites: LimitesCarga) -> None:
    if tamano_bytes > limites.tamano_maximo_bytes:
        raise ArchivoRechazado(
            "archivo_demasiado_grande",
            f"El archivo supera el máximo de {limites.tamano_maximo_bytes // (1024 * 1024)} MB. "
            "Reducí su tamaño o dividilo y volvé a cargarlo.",
        )
    if tamano_bytes != declarado:
        raise ArchivoRechazado(
            "tamano_no_coincide",
            "El archivo recibido no coincide con el autorizado. Volvé a iniciar la carga.",
        )


def validar_contenido(datos: bytes, formato: FormatoArchivo, limites: LimitesCarga) -> None:
    detectado = _detectar_formato(datos)
    if detectado is None:
        raise ArchivoRechazado(
            "formato_no_admitido",
            "Solo se admiten archivos PDF o DOCX. Convertí el documento y volvé a cargarlo.",
        )
    if detectado != formato:
        raise ArchivoRechazado(
            "formato_no_coincide",
            f"El contenido corresponde a un {detectado.value.upper()}, no al formato declarado. "
            "Volvé a iniciar la carga indicando el formato correcto.",
        )
    if formato == FormatoArchivo.PDF:
        _validar_pdf(datos, limites)
    else:
        _validar_docx(datos, limites)


def _detectar_formato(datos: bytes) -> FormatoArchivo | None:
    if datos.startswith(_FIRMA_PDF):
        return FormatoArchivo.PDF
    if datos.startswith(_FIRMA_ZIP):
        return FormatoArchivo.DOCX
    if datos.startswith(_FIRMA_OLE):
        raise ArchivoRechazado(
            "docx_protegido",
            "El documento está protegido con contraseña. Quitá la protección y volvé a cargarlo.",
        )
    return None


def _validar_pdf(datos: bytes, limites: LimitesCarga) -> None:
    try:
        lector = PdfReader(io.BytesIO(datos))
        if lector.is_encrypted:
            raise ArchivoRechazado(
                "pdf_protegido",
                "El PDF está protegido con contraseña. Quitá la protección y volvé a cargarlo.",
            )
        paginas = len(lector.pages)
    except ArchivoRechazado:
        raise
    except Exception as error:  # pypdf puede fallar de muchas formas ante un archivo dañado
        raise _danado("pdf_danado", "PDF") from error
    if paginas == 0:
        raise _danado("pdf_danado", "PDF")
    if paginas > limites.paginas_maximas_pdf:
        raise ArchivoRechazado(
            "pdf_demasiadas_paginas",
            f"El PDF tiene {paginas} páginas y el máximo es {limites.paginas_maximas_pdf}. "
            "Dividilo en partes y cargalas por separado.",
        )


def _validar_docx(datos: bytes, limites: LimitesCarga) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(datos)) as contenedor:
            nombres = set(contenedor.namelist())
            if "[Content_Types].xml" not in nombres or _DOCUMENTO_DOCX not in nombres:
                raise _danado("docx_danado", "DOCX")
            if contenedor.getinfo(_DOCUMENTO_DOCX).file_size > _XML_DOCX_MAXIMO_BYTES:
                raise _demasiado_texto(limites)
            xml = contenedor.read(_DOCUMENTO_DOCX)
        caracteres = _texto_docx(xml)
    except ArchivoRechazado:
        raise
    except Exception as error:
        raise _danado("docx_danado", "DOCX") from error
    if caracteres > limites.caracteres_maximos_docx:
        raise _demasiado_texto(limites)


def _texto_docx(xml: bytes) -> int:
    """Cuenta los caracteres de texto del cuerpo del documento.

    ElementTree usa expat >= 2.4.1, que mitiga la expansión exponencial de
    entidades; además el XML se acota antes de leerlo (_XML_DOCX_MAXIMO_BYTES).
    """
    raiz = ET.fromstring(xml)  # noqa: S314
    return sum(len(nodo.text or "") for nodo in raiz.iter(_TEXTO_WORD))


def _danado(codigo: str, nombre: str) -> ArchivoRechazado:
    return ArchivoRechazado(
        codigo,
        f"El archivo {nombre} está dañado o no se puede leer. "
        "Generalo nuevamente y volvé a cargarlo.",
    )


def _demasiado_texto(limites: LimitesCarga) -> ArchivoRechazado:
    return ArchivoRechazado(
        "docx_demasiado_texto",
        f"El DOCX supera el máximo de {limites.caracteres_maximos_docx} caracteres de texto. "
        "Dividilo en partes y cargalas por separado.",
    )
