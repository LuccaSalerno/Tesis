"""Contenido normalizado de cada documento, con el OCR una sola vez (P6, RC-P07.5).

Los PDF pasan por Textract asíncrono, igual que en producción: el archivo se sube al bucket
de evaluación (P5), se analiza con TABLES y LAYOUT y la respuesta cruda se guarda en una
caché por huella del archivo. Las repeticiones y los modelos reutilizan esa respuesta, de
modo que el OCR no se repite ni se cuenta dos veces. Los DOCX se leen con `desde_docx`.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final, Protocol

from atlas.evaluacion.oraculos import Documento
from atlas.integraciones.textract import FUNCIONES, AnalizadorTextract
from atlas.procesamiento.contenido import ContenidoNormalizado, desde_docx, desde_textract

PREFIJO_BUCKET: Final = "cargas-temporales/evaluacion"
ESPERA_MAXIMA_S: Final = 900.0


class Almacen(Protocol):
    def escribir(self, clave: str, datos: bytes, tipo_contenido: str) -> None: ...


def clave_cache(documento: Documento) -> str:
    # La caché depende del archivo y de las funciones de Textract: si cambian, se recalcula.
    return f"{documento.sha256}.{'-'.join(FUNCIONES).lower()}.textract.json"


class FuenteContenidos:
    def __init__(
        self,
        cache: Path,
        analizador: AnalizadorTextract | None = None,
        almacen: Almacen | None = None,
        *,
        registrar: Callable[[dict[str, Any]], None] = lambda _: None,
        esperar: Callable[[float], None] = time.sleep,
        intervalo_s: float = 5.0,
    ) -> None:
        self._cache = cache
        self._analizador = analizador
        self._almacen = almacen
        self._registrar = registrar
        self._esperar = esperar
        self._intervalo_s = intervalo_s
        self._memoria: dict[str, ContenidoNormalizado] = {}

    def obtener(self, documento: Documento) -> ContenidoNormalizado:
        if documento.doc_id not in self._memoria:
            self._memoria[documento.doc_id] = (
                desde_docx(documento.ruta.read_bytes())
                if documento.es_docx
                else desde_textract(self._respuestas_textract(documento))
            )
        return self._memoria[documento.doc_id]

    def _respuestas_textract(self, documento: Documento) -> list[dict[str, Any]]:
        ruta = self._cache / clave_cache(documento)
        if ruta.is_file():
            respuestas: list[dict[str, Any]] = json.loads(ruta.read_text("utf-8"))
            return respuestas
        if self._analizador is None or self._almacen is None:
            raise RuntimeError(f"falta_ocr_en_cache:{documento.doc_id}")
        inicio = time.monotonic()
        clave = f"{PREFIJO_BUCKET}/{documento.sha256}.pdf"
        self._almacen.escribir(clave, documento.ruta.read_bytes(), "application/pdf")
        # Identificador estable por archivo: un reintento no inicia un segundo análisis.
        trabajo = int(documento.sha256[:12], 16) % 2**31
        job_id = self._analizador.iniciar(clave, trabajo, 1)
        while (estado := self._analizador.estado(job_id)) == "en_curso":
            if time.monotonic() - inicio > ESPERA_MAXIMA_S:
                raise RuntimeError(f"textract_sin_terminar:{documento.doc_id}")
            self._esperar(self._intervalo_s)
        if estado != "completado":
            raise RuntimeError(f"textract_fallido:{documento.doc_id}")
        respuestas = self._analizador.resultado(job_id)
        self._cache.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(respuestas), "utf-8")
        self._registrar(
            {
                "evento": "ocr",
                "doc_id": documento.doc_id,
                "paginas": sum(
                    1 for r in respuestas for b in r["Blocks"] if b.get("BlockType") == "PAGE"
                ),
                "duracion_ms": round((time.monotonic() - inicio) * 1000),
            }
        )
        return respuestas
