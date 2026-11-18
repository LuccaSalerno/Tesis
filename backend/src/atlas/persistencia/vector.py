"""Tipo `vector` de pgvector para SQLAlchemy, sin dependencias adicionales.

Se envía y se lee con la representación de texto de pgvector (`[0.1,0.2,...]`). La
búsqueda por distancia se hace con SQL explícito (`<=>`, coseno, búsqueda
exacta).
"""

from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy.dialects.postgresql.base import ischema_names
from sqlalchemy.types import UserDefinedType


def a_texto(valores: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(v)) for v in valores) + "]"


class Vector(UserDefinedType[list[float]]):
    cache_ok = True

    def __init__(self, dimensiones: int | None = None) -> None:
        self.dimensiones = dimensiones

    def get_col_spec(self, **_: Any) -> str:
        return "vector" if self.dimensiones is None else f"vector({self.dimensiones})"

    def bind_processor(self, dialect: Any) -> Callable[[Sequence[float] | None], str | None]:
        def procesar(valor: Sequence[float] | None) -> str | None:
            return None if valor is None else a_texto(valor)

        return procesar

    def result_processor(self, dialect: Any, coltype: Any) -> Callable[[Any], list[float] | None]:
        def procesar(valor: Any) -> list[float] | None:
            if valor is None:
                return None
            return [float(v) for v in str(valor).strip("[]").split(",") if v]

        return procesar


# Para que la reflexión de la base reconozca el tipo (comparación modelo-migración).
ischema_names["vector"] = Vector
