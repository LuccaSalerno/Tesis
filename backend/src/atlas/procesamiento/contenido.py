"""Representación normalizada común del contenido (§5.3.2).

PDF (Textract) y DOCX se llevan a una misma estructura de páginas y bloques que
conserva los localizadores disponibles: página y sección en PDF; párrafo, tabla y
sección en DOCX, que no tiene paginación. Se reutiliza en clasificación, extracción
y, más adelante, en indexación.
"""

import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass
from typing import Any, Final, Literal

from atlas.procesamiento.errores import ErrorPermanente

TipoBloque = Literal["titulo", "linea", "fila", "parrafo"]
Origen = Literal["textract", "docx"]

_W: Final = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_XML_DOCX_MAXIMO_BYTES: Final = 64 * 1024 * 1024
_ENCABEZADOS_LAYOUT: Final = frozenset({"LAYOUT_TITLE", "LAYOUT_SECTION_HEADER"})


@dataclass(frozen=True)
class Bloque:
    id: str
    tipo: TipoBloque
    texto: str
    localizador: str
    seccion: str | None = None


@dataclass(frozen=True)
class Pagina:
    numero: int | None
    bloques: tuple[Bloque, ...]

    def texto(self) -> str:
        return "\n".join(b.texto for b in self.bloques)


@dataclass(frozen=True)
class ContenidoNormalizado:
    origen: Origen
    paginas: tuple[Pagina, ...]

    @property
    def paginado(self) -> bool:
        return self.origen == "textract"

    def caracteres(self) -> int:
        return sum(len(b.texto) for p in self.paginas for b in p.bloques)

    def pagina(self, numero: int) -> Pagina | None:
        return next((p for p in self.paginas if p.numero == numero), None)

    def a_json(self) -> bytes:
        return json.dumps(asdict(self), ensure_ascii=False).encode()

    @classmethod
    def desde_json(cls, datos: bytes) -> "ContenidoNormalizado":
        crudo = json.loads(datos)
        return cls(
            origen=crudo["origen"],
            paginas=tuple(
                Pagina(numero=p["numero"], bloques=tuple(Bloque(**b) for b in p["bloques"]))
                for p in crudo["paginas"]
            ),
        )


def _espacios(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


# --- Textract --------------------------------------------------------------------------


def desde_textract(respuestas: list[dict[str, Any]]) -> ContenidoNormalizado:
    """Normaliza las páginas de resultados de `GetDocumentAnalysis` (TABLES y LAYOUT).

    Ordena líneas y filas de tabla por su posición vertical en cada página. Las líneas
    que pertenecen a una tabla se presentan como filas (`celda | celda`), sin repetir
    su texto. Los encabezados de LAYOUT definen la sección vigente de cada bloque.
    """
    bloques = [b for r in respuestas for b in r.get("Blocks", [])]
    por_id = {b["Id"]: b for b in bloques}

    def hijos(bloque: dict[str, Any]) -> list[str]:
        return [
            i
            for rel in bloque.get("Relationships", [])
            if rel.get("Type") == "CHILD"
            for i in rel.get("Ids", [])
        ]

    def texto_de(ids: list[str]) -> str:
        return _espacios(" ".join(por_id[i].get("Text", "") for i in ids if i in por_id))

    palabras_en_tablas: set[str] = set()
    for tabla in (b for b in bloques if b["BlockType"] == "TABLE"):
        for celda_id in hijos(tabla):
            palabras_en_tablas.update(hijos(por_id.get(celda_id, {})))
    lineas_encabezado = {
        linea_id for b in bloques if b["BlockType"] in _ENCABEZADOS_LAYOUT for linea_id in hijos(b)
    }

    elementos: dict[int, list[tuple[float, str, dict[str, Any]]]] = {}
    for b in bloques:
        pagina = int(b.get("Page", 1))
        arriba = float(b.get("Geometry", {}).get("BoundingBox", {}).get("Top", 0.0))
        if b["BlockType"] == "LINE":
            palabras = set(hijos(b))
            if palabras and palabras <= palabras_en_tablas:
                continue
            elementos.setdefault(pagina, []).append((arriba, "linea", b))
        elif b["BlockType"] == "TABLE":
            elementos.setdefault(pagina, []).append((arriba, "tabla", b))
        elif b["BlockType"] == "PAGE":
            elementos.setdefault(pagina, [])

    paginas: list[Pagina] = []
    seccion: str | None = None
    for numero in sorted(elementos):
        salida: list[Bloque] = []
        tablas = 0
        for _, clase, b in sorted(elementos[numero], key=lambda e: e[0]):
            if clase == "linea":
                texto = _espacios(b.get("Text", ""))
                if not texto:
                    continue
                es_titulo = b["Id"] in lineas_encabezado
                if es_titulo:
                    seccion = texto
                salida.append(
                    Bloque(
                        id=f"p{numero}-b{len(salida) + 1}",
                        tipo="titulo" if es_titulo else "linea",
                        texto=texto,
                        localizador=f"página {numero}",
                        seccion=seccion,
                    )
                )
            else:
                tablas += 1
                filas: dict[int, dict[int, str]] = {}
                for celda_id in hijos(b):
                    celda = por_id.get(celda_id, {})
                    if celda.get("BlockType") != "CELL":
                        continue
                    filas.setdefault(int(celda.get("RowIndex", 1)), {})[
                        int(celda.get("ColumnIndex", 1))
                    ] = texto_de(hijos(celda))
                for fila, celdas in sorted(filas.items()):
                    texto = " | ".join(celdas[c] for c in sorted(celdas))
                    if not texto.strip(" |"):
                        continue
                    salida.append(
                        Bloque(
                            id=f"p{numero}-b{len(salida) + 1}",
                            tipo="fila",
                            texto=texto,
                            localizador=f"página {numero}, tabla {tablas}, fila {fila}",
                            seccion=seccion,
                        )
                    )
        paginas.append(Pagina(numero=numero, bloques=tuple(salida)))
    if not any(p.bloques for p in paginas):
        raise ErrorPermanente("contenido_vacio")
    return ContenidoNormalizado(origen="textract", paginas=tuple(paginas))


# --- DOCX ------------------------------------------------------------------------------


def desde_docx(datos: bytes) -> ContenidoNormalizado:
    """Lee párrafos y tablas del cuerpo en orden (§5.3.1). El archivo ya fue validado al
    confirmar la carga; igual se acota el XML descomprimido (entrada no confiable)."""
    try:
        with zipfile.ZipFile(io.BytesIO(datos)) as contenedor:
            if contenedor.getinfo("word/document.xml").file_size > _XML_DOCX_MAXIMO_BYTES:
                raise ErrorPermanente("docx_demasiado_grande")
            # expat >= 2.4.1 mitiga la expansión exponencial de entidades.
            raiz = ET.fromstring(contenedor.read("word/document.xml"))  # noqa: S314
    except ErrorPermanente:
        raise
    except Exception as error:
        raise ErrorPermanente("docx_ilegible") from error

    cuerpo = raiz.find(f"{_W}body")
    salida: list[Bloque] = []
    seccion: str | None = None
    parrafos = tablas = 0
    for elemento in list(cuerpo) if cuerpo is not None else []:
        if elemento.tag == f"{_W}p":
            texto = _espacios("".join(t.text or "" for t in elemento.iter(f"{_W}t")))
            if not texto:
                continue
            parrafos += 1
            estilo = elemento.find(f"{_W}pPr/{_W}pStyle")
            valor_estilo = (estilo.get(f"{_W}val") or "") if estilo is not None else ""
            es_titulo = valor_estilo.lower().startswith(("heading", "titulo", "ttulo", "title"))
            if es_titulo:
                seccion = texto
            salida.append(
                Bloque(
                    id=f"d-b{len(salida) + 1}",
                    tipo="titulo" if es_titulo else "parrafo",
                    texto=texto,
                    localizador=f"párrafo {parrafos}",
                    seccion=seccion,
                )
            )
        elif elemento.tag == f"{_W}tbl":
            tablas += 1
            for numero_fila, fila in enumerate(elemento.iter(f"{_W}tr"), start=1):
                celdas = [
                    _espacios("".join(t.text or "" for t in celda.iter(f"{_W}t")))
                    for celda in fila.iter(f"{_W}tc")
                ]
                texto = " | ".join(celdas)
                if not texto.strip(" |"):
                    continue
                salida.append(
                    Bloque(
                        id=f"d-b{len(salida) + 1}",
                        tipo="fila",
                        texto=texto,
                        localizador=f"tabla {tablas}, fila {numero_fila}",
                        seccion=seccion,
                    )
                )
    if not salida:
        raise ErrorPermanente("contenido_vacio")
    return ContenidoNormalizado(
        origen="docx", paginas=(Pagina(numero=None, bloques=tuple(salida)),)
    )


# --- Presentación al modelo ------------------------------------------------------------

_ETIQUETAS: Final = re.compile(r"[<>]")
# Comillas angulares simples: se ven parecidas, pero no forman etiquetas.
_ABRE: Final = "\u2039"
_CIERRA: Final = "\u203a"


def neutralizar(texto: str) -> str:
    """El contenido no puede abrir ni cerrar las etiquetas que lo delimitan (§5.4.3)."""
    return _ETIQUETAS.sub(lambda m: _ABRE if m.group(0) == "<" else _CIERRA, texto)


def renderizar(contenido: ContenidoNormalizado) -> str:
    """Texto que recibe el modelo, delimitado como datos y sin instrucciones del sistema."""
    partes = [f'<documento origen="{contenido.origen}">']
    for pagina in contenido.paginas:
        cabecera = (
            f'<pagina numero="{pagina.numero}">' if pagina.numero is not None else "<contenido>"
        )
        partes.append(cabecera)
        for bloque in pagina.bloques:
            prefijo = "[título] " if bloque.tipo == "titulo" else ""
            partes.append(prefijo + neutralizar(bloque.texto))
        partes.append("</pagina>" if pagina.numero is not None else "</contenido>")
    partes.append("</documento>")
    return "\n".join(partes)


def comparable(texto: str) -> str:
    """Forma canónica para verificar citas: sin mayúsculas, espacios ni neutralización."""
    return _espacios(texto.replace(_ABRE, "<").replace(_CIERRA, ">")).casefold()
