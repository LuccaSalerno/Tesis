"""Middleware ASGI de registro de solicitudes y contención de errores.

Registra método, plantilla de ruta (nunca la ruta concreta ni la consulta),
estado y duración. Los errores no controlados se responden con un 500 genérico
y se registran solo por su tipo, para que ningún valor llegue a los registros.
"""

import json
import logging
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from atlas.registro import registrar_evento

CABECERA_SOLICITUD = "x-solicitud-id"

_registrador = logging.getLogger("atlas.api")


class MiddlewareSolicitudes:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        solicitud_id = str(uuid.uuid4())
        scope.setdefault("state", {})["solicitud_id"] = solicitud_id
        inicio = time.perf_counter()
        estado_http = 500
        respuesta_iniciada = False

        async def enviar(mensaje: Message) -> None:
            nonlocal estado_http, respuesta_iniciada
            if mensaje["type"] == "http.response.start":
                respuesta_iniciada = True
                estado_http = mensaje["status"]
                mensaje.setdefault("headers", []).append(
                    (CABECERA_SOLICITUD.encode(), solicitud_id.encode())
                )
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        except Exception as error:
            registrar_evento(
                _registrador,
                "error_no_controlado",
                logging.ERROR,
                solicitud_id=solicitud_id,
                codigo_error=type(error).__name__,
            )
            if not respuesta_iniciada:
                await _responder_error_interno(enviar, solicitud_id)
        finally:
            ruta = scope.get("route")
            registrar_evento(
                _registrador,
                "solicitud_atendida",
                solicitud_id=solicitud_id,
                metodo=scope["method"],
                ruta=getattr(ruta, "path", "ruta_no_resuelta"),
                estado_http=estado_http,
                duracion_ms=round((time.perf_counter() - inicio) * 1000, 2),
            )


async def _responder_error_interno(enviar: Send, solicitud_id: str) -> None:
    cuerpo = json.dumps({"detalle": "Error interno", "solicitud_id": solicitud_id}).encode()
    await enviar(
        {
            "type": "http.response.start",
            "status": 500,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(cuerpo)).encode()),
            ],
        }
    )
    await enviar({"type": "http.response.body", "body": cuerpo})
