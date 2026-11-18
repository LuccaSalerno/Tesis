"""Punto de entrada de la aplicación FastAPI.

Ejecución local: `uvicorn --factory atlas.principal:crear_aplicacion --no-access-log`.
El registro de acceso de uvicorn se desactiva porque incluye la ruta concreta y
la consulta; el middleware propio registra solo la plantilla de la ruta.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from atlas import __version__
from atlas.api import administracion, consultas, cuentas, revision, salud, tramites, vinculos
from atlas.api.middleware import MiddlewareSolicitudes, MiddlewareVerificacionPrevia
from atlas.autenticacion.verificador import VerificadorJwt
from atlas.configuracion import Configuracion, ErrorConfiguracion, obtener_configuracion
from atlas.dominio.validacion_archivo import ArchivoRechazado, LimitesCarga
from atlas.integraciones.aws import AlmacenS3, OrquestadorStepFunctions, crear_cliente
from atlas.integraciones.bedrock import EmbeddingsCohereBedrock, ModeloBedrockConverse
from atlas.integraciones.identidades import GestorIdentidadesLambda, GestorIdentidadesLocal
from atlas.integraciones.puertos import ErrorIntegracion, GestorIdentidades
from atlas.operacion.mantenimiento import LectorMantenimiento, MiddlewareMantenimiento
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.procesamiento.errores import ErrorEtapa
from atlas.registro import configurar_registro
from atlas.servicios.errores import Conflicto, ErrorDominio, NoEncontrado, NoPermitido


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
    configuracion_efectiva.validar_servicios_aws()
    aplicacion.state.almacen = AlmacenS3(
        crear_cliente(configuracion_efectiva, "s3"),
        configuracion_efectiva.s3_bucket_documentos or "",
    )
    aplicacion.state.orquestador = OrquestadorStepFunctions(
        crear_cliente(configuracion_efectiva, "stepfunctions"),
        configuracion_efectiva.sfn_maquina_procesamiento_arn or "",
    )
    aplicacion.state.gestor_identidades = _gestor_identidades(configuracion_efectiva)
    aplicacion.state.limites_carga = LimitesCarga(
        tamano_maximo_bytes=configuracion_efectiva.carga_tamano_maximo_bytes,
        paginas_maximas_pdf=configuracion_efectiva.carga_paginas_maximas_pdf,
        caracteres_maximos_docx=configuracion_efectiva.carga_caracteres_maximos_docx,
    )
    aplicacion.state.vigencia_url_carga_s = configuracion_efectiva.carga_vigencia_url_s
    aplicacion.state.vigencia_carga_pendiente_s = configuracion_efectiva.carga_vigencia_pendiente_s
    aplicacion.state.limite_concurrencia = configuracion_efectiva.procesamiento_limite_concurrencia
    bedrock = crear_cliente(configuracion_efectiva, "bedrock-runtime")
    aplicacion.state.embeddings = EmbeddingsCohereBedrock(
        bedrock, configuracion_efectiva.bedrock_modelo_embeddings
    )
    aplicacion.state.modelo_generativo = ModeloBedrockConverse(
        bedrock, configuracion_efectiva.bedrock_perfil_generativo
    )
    aplicacion.state.consulta_fragmentos_recuperados = (
        configuracion_efectiva.consulta_fragmentos_recuperados
    )
    aplicacion.state.consulta_max_tokens = configuracion_efectiva.consulta_max_tokens
    aplicacion.state.motor = crear_motor(configuracion_efectiva)
    aplicacion.state.fabrica_sesiones = crear_fabrica_sesiones(aplicacion.state.motor)
    aplicacion.dependency_overrides[obtener_configuracion] = lambda: configuracion_efectiva
    # El mantenimiento se evalúa antes de cualquier operación; el registro de
    # solicitudes queda por fuera para correlacionar también las respuestas 503.
    aplicacion.state.mantenimiento = (
        LectorMantenimiento.desde_s3(
            crear_cliente(configuracion_efectiva, "s3"),
            configuracion_efectiva.s3_bucket_documentos or "",
            configuracion_efectiva.mantenimiento_cache_s,
        )
        if configuracion_efectiva.mantenimiento_fuente == "s3"
        else LectorMantenimiento.fijo_active()
    )
    aplicacion.add_middleware(
        MiddlewareMantenimiento,
        lector=aplicacion.state.mantenimiento,
        reintentar_s=configuracion_efectiva.mantenimiento_reintentar_s,
    )
    aplicacion.add_middleware(MiddlewareVerificacionPrevia)
    aplicacion.add_middleware(MiddlewareSolicitudes)
    aplicacion.add_exception_handler(HTTPException, _responder_http)
    aplicacion.add_exception_handler(ErrorDominio, _responder_dominio)
    aplicacion.add_exception_handler(ArchivoRechazado, tramites.responder_archivo_rechazado)
    aplicacion.add_exception_handler(ErrorIntegracion, _responder_integracion)
    aplicacion.add_exception_handler(ErrorEtapa, _responder_integracion)
    _incluir_rutas(aplicacion)
    return aplicacion


def _gestor_identidades(configuracion: Configuracion) -> GestorIdentidades:
    """RF-25: en demo la supresión elimina la cuenta de Cognito por la Lambda `cuentas`."""
    if configuracion.cuentas_funcion:
        return GestorIdentidadesLambda(
            crear_cliente(configuracion, "lambda"), configuracion.cuentas_funcion
        )
    if configuracion.entorno == "demo":
        raise ErrorConfiguracion("En demo falta ATLAS_CUENTAS_FUNCION (supresión, RF-25)")
    return GestorIdentidadesLocal()


def _incluir_rutas(aplicacion: FastAPI) -> None:
    for modulo in (salud, cuentas, tramites, consultas, vinculos, revision, administracion):
        aplicacion.include_router(modulo.enrutador)


def esquema_openapi() -> dict[str, Any]:
    """Contrato OpenAPI de la API, sin configuración ni servicios: lo usa la aplicación web
    para generar sus tipos."""
    aplicacion = FastAPI(title="ATLAS", version=__version__)
    _incluir_rutas(aplicacion)
    return aplicacion.openapi()


async def _responder_http(_: Request, error: Exception) -> JSONResponse:
    """Errores HTTP con el mismo formato que el resto de la API."""
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
    elif isinstance(error, NoPermitido):
        codigo = 403
    elif isinstance(error, Conflicto):
        codigo = 409
    else:
        codigo = 422
    return JSONResponse({"detalle": error.detalle}, status_code=codigo)


async def _responder_integracion(_: Request, error: Exception) -> JSONResponse:
    """Un servicio externo falló antes de producir efectos: se puede reintentar."""
    if not isinstance(error, ErrorIntegracion | ErrorEtapa):
        raise error
    return JSONResponse(
        {"detalle": "Servicio no disponible momentáneamente. Reintentá en unos minutos."},
        status_code=503,
    )
