"""Configuración del servidor (separación de entornos por configuración)."""

import pytest
from pydantic import ValidationError

from atlas.configuracion import ErrorConfiguracion
from tests.conftest import configuracion_sin_base


def test_entorno_desconocido_rechazado() -> None:
    with pytest.raises(ValidationError):
        configuracion_sin_base(entorno="produccion")


def test_url_usa_psycopg_y_oculta_la_clave() -> None:
    configuracion = configuracion_sin_base(bd_clave="clave-secreta-local")
    url = configuracion.url_aplicacion()
    assert url.drivername == "postgresql+psycopg"
    assert url.username == "nadie"
    assert "clave-secreta-local" not in str(url)
    assert "clave-secreta-local" not in repr(configuracion)


def test_migracion_exige_usuario_de_migracion() -> None:
    with pytest.raises(ErrorConfiguracion):
        configuracion_sin_base().url_migracion()


def test_url_migracion_usa_su_propio_usuario() -> None:
    configuracion = configuracion_sin_base(bd_usuario_migracion="propietario")
    assert configuracion.url_migracion().username == "propietario"
