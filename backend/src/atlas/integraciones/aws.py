"""Adaptadores boto3 de S3 y Step Functions (DT-AWS-01).

El mismo código corre en AWS y contra moto: solo cambia la configuración. Con un
endpoint local se usan credenciales ficticias fijas; sin endpoint, la cadena de
credenciales de la identidad del despliegue (rol de la Lambda).
"""

import json
from typing import Any, Final

import boto3
from botocore.config import Config as ConfiguracionBotocore
from botocore.exceptions import BotoCoreError, ClientError

from atlas.configuracion import Configuracion
from atlas.integraciones.puertos import ErrorIntegracion, MetadatosObjeto

# Solo válidas contra moto; la configuración impide un endpoint no local.
_CREDENCIALES_SIMULACION: Final = {
    "aws_access_key_id": "testing",
    "aws_secret_access_key": "testing",
}


def crear_cliente(configuracion: Configuracion, servicio: str) -> Any:
    configuracion.validar_servicios_aws()
    opciones: dict[str, Any] = {
        "region_name": configuracion.aws_region,
        "config": ConfiguracionBotocore(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=30,
        ),
    }
    if configuracion.aws_endpoint_url is not None:
        opciones.update(endpoint_url=configuracion.aws_endpoint_url, **_CREDENCIALES_SIMULACION)
    return boto3.client(servicio, **opciones)


def nombre_ejecucion(trabajo_id: int, intento: int) -> str:
    """§5.3.1: el nombre deriva del trabajo y su intento, para no duplicar ejecuciones."""
    return f"trabajo-{trabajo_id}-intento-{intento}"


class AlmacenS3:
    def __init__(self, cliente: Any, bucket: str) -> None:
        self._cliente = cliente
        self._bucket = bucket

    def url_carga(self, clave: str, tipo_contenido: str, vigencia_s: int) -> str:
        try:
            url: str = self._cliente.generate_presigned_url(
                "put_object",
                Params={"Bucket": self._bucket, "Key": clave, "ContentType": tipo_contenido},
                ExpiresIn=vigencia_s,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as error:
            raise ErrorIntegracion("s3_url_no_generada") from error
        return url

    def metadatos(self, clave: str) -> MetadatosObjeto | None:
        try:
            respuesta = self._cliente.head_object(Bucket=self._bucket, Key=clave)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return None
            raise ErrorIntegracion("s3_consulta_fallida") from error
        except BotoCoreError as error:
            raise ErrorIntegracion("s3_consulta_fallida") from error
        return MetadatosObjeto(tamano_bytes=int(respuesta["ContentLength"]))

    def leer(self, clave: str) -> bytes:
        try:
            datos: bytes = self._cliente.get_object(Bucket=self._bucket, Key=clave)["Body"].read()
        except (BotoCoreError, ClientError) as error:
            raise ErrorIntegracion("s3_lectura_fallida") from error
        return datos


class OrquestadorStepFunctions:
    def __init__(self, cliente: Any, maquina_arn: str) -> None:
        self._cliente = cliente
        self._maquina_arn = maquina_arn

    def iniciar(self, trabajo_id: int, intento: int) -> None:
        # Regla 5 de AGENTS.md: la entrada lleva solo identificadores técnicos.
        entrada = json.dumps({"trabajo_id": trabajo_id, "intento": intento})
        try:
            self._cliente.start_execution(
                stateMachineArn=self._maquina_arn,
                name=nombre_ejecucion(trabajo_id, intento),
                input=entrada,
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ExecutionAlreadyExists":
                return  # el mismo intento ya fue aceptado: idempotente
            raise ErrorIntegracion("sfn_inicio_rechazado") from error
        except BotoCoreError as error:
            raise ErrorIntegracion("sfn_inicio_incierto") from error
