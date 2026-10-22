"""Punto de entrada de la aplicación FastAPI.

Ejecución local: `uvicorn --factory atlas.principal:crear_aplicacion --no-access-log`.
El registro de acceso de uvicorn se desactiva porque incluye la ruta concreta y
la consulta; el middleware propio registra solo la plantilla de la ruta.
"""

from fastapi import FastAPI

from atlas import __version__
from atlas.api import salud
from atlas.api.middleware import MiddlewareSolicitudes
from atlas.configuracion import Configuracion, obtener_configuracion
from atlas.registro import configurar_registro


def crear_aplicacion(configuracion: Configuracion | None = None) -> FastAPI:
    """Crea la aplicación con la configuración del servidor (por defecto, la del entorno)."""
    configuracion_efectiva = configuracion or obtener_configuracion()
    configurar_registro(configuracion_efectiva.nivel_registro)
    aplicacion = FastAPI(title="ATLAS", version=__version__)
    aplicacion.dependency_overrides[obtener_configuracion] = lambda: configuracion_efectiva
    aplicacion.add_middleware(MiddlewareSolicitudes)
    aplicacion.include_router(salud.enrutador)
    return aplicacion
