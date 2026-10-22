"""Adaptadores de S3 y Step Functions contra moto, sin AWS (DT-AWS-01)."""

import json
import uuid

import httpx
import pytest

from atlas.configuracion import ErrorConfiguracion
from atlas.integraciones.aws import (
    AlmacenS3,
    OrquestadorStepFunctions,
    crear_cliente,
    nombre_ejecucion,
)
from atlas.integraciones.puertos import ErrorIntegracion
from tests.conftest import ARN_MAQUINA_PRUEBA, BUCKET_PRUEBA, configuracion_sin_base


@pytest.mark.parametrize(
    ("campos", "mensaje"),
    [
        ({"entorno": "demo"}, "En demo no se admite"),
        ({"aws_endpoint_url": "https://s3.amazonaws.com"}, "solo admite hosts locales"),
        ({"aws_endpoint_url": "http://moto.ejemplo.com:5000"}, "solo admite hosts locales"),
        ({"s3_bucket_documentos": None}, "ATLAS_S3_BUCKET_DOCUMENTOS"),
        ({"sfn_maquina_procesamiento_arn": None}, "ATLAS_SFN_MAQUINA_PROCESAMIENTO_ARN"),
    ],
)
def test_dt_aws_01_configuracion_de_servicios_invalida(
    campos: dict[str, object], mensaje: str
) -> None:
    with pytest.raises(ErrorConfiguracion, match=mensaje):
        configuracion_sin_base(**campos).validar_servicios_aws()


def test_dt_aws_01_demo_sin_endpoint_usa_aws_real() -> None:
    configuracion_sin_base(entorno="demo", aws_endpoint_url=None).validar_servicios_aws()


@pytest.fixture
def almacen(moto_local: str) -> AlmacenS3:
    configuracion = configuracion_sin_base(aws_endpoint_url=moto_local)
    return AlmacenS3(crear_cliente(configuracion, "s3"), BUCKET_PRUEBA)


@pytest.fixture
def cliente_sfn(moto_local: str) -> object:
    return crear_cliente(configuracion_sin_base(aws_endpoint_url=moto_local), "stepfunctions")


def test_rf_04_url_prefirmada_permite_transferir_y_leer(almacen: AlmacenS3) -> None:
    clave = f"tramites/1/cargas/{uuid.uuid4()}"
    url = almacen.url_carga(clave, "application/pdf", 60)
    assert almacen.metadatos(clave) is None
    respuesta = httpx.put(
        url, content=b"%PDF-1.7 ficticio", headers={"Content-Type": "application/pdf"}
    )
    assert respuesta.status_code == 200
    metadatos = almacen.metadatos(clave)
    assert metadatos is not None and metadatos.tamano_bytes == len(b"%PDF-1.7 ficticio")
    assert almacen.leer(clave) == b"%PDF-1.7 ficticio"


def test_dt_aws_01_bucket_inexistente_es_error_de_integracion(moto_local: str) -> None:
    configuracion = configuracion_sin_base(aws_endpoint_url=moto_local)
    ajeno = AlmacenS3(crear_cliente(configuracion, "s3"), "bucket-que-no-existe")
    with pytest.raises(ErrorIntegracion, match="s3_lectura_fallida"):
        ajeno.leer("x")


def test_rc_p08_ejecucion_con_nombre_de_trabajo_e_intento_y_solo_identificadores(
    cliente_sfn: object,
) -> None:
    trabajo_id = int(uuid.uuid4().int % 10**9)
    orquestador = OrquestadorStepFunctions(cliente_sfn, ARN_MAQUINA_PRUEBA)
    orquestador.iniciar(trabajo_id, 1)
    orquestador.iniciar(trabajo_id, 1)  # repetición del mismo intento: idempotente
    ejecuciones = [
        e
        for e in cliente_sfn.list_executions(stateMachineArn=ARN_MAQUINA_PRUEBA)["executions"]  # type: ignore[attr-defined]
        if e["name"] == nombre_ejecucion(trabajo_id, 1)
    ]
    assert len(ejecuciones) == 1
    detalle = cliente_sfn.describe_execution(executionArn=ejecuciones[0]["executionArn"])  # type: ignore[attr-defined]
    assert json.loads(detalle["input"]) == {"trabajo_id": trabajo_id, "intento": 1}
    assert nombre_ejecucion(trabajo_id, 2) == f"trabajo-{trabajo_id}-intento-2"


def test_rc_p08_maquina_inexistente_rechaza_el_inicio(cliente_sfn: object) -> None:
    orquestador = OrquestadorStepFunctions(
        cliente_sfn, "arn:aws:states:us-east-1:123456789012:stateMachine:no-existe"
    )
    with pytest.raises(ErrorIntegracion, match="sfn_inicio_rechazado"):
        orquestador.iniciar(1, 1)


def test_dt_aws_01_preparar_aws_local_es_idempotente_y_solo_local(
    moto_local: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from atlas.herramientas import preparar_aws_local

    configuracion = configuracion_sin_base(
        aws_endpoint_url=moto_local,
        s3_bucket_documentos=f"atlas-local-{uuid.uuid4().hex[:8]}",
        sfn_maquina_procesamiento_arn=(
            f"arn:aws:states:us-east-1:123456789012:stateMachine:local-{uuid.uuid4().hex[:8]}"
        ),
    )
    monkeypatch.setattr(preparar_aws_local, "obtener_configuracion", lambda: configuracion)
    assert preparar_aws_local.main() == 0
    assert preparar_aws_local.main() == 0
    reglas = crear_cliente(configuracion, "s3").get_bucket_cors(
        Bucket=configuracion.s3_bucket_documentos
    )["CORSRules"]
    assert set(reglas[0]["AllowedMethods"]) == {"PUT", "GET"}  # aplicación web local (WEB F7)
    sin_endpoint = configuracion.model_copy(update={"aws_endpoint_url": None})
    monkeypatch.setattr(preparar_aws_local, "obtener_configuracion", lambda: sin_endpoint)
    assert preparar_aws_local.main() == 1


def test_dt_aws_01_preparar_aws_local_con_configuracion_incompleta(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from atlas.herramientas import preparar_aws_local

    incompleta = configuracion_sin_base(s3_bucket_documentos=None)
    monkeypatch.setattr(preparar_aws_local, "obtener_configuracion", lambda: incompleta)
    assert preparar_aws_local.main() == 1
    assert "No se preparó" in capsys.readouterr().err
