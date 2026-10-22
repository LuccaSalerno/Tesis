"""Modo mantenimiento por entorno, independiente de PostgreSQL (RC-P10-09, DO-2026-10-22-OPS P2).

El estado vive en un objeto de control de S3 del propio entorno. Solo el operador lo
modifica; la aplicación solo lo lee. Si no puede leerse o no es válido, se deniega:

- `active`: operaciones según los permisos del dominio.
- `draining`: solo consultas; lo que modifica responde 503 (no hay URLs ni cargas nuevas).
- `offline`: todo responde 503 salvo `/salud`.
"""

import json
import logging
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any, Final

from starlette.types import ASGIApp, Receive, Scope, Send

from atlas.registro import registrar_evento

CLAVE_CONTROL: Final = "control/mantenimiento.json"
RUTAS_SIEMPRE_DISPONIBLES: Final = frozenset({"/salud"})
METODOS_DE_CONSULTA: Final = frozenset({"GET", "HEAD", "OPTIONS"})

_registrador = logging.getLogger("atlas.mantenimiento")


class EstadoOperativo(StrEnum):
    ACTIVE = "active"
    DRAINING = "draining"
    OFFLINE = "offline"


class LectorMantenimiento:
    """Lee el estado con una caché breve. `None`: no se pudo determinar (se deniega)."""

    def __init__(
        self,
        leer: Callable[[], bytes] | None,
        *,
        cache_s: float = 15.0,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._leer = leer
        self._cache_s = cache_s
        self._reloj = reloj
        self._valor: EstadoOperativo | None = None
        self._leido_en: float | None = None

    @classmethod
    def fijo_active(cls) -> "LectorMantenimiento":
        """Fuera de AWS (desarrollo y CI): siempre `active`."""
        return cls(None)

    @classmethod
    def desde_s3(cls, cliente_s3: Any, bucket: str, cache_s: float) -> "LectorMantenimiento":
        def leer() -> bytes:
            cuerpo: bytes = cliente_s3.get_object(Bucket=bucket, Key=CLAVE_CONTROL)["Body"].read()
            return cuerpo

        return cls(leer, cache_s=cache_s)

    def estado(self) -> EstadoOperativo | None:
        if self._leer is None:
            return EstadoOperativo.ACTIVE
        ahora = self._reloj()
        if self._leido_en is not None and ahora - self._leido_en < self._cache_s:
            return self._valor
        try:
            datos = json.loads(self._leer())
            self._valor = EstadoOperativo(datos["estado"])
        except Exception as error:  # objeto ausente, ilegible o inválido: se deniega
            registrar_evento(
                _registrador,
                "mantenimiento_ilegible",
                logging.WARNING,
                codigo_error=type(error).__name__,
            )
            self._valor = None
        self._leido_en = ahora
        return self._valor


def admite(estado: EstadoOperativo | None, metodo: str, ruta: str) -> bool:
    if ruta in RUTAS_SIEMPRE_DISPONIBLES or estado == EstadoOperativo.ACTIVE:
        return True
    return estado == EstadoOperativo.DRAINING and metodo in METODOS_DE_CONSULTA


class MiddlewareMantenimiento:
    def __init__(self, app: ASGIApp, lector: LectorMantenimiento, reintentar_s: int) -> None:
        self.app = app
        self.lector = lector
        self.reintentar_s = reintentar_s

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or admite(self.lector.estado(), scope["method"], scope["path"]):
            await self.app(scope, receive, send)
            return
        cuerpo = json.dumps(
            {"detalle": "ATLAS está en mantenimiento. Reintentá más tarde."}
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(cuerpo)).encode()),
                    (b"retry-after", str(self.reintentar_s).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": cuerpo})
