"""Punto de entrada de la aplicación FastAPI.

Ejecución local: `uvicorn --factory atlas.principal:crear_aplicacion --no-access-log`.
El registro de acceso de uvicorn se desactiva porque incluye la ruta concreta y
la consulta; el middleware propio registra solo la plantilla de la ruta.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from atlas import __version__
from atlas.api import cuentas, salud
from atlas.api.middleware import MiddlewareSolicitudes
from atlas.autenticacion.verificador import VerificadorJwt
from atlas.configuracion import Configuracion, obtener_configuracion
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.registro import configurar_registro
from atlas.servicios.errores import Conflicto, ErrorDominio, NoEncontrado


def crear_aplicacion(configuracion: Configuracion | None = None) -> FastAPI:
    """Crea la aplicación con la configuración del servidor (por defecto, la del entorno).

    Falla al arrancar si la verificación de tokens no está configurada.
    """
    configuracion_efectiva = configuracion or obtener_configuracion()
    configurar_registro(configuracion_efectiva.nivel_registro)
    verificador = VerificadorJwt(
        configuracion_efectiva.cargar_jwks(),
        emisor=configuracion_efectiva.jwt_emisor or "",
        cliente=configuracion_efectiva.jwt_cliente or "",
    )

    aplicacion = FastAPI(title="ATLAS", version=__version__)
    aplicacion.state.verificador_jwt = verificador
    aplicacion.state.motor = crear_motor(configuracion_efectiva)
    aplicacion.state.fabrica_sesiones = crear_fabrica_sesiones(aplicacion.state.motor)
    aplicacion.dependency_overrides[obtener_configuracion] = lambda: configuracion_efectiva
    aplicacion.add_middleware(MiddlewareSolicitudes)
    aplicacion.add_exception_handler(HTTPException, _responder_http)
    aplicacion.add_exception_handler(ErrorDominio, _responder_dominio)
    aplicacion.include_router(salud.enrutador)
    aplicacion.include_router(cuentas.enrutador)
    return aplicacion


async def _responder_http(_: Request, error: Exception) -> JSONResponse:
    """Errores HTTP con el mismo formato que el resto de la API (RC-P01-002)."""
    if not isinstance(error, HTTPException):
        raise error
    return JSONResponse(
        {"detalle": error.detail}, status_code=error.status_code, headers=error.headers
    )


async def _responder_dominio(_: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, ErrorDominio):
        raise error
    if isinstance(error, NoEncontrado):
        codigo = 404
    elif isinstance(error, Conflicto):
        codigo = 409
    else:
        codigo = 422
    return JSONResponse({"detalle": error.detalle}, status_code=codigo)
