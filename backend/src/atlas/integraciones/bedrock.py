"""Adaptador de Amazon Bedrock Converse para el modelo generativo (DO-2026-10-22-PROC, P2).

Una única llamada con herramienta forzada y muestreo fijo (`temperature` 0, RC-P07.1).
El documento va como mensaje de usuario; las instrucciones, como mensaje de sistema.
Los errores se traducen a códigos técnicos: nunca se propaga el texto de la respuesta.
"""

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
