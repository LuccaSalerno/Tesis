"""Ramas de error de los adaptadores AWS, sin contactar AWS.

Un cliente sustituto lanza las excepciones de botocore; se verifica que cada una se
traduzca a un código técnico y que los errores de red o de servicio sean reintentables.
"""

from typing import Any

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError
from botocore.stub import Stubber

from atlas.integraciones.aws import AlmacenS3, OrquestadorStepFunctions, crear_cliente
from atlas.integraciones.bedrock import ModeloBedrockConverse
from atlas.integraciones.puertos import ErrorIntegracion
from atlas.integraciones.textract import AnalizadorTextract
from atlas.procesamiento import esquemas
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from tests.conftest import configuracion_sin_base
from tests.test_procesamiento_adaptadores import cliente

RED = EndpointConnectionError(endpoint_url="https://s3.amazonaws.com")


def error_cliente(codigo: str, operacion: str = "Operacion") -> ClientError:
    return ClientError({"Error": {"Code": codigo, "Message": "detalle del servicio"}}, operacion)


class Paginador:
    def __init__(self, paginas: list[dict[str, Any]] | Exception) -> None:
        self._paginas = paginas

    def paginate(self, **_: Any) -> Any:
        if isinstance(self._paginas, Exception):
            raise self._paginas
        return iter(self._paginas)


class ClienteS3Sustituto:
    """Cada operación lanza la excepción configurada o devuelve la respuesta configurada."""

    def __init__(self, **comportamiento: Any) -> None:
        self._comportamiento = comportamiento

    def __getattr__(self, operacion: str) -> Any:
        def llamada(*_: Any, **__: Any) -> Any:
            resultado = self._comportamiento[operacion]
            if isinstance(resultado, Exception):
                raise resultado
            return resultado

        return llamada

    def get_paginator(self, operacion: str) -> Paginador:
        resultado: Any = self._comportamiento[operacion]
        return Paginador(resultado)


@pytest.mark.parametrize(
    ("comportamiento", "llamada", "codigo"),
    [
        (
            {"generate_presigned_url": RED},
            lambda a: a.url_carga("k", "application/pdf", 60),
            "s3_url_no_generada",
        ),
        ({"head_object": error_cliente("500")}, lambda a: a.metadatos("k"), "s3_consulta_fallida"),
        ({"head_object": RED}, lambda a: a.metadatos("k"), "s3_consulta_fallida"),
        ({"get_object": error_cliente("NoSuchKey")}, lambda a: a.leer("k"), "s3_lectura_fallida"),
        (
            {"put_object": RED},
            lambda a: a.escribir("k", b"{}", "application/json"),
            "s3_escritura_fallida",
        ),
        (
            {"copy_object": error_cliente("AccessDenied")},
            lambda a: a.copiar("a", "b"),
            "s3_copia_fallida",
        ),
        (
            {"list_object_versions": RED},
            lambda a: a.eliminar_definitivamente("k"),
            "s3_eliminacion_fallida",
        ),
        (
            {"list_object_versions": RED},
            lambda a: a.eliminar_prefijo("resultados/"),
            "s3_eliminacion_fallida",
        ),
        (
            {"list_multipart_uploads": error_cliente("500")},
            lambda a: a.abortar_multipartes("p/", None),
            "s3_multiparte_fallida",
        ),
        (
            {
                "list_object_versions": [{"Versions": [{"Key": "k", "VersionId": "v1"}]}],
                "delete_objects": {"Errors": [{"Key": "k", "Code": "AccessDenied"}]},
            },
            lambda a: a.eliminar_definitivamente("k"),
            "s3_eliminacion_incompleta",
        ),
        (
            {
                "list_object_versions": [{"Versions": [{"Key": "r/k", "VersionId": "v1"}]}],
                "delete_objects": {"Errors": [{"Key": "r/k", "Code": "AccessDenied"}]},
            },
            lambda a: a.eliminar_prefijo("r/"),
            "s3_eliminacion_incompleta",
        ),
    ],
    ids=[
        "url",
        "consulta_servicio",
        "consulta_red",
        "lectura",
        "escritura",
        "copia",
        "listar_versiones",
        "listar_prefijo",
        "multipartes",
        "borrado_parcial",
        "borrado_parcial_prefijo",
    ],
)
def test_errores_de_s3_son_codigos_tecnicos(
    comportamiento: dict[str, Any], llamada: Any, codigo: str
) -> None:
    almacen = AlmacenS3(ClienteS3Sustituto(**comportamiento), "atlas-bucket")
    with pytest.raises(ErrorIntegracion) as error:
        llamada(almacen)
    assert error.value.codigo == codigo
    assert "detalle del servicio" not in str(error.value)


def test_eliminar_solo_la_clave_exacta_del_prefijo() -> None:
    borrados: list[Any] = []

    class Cliente(ClienteS3Sustituto):
        def delete_objects(self, **parametros: Any) -> dict[str, Any]:
            borrados.append(parametros["Delete"]["Objects"])
            return {}

    almacen = AlmacenS3(
        Cliente(
            list_object_versions=[
                {"Versions": [{"Key": "k", "VersionId": "1"}, {"Key": "k-otra", "VersionId": "2"}]}
            ]
        ),
        "atlas-bucket",
    )
    assert almacen.eliminar_definitivamente("k") == 1
    assert borrados == [[{"Key": "k", "VersionId": "1"}]]


@pytest.mark.parametrize(
    ("excepcion", "codigo"),
    [
        (error_cliente("StateMachineDoesNotExist"), "sfn_inicio_rechazado"),
        (RED, "sfn_inicio_incierto"),
    ],
)
def test_inicio_incierto_queda_para_el_reconciliador(excepcion: Exception, codigo: str) -> None:
    orquestador = OrquestadorStepFunctions(ClienteS3Sustituto(start_execution=excepcion), "arn")
    with pytest.raises(ErrorIntegracion, match=codigo):
        orquestador.iniciar(1, 1)


def test_sin_endpoint_usa_la_cadena_de_credenciales_del_despliegue() -> None:
    configuracion = configuracion_sin_base(entorno="demo", aws_endpoint_url=None)
    s3 = crear_cliente(configuracion, "s3")
    assert s3.meta.endpoint_url == "https://s3.amazonaws.com"
    assert s3.meta.region_name == "us-east-1"


@pytest.mark.parametrize(
    ("excepcion", "error", "codigo"),
    [
        (
            ParamValidationError(report="parámetro inválido"),
            ErrorPermanente,
            "bedrock_parametros_invalidos",
        ),
        (
            EndpointConnectionError(endpoint_url="https://bedrock"),
            ErrorTransitorio,
            "bedrock_conexion",
        ),
    ],
)
def test_errores_locales_de_bedrock(
    excepcion: Exception, error: type[Exception], codigo: str
) -> None:
    modelo = ModeloBedrockConverse(ClienteS3Sustituto(converse=excepcion), "perfil")
    with pytest.raises(error, match=codigo):
        modelo.invocar_herramienta(
            instrucciones="x",
            contenido="y",
            herramienta=esquemas.herramienta_clasificacion(),
            max_tokens=10,
        )


@pytest.mark.parametrize(
    ("excepcion", "error", "codigo"),
    [
        (
            error_cliente("InvalidS3ObjectException"),
            ErrorPermanente,
            "textract_InvalidS3ObjectException",
        ),
        (
            EndpointConnectionError(endpoint_url="https://textract"),
            ErrorTransitorio,
            "textract_conexion",
        ),
    ],
)
def test_errores_de_textract(excepcion: Exception, error: type[Exception], codigo: str) -> None:
    analizador = AnalizadorTextract(
        ClienteS3Sustituto(start_document_analysis=excepcion), "atlas-bucket"
    )
    with pytest.raises(error, match=codigo):
        analizador.iniciar("k", 1, 1)


def test_resultado_de_textract_incompleto_es_fallo_permanente() -> None:
    textract = cliente("textract")
    with Stubber(textract) as stub:
        stub.add_response(
            "get_document_analysis",
            {"JobStatus": "PARTIAL_SUCCESS"},
            {"JobId": "j", "MaxResults": 1000},
        )
        with pytest.raises(ErrorPermanente, match="textract_incompleto"):
            AnalizadorTextract(textract, "atlas-bucket").resultado("j")
