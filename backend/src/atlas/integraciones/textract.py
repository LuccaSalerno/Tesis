"""Adaptador de Amazon Textract para el análisis asíncrono de PDF (§5.3.1, RC-P08, P4).

`StartDocumentAnalysis` con TABLES y LAYOUT y un `ClientRequestToken` estable por
trabajo e intento: un reintento no inicia un segundo análisis (RC-P08.7). El token incluye
la huella del objeto: los identificadores de trabajo se repiten entre sesiones E90A de una
misma cuenta, y Textract rechaza un token conocido con otro documento
(`IdempotentParameterMismatchException`).
"""

import hashlib
from typing import Any, Final, Literal

from botocore.exceptions import BotoCoreError, ClientError, ParamValidationError

from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio

EstadoAnalisis = Literal["en_curso", "completado", "fallido"]

FUNCIONES: Final = ["TABLES", "LAYOUT"]
_TRANSITORIOS: Final = frozenset(
    {
        "ThrottlingException",
        "ProvisionedThroughputExceededException",
        "InternalServerError",
        "LimitExceededException",
    }
)


def token_solicitud(trabajo_id: int, intento: int, bucket: str, clave: str) -> str:
    huella = hashlib.sha256(f"s3://{bucket}/{clave}".encode()).hexdigest()[:32]
    return f"atlas-{trabajo_id}-{intento}-{huella}"


class AnalizadorTextract:
    def __init__(self, cliente: Any, bucket: str) -> None:
        self._cliente = cliente
        self._bucket = bucket

    def iniciar(self, clave: str, trabajo_id: int, intento: int) -> str:
        respuesta = self._llamar(
            "start_document_analysis",
            DocumentLocation={"S3Object": {"Bucket": self._bucket, "Name": clave}},
            FeatureTypes=FUNCIONES,
            ClientRequestToken=token_solicitud(trabajo_id, intento, self._bucket, clave),
            JobTag=f"trabajo-{trabajo_id}",
        )
        job_id: str = respuesta["JobId"]
        return job_id

    def estado(self, job_id: str) -> EstadoAnalisis:
        respuesta = self._llamar("get_document_analysis", JobId=job_id, MaxResults=1)
        estado = respuesta["JobStatus"]
        if estado == "IN_PROGRESS":
            return "en_curso"
        # §5.3.1: un análisis incompleto (PARTIAL_SUCCESS) es un fallo técnico.
        return "completado" if estado == "SUCCEEDED" else "fallido"

    def resultado(self, job_id: str) -> list[dict[str, Any]]:
        paginas: list[dict[str, Any]] = []
        parametros: dict[str, Any] = {"JobId": job_id, "MaxResults": 1000}
        while True:
            respuesta = self._llamar("get_document_analysis", **parametros)
            if respuesta["JobStatus"] != "SUCCEEDED":
                raise ErrorPermanente("textract_incompleto")
            paginas.append({"Blocks": respuesta.get("Blocks", [])})
            if not respuesta.get("NextToken"):
                return paginas
            parametros["NextToken"] = respuesta["NextToken"]

    def _llamar(self, operacion: str, **parametros: Any) -> dict[str, Any]:
        try:
            respuesta: dict[str, Any] = getattr(self._cliente, operacion)(**parametros)
        except ClientError as error:
            codigo = error.response.get("Error", {}).get("Code", "")
            if codigo in _TRANSITORIOS:
                raise ErrorTransitorio(f"textract_{codigo}") from None
            raise ErrorPermanente(f"textract_{codigo or 'error'}") from None
        except ParamValidationError:
            # Una solicitud mal formada no mejora reintentando.
            raise ErrorPermanente("textract_parametros_invalidos") from None
        except BotoCoreError:
            raise ErrorTransitorio("textract_conexion") from None
        return respuesta
