"""Segmentación del contenido normalizado para la indexación (§5.3.4, DO-2026-10-22-RAG).

Los fragmentos respetan los límites de página y de sección y agrupan bloques
consecutivos hasta un máximo de caracteres por debajo del límite de 512 tokens de
Cohere Embed Multilingual v3 (§5.4.1). Un bloque que excede el máximo se divide por
oraciones y, si hace falta, por palabras. Cada fragmento conserva su localizador.
"""

import re
from dataclasses import dataclass
from typing import Final

from atlas.procesamiento.contenido import Bloque, ContenidoNormalizado

VERSION_SEGMENTACION: Final = "segmentacion-v1"
CARACTERES_MAXIMOS: Final = 1200


@dataclass(frozen=True)
class FragmentoTexto:
    orden: int
    texto: str
    pagina: int | None
    seccion: str | None
    localizador: str


def segmentar(
    contenido: ContenidoNormalizado, maximo: int = CARACTERES_MAXIMOS
) -> list[FragmentoTexto]:
    fragmentos: list[FragmentoTexto] = []
    for pagina in contenido.paginas:
        grupo: list[Bloque] = []
        for bloque in pagina.bloques:
            if grupo and (
                bloque.seccion != grupo[0].seccion or len(_unir([*grupo, bloque])) > maximo
            ):
                _cerrar(fragmentos, grupo, pagina.numero, contenido.paginado, maximo)
                grupo = []
            grupo.append(bloque)
        if grupo:
            _cerrar(fragmentos, grupo, pagina.numero, contenido.paginado, maximo)
    return fragmentos


def _unir(bloques: list[Bloque]) -> str:
    return "\n".join(b.texto for b in bloques)


def _cerrar(
    fragmentos: list[FragmentoTexto],
    grupo: list[Bloque],
    pagina: int | None,
    paginado: bool,
    maximo: int,
) -> None:
    localizador = (
        grupo[0].localizador
        if len(grupo) == 1
        else (
            f"página {pagina}" if paginado else f"{grupo[0].localizador} a {grupo[-1].localizador}"
        )
    )
    for parte in _partir(_unir(grupo), maximo):
        fragmentos.append(
            FragmentoTexto(
                orden=len(fragmentos) + 1,
                texto=parte,
                pagina=pagina,
                seccion=grupo[0].seccion,
                localizador=localizador,
            )
        )


def _partir(texto: str, maximo: int) -> list[str]:
    if len(texto) <= maximo:
        return [texto]
    partes: list[str] = []
    actual = ""
    for unidad in _unidades(texto, maximo):
        candidato = f"{actual} {unidad}".strip()
        if actual and len(candidato) > maximo:
            partes.append(actual)
            actual = unidad
        else:
            actual = candidato
    if actual:
        partes.append(actual)
    return partes


def _unidades(texto: str, maximo: int) -> list[str]:
    """Oraciones y, para oraciones demasiado largas, tramos de palabras."""
    unidades: list[str] = []
    for oracion in re.split(r"(?<=[.;:])\s+|\n+", texto):
        if len(oracion) <= maximo:
            unidades.append(oracion)
            continue
        tramo = ""
        for palabra in oracion.split():
            if tramo and len(tramo) + 1 + len(palabra) > maximo:
                unidades.append(tramo)
                tramo = palabra
            else:
                tramo = f"{tramo} {palabra}".strip()
        if tramo:
            unidades.append(tramo)
    return [u for u in unidades if u.strip()]
