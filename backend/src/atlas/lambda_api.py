"""Punto de entrada de la API en AWS Lambda detrás de API Gateway (§5.4.2, DO-2026-10-22-OPS P5).

Mangum traduce los eventos de API Gateway HTTP API (payload 2.0) a ASGI. La aplicación
se crea una vez por contenedor con la configuración del despliegue: el entorno nunca se
elige por la petición (RC-P10-05).
"""

import asyncio
from functools import lru_cache
from typing import Any

from mangum import Mangum

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion


def crear_manejador(configuracion: Configuracion | None = None) -> Mangum:
    return Mangum(crear_aplicacion(configuracion), lifespan="off")


@lru_cache(maxsize=1)
def _manejador() -> Mangum:
    return crear_manejador()


def _asegurar_bucle() -> None:
    """Mangum 0.19 usa `asyncio.get_event_loop()`, que en Python 3.12 falla si el hilo
    principal no tiene un bucle (por ejemplo, tras cerrarse el anterior)."""
    try:
        asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def manejar(evento: dict[str, Any], contexto: Any) -> dict[str, Any]:
    _asegurar_bucle()
    respuesta: dict[str, Any] = _manejador()(evento, contexto)
    return respuesta
