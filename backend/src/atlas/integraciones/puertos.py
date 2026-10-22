"""Puertos que usa el dominio. Ningún método recibe ni devuelve contenido documental
hacia los registros: solo claves, tamaños e identificadores."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MetadatosObjeto:
    tamano_bytes: int


class ErrorIntegracion(Exception):
    """Falla de un servicio externo. `codigo` es técnico y apto para registros."""

    def __init__(self, codigo: str) -> None:
        super().__init__(codigo)
        self.codigo = codigo


class AlmacenDocumental(Protocol):
    def url_carga(self, clave: str, tipo_contenido: str, vigencia_s: int) -> str:
        """URL prefirmada de PUT para que el navegador transfiera el archivo directamente."""
        ...

    def metadatos(self, clave: str) -> MetadatosObjeto | None:
        """None si el objeto no existe."""
        ...

    def leer(self, clave: str) -> bytes: ...


class OrquestadorProcesamiento(Protocol):
    def iniciar(self, trabajo_id: int, intento: int) -> None:
        """Inicia la ejecución del intento; idempotente para el mismo trabajo e intento."""
        ...
