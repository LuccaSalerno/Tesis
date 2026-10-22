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
from urllib.parse import urlparse

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

Entorno = Literal["desarrollo", "tests", "demo"]


HOSTS_LOCALES = frozenset({"localhost", "127.0.0.1", "::1"})

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

    # Servicios AWS (DT-AWS-01). Sin endpoint: AWS real con la identidad del despliegue.
    # Con endpoint: simulación local (moto), prohibida en demo y solo en hosts locales.
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None
    s3_bucket_documentos: str | None = None
    sfn_maquina_procesamiento_arn: str | None = None

    # Límites de carga (RC-P04), configurables sin modificar el código.
    carga_tamano_maximo_bytes: int = 20 * 1024 * 1024
    carga_paginas_maximas_pdf: int = 50
    carga_caracteres_maximos_docx: int = 150_000
    # DO-2026-10-22-CARGAS: URL prefirmada de 5 minutos; 24 horas para confirmar la carga.
    carga_vigencia_url_s: int = 300
    carga_vigencia_pendiente_s: int = 24 * 60 * 60

    # Procesamiento (hito 1.4, DO-2026-10-22-PROC). Perfil geográfico de EE. UU. (RC-P09).
    bedrock_perfil_generativo: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    procesamiento_max_tokens_clasificacion: int = 256
    procesamiento_max_tokens_extraccion: int = 2048
    procesamiento_caracteres_maximos: int = 400_000
    # Consulta asistida (hito 1.6, DO-2026-10-22-RAG, RC-P07.3).
    bedrock_modelo_embeddings: str = "cohere.embed-multilingual-v3"
    consulta_fragmentos_recuperados: int = 5
    consulta_max_tokens: int = 1024

    def validar_servicios_aws(self) -> None:
        if not self.s3_bucket_documentos or not self.sfn_maquina_procesamiento_arn:
            raise ErrorConfiguracion(
                "Faltan ATLAS_S3_BUCKET_DOCUMENTOS y ATLAS_SFN_MAQUINA_PROCESAMIENTO_ARN"
            )
        if self.aws_endpoint_url is None:
            return
        if self.entorno == "demo":
            raise ErrorConfiguracion("En demo no se admite ATLAS_AWS_ENDPOINT_URL")
        if urlparse(self.aws_endpoint_url).hostname not in HOSTS_LOCALES:
            raise ErrorConfiguracion("ATLAS_AWS_ENDPOINT_URL solo admite hosts locales")

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
