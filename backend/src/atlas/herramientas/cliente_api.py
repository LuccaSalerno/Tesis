"""Cliente HTTP mínimo de la API para las herramientas del operador.

Usa solo la biblioteca estándar. Los tokens nunca se escriben en archivos ni en la salida:
viven en memoria mientras corre la herramienta. Los mensajes de error informan método, ruta
y estado HTTP, nunca cuerpos de respuesta (pueden contener datos documentales).
"""

import base64
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

# (método, URL, encabezados, cuerpo) -> (estado, cuerpo)
Transporte = Callable[[str, str, Mapping[str, str], bytes | None], tuple[int, bytes]]


class ErrorApi(RuntimeError):
    def __init__(self, metodo: str, ruta: str, estado: int) -> None:
        super().__init__(f"{metodo} {ruta} respondió {estado}")
        self.estado = estado


def transporte_urllib(
    metodo: str, url: str, encabezados: Mapping[str, str], cuerpo: bytes | None
) -> tuple[int, bytes]:
    if not url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        raise ValueError("Solo HTTPS, salvo un servidor local")
    # Esquema verificado arriba: solo https o un servidor local.
    solicitud = urllib.request.Request(  # noqa: S310
        url, data=cuerpo, method=metodo, headers=dict(encabezados)
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=60) as respuesta:  # noqa: S310
            return respuesta.status, respuesta.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def sub_del_token(token: str) -> str:
    """`sub` de un token propio (ya verificado por quien lo emitió); no valida la firma."""
    carga = token.split(".")[1]
    datos = json.loads(base64.urlsafe_b64decode(carga + "=" * (-len(carga) % 4)))
    sub: str = datos["sub"]
    return sub


def tokens_cognito(
    region: str, cliente_id: str, usuarios: Mapping[str, str], cliente_idp: Any = None
) -> dict[str, str]:
    """Inicia sesión con USER_PASSWORD_AUTH. La contraseña de cada rol sale de la
    variable de entorno `ATLAS_SEED_CLAVE_<ROL>` de la terminal del operador."""
    if cliente_idp is None:
        import boto3

        cliente_idp = boto3.client("cognito-idp", region_name=region)
    tokens: dict[str, str] = {}
    for rol, usuario in usuarios.items():
        clave = os.environ.get(f"ATLAS_SEED_CLAVE_{rol.upper()}")
        if not clave:
            raise RuntimeError(f"Falta ATLAS_SEED_CLAVE_{rol.upper()}")
        respuesta = cliente_idp.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            ClientId=cliente_id,
            AuthParameters={"USERNAME": usuario, "PASSWORD": clave},
        )
        tokens[rol] = respuesta["AuthenticationResult"]["AccessToken"]
    return tokens


@dataclass
class ClienteApi:
    url_base: str
    tokens: Mapping[str, str]
    transporte: Transporte = transporte_urllib
    llamadas: list[tuple[str, str, int]] = field(default_factory=list)

    def solicitar(
        self,
        metodo: str,
        ruta: str,
        rol: str | None = None,
        cuerpo: Any = None,
        esperado: tuple[int, ...] = (200, 201),
    ) -> Any:
        encabezados = {"Accept": "application/json"}
        datos = None
        if cuerpo is not None:
            datos = json.dumps(cuerpo).encode()
            encabezados["Content-Type"] = "application/json"
        if rol is not None:
            encabezados["Authorization"] = f"Bearer {self.tokens[rol]}"
        estado, respuesta = self.transporte(
            metodo, self.url_base.rstrip("/") + ruta, encabezados, datos
        )
        self.llamadas.append((metodo, ruta, estado))
        if estado not in esperado:
            raise ErrorApi(metodo, ruta, estado)
        return json.loads(respuesta) if respuesta else None

    def get(self, ruta: str, rol: str | None = None) -> Any:
        return self.solicitar("GET", ruta, rol)

    def post(self, ruta: str, rol: str, cuerpo: Any = None) -> Any:
        return self.solicitar("POST", ruta, rol, cuerpo)

    def put(self, ruta: str, rol: str, cuerpo: Any = None) -> Any:
        return self.solicitar("PUT", ruta, rol, cuerpo)

    def transferir(self, url: str, encabezados: Mapping[str, str], datos: bytes) -> None:
        """PUT directo a la URL prefirmada, como lo haría el navegador (§5.3.1)."""
        estado, _ = self.transporte("PUT", url, encabezados, datos)
        if estado != 200:
            raise ErrorApi("PUT", "<url prefirmada>", estado)
