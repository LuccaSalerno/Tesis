"""Creación del motor y de las sesiones de base de datos."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from atlas.configuracion import Configuracion


def crear_motor(configuracion: Configuracion) -> Engine:
    return create_engine(configuracion.url_aplicacion(), pool_pre_ping=True)


def crear_fabrica_sesiones(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=motor, expire_on_commit=False)
