"""Puntos de entrada de las funciones Lambda del procesamiento (§5.4.2).

- `manejar_procesamiento`: fuera de la VPC; usa S3, Textract y Bedrock.
- `manejar_persistencia`: dentro de la VPC; usa PostgreSQL (vía RDS Proxy) y S3.

Toda falla sale como `ErrorTransitorio` o `ErrorPermanente` con un código técnico como
único mensaje y sin encadenar la excepción original: lo que llega a Step Functions y a
los registros no puede contener contenido documental (AGENTS.md §2.5, RNF-09).
"""

import json
import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any, Final

from atlas.configuracion import obtener_configuracion
from atlas.integraciones.aws import AlmacenS3, crear_cliente
from atlas.integraciones.bedrock import ModeloBedrockConverse
from atlas.integraciones.textract import AnalizadorTextract
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.procesamiento import etapas
from atlas.procesamiento.errores import ErrorEtapa, ErrorPermanente, ErrorTransitorio
from atlas.registro import configurar_registro, registrar_evento

_registrador = logging.getLogger("atlas.procesamiento")

CLAVES_EVENTO: Final = frozenset(
    {
        "etapa",
        "trabajo_id",
        "intento",
        "clave_objeto",
        "job_id",
        "contenido",
        "clasificacion",
        "extraccion",
        "error",
        "causa",
    }
)


ETAPAS_PROCESAMIENTO: Final = frozenset(
    {
        "iniciar_textract",
        "consultar_textract",
        "normalizar_textract",
        "normalizar_docx",
        "clasificar",
        "extraer",
    }
)
ETAPAS_PERSISTENCIA: Final = frozenset({"preparar", "persistir", "registrar_fallo"})


@lru_cache
def _dependencias() -> dict[str, Any]:
    configuracion = obtener_configuracion()
    configurar_registro(configuracion.nivel_registro)
    bucket = configuracion.s3_bucket_documentos or ""
    return {
        "configuracion": configuracion,
        "almacen": AlmacenS3(crear_cliente(configuracion, "s3"), bucket),
        "analizador": AnalizadorTextract(crear_cliente(configuracion, "textract"), bucket),
        "modelo": ModeloBedrockConverse(
            crear_cliente(configuracion, "bedrock-runtime"), configuracion.bedrock_perfil_generativo
        ),
        "limites": etapas.LimitesProcesamiento(
            max_tokens_clasificacion=configuracion.procesamiento_max_tokens_clasificacion,
            max_tokens_extraccion=configuracion.procesamiento_max_tokens_extraccion,
            caracteres_maximos=configuracion.procesamiento_caracteres_maximos,
        ),
    }


@lru_cache
def _fabrica_sesiones() -> Any:
    return crear_fabrica_sesiones(crear_motor(_dependencias()["configuracion"]))


def codigo_de_falla(error: str | None, causa: str | None) -> str:
    """Extrae el código técnico que una etapa informó (su `errorMessage`)."""
    try:
        detalle = json.loads(causa or "")
        mensaje = detalle.get("errorMessage") if isinstance(detalle, dict) else None
    except ValueError:
        mensaje = None
    if isinstance(mensaje, str) and mensaje.replace("_", "").isalnum() and len(mensaje) <= 60:
        return mensaje
    return (error or "error_desconocido")[:60]


def ejecutar(evento: dict[str, Any], etapas_disponibles: dict[str, Callable[..., Any]]) -> Any:
    trabajo_id = evento.get("trabajo_id")
    try:
        if not set(evento) <= CLAVES_EVENTO or evento.get("etapa") not in etapas_disponibles:
            raise ErrorPermanente("evento_invalido")
        parametros = {k: v for k, v in evento.items() if k != "etapa"}
        return etapas_disponibles[evento["etapa"]](**parametros)
    except ErrorEtapa as error:
        registrar_evento(
            _registrador,
            "etapa_fallida",
            logging.WARNING,
            trabajo_id=trabajo_id,
            codigo_error=error.codigo,
        )
        raise type(error)(error.codigo) from None
    except Exception as error:  # nunca se propaga el mensaje de una excepción ajena
        codigo = f"inesperado_{type(error).__name__}"
        registrar_evento(
            _registrador, "etapa_fallida", logging.ERROR, trabajo_id=trabajo_id, codigo_error=codigo
        )
        raise ErrorPermanente(codigo) from None


def manejar_procesamiento(evento: dict[str, Any], _contexto: Any) -> Any:
    d = _dependencias()
    return ejecutar(
        evento,
        {
            "iniciar_textract": lambda **p: etapas.iniciar_textract(d["analizador"], **p),
            "consultar_textract": lambda job_id, **_: etapas.consultar_textract(
                d["analizador"], job_id=job_id
            ),
            "normalizar_textract": lambda **p: etapas.normalizar_textract(
                d["analizador"], d["almacen"], **p
            ),
            "normalizar_docx": lambda **p: etapas.normalizar_docx(d["almacen"], **p),
            "clasificar": lambda **p: etapas.clasificar(
                d["almacen"], d["modelo"], d["limites"], **p
            ),
            "extraer": lambda **p: etapas.extraer(d["almacen"], d["modelo"], d["limites"], **p),
        },
    )


def manejar_persistencia(evento: dict[str, Any], _contexto: Any) -> Any:
    d = _dependencias()

    def en_transaccion(funcion: Callable[..., Any]) -> Callable[..., Any]:
        def envoltura(**parametros: Any) -> Any:
            with _fabrica_sesiones()() as sesion:
                try:
                    resultado = funcion(sesion, **parametros)
                    sesion.commit()
                    return resultado
                except Exception:
                    sesion.rollback()
                    raise

        return envoltura

    return ejecutar(
        evento,
        {
            "preparar": en_transaccion(etapas.preparar),
            "persistir": en_transaccion(
                lambda sesion, **p: etapas.persistir(sesion, d["almacen"], **p)
            ),
            "registrar_fallo": en_transaccion(
                lambda sesion, trabajo_id, intento, error=None, causa=None: etapas.registrar_fallo(
                    sesion,
                    trabajo_id=trabajo_id,
                    intento=intento,
                    codigo=codigo_de_falla(error, causa),
                )
            ),
        },
    )


__all__ = ["ErrorPermanente", "ErrorTransitorio", "manejar_persistencia", "manejar_procesamiento"]
