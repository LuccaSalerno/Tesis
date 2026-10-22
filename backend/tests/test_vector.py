"""Tipo `vector` de pgvector sin dependencias adicionales (DO-2026-10-22-RAG)."""

import pytest
from sqlalchemy import Engine, text

from atlas.persistencia.vector import Vector, a_texto


def test_dt_rag_especificacion_de_columna() -> None:
    assert Vector(1024).get_col_spec() == "vector(1024)"
    assert Vector().get_col_spec() == "vector"


def test_dt_rag_conversion_de_ida_y_vuelta() -> None:
    tipo = Vector(3)
    enviar = tipo.bind_processor(None)
    leer = tipo.result_processor(None, None)
    assert enviar(None) is None and leer(None) is None
    assert enviar([0.5, 1, -2.25]) == "[0.5,1.0,-2.25]" == a_texto([0.5, 1, -2.25])
    assert leer("[0.5,1,-2.25]") == [0.5, 1.0, -2.25]


@pytest.mark.integracion
def test_dt_rag_lectura_desde_postgresql(motor_aplicacion: Engine) -> None:
    consulta = text("SELECT '[0.25,0.5,1]'::vector AS v").columns(v=Vector(3))
    with motor_aplicacion.connect() as conexion:
        valor = conexion.execute(consulta).scalar_one()
    assert valor == [0.25, 0.5, 1.0]
