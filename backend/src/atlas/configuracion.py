"""Configuración del servidor, leída exclusivamente del entorno del proceso.

La separación entre entornos (desarrollo, tests, demo) se fija por despliegue y
configuración del servidor, nunca por un parámetro de la petición (RC-P10).
No hay valores secretos por defecto: las claves solo llegan por variables de
entorno o por un archivo `.env` local que no se versiona.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

Entorno = Literal["desarrollo", "tests", "demo"]


# Emisor de un User Pool de Cognito: https://cognito-idp.<región>.amazonaws.com/<pool>
_EMISOR_COGNITO = re.compile(
    r"^https://cognito-idp\.[a-z0-9-]+\.amazonaws\.com/[a-z0-9-]+_[0-9A-Za-z]+$"
)


class ErrorConfiguracion(RuntimeError):
    """La configuración del proceso no permite la operación solicitada."""


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ATLAS_", env_file=".env", extra="ignore")

    entorno: Entorno
    nivel_registro: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    bd_host: str = "localhost"
    bd_puerto: int = 5432
    bd_nombre: str
    bd_usuario: str
    bd_clave: SecretStr | None = None
    bd_usuario_migracion: str | None = None
    bd_clave_migracion: SecretStr | None = None

    # Verificación de tokens de acceso (DT-AUT-01). El JWKS llega por configuración:
    # en AWS lo provee el despliegue (sin salida a Internet); en local, claves locales.
    jwt_emisor: str | None = None
    jwt_cliente: str | None = None
    jwt_jwks: str | None = None
    jwt_jwks_archivo: Path | None = None

    def cargar_jwks(self) -> dict[str, Any]:
        """Devuelve el JWKS configurado, validando que la configuración de tokens esté completa."""
        if not self.jwt_emisor or not self.jwt_cliente:
            raise ErrorConfiguracion("Faltan ATLAS_JWT_EMISOR y ATLAS_JWT_CLIENTE")
        if self.entorno == "demo" and not _EMISOR_COGNITO.match(self.jwt_emisor):
            raise ErrorConfiguracion("En demo el emisor de tokens debe ser un User Pool de Cognito")
        if (self.jwt_jwks is None) == (self.jwt_jwks_archivo is None):
            raise ErrorConfiguracion(
                "Definir exactamente uno: ATLAS_JWT_JWKS o ATLAS_JWT_JWKS_ARCHIVO"
            )
        contenido = (
            self.jwt_jwks
            if self.jwt_jwks is not None
            else self.jwt_jwks_archivo.read_text(encoding="utf-8")  # type: ignore[union-attr]
        )
        jwks: dict[str, Any] = json.loads(contenido)
        return jwks

    def url_aplicacion(self) -> URL:
        """URL del usuario de aplicación (solo DML sobre su propia base)."""
        return self._url(self.bd_usuario, self.bd_clave)

    def url_migracion(self) -> URL:
        """URL del usuario de migración (propietario del esquema)."""
        if self.bd_usuario_migracion is None:
            raise ErrorConfiguracion("Falta ATLAS_BD_USUARIO_MIGRACION para ejecutar migraciones")
        return self._url(self.bd_usuario_migracion, self.bd_clave_migracion)

    def _url(self, usuario: str, clave: SecretStr | None) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=usuario,
            password=clave.get_secret_value() if clave is not None else None,
            host=self.bd_host,
            port=self.bd_puerto,
            database=self.bd_nombre,
        )


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()  # type: ignore[call-arg]  # campos obligatorios llegan del entorno
