"""Adaptadores de Bedrock Converse y Textract.

`botocore.stub.Stubber` valida cada solicitud contra el modelo de servicio de AWS que
trae botocore y devuelve respuestas fijas: comprueba la forma de las llamadas sin
contactar AWS. No evalúa la calidad de los servicios.
"""

import re
from typing import Any

import boto3
import pytest
from botocore.stub import Stubber

from atlas.integraciones.bedrock import ModeloBedrockConverse
from atlas.integraciones.textract import AnalizadorTextract, token_solicitud
from atlas.procesamiento import esquemas
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio

PERFIL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def cliente(servicio: str) -> Any:
    return boto3.client(
        servicio,
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )


def respuesta_converse(entrada: Any, *, motivo: str = "tool_use") -> dict[str, Any]:
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "t1",
                            "name": "registrar_clasificacion",
                            "input": entrada,
                        }
                    }
                ],
            }
        },
        "stopReason": motivo,
        "usage": {"inputTokens": 1200, "outputTokens": 15, "totalTokens": 1215},
        "metrics": {"latencyMs": 300},
    }


def test_converse_con_herramienta_forzada_y_muestreo_fijo() -> None:
    bedrock = cliente("bedrock-runtime")
    herramienta = esquemas.herramienta_clasificacion()
    esperado = {
        "modelId": PERFIL,
        "system": [{"text": "INSTRUCCIONES"}],
        "messages": [{"role": "user", "content": [{"text": "<documento>...</documento>"}]}],
        "inferenceConfig": {"maxTokens": 256, "temperature": 0.0},
        "toolConfig": {
            "tools": [
                {
                    "toolSpec": {
                        "name": "registrar_clasificacion",
                        "description": herramienta["description"],
                        "inputSchema": {"json": herramienta["schema"]},
                    }
                }
            ],
            "toolChoice": {"tool": {"name": "registrar_clasificacion"}},
        },
    }
    with Stubber(bedrock) as stub:
        stub.add_response("converse", respuesta_converse({"tipo": "contrato"}), esperado)
        respuesta = ModeloBedrockConverse(bedrock, PERFIL).invocar_herramienta(
            instrucciones="INSTRUCCIONES",
            contenido="<documento>...</documento>",
            herramienta=herramienta,
            max_tokens=256,
        )
        stub.assert_no_pending_responses()
    assert respuesta.entrada == {"tipo": "contrato"}
    assert (respuesta.modelo, respuesta.tokens_entrada, respuesta.tokens_salida) == (
        PERFIL,
        1200,
        15,
    )


@pytest.mark.parametrize(
    ("configurar", "error", "codigo"),
    [
        (
            lambda s: s.add_client_error("converse", "ThrottlingException"),
            ErrorTransitorio,
            "bedrock_ThrottlingException",
        ),
        (
            lambda s: s.add_client_error("converse", "ValidationException"),
            ErrorPermanente,
            "bedrock_ValidationException",
        ),
        (
            lambda s: s.add_client_error("converse", "AccessDeniedException"),
            ErrorPermanente,
            "bedrock_AccessDeniedException",
        ),
        (
            lambda s: s.add_response("converse", respuesta_converse({}, motivo="max_tokens")),
            ErrorPermanente,
            "respuesta_truncada",
        ),
        (
            lambda s: s.add_response(
                "converse",
                {
                    "output": {
                        "message": {"role": "assistant", "content": [{"text": "No puedo."}]}
                    },
                    "stopReason": "end_turn",
                    "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                    "metrics": {"latencyMs": 1},
                },
            ),
            ErrorPermanente,
            "respuesta_sin_herramienta",
        ),
    ],
    ids=["limitacion", "validacion", "acceso", "truncada", "texto_libre"],
)
def test_errores_de_bedrock_se_clasifican_sin_contenido(
    configurar: Any, error: type[Exception], codigo: str
) -> None:
    bedrock = cliente("bedrock-runtime")
    with Stubber(bedrock) as stub:
        configurar(stub)
        with pytest.raises(error) as excepcion:
            ModeloBedrockConverse(bedrock, PERFIL).invocar_herramienta(
                instrucciones="x",
                contenido="y",
                herramienta=esquemas.herramienta_clasificacion(),
                max_tokens=256,
            )
    assert str(excepcion.value) == codigo
    # Sin la excepción original encadenada: su mensaje podría traer contenido.
    assert excepcion.value.__cause__ is None
    assert excepcion.value.__context__ is None or excepcion.value.__suppress_context__


def test_textract_con_tables_layout_y_token_estable() -> None:
    textract = cliente("textract")
    with Stubber(textract) as stub:
        stub.add_response(
            "start_document_analysis",
            {"JobId": "job-1"},
            {
                "DocumentLocation": {"S3Object": {"Bucket": "bucket", "Name": "documentos/x"}},
                "FeatureTypes": ["TABLES", "LAYOUT"],
                "ClientRequestToken": token_solicitud(7, 2, "bucket", "documentos/x"),
                "JobTag": "trabajo-7",
            },
        )
        assert AnalizadorTextract(textract, "bucket").iniciar("documentos/x", 7, 2) == "job-1"
    token = token_solicitud(7, 2, "bucket", "documentos/x")
    assert token == token_solicitud(7, 2, "bucket", "documentos/x")
    assert token != token_solicitud(7, 3, "bucket", "documentos/x")
    assert re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", token)


def test_token_distinto_entre_sesiones_con_el_mismo_trabajo() -> None:
    """Sesión E90A del 24/10: el trabajo 4 de una base nueva repetía el token de una sesión
    anterior en la misma cuenta y Textract respondía IdempotentParameterMismatchException."""
    anterior = token_solicitud(4, 1, "atlas-demo-documentos-e90-2026-10-21-5566", "documentos/4")
    actual = token_solicitud(4, 1, "atlas-demo-documentos-e90-2026-10-24-5566", "documentos/4")
    assert anterior != actual
    assert token_solicitud(4, 1, "b", "documentos/4") != token_solicitud(4, 1, "b", "documentos/5")


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        ("IN_PROGRESS", "en_curso"),
        ("SUCCEEDED", "completado"),
        ("FAILED", "fallido"),
        ("PARTIAL_SUCCESS", "fallido"),
    ],
)
def test_estado_del_analisis(estado: str, esperado: str) -> None:
    textract = cliente("textract")
    with Stubber(textract) as stub:
        stub.add_response(
            "get_document_analysis", {"JobStatus": estado}, {"JobId": "j", "MaxResults": 1}
        )
        assert AnalizadorTextract(textract, "atlas-bucket").estado("j") == esperado


def test_resultado_paginado_completo() -> None:
    textract = cliente("textract")
    bloque = {"BlockType": "PAGE", "Id": "p1", "Page": 1}
    with Stubber(textract) as stub:
        stub.add_response(
            "get_document_analysis",
            {"JobStatus": "SUCCEEDED", "Blocks": [bloque], "NextToken": "n1"},
            {"JobId": "j", "MaxResults": 1000},
        )
        stub.add_response(
            "get_document_analysis",
            {"JobStatus": "SUCCEEDED", "Blocks": [{**bloque, "Id": "p2", "Page": 2}]},
            {"JobId": "j", "MaxResults": 1000, "NextToken": "n1"},
        )
        paginas = AnalizadorTextract(textract, "atlas-bucket").resultado("j")
    assert [b["Id"] for p in paginas for b in p["Blocks"]] == ["p1", "p2"]


def test_textract_limitado_es_transitorio() -> None:
    textract = cliente("textract")
    with Stubber(textract) as stub:
        stub.add_client_error("start_document_analysis", "ProvisionedThroughputExceededException")
        with pytest.raises(
            ErrorTransitorio, match="textract_ProvisionedThroughputExceededException"
        ):
            AnalizadorTextract(textract, "atlas-bucket").iniciar("k", 1, 1)


def test_parametros_invalidos_son_fallo_permanente() -> None:
    textract = cliente("textract")
    with Stubber(textract) as stub:
        stub.add_response("start_document_analysis", {"JobId": "j"})
        with pytest.raises(ErrorPermanente, match="textract_parametros_invalidos"):
            AnalizadorTextract(textract, "b").iniciar("k", 1, 1)  # bucket demasiado corto
