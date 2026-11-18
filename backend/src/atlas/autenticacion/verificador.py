"""Verificación de tokens de acceso de Cognito en el backend (RF-01, RNF-01).

En AWS, API Gateway valida el token antes de invocar la API; el backend vuelve
a verificarlo (defensa en profundidad) con el JWKS que recibe por configuración.
En local y en la CI se usa el mismo verificador con claves generadas localmente.
Los motivos de rechazo son códigos fijos: nunca se registra el token ni sus valores.
"""

from dataclasses import dataclass
from typing import Any, Final

import jwt

ALGORITMO: Final = "RS256"
CLAIMS_OBLIGATORIOS: Final = ["exp", "iat", "iss", "sub", "token_use", "client_id"]
USO_ACCESO: Final = "access"  # valor de `token_use` en los tokens de acceso de Cognito


class ErrorAutenticacion(Exception):
    """Token rechazado. `codigo` es un motivo técnico fijo, apto para registros."""

    def __init__(self, codigo: str) -> None:
        super().__init__(codigo)
        self.codigo = codigo


@dataclass(frozen=True)
class IdentidadAutenticada:
    """Identidad probada por el token: solo el identificador externo (sub)."""

    identificador_externo: str


class VerificadorJwt:
    def __init__(self, jwks: dict[str, Any], emisor: str, cliente: str) -> None:
        try:
            claves = jwt.PyJWKSet.from_dict(jwks).keys
        except jwt.PyJWTError:
            claves = []
        self._claves = {
            clave.key_id: clave for clave in claves if clave.key_id and clave.key_type == "RSA"
        }
        if not self._claves:
            raise ValueError("El JWKS no contiene claves RSA con identificador (kid)")
        self._emisor = emisor
        self._cliente = cliente

    def verificar(self, token: str) -> IdentidadAutenticada:
        try:
            encabezado = jwt.get_unverified_header(token)
        except jwt.PyJWTError as error:
            raise ErrorAutenticacion("token_malformado") from error
        if encabezado.get("alg") != ALGORITMO:
            raise ErrorAutenticacion("algoritmo_no_admitido")
        clave = self._claves.get(encabezado.get("kid", ""))
        if clave is None:
            raise ErrorAutenticacion("clave_desconocida")
        try:
            claims = jwt.decode(
                token,
                key=clave.key,
                algorithms=[ALGORITMO],
                issuer=self._emisor,
                options={"require": CLAIMS_OBLIGATORIOS, "verify_aud": False},
            )
        except jwt.ExpiredSignatureError as error:
            raise ErrorAutenticacion("token_vencido") from error
        except jwt.InvalidIssuerError as error:
            raise ErrorAutenticacion("emisor_invalido") from error
        except jwt.InvalidSignatureError as error:
            raise ErrorAutenticacion("firma_invalida") from error
        except jwt.PyJWTError as error:
            raise ErrorAutenticacion("token_invalido") from error
        # Los tokens de acceso de Cognito identifican al cliente con `client_id`, no `aud`.
        if claims["token_use"] != USO_ACCESO:
            raise ErrorAutenticacion("tipo_de_token_invalido")
        if claims["client_id"] != self._cliente:
            raise ErrorAutenticacion("cliente_invalido")
        sub = claims["sub"]
        if not isinstance(sub, str) or not sub:
            raise ErrorAutenticacion("token_invalido")
        return IdentidadAutenticada(identificador_externo=sub)
