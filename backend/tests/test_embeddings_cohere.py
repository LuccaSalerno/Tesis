"""Adaptador de Cohere Embed Multilingual v3 en Bedrock.

Stubber valida cada `InvokeModel` contra el modelo de servicio; no contacta AWS.
"""

import io
import json
from typing import Any

import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from atlas.integraciones.bedrock import EmbeddingsCohereBedrock
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from tests.test_integraciones_errores import ClienteS3Sustituto
from tests.test_procesamiento_adaptadores import cliente

MODELO = "cohere.embed-multilingual-v3"


def cuerpo(vectores: list[list[float]]) -> StreamingBody:
    datos = json.dumps(
        {"id": "x", "embeddings": vectores, "response_type": "embeddings_floats"}
    ).encode()
    return StreamingBody(io.BytesIO(datos), len(datos))


def esperado(textos: list[str], tipo: str) -> dict[str, Any]:
    return {
        "modelId": MODELO,
        "body": json.dumps({"texts": textos, "input_type": tipo, "truncate": "NONE"}),
        "contentType": "application/json",
        "accept": "application/json",
    }


def test_documentos_y_consultas_con_su_tipo_y_sin_truncado() -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        stub.add_response(
            "invoke_model",
            {"body": cuerpo([[0.1] * 1024] * 2), "contentType": "application/json"},
            esperado(["a", "b"], "search_document"),
        )
        stub.add_response(
            "invoke_model",
            {"body": cuerpo([[0.2] * 1024]), "contentType": "application/json"},
            esperado(["¿hasta cuándo?"], "search_query"),
        )
        modelo = EmbeddingsCohereBedrock(bedrock, MODELO)
        documentos = modelo.embeber(["a", "b"], "search_document")
        consulta = modelo.embeber(["¿hasta cuándo?"], "search_query")
        stub.assert_no_pending_responses()
    assert [len(v) for v in documentos] == [1024, 1024]
    assert consulta[0][0] == pytest.approx(0.2)


def test_lotes_de_hasta_96_textos() -> None:
    bedrock = cliente("bedrock-runtime")
    textos = [f"t{i}" for i in range(100)]
    with Stubber(bedrock) as stub:
        stub.add_response(
            "invoke_model",
            {"body": cuerpo([[0.0] * 1024] * 96), "contentType": "application/json"},
            esperado(textos[:96], "search_document"),
        )
        stub.add_response(
            "invoke_model",
            {"body": cuerpo([[0.0] * 1024] * 4), "contentType": "application/json"},
            esperado(textos[96:], "search_document"),
        )
        assert (
            len(EmbeddingsCohereBedrock(bedrock, MODELO).embeber(textos, "search_document")) == 100
        )


@pytest.mark.parametrize(
    ("vectores", "codigo"),
    [([[0.1] * 512], "embeddings_respuesta_invalida"), ([], "embeddings_respuesta_invalida")],
    ids=["dimensiones", "cantidad"],
)
def test_respuesta_fuera_de_contrato(vectores: list[list[float]], codigo: str) -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        stub.add_response(
            "invoke_model", {"body": cuerpo(vectores), "contentType": "application/json"}
        )
        with pytest.raises(ErrorPermanente, match=codigo):
            EmbeddingsCohereBedrock(bedrock, MODELO).embeber(["a"], "search_document")


def test_cuerpo_no_json() -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        stub.add_response(
            "invoke_model",
            {"body": StreamingBody(io.BytesIO(b"no"), 2), "contentType": "text/plain"},
        )
        with pytest.raises(ErrorPermanente, match="embeddings_respuesta_invalida"):
            EmbeddingsCohereBedrock(bedrock, MODELO).embeber(["a"], "search_document")


@pytest.mark.parametrize(
    ("excepcion", "error", "codigo"),
    [
        ("ThrottlingException", ErrorTransitorio, "embeddings_ThrottlingException"),
        ("ValidationException", ErrorPermanente, "embeddings_ValidationException"),
    ],
)
def test_errores_de_cohere(excepcion: str, error: type[Exception], codigo: str) -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        stub.add_client_error("invoke_model", excepcion)
        with pytest.raises(error, match=codigo):
            EmbeddingsCohereBedrock(bedrock, MODELO).embeber(["a"], "search_document")


def test_errores_locales_de_cohere() -> None:
    from botocore.exceptions import EndpointConnectionError, ParamValidationError

    for excepcion, error, codigo in (
        (
            EndpointConnectionError(endpoint_url="https://bedrock"),
            ErrorTransitorio,
            "embeddings_conexion",
        ),
        (ParamValidationError(report="x"), ErrorPermanente, "embeddings_parametros_invalidos"),
    ):
        modelo = EmbeddingsCohereBedrock(ClienteS3Sustituto(invoke_model=excepcion), MODELO)
        with pytest.raises(error, match=codigo):
            modelo.embeber(["a"], "search_document")
