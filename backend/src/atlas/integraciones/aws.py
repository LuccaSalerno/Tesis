"""Adaptadores boto3 de S3 y Step Functions.

El mismo código corre en AWS y contra moto: solo cambia la configuración. Con un
endpoint local se usan credenciales ficticias fijas; sin endpoint, la cadena de
credenciales de la identidad del despliegue (rol de la Lambda).
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
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
    return crear_cliente_region(servicio, configuracion.aws_region, configuracion.aws_endpoint_url)


def crear_cliente_region(servicio: str, region: str, endpoint_url: str | None = None) -> Any:
    """Cliente con la configuración común; lo usan también las herramientas del operador que
    no levantan la aplicación (arnés de §6.3)."""
    # La firma de S3 solo para S3 (URL prefirmadas): en otros servicios no codifica la ruta
    # como SigV4 estándar y Bedrock rechaza los ID de modelo con «:».
    firma = {"signature_version": "s3v4"} if servicio == "s3" else {}
    opciones: dict[str, Any] = {
        "region_name": region,
        "config": ConfiguracionBotocore(
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=30,
            **firma,
        ),
    }
    if endpoint_url is not None:
        opciones.update(endpoint_url=endpoint_url, **_CREDENCIALES_SIMULACION)
    return boto3.client(servicio, **opciones)


def nombre_ejecucion(trabajo_id: int, intento: int) -> str:
    """§5.3.1: el nombre deriva del trabajo y su intento, para no duplicar ejecuciones."""
    return f"trabajo-{trabajo_id}-intento-{intento}"


@contextmanager
def _errores_s3(codigo: str) -> Iterator[None]:
    try:
        yield
    except (BotoCoreError, ClientError) as error:
        raise ErrorIntegracion(codigo) from error


class AlmacenS3:
    def __init__(self, cliente: Any, bucket: str) -> None:
        self._cliente = cliente
        self._bucket = bucket

    def url_carga(self, clave: str, tipo_contenido: str, vigencia_s: int) -> str:
        with _errores_s3("s3_url_no_generada"):
            url: str = self._cliente.generate_presigned_url(
                "put_object",
                Params={"Bucket": self._bucket, "Key": clave, "ContentType": tipo_contenido},
                ExpiresIn=vigencia_s,
                HttpMethod="PUT",
            )
        return url

    def url_lectura(self, clave: str, vigencia_s: int, nombre: str) -> str:
        # El nombre solo va como sugerencia de descarga; se limpia de comillas.
        limpio = nombre.replace('"', "").replace("\\", "")
        with _errores_s3("s3_url_no_generada"):
            url: str = self._cliente.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": clave,
                    "ResponseContentDisposition": f'inline; filename="{limpio}"',
                },
                ExpiresIn=vigencia_s,
            )
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
        with _errores_s3("s3_lectura_fallida"):
            datos: bytes = self._cliente.get_object(Bucket=self._bucket, Key=clave)["Body"].read()
        return datos

    def escribir(self, clave: str, datos: bytes, tipo_contenido: str) -> None:
        with _errores_s3("s3_escritura_fallida"):
            self._cliente.put_object(
                Bucket=self._bucket, Key=clave, Body=datos, ContentType=tipo_contenido
            )

    def eliminar_prefijo(self, prefijo: str) -> int:
        return self._borrar_versiones(prefijo)

    def copiar(self, origen: str, destino: str) -> None:
        with _errores_s3("s3_copia_fallida"):
            self._cliente.copy_object(
                Bucket=self._bucket,
                Key=destino,
                CopySource={"Bucket": self._bucket, "Key": origen},
                MetadataDirective="COPY",
            )

    def eliminar_definitivamente(self, clave: str) -> int:
        return self._borrar_versiones(clave, exacta=True)

    def _borrar_versiones(self, prefijo: str, *, exacta: bool = False) -> int:
        # Una sola enumeración y borrado por lotes: listar por clave hacía el costo cuadrático
        # en la cantidad de objetos del prefijo. Con `exacta` se excluyen otras claves que el
        # prefijo podría abarcar.
        with _errores_s3("s3_eliminacion_fallida"):
            versiones = [
                {"Key": v["Key"], "VersionId": v["VersionId"]}
                for pagina in self._cliente.get_paginator("list_object_versions").paginate(
                    Bucket=self._bucket, Prefix=prefijo
                )
                for v in pagina.get("Versions", []) + pagina.get("DeleteMarkers", [])
                if not exacta or v["Key"] == prefijo
            ]
            for inicio in range(0, len(versiones), 1000):
                respuesta = self._cliente.delete_objects(
                    Bucket=self._bucket,
                    Delete={"Objects": versiones[inicio : inicio + 1000], "Quiet": True},
                )
                if respuesta.get("Errors"):
                    raise ErrorIntegracion("s3_eliminacion_incompleta")
        return len(versiones)

    def abortar_multipartes(self, prefijo: str, iniciadas_antes: datetime) -> int:
        abortadas = 0
        with _errores_s3("s3_multiparte_fallida"):
            for pagina in self._cliente.get_paginator("list_multipart_uploads").paginate(
                Bucket=self._bucket, Prefix=prefijo
            ):
                for carga in pagina.get("Uploads", []):
                    if carga["Initiated"] < iniciadas_antes:
                        self._cliente.abort_multipart_upload(
                            Bucket=self._bucket, Key=carga["Key"], UploadId=carga["UploadId"]
                        )
                        abortadas += 1
        return abortadas


class OrquestadorStepFunctions:
    def __init__(self, cliente: Any, maquina_arn: str) -> None:
        self._cliente = cliente
        self._maquina_arn = maquina_arn

    def iniciar(self, trabajo_id: int, intento: int) -> None:
        # La entrada lleva solo identificadores técnicos.
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

    def estado(self, trabajo_id: int, intento: int) -> str:
        """Estado real de la ejecución del intento: `inexistente`, `RUNNING`,
        `SUCCEEDED`, `FAILED`, `TIMED_OUT`, `ABORTED` o `PENDING_REDRIVE`."""
        arn = (
            self._maquina_arn.replace(":stateMachine:", ":execution:", 1)
            + ":"
            + nombre_ejecucion(trabajo_id, intento)
        )
        try:
            respuesta = self._cliente.describe_execution(executionArn=arn)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ExecutionDoesNotExist":
                return "inexistente"
            raise ErrorIntegracion("sfn_consulta_fallida") from error
        except BotoCoreError as error:
            raise ErrorIntegracion("sfn_consulta_incierta") from error
        estado: str = respuesta["status"]
        return estado
