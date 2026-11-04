"""Fixture y paso comunes de los escenarios BDD (DO-2026-10-22-BDD)."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given
from sqlalchemy import Engine

from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto


@pytest.fixture
def estado() -> dict[str, Any]:
    """Lo que un paso deja a los siguientes dentro del mismo escenario."""
    return {}


@given("un responsable del trámite autenticado", target_fixture="ctx")
def responsable_autenticado(aplicacion: Any, motor_aplicacion: Engine) -> Iterator[Contexto]:
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
