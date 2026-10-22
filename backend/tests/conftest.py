"""Fixtures comunes. Las pruebas de integración usan PostgreSQL + pgvector real.

Solo se aceptan bases de prueba: ATLAS_ENTORNO=tests y nombre terminado en
`_tests`, para que una configuración equivocada nunca migre ni modifique la
base de desarrollo o de demo (RC-P10, regla 8 de AGENTS.md).
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import NullPool

from atlas.configuracion import Configuracion, ErrorConfiguracion

RAIZ_BACKEND = Path(__file__).resolve().parents[1]


def configuracion_sin_base(**campos: Any) -> Configuracion:
    """Configuración para pruebas unitarias que no tocan la base.

    Todos los campos se fijan explícitamente para que las variables ATLAS_* del
    proceso (por ejemplo, las de la CI) no alteren el resultado.
    """
    valores: dict[str, Any] = {
        "entorno": "tests",
        "nivel_registro": "INFO",
        "bd_host": "localhost",
        "bd_puerto": 5432,
        "bd_nombre": "sin_base",
        "bd_usuario": "nadie",
        "bd_clave": None,
        "bd_usuario_migracion": None,
        "bd_clave_migracion": None,
    }
    valores.update(campos)
    return Configuracion(_env_file=None, **valores)


def cargar_configuracion_tests() -> Configuracion:
    configuracion = Configuracion(_env_file=RAIZ_BACKEND / ".env.tests")  # type: ignore[call-arg]
    if configuracion.entorno != "tests" or not configuracion.bd_nombre.endswith("_tests"):
        raise ErrorConfiguracion(
            "Las pruebas de integración solo corren con ATLAS_ENTORNO=tests sobre una base *_tests"
        )
    return configuracion


def configuracion_alembic(configuracion: Configuracion) -> Config:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.attributes["configuracion"] = configuracion
    return config


def lineas_registro(salida: str) -> list[dict[str, Any]]:
    return [json.loads(linea) for linea in salida.splitlines() if linea.startswith("{")]


@pytest.fixture(scope="session")
def configuracion_tests() -> Configuracion:
    return cargar_configuracion_tests()


@pytest.fixture(scope="session")
def motor_migracion(configuracion_tests: Configuracion) -> Iterator[Engine]:
    motor = create_engine(configuracion_tests.url_migracion(), poolclass=NullPool)
    yield motor
    motor.dispose()


@pytest.fixture(scope="session")
def motor_aplicacion(configuracion_tests: Configuracion) -> Iterator[Engine]:
    motor = create_engine(configuracion_tests.url_aplicacion(), poolclass=NullPool)
    yield motor
    motor.dispose()
