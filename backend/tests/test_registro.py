"""Los registros no contienen contenido documental (AGENTS.md §2.5, RNF-03)."""

import logging
import sys

import pytest

from atlas.registro import FormateadorJson, configurar_registro, registrar_evento
from tests.conftest import lineas_registro

VALOR_DOCUMENTAL = "CUIT 30-71234567-8 importe 10500"


def test_rnf_03_metadatos_fuera_de_lista_se_descartan_sin_su_valor(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configurar_registro()
    registrar_evento(
        logging.getLogger("prueba"), "campo_validado", tramite_id="T-1", valor=VALOR_DOCUMENTAL
    )
    (linea,) = lineas_registro(capsys.readouterr().out)
    assert linea["evento"] == "campo_validado"
    assert linea["tramite_id"] == "T-1"
    assert linea["metadatos_descartados"] == ["valor"]
    assert VALOR_DOCUMENTAL not in str(linea)


def test_rnf_03_mensaje_de_excepcion_no_se_registra() -> None:
    registrador = logging.getLogger("prueba")
    try:
        raise ValueError(VALOR_DOCUMENTAL)
    except ValueError:
        registro = registrador.makeRecord(
            "prueba", logging.ERROR, __file__, 1, "fallo_extraccion", None, sys.exc_info()
        )
    salida = FormateadorJson().format(registro)
    assert "ValueError" in salida
    assert VALOR_DOCUMENTAL not in salida


def test_rnf_03_argumentos_de_bibliotecas_no_se_interpolan() -> None:
    registro = logging.LogRecord(
        "biblioteca", logging.INFO, __file__, 1, "parametros %s", (VALOR_DOCUMENTAL,), None
    )
    salida = FormateadorJson().format(registro)
    assert "parametros %s" in salida
    assert VALOR_DOCUMENTAL not in salida
