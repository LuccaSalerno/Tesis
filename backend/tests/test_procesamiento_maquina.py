"""Definición de la máquina de estados (§5.3.1)."""

import json
from importlib import resources
from typing import Any

import pytest

from atlas.procesamiento.lambdas import CLAVES_EVENTO, ETAPAS_PERSISTENCIA, ETAPAS_PROCESAMIENTO

DEFINICION: dict[str, Any] = json.loads(
    (resources.files("atlas.procesamiento") / "maquina_estados.asl.json").read_text("utf-8")
)
ESTADOS: dict[str, Any] = DEFINICION["States"]
TAREAS = {n: e for n, e in ESTADOS.items() if e["Type"] == "Task"}
REFERENCIAS_PERMITIDAS = {
    "formato",
    "clave_objeto",
    "job_id",
    "estado",
    "contenido",
    "clasificacion",
    "extraccion",
    "fragmentos",
}


def test_limites_de_tiempo() -> None:
    assert 1800 <= DEFINICION["TimeoutSeconds"] <= 2400
    espera = ESTADOS["EsperarTextract"]["Seconds"]
    assert 10 <= espera <= 15
    limite = next(
        c["NumericGreaterThanEquals"]
        for c in ESTADOS["EvaluarTextract"]["Choices"]
        if "NumericGreaterThanEquals" in c
    )
    assert limite * espera <= 30 * 60


@pytest.mark.parametrize("nombre", sorted(TAREAS))
def test_reintentos_solo_ante_errores_transitorios(nombre: str) -> None:
    (reintento,) = TAREAS[nombre]["Retry"]
    assert (reintento["MaxAttempts"], reintento["IntervalSeconds"], reintento["BackoffRate"]) == (
        3,
        2,
        2.0,
    )
    assert reintento["JitterStrategy"] == "FULL"
    assert "ErrorTransitorio" in reintento["ErrorEquals"]
    assert not {"ErrorPermanente", "States.ALL"} & set(reintento["ErrorEquals"])


@pytest.mark.parametrize("nombre", sorted(set(TAREAS) - {"RegistrarFallo"}))
def test_toda_falla_registra_el_fallo_tecnico(nombre: str) -> None:
    (captura,) = TAREAS[nombre]["Catch"]
    assert captura == {
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "RegistrarFallo",
    }


@pytest.mark.parametrize("nombre", sorted(TAREAS))
def test_rnf_09_entradas_y_salidas_solo_con_identificadores(nombre: str) -> None:
    tarea = TAREAS[nombre]
    carga = tarea["Parameters"]["Payload"]
    assert {k.removesuffix(".$") for k in carga} <= CLAVES_EVENTO
    for clave, valor in carga.items():
        if clave.endswith(".$"):
            assert valor.startswith("$.") and not valor.startswith("$.Payload")
    for clave, valor in tarea.get("ResultSelector", {}).items():
        assert clave.removesuffix(".$") in REFERENCIAS_PERMITIDAS
        assert valor == f"$.Payload.{clave.removesuffix('.$')}"
    if "ResultSelector" not in tarea:
        assert tarea["ResultPath"] is None  # el resultado no se incorpora al estado


@pytest.mark.parametrize("nombre", sorted(TAREAS))
def test_cada_etapa_existe_en_su_funcion(nombre: str) -> None:
    parametros = TAREAS[nombre]["Parameters"]
    etapa = parametros["Payload"]["etapa"]
    funcion = parametros["FunctionName"]
    if funcion == "${ArnLambdaPersistencia}":
        assert etapa in ETAPAS_PERSISTENCIA
    else:
        assert funcion == "${ArnLambdaProcesamiento}"
        assert etapa in ETAPAS_PROCESAMIENTO


def test_textract_fallido_o_incompleto_es_fallo_tecnico() -> None:
    destinos = {c.get("StringEquals"): c["Next"] for c in ESTADOS["EvaluarTextract"]["Choices"]}
    assert destinos["completado"] == "NormalizarTextract"
    assert destinos["fallido"] == "TextractFallido"
    assert ESTADOS["TextractFallido"]["Next"] == "RegistrarFallo"
    assert ESTADOS["ElegirLectura"]["Default"] == "NormalizarDocx"


def test_definicion_aceptada_por_step_functions_simulado(moto_local: str) -> None:
    from atlas.integraciones.aws import crear_cliente
    from tests.conftest import configuracion_sin_base

    texto = (
        json.dumps(DEFINICION)
        .replace(
            "${ArnLambdaProcesamiento}",
            "arn:aws:lambda:us-east-1:123456789012:function:procesamiento",
        )
        .replace(
            "${ArnLambdaPersistencia}",
            "arn:aws:lambda:us-east-1:123456789012:function:persistencia",
        )
    )
    sfn = crear_cliente(configuracion_sin_base(aws_endpoint_url=moto_local), "stepfunctions")
    respuesta = sfn.create_state_machine(
        name="atlas-procesamiento-definicion",
        definition=texto,
        roleArn="arn:aws:iam::123456789012:role/atlas-procesamiento",
    )
    assert respuesta["stateMachineArn"].endswith("atlas-procesamiento-definicion")
