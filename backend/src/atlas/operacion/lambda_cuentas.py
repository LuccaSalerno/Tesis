"""Lambda `cuentas`: operaciones administrativas sobre Cognito (RF-25, §5.4.2,
DO-2026-10-23-CIERRE P7).

Fuera de la VPC; solo la invoca la API, que ya verificó el permiso del administrador. Busca
la cuenta por su `sub` y la elimina; si ya no existe, la supresión está completa
(idempotente). Los registros y la respuesta no incluyen el identificador.
"""

import logging
import os
import re
from functools import lru_cache
from typing import Any, Final

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from atlas.registro import configurar_registro, registrar_evento

_registrador = logging.getLogger(__name__)
# El `sub` de Cognito es un UUID: el formato se exige antes de usarlo en el filtro.
FORMATO_SUB: Final = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@lru_cache(maxsize=1)
def _cliente() -> Any:
    configurar_registro(os.environ.get("ATLAS_NIVEL_REGISTRO", "INFO"))
    return boto3.client("cognito-idp", region_name=os.environ["ATLAS_AWS_REGION"])


def suprimir(cliente: Any, grupo: str, sub: str) -> bool:
    """Devuelve si había una cuenta que eliminar."""
    usuarios = cliente.list_users(UserPoolId=grupo, Filter=f'sub = "{sub}"', Limit=1)["Users"]
    if not usuarios:
        return False
    try:
        cliente.admin_delete_user(UserPoolId=grupo, Username=usuarios[0]["Username"])
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "UserNotFoundException":
            raise
        return False
    return True


def manejar(evento: dict[str, Any], _contexto: Any) -> dict[str, Any]:
    sub = str(evento.get("sub", ""))
    if evento.get("accion") != "suprimir" or not FORMATO_SUB.match(sub):
        registrar_evento(_registrador, "cuentas_rechazada")
        return {"resultado": "rechazada"}
    try:
        eliminada = suprimir(_cliente(), os.environ["ATLAS_COGNITO_GRUPO_USUARIOS"], sub)
    except (BotoCoreError, ClientError) as error:
        registrar_evento(_registrador, "cuentas_fallida", codigo_error=type(error).__name__)
        return {"resultado": "fallida"}
    registrar_evento(_registrador, "cuenta_suprimida_en_cognito", eliminada=eliminada)
    return {"resultado": "completada", "eliminada": eliminada}
