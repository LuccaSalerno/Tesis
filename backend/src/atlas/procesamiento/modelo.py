"""Puerto del modelo generativo: una invocación con herramienta forzada (DO-2026-10-22-PROC).

Las instrucciones viajan separadas del contenido documental (§5.4.3). El adaptador
real usa Bedrock Converse (`atlas.integraciones.bedrock`); las pruebas de la lógica
propia usan respuestas fijas (P1).
"""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class RespuestaHerramienta:
    entrada: Any
    modelo: str
    tokens_entrada: int
    tokens_salida: int


class ModeloGenerativo(Protocol):
    identificador: str

    def invocar_herramienta(
        self, *, instrucciones: str, contenido: str, herramienta: dict[str, Any], max_tokens: int
    ) -> RespuestaHerramienta: ...
