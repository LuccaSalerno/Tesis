"""Fixtures comunes. Las pruebas de integración usan PostgreSQL + pgvector real.

Solo se aceptan bases de prueba: ATLAS_ENTORNO=tests y nombre terminado en
`_tests`, para que una configuración equivocada nunca migre ni modifique la
base de desarrollo o de demo (RC-P10, regla 8 de AGENTS.md).
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from moto.server import ThreadedMotoServer
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.pool import NullPool

from atlas.autenticacion.claves_locales import CLIENTE_LOCAL, EMISOR_LOCAL, ClavesLocales
from atlas.configuracion import Configuracion, ErrorConfiguracion
from atlas.integraciones.aws import crear_cliente
from atlas.integraciones.ciclo_vida_s3 import aplicar_ciclo_vida

RAIZ_BACKEND = Path(__file__).resolve().parents[1]

# Par de claves de la sesión de pruebas: firma los tokens con la forma de Cognito.
CLAVES_PRUEBA = ClavesLocales.generar()
BUCKET_PRUEBA = "atlas-documentos-pruebas"
ARN_MAQUINA_PRUEBA = (
    "arn:aws:states:us-east-1:123456789012:stateMachine:atlas-procesamiento-pruebas"
)
CONFIGURACION_JWT: dict[str, Any] = {
    "jwt_emisor": EMISOR_LOCAL,
    "jwt_cliente": CLIENTE_LOCAL,
    "jwt_jwks": json.dumps(CLAVES_PRUEBA.jwks()),
    "jwt_jwks_archivo": None,
    # Servicios AWS simulados (DT-AWS-01). Las pruebas unitarias no los contactan.
    "aws_region": "us-east-1",
    "aws_endpoint_url": "http://127.0.0.1:9",
    "s3_bucket_documentos": BUCKET_PRUEBA,
    "sfn_maquina_procesamiento_arn": ARN_MAQUINA_PRUEBA,
}


def configuracion_sin_base(**campos: Any) -> Configuracion:
    """Configuración para pruebas unitarias que no tocan la base.

    Todos los campos se fijan explícitamente para que las variables ATLAS_* del
    proceso (por ejemplo, las de la CI) no alteren el resultado.
    """
    valores: dict[str, Any] = {
        "entorno": "tests",
        "nivel_registro": "INFO",
        "bd_host": "localhost",
        "bd_puerto": 5432,
        "bd_nombre": "sin_base",
        "bd_usuario": "nadie",
        "bd_clave": None,
        "bd_usuario_migracion": None,
        "bd_clave_migracion": None,
        **CONFIGURACION_JWT,
    }
    valores.update(campos)
    return Configuracion(_env_file=None, **valores)


def cargar_configuracion_tests() -> Configuracion:
    configuracion = Configuracion(_env_file=RAIZ_BACKEND / ".env.tests")  # type: ignore[call-arg]
    if configuracion.entorno != "tests" or not configuracion.bd_nombre.endswith("_tests"):
        raise ErrorConfiguracion(
            "Las pruebas de integración solo corren con ATLAS_ENTORNO=tests sobre una base *_tests"
        )
    return configuracion


def configuracion_alembic(configuracion: Configuracion) -> Config:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.attributes["configuracion"] = configuracion
    return config


def lineas_registro(salida: str) -> list[dict[str, Any]]:
    return [json.loads(linea) for linea in salida.splitlines() if linea.startswith("{")]


@pytest.fixture(scope="session")
def moto_local() -> Iterator[str]:
    """Servidor moto efímero dentro de pytest (DT-AWS-01): S3 y Step Functions sin AWS.

    Atiende las URL prefirmadas por HTTP, como lo haría S3 con el navegador.
    """
    servidor = ThreadedMotoServer(ip_address="127.0.0.1", port=0, verbose=False)
    servidor.start()
    host, puerto = servidor.get_host_and_port()
    endpoint = f"http://{host}:{puerto}"
    configuracion = configuracion_sin_base(aws_endpoint_url=endpoint)
    s3 = crear_cliente(configuracion, "s3")
    s3.create_bucket(Bucket=BUCKET_PRUEBA)
    s3.put_bucket_versioning(Bucket=BUCKET_PRUEBA, VersioningConfiguration={"Status": "Enabled"})
    aplicar_ciclo_vida(s3, BUCKET_PRUEBA)
    crear_cliente(configuracion, "stepfunctions").create_state_machine(
        name=ARN_MAQUINA_PRUEBA.rsplit(":", 1)[1],
        definition=json.dumps({"StartAt": "Fin", "States": {"Fin": {"Type": "Succeed"}}}),
        roleArn="arn:aws:iam::123456789012:role/atlas-procesamiento-pruebas",
    )
    yield endpoint
    servidor.stop()


@pytest.fixture(scope="session")
def configuracion_tests(moto_local: str) -> Configuracion:
    return cargar_configuracion_tests().model_copy(
        update={**CONFIGURACION_JWT, "aws_endpoint_url": moto_local}
    )


@pytest.fixture(scope="session")
def motor_migracion(configuracion_tests: Configuracion) -> Iterator[Engine]:
    motor = create_engine(configuracion_tests.url_migracion(), poolclass=NullPool)
    yield motor
    motor.dispose()


@pytest.fixture(scope="session")
def motor_aplicacion(configuracion_tests: Configuracion) -> Iterator[Engine]:
    motor = create_engine(configuracion_tests.url_aplicacion(), poolclass=NullPool)
    yield motor
    motor.dispose()


@pytest.fixture(scope="session")
def base_migrada(configuracion_tests: Configuracion) -> Configuracion:
    """Lleva `atlas_tests` a la última revisión antes de las pruebas del modelo."""
    command.upgrade(configuracion_alembic(configuracion_tests), "head")
    return configuracion_tests


def _conexion_revertida(motor: Engine) -> Iterator[Connection]:
    with motor.connect() as conexion:
        transaccion = conexion.begin()
        try:
            yield conexion
        finally:
            transaccion.rollback()


@pytest.fixture
def conexion_aplicacion(
    base_migrada: Configuracion, motor_aplicacion: Engine
) -> Iterator[Connection]:
    """Conexión del usuario de aplicación dentro de una transacción que se revierte.

    La aplicación no puede borrar (RNF-04); revertir es la única limpieza posible.
    """
    yield from _conexion_revertida(motor_aplicacion)


@pytest.fixture
def conexion_migracion(
    base_migrada: Configuracion, motor_migracion: Engine
) -> Iterator[Connection]:
    """Conexión del usuario de migración (propietario) en una transacción que se revierte."""
    yield from _conexion_revertida(motor_migracion)


@pytest.fixture
def base_reiniciada(configuracion_tests: Configuracion) -> Configuracion:
    """Esquema recreado desde cero: para operaciones que exigen una base sin cuentas."""
    config = configuracion_alembic(configuracion_tests)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return configuracion_tests
