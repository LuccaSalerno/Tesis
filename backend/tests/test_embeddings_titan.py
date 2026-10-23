"""Adaptador de Titan Text Embeddings V2 (RC-P07.3, DO-2026-10-23-E90-MEDICION P12).

Stubber valida cada `InvokeModel` contra el modelo de servicio; no contacta AWS.
"""

import io
import json

import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from atlas.integraciones.bedrock import EmbeddingsTitanBedrock
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from tests.test_procesamiento_adaptadores import cliente

MODELO = "amazon.titan-embed-text-v2:0"


def cuerpo(vector: list[float]) -> StreamingBody:
    datos = json.dumps({"embedding": vector, "inputTextTokenCount": 3}).encode()
    return StreamingBody(io.BytesIO(datos), len(datos))


def esperado(texto: str) -> dict[str, str]:
    return {
        "modelId": MODELO,
        "body": json.dumps({"inputText": texto, "dimensions": 1024, "normalize": True}),
        "contentType": "application/json",
        "accept": "application/json",
    }


def test_rc_p07_3_titan_un_texto_por_llamada_1024_y_normalizado() -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        for texto, valor in (("a", 0.1), ("b", 0.2)):
            stub.add_response(
                "invoke_model",
                {"body": cuerpo([valor] * 1024), "contentType": "application/json"},
                esperado(texto),
            )
        vectores = EmbeddingsTitanBedrock(bedrock, MODELO).embeber(["a", "b"], "search_query")
        stub.assert_no_pending_responses()
    assert [len(v) for v in vectores] == [1024, 1024]
    assert vectores[1][0] == pytest.approx(0.2)


def test_rc_p07_3_titan_rechaza_dimensiones_distintas() -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        stub.add_response(
            "invoke_model",
            {"body": cuerpo([0.1] * 256), "contentType": "application/json"},
            esperado("a"),
        )
        with pytest.raises(ErrorPermanente, match="embeddings_respuesta_invalida"):
            EmbeddingsTitanBedrock(bedrock, MODELO).embeber(["a"], "search_document")


@pytest.mark.parametrize(
    ("excepcion", "error"),
    [("ThrottlingException", ErrorTransitorio), ("AccessDeniedException", ErrorPermanente)],
)
def test_rc_p08_errores_de_titan(excepcion: str, error: type[Exception]) -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        stub.add_client_error("invoke_model", excepcion)
        with pytest.raises(error, match=f"embeddings_{excepcion}"):
            EmbeddingsTitanBedrock(bedrock, MODELO).embeber(["a"], "search_document")
