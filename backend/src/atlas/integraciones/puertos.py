"""Puertos que usa el dominio. Ningún método recibe ni devuelve contenido documental
hacia los registros: solo claves, tamaños e identificadores."""

from dataclasses import dataclass
from datetime import datetime
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

    def url_lectura(self, clave: str, vigencia_s: int, nombre: str) -> str:
        """URL prefirmada de GET para consultar el original (HU-04, DO-2026-10-22-WEB F4)."""
        ...

    def metadatos(self, clave: str) -> MetadatosObjeto | None:
        """None si el objeto no existe."""
        ...

    def leer(self, clave: str) -> bytes: ...

    def escribir(self, clave: str, datos: bytes, tipo_contenido: str) -> None: ...

    def eliminar_prefijo(self, prefijo: str) -> int:
        """Elimina todas las versiones de todos los objetos bajo `prefijo`. Idempotente."""
        ...

    def copiar(self, origen: str, destino: str) -> None:
        """Copia del lado del servidor, sin que el contenido pase por la aplicación."""
        ...

    def eliminar_definitivamente(self, clave: str) -> int:
        """Elimina todas las versiones y marcadores de eliminación de `clave`.

        Idempotente: devuelve cuántas versiones eliminó (0 si no quedaba nada).
        """
        ...

    def abortar_multipartes(self, prefijo: str, iniciadas_antes: datetime) -> int:
        """Aborta las cargas multiparte incompletas del prefijo iniciadas antes del instante."""
        ...


class OrquestadorProcesamiento(Protocol):
    def iniciar(self, trabajo_id: int, intento: int) -> None:
        """Inicia la ejecución del intento; idempotente para el mismo trabajo e intento."""
        ...


class GestorIdentidades(Protocol):
    def suprimir(self, identificador_externo: str) -> None:
        """Elimina la cuenta del proveedor de identidad (RF-25, §5.4.3); idempotente: si ya
        no existe, no es un error."""
        ...
