"""Arranque en frío del contenedor de Lambda (IA-M08).

El manejador de Lambda marca cada invocación; la primera de un contenedor es un arranque
en frío. Fuera de Lambda (uvicorn, pruebas) nunca se marca y el estado es «desconocido».
Solo es un metadato técnico para separar la latencia de inicialización: no se excluye
ninguna observación por esta marca.
"""

from typing import Literal

Arranque = Literal["frio", "caliente", "desconocido"]

_invocaciones = 0


def marcar_invocacion() -> None:
    global _invocaciones
    _invocaciones += 1


def estado() -> Arranque:
    if _invocaciones == 0:
        return "desconocido"
    return "frio" if _invocaciones == 1 else "caliente"
