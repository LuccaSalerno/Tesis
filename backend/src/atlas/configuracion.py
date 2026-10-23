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

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

Entorno = Literal["desarrollo", "tests", "demo"]
# DO-2026-10-22-OPS P4: clave en local y CI; token IAM de RDS en AWS (RC-P10-04).
AutenticacionBd = Literal["clave", "iam"]
# DO-2026-10-22-OPS P2: estado operativo leído de S3 o fijo en `active` fuera de AWS.
FuenteMantenimiento = Literal["s3", "fija_active"]


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
    # Las migraciones y la administración se conectan directo a RDS, no al proxy (RC-P10).
    bd_host_migracion: str | None = None
    bd_autenticacion: AutenticacionBd = "clave"
    # Paquete de certificados de RDS: TLS verify-full (obligatorio con IAM).
    bd_ca_certificados: Path | None = None

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

    # Lambda privada de operaciones (RC-P10-15, DO-2026-10-22-OPS P3): credencial maestra
    # administrada por RDS en Secrets Manager, solo para la inicialización privilegiada.
    ops_secreto_maestro_arn: str | None = None
    ops_directorio_migraciones: Path = Path(__file__).resolve().parents[2] / "migraciones"

    # Modo mantenimiento (RC-P10-09, DO-2026-10-22-OPS P2).
    mantenimiento_fuente: FuenteMantenimiento = "fija_active"
    mantenimiento_cache_s: float = 15.0
    mantenimiento_reintentar_s: int = 300

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
    # RC-P08.5: trabajos completos simultáneos por despliegue (demo 10; el entorno AWS
    # `tests` fija 5 con su variable de Terraform).
    procesamiento_limite_concurrencia: int = Field(default=10, ge=1)
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

    def validar_despliegue(self) -> None:
        """Demo exige base con IAM y TLS verificado, y mantenimiento leído de S3 (RC-P10)."""
        if self.bd_autenticacion == "iam" and self.bd_ca_certificados is None:
            raise ErrorConfiguracion(
                "Con ATLAS_BD_AUTENTICACION=iam falta ATLAS_BD_CA_CERTIFICADOS"
            )
        if self.entorno != "demo":
            return
        if self.bd_autenticacion != "iam":
            raise ErrorConfiguracion("En demo la base usa autenticación IAM")
        if self.mantenimiento_fuente != "s3":
            raise ErrorConfiguracion("En demo el modo mantenimiento se lee de S3")

    def argumentos_conexion(self) -> dict[str, str]:
        if self.bd_ca_certificados is None:
            return {}
        return {"sslmode": "verify-full", "sslrootcert": str(self.bd_ca_certificados)}

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
        return self._url(
            self.bd_usuario_migracion,
            self.bd_clave_migracion,
            host=self.bd_host_migracion or self.bd_host,
        )

    def _url(self, usuario: str, clave: SecretStr | None, host: str | None = None) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=usuario,
            password=clave.get_secret_value() if clave is not None else None,
            host=host or self.bd_host,
            port=self.bd_puerto,
            database=self.bd_nombre,
        )


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()  # type: ignore[call-arg]  # campos obligatorios llegan del entorno
