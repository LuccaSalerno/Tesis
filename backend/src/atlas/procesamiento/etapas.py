"""Etapas de la máquina de estados (§5.3.1, DO-2026-10-22-PROC).

Cada etapa recibe y devuelve solo identificadores y claves de S3. El contenido y los
resultados documentales se leen y escriben en `resultados/{trabajo}/{intento}/`
(P3) y nunca forman parte de las entradas ni salidas de Step Functions.
"""

import json
from dataclasses import asdict, dataclass
from typing import Any, Final

from sqlalchemy.orm import Session

from atlas.integraciones.ciclo_vida_s3 import PREFIJO_RESULTADOS
from atlas.integraciones.puertos import AlmacenDocumental, ErrorIntegracion
from atlas.integraciones.textract import AnalizadorTextract
from atlas.procesamiento import analisis
from atlas.procesamiento.contenido import ContenidoNormalizado, desde_docx, desde_textract
from atlas.procesamiento.embeddings import ModeloEmbeddings
from atlas.procesamiento.errores import ErrorTransitorio
from atlas.procesamiento.modelo import ModeloGenerativo
from atlas.procesamiento.segmentacion import VERSION_SEGMENTACION, segmentar
from atlas.servicios import resultados

_JSON: Final = "application/json"


def prefijo_resultados(trabajo_id: int) -> str:
    return f"{PREFIJO_RESULTADOS}{trabajo_id}/"


def clave_resultado(trabajo_id: int, intento: int, nombre: str) -> str:
    return f"{prefijo_resultados(trabajo_id)}{intento}/{nombre}"


@dataclass(frozen=True)
class LimitesProcesamiento:
    max_tokens_clasificacion: int
    max_tokens_extraccion: int
    caracteres_maximos: int


def _leer(almacen: AlmacenDocumental, clave: str) -> bytes:
    try:
        return almacen.leer(clave)
    except ErrorIntegracion as error:
        raise ErrorTransitorio(error.codigo) from None


def _escribir(almacen: AlmacenDocumental, clave: str, datos: bytes) -> None:
    try:
        almacen.escribir(clave, datos, _JSON)
    except ErrorIntegracion as error:
        raise ErrorTransitorio(error.codigo) from None


def preparar(sesion: Session, trabajo_id: int, intento: int) -> dict[str, Any]:
    formato, clave = resultados.preparar(sesion, trabajo_id, intento)
    return {"formato": formato, "clave_objeto": clave}


def iniciar_textract(
    analizador: AnalizadorTextract, *, clave_objeto: str, trabajo_id: int, intento: int
) -> dict[str, Any]:
    return {"job_id": analizador.iniciar(clave_objeto, trabajo_id, intento)}


def consultar_textract(analizador: AnalizadorTextract, *, job_id: str) -> dict[str, Any]:
    return {"estado": analizador.estado(job_id)}


def normalizar_textract(
    analizador: AnalizadorTextract,
    almacen: AlmacenDocumental,
    *,
    job_id: str,
    trabajo_id: int,
    intento: int,
) -> dict[str, Any]:
    respuestas = analizador.resultado(job_id)
    _escribir(
        almacen,
        clave_resultado(trabajo_id, intento, "textract.json"),
        json.dumps(respuestas).encode(),
    )
    contenido = desde_textract(respuestas)
    clave = clave_resultado(trabajo_id, intento, "contenido.json")
    _escribir(almacen, clave, contenido.a_json())
    return {"contenido": clave}


def normalizar_docx(
    almacen: AlmacenDocumental, *, clave_objeto: str, trabajo_id: int, intento: int
) -> dict[str, Any]:
    contenido = desde_docx(_leer(almacen, clave_objeto))
    clave = clave_resultado(trabajo_id, intento, "contenido.json")
    _escribir(almacen, clave, contenido.a_json())
    return {"contenido": clave}


def clasificar(
    almacen: AlmacenDocumental,
    modelo: ModeloGenerativo,
    limites: LimitesProcesamiento,
    *,
    contenido: str,
    trabajo_id: int,
    intento: int,
) -> dict[str, Any]:
    resultado = analisis.clasificar(
        ContenidoNormalizado.desde_json(_leer(almacen, contenido)),
        modelo,
        max_tokens=limites.max_tokens_clasificacion,
        caracteres_maximos=limites.caracteres_maximos,
    )
    clave = clave_resultado(trabajo_id, intento, "clasificacion.json")
    _escribir(almacen, clave, json.dumps(analisis.a_dict(resultado)).encode())
    return {"clasificacion": clave}


def extraer(
    almacen: AlmacenDocumental,
    modelo: ModeloGenerativo,
    limites: LimitesProcesamiento,
    *,
    contenido: str,
    clasificacion: str,
    trabajo_id: int,
    intento: int,
) -> dict[str, Any]:
    tipo = analisis.clasificacion_desde_dict(json.loads(_leer(almacen, clasificacion))).tipo
    resultado = analisis.extraer(
        ContenidoNormalizado.desde_json(_leer(almacen, contenido)),
        tipo,
        modelo,
        max_tokens=limites.max_tokens_extraccion,
        caracteres_maximos=limites.caracteres_maximos,
    )
    clave = clave_resultado(trabajo_id, intento, "extraccion.json")
    _escribir(almacen, clave, json.dumps(analisis.a_dict(resultado)).encode())
    return {"extraccion": clave}


def indexar(
    almacen: AlmacenDocumental,
    embeddings: ModeloEmbeddings,
    *,
    contenido: str,
    trabajo_id: int,
    intento: int,
) -> dict[str, Any]:
    """§5.3.1, DO-2026-10-22-RAG (P4): fragmentos y sus vectores para la consulta asistida."""
    fragmentos = segmentar(ContenidoNormalizado.desde_json(_leer(almacen, contenido)))
    vectores = embeddings.embeber([f.texto for f in fragmentos], "search_document")
    datos = {
        "modelo_embeddings": embeddings.identificador,
        "version_segmentacion": VERSION_SEGMENTACION,
        "fragmentos": [
            {**asdict(f), "embedding": v} for f, v in zip(fragmentos, vectores, strict=True)
        ],
    }
    clave = clave_resultado(trabajo_id, intento, "fragmentos.json")
    _escribir(almacen, clave, json.dumps(datos).encode())
    return {"fragmentos": clave}


def persistir(
    sesion: Session,
    almacen: AlmacenDocumental,
    *,
    clasificacion: str,
    extraccion: str,
    fragmentos: str,
    trabajo_id: int,
    intento: int,
) -> dict[str, Any]:
    estado = resultados.persistir(
        sesion,
        trabajo_id=trabajo_id,
        intento=intento,
        clasificacion=analisis.clasificacion_desde_dict(json.loads(_leer(almacen, clasificacion))),
        extraccion=analisis.extraccion_desde_dict(json.loads(_leer(almacen, extraccion))),
        indexacion=json.loads(_leer(almacen, fragmentos)),
    )
    return {"resultado": estado}


def registrar_fallo(
    sesion: Session, *, trabajo_id: int, intento: int, codigo: str
) -> dict[str, Any]:
    return {
        "registrado": resultados.registrar_fallo(
            sesion, trabajo_id=trabajo_id, intento=intento, codigo=codigo
        )
    }
