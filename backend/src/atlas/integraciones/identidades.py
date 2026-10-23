"""Supresión de la cuenta en el proveedor de identidad (RF-25, §5.4.2, DO-2026-10-23-CIERRE P7).

La API no llama a Cognito: invoca la Lambda `cuentas`, fuera de la VPC, por el endpoint
privado de Lambda. Fuera de AWS (desarrollo y CI) no hay Cognito y la supresión solo
desvincula la cuenta en la base (P9, DIF).
"""

import json
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from atlas.integraciones.puertos import ErrorIntegracion


class GestorIdentidadesLambda:
    def __init__(self, cliente: Any, nombre_funcion: str) -> None:
        self._cliente = cliente
        self._nombre_funcion = nombre_funcion

    def suprimir(self, identificador_externo: str) -> None:
        try:
            respuesta = self._cliente.invoke(
                FunctionName=self._nombre_funcion,
                InvocationType="RequestResponse",
                Payload=json.dumps({"accion": "suprimir", "sub": identificador_externo}),
            )
            cuerpo = json.loads(respuesta["Payload"].read() or b"{}")
        except (BotoCoreError, ClientError, ValueError) as error:
            raise ErrorIntegracion("cognito_supresion_incierta") from error
        if respuesta.get("FunctionError") or cuerpo.get("resultado") != "completada":
            raise ErrorIntegracion("cognito_supresion_fallida")


class GestorIdentidadesLocal:
    """Sin proveedor de identidad (tokens locales): no hay cuenta externa que eliminar."""

    def suprimir(self, identificador_externo: str) -> None:
        return None
