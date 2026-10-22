"""Escenarios EVD-01 de `cadena_evidencia.feature` (DO-2026-10-22-BDD).

Se recolectan para que el contrato sea visible en cada ejecución, pero se
**omiten con motivo explícito**: verifican ciclos de revisión, tareas y
decisiones, que todavía no existen (hito 1.8). pytest los informa como
omitidos, nunca como aprobados; ningún criterio EVD-01 se da por cumplido.
"""

import pytest
from pytest_bdd import given, scenarios

scenarios("cadena_evidencia.feature")

PENDIENTE = (
    "EVD-01 pendiente: requiere ciclos de revisión, tareas y decisiones (hito 1.8); "
    "no acredita cumplimiento"
)


@given("un trámite con un conjunto documental validado y un primer ciclo aprobado")
@given("un primer ciclo con una observación motivada")
@given("un ciclo observado con el documento vigente identificado")
@given("un ciclo de revisión con una tarea pendiente")
def capacidad_pendiente() -> None:
    pytest.skip(PENDIENTE)
