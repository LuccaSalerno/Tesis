"""Adaptador de Amazon Bedrock Converse para el modelo generativo.

Una única llamada con herramienta forzada y muestreo fijo (`temperature` 0).
El documento va como mensaje de usuario; las instrucciones, como mensaje de sistema.
Los errores se traducen a códigos técnicos: nunca se propaga el texto de la respuesta.
"""

import json
from typing import Any, Final

from botocore.exceptions import BotoCoreError, ClientError, ParamValidationError

from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from atlas.procesamiento.modelo import RespuestaHerramienta

_TRANSITORIOS: Final = frozenset(
    {
        "ThrottlingException",
        "ServiceUnavailableException",
        "InternalServerException",
        "ModelNotReadyException",
        "ModelTimeoutException",
    }
)


class ModeloBedrockConverse:
    def __init__(self, cliente: Any, perfil: str) -> None:
        self._cliente = cliente
        self.identificador = perfil

    def invocar_herramienta(
        self, *, instrucciones: str, contenido: str, herramienta: dict[str, Any], max_tokens: int
    ) -> RespuestaHerramienta:
        nombre = herramienta["name"]
        try:
            respuesta = self._cliente.converse(
                modelId=self.identificador,
                system=[{"text": instrucciones}],
                messages=[{"role": "user", "content": [{"text": contenido}]}],
                inferenceConfig={"maxTokens": max_tokens, "temperature": 0.0},
                toolConfig={
                    "tools": [
                        {
                            "toolSpec": {
                                "name": nombre,
                                "description": herramienta["description"],
                                "inputSchema": {"json": herramienta["schema"]},
                            }
                        }
                    ],
                    "toolChoice": {"tool": {"name": nombre}},
                },
            )
        except ClientError as error:
            codigo = error.response.get("Error", {}).get("Code", "")
            if codigo in _TRANSITORIOS:
                raise ErrorTransitorio(f"bedrock_{codigo}") from None
            raise ErrorPermanente(f"bedrock_{codigo or 'error'}") from None
        except ParamValidationError:
            # Una solicitud mal formada no mejora reintentando.
            raise ErrorPermanente("bedrock_parametros_invalidos") from None
        except BotoCoreError:
            raise ErrorTransitorio("bedrock_conexion") from None

        if respuesta.get("stopReason") == "max_tokens":
            raise ErrorPermanente("respuesta_truncada")
        usos = [
            bloque["toolUse"]
            for bloque in respuesta.get("output", {}).get("message", {}).get("content", [])
            if "toolUse" in bloque and bloque["toolUse"].get("name") == nombre
        ]
        if len(usos) != 1:
            raise ErrorPermanente("respuesta_sin_herramienta")
        uso = respuesta.get("usage", {})
        return RespuestaHerramienta(
            entrada=usos[0].get("input"),
            modelo=self.identificador,
            tokens_entrada=int(uso.get("inputTokens", 0)),
            tokens_salida=int(uso.get("outputTokens", 0)),
        )


DIMENSIONES: Final = 1024
LOTE_MAXIMO: Final = 96  # textos por invocación admitidos por Cohere Embed v3


class EmbeddingsCohereBedrock:
    """Cohere Embed Multilingual v3 vía `InvokeModel`.

    `search_document` para los fragmentos y `search_query` para las consultas; sin
    truncado: un texto demasiado largo es un error, no se recorta en silencio.
    """

    def __init__(self, cliente: Any, modelo: str) -> None:
        self._cliente = cliente
        self.identificador = modelo

    def embeber(self, textos: list[str], tipo: str) -> list[list[float]]:
        vectores: list[list[float]] = []
        for inicio in range(0, len(textos), LOTE_MAXIMO):
            lote = textos[inicio : inicio + LOTE_MAXIMO]
            cuerpo = {"texts": lote, "input_type": tipo, "truncate": "NONE"}
            datos = _invocar_json(self._cliente, self.identificador, cuerpo)
            obtenidos = datos.get("embeddings") if isinstance(datos, dict) else None
            if (
                not isinstance(obtenidos, list)
                or len(obtenidos) != len(lote)
                or any(len(v) != DIMENSIONES for v in obtenidos)
            ):
                raise ErrorPermanente("embeddings_respuesta_invalida")
            vectores.extend([float(x) for x in v] for v in obtenidos)
        return vectores


class EmbeddingsTitanBedrock:
    """Amazon Titan Text Embeddings V2 vía `InvokeModel`, alternativa de comparación
    : 1024 dimensiones y normalización fijadas
        explícitamente. Titan no distingue documentos de consultas: `tipo` no cambia la solicitud.
        Un texto por invocación, como admite el modelo."""

    def __init__(self, cliente: Any, modelo: str) -> None:
        self._cliente = cliente
        self.identificador = modelo

    def embeber(self, textos: list[str], tipo: str) -> list[list[float]]:
        vectores: list[list[float]] = []
        for texto in textos:
            cuerpo = {"inputText": texto, "dimensions": DIMENSIONES, "normalize": True}
            datos = _invocar_json(self._cliente, self.identificador, cuerpo)
            vector = datos.get("embedding") if isinstance(datos, dict) else None
            if not isinstance(vector, list) or len(vector) != DIMENSIONES:
                raise ErrorPermanente("embeddings_respuesta_invalida")
            vectores.append([float(x) for x in vector])
        return vectores


def _invocar_json(cliente: Any, modelo: str, cuerpo: dict[str, Any]) -> Any:
    """`InvokeModel` con cuerpo JSON; los errores se traducen a códigos técnicos."""
    try:
        respuesta = cliente.invoke_model(
            modelId=modelo,
            body=json.dumps(cuerpo),
            contentType="application/json",
            accept="application/json",
        )
        return json.loads(respuesta["body"].read())
    except ClientError as error:
        codigo = error.response.get("Error", {}).get("Code", "")
        if codigo in _TRANSITORIOS:
            raise ErrorTransitorio(f"embeddings_{codigo}") from None
        raise ErrorPermanente(f"embeddings_{codigo or 'error'}") from None
    except ParamValidationError:
        raise ErrorPermanente("embeddings_parametros_invalidos") from None
    except BotoCoreError:
        raise ErrorTransitorio("embeddings_conexion") from None
    except ValueError:
        raise ErrorPermanente("embeddings_respuesta_invalida") from None
