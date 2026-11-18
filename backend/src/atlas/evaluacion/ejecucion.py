"""Clasificación y extracción medidas con el código de producción.

Para cada repetición y documento se invoca cada modelo generativo con el mismo contenido,
instrucciones y esquemas. El orden de los modelos se alterna entre repeticiones (H→S, S→H,
H→S) y las llamadas se intercalan por documento. La extracción usa el tipo **sugerido**,
como en producción. Los fallos transitorios se reintentan con espera creciente y se
registran sus intentos; un fallo definitivo queda como error, sin descartar la muestra.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import asdict
from functools import partial
from typing import Any, Final

from atlas.evaluacion.contenidos import FuenteContenidos
from atlas.evaluacion.oraculos import Documento
from atlas.evaluacion.registro import Registro
from atlas.procesamiento import analisis
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from atlas.procesamiento.modelo import ModeloGenerativo

INTENTOS_MAXIMOS: Final = 3


def orden_modelos(alias: Sequence[str], repeticion: int) -> list[str]:
    """Repetición 1: orden dado; 2: inverso; 3: dado."""
    return list(alias) if repeticion % 2 == 1 else list(reversed(alias))


def con_reintentos[T](
    llamada: Callable[[], T], esperar: Callable[[float], None] = time.sleep
) -> tuple[T | None, str | None, int, int]:
    """Devuelve (resultado, código de error, intentos, duración en ms)."""
    inicio = time.monotonic()
    for intento in range(1, INTENTOS_MAXIMOS + 1):
        try:
            resultado = llamada()
            return resultado, None, intento, round((time.monotonic() - inicio) * 1000)
        except ErrorTransitorio as error:
            if intento == INTENTOS_MAXIMOS:
                return None, str(error), intento, round((time.monotonic() - inicio) * 1000)
            esperar(2.0**intento)
        except ErrorPermanente as error:
            return None, str(error), intento, round((time.monotonic() - inicio) * 1000)
    raise AssertionError("inalcanzable")  # pragma: no cover


def _campos(extraccion: analisis.Extraccion) -> list[dict[str, Any]]:
    return [asdict(c) for c in extraccion.campos]


def medir_documentos(
    documentos: Sequence[Documento],
    contenidos: FuenteContenidos,
    modelos: dict[str, ModeloGenerativo],
    registro: Registro,
    *,
    repeticiones: int,
    max_tokens_clasificacion: int,
    max_tokens_extraccion: int,
    caracteres_maximos: int,
    esperar: Callable[[float], None] = time.sleep,
) -> int:
    """Devuelve la cantidad de mediciones nuevas registradas."""
    hechas = registro.claves(("repeticion", "modelo", "doc_id"))
    nuevas = 0
    for repeticion in range(1, repeticiones + 1):
        for documento in documentos:
            contenido = contenidos.obtener(documento)
            for alias in orden_modelos(list(modelos), repeticion):
                if (repeticion, alias, documento.doc_id) in hechas:
                    continue
                modelo = modelos[alias]
                clasificacion, error_c, intentos_c, ms_c = con_reintentos(
                    partial(
                        analisis.clasificar,
                        contenido,
                        modelo,
                        max_tokens=max_tokens_clasificacion,
                        caracteres_maximos=caracteres_maximos,
                    ),
                    esperar,
                )
                fila: dict[str, Any] = {
                    "repeticion": repeticion,
                    "modelo": alias,
                    "doc_id": documento.doc_id,
                    "clasificacion": clasificacion.tipo.value if clasificacion else None,
                    "error_clasificacion": error_c,
                    "intentos_clasificacion": intentos_c,
                    "duracion_clasificacion_ms": ms_c,
                    "tokens_clasificacion": [
                        clasificacion.uso.tokens_entrada,
                        clasificacion.uso.tokens_salida,
                    ]
                    if clasificacion
                    else None,
                    "campos": None,
                    "error_extraccion": None,
                }
                if clasificacion is not None:
                    tipo = clasificacion.tipo
                    extraccion, error_e, intentos_e, ms_e = con_reintentos(
                        partial(
                            analisis.extraer,
                            contenido,
                            tipo,
                            modelo,
                            max_tokens=max_tokens_extraccion,
                            caracteres_maximos=caracteres_maximos,
                        ),
                        esperar,
                    )
                    fila |= {
                        "campos": _campos(extraccion) if extraccion else None,
                        "error_extraccion": error_e,
                        "intentos_extraccion": intentos_e,
                        "duracion_extraccion_ms": ms_e,
                        "tokens_extraccion": [
                            extraccion.uso.tokens_entrada,
                            extraccion.uso.tokens_salida,
                        ]
                        if extraccion
                        else None,
                    }
                registro.escribir(fila)
                nuevas += 1
    return nuevas
