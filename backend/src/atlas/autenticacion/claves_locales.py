"""Claves y tokens locales con la forma de los tokens de acceso de Cognito.

Solo para desarrollo local y pruebas: permiten ejercitar el mismo
verificador que en AWS sin acceder a AWS. Las claves privadas nunca se versionan.
"""

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from atlas.autenticacion.verificador import USO_ACCESO

EMISOR_LOCAL = "http://localhost/atlas-local"
CLIENTE_LOCAL = "atlas-local"


@dataclass(frozen=True)
class ClavesLocales:
    privada: RSAPrivateKey
    kid: str

    @classmethod
    def generar(cls) -> "ClavesLocales":
        return cls(
            rsa.generate_private_key(public_exponent=65537, key_size=2048), str(uuid.uuid4())
        )

    def jwks(self) -> dict[str, Any]:
        publica: dict[str, Any] = json.loads(
            jwt.algorithms.RSAAlgorithm.to_jwk(self.privada.public_key())
        )
        publica.update({"kid": self.kid, "alg": "RS256", "use": "sig"})
        return {"keys": [publica]}

    def emitir(
        self,
        sub: str,
        *,
        emisor: str = EMISOR_LOCAL,
        cliente: str = CLIENTE_LOCAL,
        token_use: str = USO_ACCESO,
        vigencia_s: int = 3600,
        **extra: Any,
    ) -> str:
        ahora = int(time.time())
        claims = {
            "sub": sub,
            "iss": emisor,
            "client_id": cliente,
            "token_use": token_use,
            "iat": ahora,
            "exp": ahora + vigencia_s,
            **extra,
        }
        return jwt.encode(claims, self.privada, algorithm="RS256", headers={"kid": self.kid})

    def guardar(self, directorio: Path) -> Path:
        """Guarda la clave privada y el JWKS; devuelve la ruta del JWKS."""
        directorio.mkdir(mode=0o700, parents=True, exist_ok=True)
        privada = directorio / "privada.pem"
        privada.write_bytes(
            self.privada.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        privada.chmod(0o600)
        (directorio / "kid").write_text(self.kid, encoding="utf-8")
        ruta_jwks = directorio / "jwks.json"
        ruta_jwks.write_text(json.dumps(self.jwks()), encoding="utf-8")
        return ruta_jwks

    @classmethod
    def cargar(cls, directorio: Path) -> "ClavesLocales":
        privada = serialization.load_pem_private_key(
            (directorio / "privada.pem").read_bytes(), password=None
        )
        if not isinstance(privada, RSAPrivateKey):
            raise ValueError("La clave local no es RSA")
        return cls(privada, (directorio / "kid").read_text(encoding="utf-8").strip())
