"""Recuperación y respuestas de la consulta asistida.

Cada modelo de embeddings tiene su índice propio y congelado: los mismos *chunks* de
`segmentar` (producción), vectores de 1024 dimensiones y búsqueda exacta por coseno, con el
filtro de documentos autorizados de cada pregunta y k = 5. Es el mismo cálculo que pgvector
con `<=>` sin índice aproximado. Las respuestas usan `consultas.generar` (producción) con
los fragmentos que recupera el modelo de embeddings principal: ambos modelos generativos
reciben fragmentos idénticos.
"""

import hashlib
import json
import math
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from functools import partial
from pathlib import Path
from typing import Any, Final

from atlas.evaluacion.contenidos import FuenteContenidos
from atlas.evaluacion.ejecucion import con_reintentos, orden_modelos
from atlas.evaluacion.oraculos import Consulta, Documento, Fragmento
from atlas.evaluacion.registro import Registro
from atlas.procesamiento.contenido import comparable
from atlas.procesamiento.embeddings import ModeloEmbeddings
from atlas.procesamiento.modelo import ModeloGenerativo
from atlas.procesamiento.segmentacion import VERSION_SEGMENTACION, segmentar
from atlas.servicios.consultas import FragmentoRecuperado, generar

K: Final = 5
# Un fragmento del oráculo está en un *chunk* si este contiene al menos esta fracción de sus
# palabras normalizadas: tolera diferencias menores del OCR sin depender de igualdad exacta.
COBERTURA_MINIMA: Final = 0.8


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    orden: int
    texto: str
    pagina: int | None
    nombre_archivo: str


@dataclass(frozen=True)
class Indice:
    modelo: str
    chunks: tuple[Chunk, ...]
    vectores: tuple[tuple[float, ...], ...]

    def huella(self) -> str:
        datos = json.dumps(
            {"modelo": self.modelo, "chunks": [asdict(c) for c in self.chunks]}, sort_keys=True
        )
        return hashlib.sha256(datos.encode()).hexdigest()


def chunks_de(documentos: Sequence[Documento], contenidos: FuenteContenidos) -> list[Chunk]:
    salida = []
    for documento in documentos:
        for fragmento in segmentar(contenidos.obtener(documento)):
            salida.append(
                Chunk(
                    chunk_id=f"{documento.doc_id}#{fragmento.orden}",
                    doc_id=documento.doc_id,
                    orden=fragmento.orden,
                    texto=fragmento.texto,
                    pagina=fragmento.pagina,
                    nombre_archivo=documento.ruta.name,
                )
            )
    return salida


def construir_indice(chunks: Sequence[Chunk], embeddings: ModeloEmbeddings) -> Indice:
    vectores = embeddings.embeber([c.texto for c in chunks], "search_document")
    return Indice(embeddings.identificador, tuple(chunks), tuple(tuple(v) for v in vectores))


def guardar_indice(indice: Indice, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(
            {
                "modelo": indice.modelo,
                "segmentacion": VERSION_SEGMENTACION,
                "huella": indice.huella(),
                "chunks": [asdict(c) for c in indice.chunks],
                "vectores": [list(v) for v in indice.vectores],
            }
        ),
        "utf-8",
    )


def cargar_indice(ruta: Path) -> Indice:
    datos = json.loads(ruta.read_text("utf-8"))
    indice = Indice(
        datos["modelo"],
        tuple(Chunk(**c) for c in datos["chunks"]),
        tuple(tuple(v) for v in datos["vectores"]),
    )
    if indice.huella() != datos["huella"]:
        raise ValueError("indice_alterado")
    return indice


def _coseno(a: Sequence[float], b: Sequence[float]) -> float:
    norma = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norma if norma else 0.0


def buscar(
    indice: Indice, vector: Sequence[float], documentos: Sequence[str], k: int = K
) -> list[tuple[Chunk, float]]:
    """Los k más cercanos por distancia coseno (1 - similitud), desempate por orden estable."""
    autorizados = set(documentos)
    candidatos = [
        (chunk, 1.0 - _coseno(vector, v))
        for chunk, v in zip(indice.chunks, indice.vectores, strict=True)
        if chunk.doc_id in autorizados
    ]
    candidatos.sort(key=lambda par: (par[1], par[0].doc_id, par[0].orden))
    return candidatos[:k]


def _palabras(texto: str) -> list[str]:
    return re.findall(r"\w+", comparable(texto))


def contiene(chunk: Chunk, fragmento: Fragmento) -> bool:
    """Mismo documento, misma página si ambos la tienen y cobertura de palabras."""
    if chunk.doc_id != fragmento.doc_id:
        return False
    if (
        chunk.pagina is not None
        and fragmento.pagina is not None
        and chunk.pagina != fragmento.pagina
    ):
        return False
    buscadas = _palabras(fragmento.texto)
    if not buscadas:
        return False
    presentes = set(_palabras(chunk.texto))
    return sum(p in presentes for p in buscadas) / len(buscadas) >= COBERTURA_MINIMA


def medir_recuperacion(
    consultas: Sequence[Consulta],
    indices: dict[str, Indice],
    embeddings: dict[str, ModeloEmbeddings],
    fragmentos: dict[str, Fragmento],
    registro: Registro,
) -> int:
    """Una fila por pregunta y modelo de embeddings, con el ranking y los relevantes."""
    hechas = registro.claves(("embeddings", "pregunta_id"))
    nuevas = 0
    for alias, indice in indices.items():
        for consulta in consultas:
            if (alias, consulta.pregunta_id) in hechas:
                continue
            vector = embeddings[alias].embeber([consulta.pregunta], "search_query")[0]
            ranking = buscar(indice, vector, consulta.documentos)
            relevantes = [fragmentos[f] for f in consulta.fragmentos_relevantes]
            registro.escribir(
                {
                    "embeddings": alias,
                    "pregunta_id": consulta.pregunta_id,
                    "clase": consulta.clase,
                    "ranking": [
                        {
                            "chunk_id": chunk.chunk_id,
                            "distancia": round(distancia, 6),
                            "cubre": [f.fragmento_id for f in relevantes if contiene(chunk, f)],
                        }
                        for chunk, distancia in ranking
                    ],
                    "relevantes": [f.fragmento_id for f in relevantes],
                }
            )
            nuevas += 1
    return nuevas


def recuperados(indice: Indice, chunk_ids: Sequence[str]) -> list[FragmentoRecuperado]:
    """Los *chunks* con la forma que reciben las instrucciones de producción."""
    por_id = {c.chunk_id: (posicion, c) for posicion, c in enumerate(indice.chunks)}
    salida = []
    for numero, chunk_id in enumerate(chunk_ids, start=1):
        posicion, chunk = por_id[chunk_id]
        salida.append(
            FragmentoRecuperado(
                etiqueta=f"F{numero}",
                fragmento_id=posicion,
                contenido=chunk.texto,
                distancia=0.0,
                documento_id=0,
                documento_nombre=chunk.nombre_archivo,
                version_id=0,
                version_numero=1,
                pagina=chunk.pagina,
                seccion=None,
            )
        )
    return salida


def medir_respuestas(
    consultas: Sequence[Consulta],
    indice: Indice,
    rankings: dict[str, list[str]],
    modelos: dict[str, ModeloGenerativo],
    registro: Registro,
    *,
    repeticiones: int,
    max_tokens: int,
    esperar: Callable[[float], None] = time.sleep,
) -> int:
    """`rankings`: pregunta → *chunks* recuperados por el modelo de embeddings principal."""
    hechas = registro.claves(("repeticion", "modelo", "pregunta_id"))
    nuevas = 0
    for repeticion in range(1, repeticiones + 1):
        for consulta in consultas:
            fragmentos = recuperados(indice, rankings[consulta.pregunta_id])
            for alias in orden_modelos(list(modelos), repeticion):
                if (repeticion, alias, consulta.pregunta_id) in hechas:
                    continue
                generada, error, intentos, duracion = con_reintentos(
                    partial(generar, consulta.pregunta, fragmentos, modelos[alias], max_tokens),
                    esperar,
                )
                fila: dict[str, Any] = {
                    "repeticion": repeticion,
                    "modelo": alias,
                    "pregunta_id": consulta.pregunta_id,
                    "error": error,
                    "intentos": intentos,
                    "duracion_ms": duracion,
                    "suficiente": None,
                    "motivo": None,
                    "afirmaciones": None,
                    "tokens": None,
                }
                if generada is not None:
                    fila |= {
                        "suficiente": generada.motivo is None,
                        "motivo": generada.motivo.value if generada.motivo else None,
                        "afirmaciones": [
                            {
                                "texto": a.texto,
                                "citas": [
                                    indice.chunks[r.fragmento_id].chunk_id for r in a.referencias
                                ],
                            }
                            for a in generada.afirmaciones
                        ],
                        "tokens": [generada.uso[2], generada.uso[3]],
                    }
                registro.escribir(fila)
                nuevas += 1
    return nuevas
