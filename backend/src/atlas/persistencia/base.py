"""Metadatos comunes del modelo físico (PD-04).

Todas las tablas viven en el esquema `atlas`, propiedad del usuario de
migración. Las restricciones usan una convención de nombres fija para que las
migraciones de Alembic sean deterministas.
"""

from typing import Final

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

ESQUEMA: Final = "atlas"

CONVENCION_NOMBRES: Final = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA, naming_convention=CONVENCION_NOMBRES)
