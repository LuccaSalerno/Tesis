"""Pasos de `consulta_asistida.feature`: punto de demo B (DO-2026-10-22-BDD, DO-2026-10-22-RAG).

Contra la API y PostgreSQL con pgvector real; embeddings deterministas y respuesta fija
del modelo (P1 de DO-2026-10-22-PROC). La calidad real se verifica en `tests/aws_real`.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from tests.flujo_api import Contexto
from tests.flujo_procesamiento import contrato_procesado_e_incorporado
from tests.procesamiento_fijo import EmbeddingsFijos, ModeloConsultaFijo

pytestmark = pytest.mark.integracion

scenarios("consulta_asistida.feature")


@pytest.fixture
def aplicacion(base_migrada: Configuracion) -> Iterator[Any]:
    aplicacion = crear_aplicacion(base_migrada)
    aplicacion.state.embeddings = EmbeddingsFijos()
    aplicacion.state.modelo_generativo = ModeloConsultaFijo(buscar="28/02/2027")
    yield aplicacion
    aplicacion.state.motor.dispose()


@given("el contrato sintético C-v1 procesado e incorporado a su trámite")
def contrato_incorporado(aplicacion: Any, ctx: Contexto, estado: dict[str, Any]) -> None:
    estado.update(contrato_procesado_e_incorporado(aplicacion, ctx))


@given("que el modelo indica que los fragmentos no alcanzan")
def modelo_sin_evidencia(aplicacion: Any) -> None:
    aplicacion.state.modelo_generativo = ModeloConsultaFijo(suficiente=False)


@when(parsers.parse('pregunta "{pregunta}"'))
def pregunta(ctx: Contexto, estado: dict[str, Any], pregunta: str) -> None:
    respuesta = ctx.cliente.post(
        f"/tramites/{estado['tramite']['id']}/consultas",
        json={"pregunta": pregunta},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 201
    estado["consulta"] = respuesta.json()


@then("la respuesta afirma que está vigente hasta el 28/02/2027")
def respuesta_vigencia(estado: dict[str, Any]) -> None:
    consulta = estado["consulta"]
    assert consulta["suficiente"] is True
    assert "28/02/2027" in consulta["respuesta"]


@then(parsers.parse('cita el documento "{nombre}", versión {version:d}, página {pagina:d}'))
def cita(estado: dict[str, Any], nombre: str, version: int, pagina: int) -> None:
    (afirmacion,) = estado["consulta"]["afirmaciones"]
    (referencia,) = afirmacion["referencias"]
    assert (referencia["documento_nombre"], referencia["version_numero"], referencia["pagina"]) == (
        nombre,
        version,
        pagina,
    )


@then("la respuesta informa que la evidencia es insuficiente y no afirma nada")
def abstencion(estado: dict[str, Any]) -> None:
    consulta = estado["consulta"]
    assert (consulta["suficiente"], consulta["respuesta"], consulta["afirmaciones"]) == (
        False,
        None,
        [],
    )
    assert consulta["motivo_abstencion"] == "evidencia_insuficiente"
