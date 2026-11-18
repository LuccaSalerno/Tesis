"""Resultados brutos de una campaña: un JSON por línea, solo agregados.

Cada llamada medida queda registrada con su salida estructurada, tokens, duración, errores
e intentos. Una campaña interrumpida se retoma salteando lo ya registrado: no se repiten
llamadas selectivamente.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class Registro:
    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta

    def leer(self) -> list[dict[str, Any]]:
        if not self.ruta.is_file():
            return []
        return [json.loads(linea) for linea in self.ruta.read_text("utf-8").splitlines() if linea]

    def claves(self, campos: Iterable[str]) -> set[tuple[Any, ...]]:
        nombres = tuple(campos)
        return {tuple(fila.get(n) for n in nombres) for fila in self.leer()}

    def escribir(self, fila: dict[str, Any]) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self.ruta.open("a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(fila, ensure_ascii=False, sort_keys=True) + "\n")
