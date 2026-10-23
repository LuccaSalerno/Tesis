"""Ejecutor de seguridad de §6.3.3 contra la aplicación local (DO-2026-10-23-SEG, P12).

El escenario se arma por la API con cuentas y documentos sintéticos; la matriz de la Tabla
3.II, el acceso directo por identificador, la consulta cruzada, la inmutabilidad del historial
y el caso adversarial se ejecutan con tolerancia cero. Es el nivel A (CI); el nivel B corre la
misma matriz contra la API desplegada en una sesión AWS.
"""

import json
import uuid
from collections.abc import Iterator, Mapping
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
from atlas.evaluacion.seguridad import escenario as esc
from atlas.evaluacion.seguridad import matriz
from atlas.herramientas.cliente_api import ClienteApi
from atlas.principal import crear_aplicacion
from tests.conftest import CLAVES_PRUEBA
from tests.datos import crear_cuenta
from tests.procesamiento_fijo import EmbeddingsFijos, ModeloConsultaFijo

BASE = "http://testserver"


@pytest.fixture
def cliente(base_migrada: Configuracion) -> Iterator[TestClient]:
    aplicacion = crear_aplicacion(base_migrada)
    aplicacion.state.embeddings = EmbeddingsFijos()
    aplicacion.state.modelo_generativo = ModeloConsultaFijo(buscar="Monto")
    with TestClient(aplicacion) as cliente:
        yield cliente
    aplicacion.state.motor.dispose()


def _transporte(cliente: TestClient) -> Any:
    def transporte(
        metodo: str, url: str, encabezados: Mapping[str, str], cuerpo: bytes | None
    ) -> tuple[int, bytes]:
        if url.startswith(BASE):
            respuesta = cliente.request(
                metodo, url.removeprefix(BASE), headers=dict(encabezados), content=cuerpo
            )
        else:  # URL prefirmada de moto: como el navegador, directo al almacenamiento
            respuesta = httpx.request(metodo, url, headers=dict(encabezados), content=cuerpo)
        return respuesta.status_code, respuesta.content

    return transporte


def _tokens(motor: Engine) -> dict[str, str | None]:
    _, sub_admin = crear_cuenta(motor, "administrador_operativo")
    tokens: dict[str, str | None] = {esc.ADMINISTRADOR: CLAVES_PRUEBA.emitir(sub_admin)}
    for actor in esc.ROLES:
        tokens[actor] = CLAVES_PRUEBA.emitir(f"sub-seg-{actor}-{uuid.uuid4()}")
    tokens[esc.SIN_TOKEN] = None
    return tokens


def _solicitar(cliente: TestClient) -> matriz.Solicitar:
    def solicitar(metodo: str, ruta: str, token: str | None, cuerpo: Any) -> tuple[int, str]:
        encabezados = {"Authorization": f"Bearer {token}"} if token else {}
        if cuerpo is not None:
            encabezados["Content-Type"] = "application/json"
        respuesta = cliente.request(
            metodo,
            ruta,
            headers=encabezados,
            content=None if cuerpo is None else json.dumps(cuerpo),
        )
        return respuesta.status_code, respuesta.text

    return solicitar


@pytest.mark.integracion
def test_seg_01_03_rnf_08_matriz_completa_sin_fallas(
    cliente: TestClient, motor_aplicacion: Engine
) -> None:
    tokens = _tokens(motor_aplicacion)
    api = ClienteApi(BASE, {k: v for k, v in tokens.items() if v}, transporte=_transporte(cliente))
    escenario = esc.construir(api)
    ejecucion = matriz.Ejecucion(_solicitar(cliente), tokens, escenario)
    filas = ejecucion.todo()
    resultado = matriz.resumen(filas)
    assert resultado["fallas"] == [], json.dumps(resultado["fallas"], ensure_ascii=False, indent=1)
    assert resultado["cumple"] and resultado["casos"] > 150
    assert resultado["no_implementadas"] == []  # DO-2026-10-23-VER y CIERRE
    # Cada operación de la matriz se probó con los ocho actores.
    for caso in matriz.CASOS:
        actores = {f["actor"] for f in filas if f["caso"] == caso.codigo}
        esperados = set(esc.ACTORES) - (caso.permitidos if not caso.positivo else set())
        assert actores == esperados, caso.codigo


# --- Nivel B: línea de comandos contra la aplicación local y verificaciones de AWS --------


class EntornoLocal:
    """El mismo flujo de la sesión AWS, con la aplicación local en lugar de API Gateway."""

    def __init__(self, cliente: TestClient, tokens: dict[str, str | None]) -> None:
        self.cliente = cliente
        self._tokens = tokens
        self.esperar = None
        self.aws: dict[str, Any] = {}

    def envio(
        self, metodo: str, url: str, encabezados: dict[str, str], cuerpo: bytes | None
    ) -> Any:
        respuesta = self.cliente.request(
            metodo, url.removeprefix(BASE), headers=encabezados, content=cuerpo
        )
        return respuesta.status_code, dict(respuesta.headers), respuesta.content

    def tokens(self, m: dict[str, Any]) -> dict[str, str | None]:
        return self._tokens

    def api(self, m: dict[str, Any], tokens: dict[str, str | None]) -> ClienteApi:
        return ClienteApi(
            BASE, {k: v for k, v in tokens.items() if v}, transporte=_transporte(self.cliente)
        )

    def cliente_aws(self, servicio: str, region: str) -> Any:
        return self.aws[servicio]


@pytest.mark.integracion
def test_seg_nivel_b_linea_de_comandos(
    cliente: TestClient, motor_aplicacion: Engine, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from atlas.evaluacion import campana as cmp
    from atlas.evaluacion.seguridad import __main__ as cli

    monkeypatch.setattr(cli, "DIRECTORIO", tmp_path)
    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": "abc", "cambios_sin_commit": False})
    entorno = EntornoLocal(cliente, _tokens(motor_aplicacion))
    entorno.aws = aws_simulado(fallas=False)
    inicio = [
        "iniciar",
        "--campana",
        "s1",
        "--url-api",
        BASE,
        "--cliente-cognito",
        "c",
        "--bucket",
        "atlas-demo-documentos",
        "--maquina",
        "arn:maquina",
    ]
    assert cli.main(inicio, entorno) == 0  # type: ignore[arg-type]
    assert cli.main(inicio, entorno) == 1  # type: ignore[arg-type]
    for paso in ("escenario", "matriz", "configuracion", "marcadores", "informe"):
        assert cli.main([paso, "--campana", "s1"], entorno) == 0, paso  # type: ignore[arg-type]
    assert cli.main(["escenario", "--campana", "s1"], entorno) == 1  # type: ignore[arg-type]
    informe = (tmp_path / "s1" / "informe.md").read_text("utf-8")
    assert "SEG-01, SEG-03 y RNF-08: Cumple" in informe
    assert "No cumple" not in informe and "| s3_solo_tls | Cumple |" in informe
    (tmp_path / "otra").mkdir()
    (tmp_path / "otra" / "manifiesto.json").write_text('{"tipo": "api"}', "utf-8")
    assert cli.main(["matriz", "--campana", "otra"], entorno) == 1  # type: ignore[arg-type]


class _Paginador:
    def __init__(self, paginas: list[dict[str, Any]]) -> None:
        self.paginas = paginas

    def paginate(self, **_: Any) -> list[dict[str, Any]]:
        return self.paginas


def aws_simulado(*, fallas: bool) -> dict[str, Any]:
    """Respuestas de solo lectura con la forma de boto3; `fallas` arma una cuenta mal
    configurada."""
    from datetime import UTC, datetime
    from types import SimpleNamespace

    def ns(**metodos: Any) -> Any:
        return SimpleNamespace(**{k: (lambda v=v, **_: v) for k, v in metodos.items()})

    politica = {
        "Statement": []
        if fallas
        else [{"Effect": "Deny", "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]
    }
    variables = {"ATLAS_ENTORNO": "demo", "ATLAS_OPS_SECRETO_MAESTRO_ARN": "arn"} | (
        {"ATLAS_BD_CLAVE": "x"} if fallas else {}
    )
    s3 = ns(
        get_bucket_encryption={
            "ServerSideEncryptionConfiguration": {
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            }
        },
        get_bucket_policy={"Policy": json.dumps(politica)},
        get_public_access_block={
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "RestrictPublicBuckets": not fallas,
            }
        },
    )
    rds = ns(
        describe_db_instances={
            "DBInstances": [
                {
                    "StorageEncrypted": True,
                    "PubliclyAccessible": fallas,
                    "DBParameterGroups": [{"DBParameterGroupName": "g"}],
                }
            ]
        },
        describe_db_parameters={
            "Parameters": [{"ParameterName": "rds.force_ssl", "ParameterValue": "1"}]
        },
    )
    eventos = [{"message": "x"}] if fallas else []
    logs = SimpleNamespace(
        describe_log_groups=lambda **_: {"logGroups": [{"retentionInDays": 7}]},
        get_paginator=lambda _: SimpleNamespace(
            paginate=lambda **k: [
                {
                    "events": [{"m": 1}]
                    if "correlacion" in k["filterPattern"]
                    or "solicitud_atendida" in k["filterPattern"]
                    or "trabajo_id" in k["filterPattern"]
                    else eventos
                }
            ]
        ),
    )
    ahora = datetime.now(UTC)
    sfn = SimpleNamespace(
        get_paginator=lambda nombre: _Paginador(
            [
                {
                    "executions": [
                        {
                            "executionArn": "e1",
                            "startDate": ahora.replace(year=ahora.year + 1),
                            "status": "FAILED",
                        }
                    ]
                }
            ]
            if nombre == "list_executions"
            else [{"events": [{"input": "SEGMARCAA1" if fallas else "trabajo 1"}]}]
        )
    )
    return {
        "s3": s3,
        "rds": rds,
        "lambda": ns(get_function_configuration={"Environment": {"Variables": variables}}),
        "logs": logs,
        "bedrock": ns(
            get_model_invocation_logging_configuration={"loggingConfig": {"x": 1}} if fallas else {}
        ),
        "ec2": ns(
            describe_vpc_endpoints={
                "VpcEndpoints": [{"ServiceName": "com.amazonaws.us-east-1.states"}]
            }
        ),
        "stepfunctions": sfn,
    }


def test_seg_02_04_detectan_una_cuenta_mal_configurada() -> None:
    from datetime import UTC, datetime

    from atlas.evaluacion.seguridad import aws

    cuenta = aws_simulado(fallas=True)
    configuracion = {
        v["verificacion"]: v["cumple"]
        for v in aws.configuracion(cuenta.__getitem__, prefijo="atlas-demo", bucket="b", rds="r")
    }
    assert not configuracion["s3_solo_tls"] and not configuracion["s3_bloqueo_publico"]
    assert (
        not configuracion["rds_sin_acceso_publico"] and not configuracion["lambda_api_sin_secretos"]
    )
    assert (
        not configuracion["bedrock_sin_registro_de_invocaciones"]
        and configuracion["sin_endpoint_secrets_manager"]
    )
    marcadores = aws.buscar_marcadores(
        cuenta.__getitem__,
        prefijo="atlas-demo",
        maquina_arn="arn",
        marcadores=["SEGMARCAA1"],
        desde=datetime.now(UTC),
    )
    resultado = {v["verificacion"]: v["cumple"] for v in marcadores}
    assert (
        not resultado["logs_api_sin_SEGMARCAA1"] and not resultado["stepfunctions_sin_marcadores"]
    )
    assert resultado["logs_api_con_correlacion"] and resultado["camino_de_error_ejercitado"]


def test_p3_espera_del_procesamiento_real() -> None:
    from itertools import chain, repeat

    en_curso = [{"id": 7, "trabajo": {"estado": "en_ejecucion"}}]
    llamadas = chain([en_curso, [{"id": 7, "trabajo": {"estado": "completado"}}]], repeat(en_curso))

    class Api:
        def get(self, ruta: str, rol: str) -> Any:
            return next(llamadas)

    esc.esperar_trabajo(Api(), esc.DUENO, 1, 7, dormir=lambda _: None)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="procesamiento_sin_terminar"):
        esc.esperar_trabajo(Api(), esc.DUENO, 1, 8, dormir=lambda _: None, maximo_s=-1)  # type: ignore[arg-type]


def test_seg_entorno_real_arma_tokens_y_clientes(monkeypatch: pytest.MonkeyPatch) -> None:
    from atlas.evaluacion.seguridad import __main__ as cli

    monkeypatch.setattr(
        cli, "tokens_cognito", lambda _r, _c, usuarios: {c: f"t-{u}" for c, u in usuarios.items()}
    )
    entorno = cli.Entorno()
    m = {"region": "us-east-1", "cliente_cognito": "c", "url_api": "https://api.ejemplo"}
    tokens = entorno.tokens(m)
    assert tokens[esc.AJENO] == "t-atlas-responsable-2" and tokens[esc.SIN_TOKEN] is None
    assert esc.SIN_TOKEN not in entorno.api(m, tokens).tokens
    assert entorno.cliente_aws("logs", "us-east-1").meta.region_name == "us-east-1"
