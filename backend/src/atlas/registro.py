"""Registro estructurado sin contenido documental (AGENTS.md §2.5, RNF-03).

Los registros solo contienen un código de evento fijo y metadatos técnicos de
una lista cerrada. Cualquier otra clave se descarta y se informa su nombre,
nunca su valor. Los mensajes de las excepciones tampoco se registran: pueden
transportar valores de la base o del documento; solo se conserva su tipo.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, Final

METADATOS_PERMITIDOS: Final = frozenset(
    {
        "solicitud_id",
        "tramite_id",
        "documento_id",
        "version_id",
        "trabajo_id",
        "tarea_id",
        "usuario_id",
        "metodo",
        "ruta",
        "estado_http",
        "duracion_ms",
        "codigo_error",
        "entorno",
        "revision",
    }
)

_CLAVE_METADATOS: Final = "atlas_metadatos"


def registrar_evento(
    registrador: logging.Logger, evento: str, nivel: int = logging.INFO, **metadatos: Any
) -> None:
    """Registra `evento` (código fijo, sin datos variables) con metadatos permitidos."""
    permitidos = {k: v for k, v in metadatos.items() if k in METADATOS_PERMITIDOS}
    descartados = sorted(k for k in metadatos if k not in METADATOS_PERMITIDOS)
    if descartados:
        permitidos["metadatos_descartados"] = descartados
    registrador.log(nivel, evento, extra={_CLAVE_METADATOS: permitidos})


class FormateadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        salida: dict[str, Any] = {
            "momento": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "nivel": record.levelname,
            "registrador": record.name,
            "evento": record.msg if isinstance(record.msg, str) else type(record.msg).__name__,
        }
        salida.update(getattr(record, _CLAVE_METADATOS, {}))
        if record.exc_info and record.exc_info[0] is not None:
            salida["tipo_excepcion"] = record.exc_info[0].__name__
        return json.dumps(salida, ensure_ascii=False, default=str)


class ManejadorSalidaEstandar(logging.Handler):
    """Escribe en el `sys.stdout` vigente al emitir (no el de su creación)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            sys.stdout.write(self.format(record) + "\n")
        except Exception:
            self.handleError(record)


def configurar_registro(nivel: str = "INFO") -> None:
    manejador = ManejadorSalidaEstandar()
    manejador.setFormatter(FormateadorJson())
    raiz = logging.getLogger()
    raiz.handlers[:] = [manejador]
    raiz.setLevel(nivel)
