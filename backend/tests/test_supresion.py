"""Supresión de cuentas (RF-25, §5.4.2, §5.4.3, DO-2026-10-23-CIERRE P6, P7 y P9).

La API contra PostgreSQL real con un proveedor de identidad sustituto; la Lambda `cuentas`
contra Cognito simulado por moto. Cuentas ficticias (AGENTS.md §2.4).
"""

import io
import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from atlas.configuracion import Configuracion, ErrorConfiguracion
from atlas.integraciones.identidades import GestorIdentidadesLambda, GestorIdentidadesLocal
from atlas.integraciones.puertos import ErrorIntegracion
from atlas.operacion import lambda_cuentas
from atlas.principal import _gestor_identidades, crear_aplicacion
from tests.conftest import configuracion_sin_base
from tests.flujo_revision import (
    Equipo,
    decidida,
    equipo,
    evidencia,
    iniciar_ciclo,
    obtener,
    plantilla_de_contratos,
    tramite_con_conjunto,
)

pytestmark = pytest.mark.integracion


@dataclass
class GestorFijo:
    suprimidos: list[str] = field(default_factory=list)
    falla: bool = False

    def suprimir(self, identificador_externo: str) -> None:
        if self.falla:
            raise ErrorIntegracion("cognito_supresion_fallida")
        self.suprimidos.append(identificador_externo)


@pytest.fixture
def gestor() -> GestorFijo:
    return GestorFijo()


@pytest.fixture
def e(
    base_migrada: Configuracion, motor_aplicacion: Engine, gestor: GestorFijo
) -> Iterator[Equipo]:
    aplicacion = crear_aplicacion(base_migrada)
    aplicacion.state.gestor_identidades = gestor
    with TestClient(aplicacion) as cliente:
        actual = equipo(cliente, motor_aplicacion)
        plantilla_de_contratos(actual)
        yield actual
    aplicacion.state.motor.dispose()


def suprimir(e: Equipo, usuario_id: int, ctx: Any = None) -> Any:
    quien = ctx or e.administrador
    return e.cliente.post(f"/usuarios/{usuario_id}/supresion", headers=quien.encabezados)


def _sub(motor: Engine, usuario_id: int) -> str | None:
    with motor.connect() as conexion:
        valor: str | None = conexion.execute(
            text("SELECT identificador_externo FROM atlas.usuario WHERE id = :u"),
            {"u": usuario_id},
        ).scalar_one()
        return valor


# --- Supresión (RF-25, P6) --------------------------------------------------------------


def test_rf_25_suprimir_desvincula_los_datos_identificatorios(
    e: Equipo, gestor: GestorFijo
) -> None:
    revisor = e.revisor.usuario_id
    sub = _sub(e.revisor.motor, revisor)
    e.cliente.put(
        f"/usuarios/{revisor}/nombre",
        json={"nombre_visible": "Martín Ríos"},
        headers=e.administrador.encabezados,
    )
    respuesta = suprimir(e, revisor)
    assert respuesta.status_code == 200, respuesta.text
    cuenta = respuesta.json()
    assert cuenta["estado"] == "suprimida"
    assert (cuenta["identificador_externo"], cuenta["nombre_visible"]) == (None, None)
    assert (cuenta["roles"], cuenta["autorizacion_cierre"]) == ([], False)
    assert gestor.suprimidos == [sub]  # primero el proveedor de identidad (P7)
    with e.revisor.motor.connect() as conexion:
        accion = conexion.execute(
            text(
                "SELECT accion FROM atlas.evento_auditoria"
                " WHERE entidad_tipo = 'usuario' AND entidad_id = :u ORDER BY id DESC LIMIT 1"
            ),
            {"u": revisor},
        ).scalar_one()
    assert accion == "cuenta_suprimida"


def test_rf_25_las_intervenciones_conservan_el_identificador_interno(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    decision = decidida(e.revisor, ciclo["tareas"][0]["id"])
    antes = evidencia(e.responsable, decision["id"])
    assert suprimir(e, e.revisor.usuario_id).status_code == 200
    despues = evidencia(e.responsable, decision["id"])
    assert despues["decision"] == antes["decision"]
    assert despues["decision"]["actor_id"] == e.revisor.usuario_id
    directorio = obtener(e.responsable, f"/usuarios/directorio?ids={e.revisor.usuario_id}")
    assert directorio == [{"id": e.revisor.usuario_id, "nombre_visible": None, "suprimida": True}]
    # La tarea del suprimido ya estaba decidida y la abierta es del aprobador habilitado:
    # nada de este trámite queda por reasignar (P4).
    bloqueadas = obtener(e.administrador, "/administracion/estado-general")["tareas_bloqueadas"]
    assert all(t["tramite_id"] != ids["tramite"] for t in bloqueadas)


def test_rf_25_la_cuenta_suprimida_ya_no_ingresa(e: Equipo) -> None:
    assert suprimir(e, e.revisor.usuario_id).status_code == 200
    respuesta = e.cliente.get("/usuarios/yo", headers=e.revisor.encabezados)
    assert respuesta.status_code in (401, 403)
    assert e.cliente.get("/tareas", headers=e.revisor.encabezados).status_code in (401, 403)


def test_rf_25_la_supresion_es_irreversible(e: Equipo) -> None:
    usuario = e.revisor.usuario_id
    assert suprimir(e, usuario).status_code == 200
    admin = e.administrador.encabezados
    assert suprimir(e, usuario).status_code == 409
    for respuesta in (
        e.cliente.put(f"/usuarios/{usuario}/estado", json={"estado": "habilitada"}, headers=admin),
        e.cliente.put(f"/usuarios/{usuario}/roles/revisor_aprobador", headers=admin),
        e.cliente.put(
            f"/usuarios/{usuario}/nombre", json={"nombre_visible": "Otra"}, headers=admin
        ),
    ):
        assert respuesta.status_code == 409


def test_rf_25_las_tareas_abiertas_del_suprimido_se_senalan(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    assert suprimir(e, e.revisor.usuario_id).status_code == 200
    bloqueadas = obtener(e.administrador, "/administracion/estado-general")["tareas_bloqueadas"]
    assert {
        "tarea_id": ciclo["tareas"][0]["id"],
        "tramite_id": ids["tramite"],
        "asignada_a_id": e.revisor.usuario_id,
    } in bloqueadas


def test_rnf_01_solo_el_administrador_suprime_y_no_a_si_mismo(
    e: Equipo, gestor: GestorFijo
) -> None:
    for ctx in (e.responsable, e.revisor, e.aprobador):
        assert suprimir(e, e.aprobador.usuario_id, ctx).status_code == 403
    respuesta = suprimir(e, e.administrador.usuario_id)
    assert respuesta.status_code == 409
    assert suprimir(e, 999_999_999).status_code == 404
    assert gestor.suprimidos == []


def test_rf_25_si_falla_el_proveedor_la_cuenta_no_cambia(e: Equipo, gestor: GestorFijo) -> None:
    gestor.falla = True
    respuesta = suprimir(e, e.revisor.usuario_id)
    assert respuesta.status_code == 503
    cuenta = obtener(e.administrador, f"/usuarios/{e.revisor.usuario_id}")
    assert cuenta["estado"] == "habilitada" and cuenta["identificador_externo"] is not None


# --- Adaptadores (P7, P9) ---------------------------------------------------------------


@dataclass
class ClienteLambdaFijo:
    payload: dict[str, Any]
    error_funcion: bool = False
    falla: Exception | None = None
    llamadas: list[dict[str, Any]] = field(default_factory=list)

    def invoke(self, **parametros: Any) -> dict[str, Any]:
        self.llamadas.append(parametros)
        if self.falla is not None:
            raise self.falla
        respuesta: dict[str, Any] = {"Payload": io.BytesIO(json.dumps(self.payload).encode())}
        if self.error_funcion:
            respuesta["FunctionError"] = "Unhandled"
        return respuesta


def test_p7_el_adaptador_invoca_la_lambda_con_el_sub() -> None:
    cliente = ClienteLambdaFijo({"resultado": "completada", "eliminada": True})
    GestorIdentidadesLambda(cliente, "atlas-cuentas").suprimir("sub-1")
    (llamada,) = cliente.llamadas
    assert llamada["FunctionName"] == "atlas-cuentas"
    assert llamada["InvocationType"] == "RequestResponse"
    assert json.loads(llamada["Payload"]) == {"accion": "suprimir", "sub": "sub-1"}


@pytest.mark.parametrize(
    ("cliente", "codigo"),
    [
        (ClienteLambdaFijo({"resultado": "fallida"}), "cognito_supresion_fallida"),
        (ClienteLambdaFijo({}, error_funcion=True), "cognito_supresion_fallida"),
        (
            ClienteLambdaFijo({}, falla=ClientError({"Error": {"Code": "AccessDenied"}}, "Invoke")),
            "cognito_supresion_incierta",
        ),
    ],
)
def test_p7_el_adaptador_informa_las_fallas(cliente: ClienteLambdaFijo, codigo: str) -> None:
    with pytest.raises(ErrorIntegracion) as error:
        GestorIdentidadesLambda(cliente, "atlas-cuentas").suprimir("sub-1")
    assert error.value.codigo == codigo


def test_p9_sin_lambda_solo_fuera_de_demo() -> None:
    assert isinstance(_gestor_identidades(configuracion_sin_base()), GestorIdentidadesLocal)
    assert GestorIdentidadesLocal().suprimir("sub-1") is None
    with pytest.raises(ErrorConfiguracion):
        _gestor_identidades(configuracion_sin_base(entorno="demo"))
    configurada = configuracion_sin_base(cuentas_funcion="atlas-cuentas")
    assert isinstance(_gestor_identidades(configurada), GestorIdentidadesLambda)


# --- Lambda `cuentas` contra Cognito simulado (P7) --------------------------------------


@pytest.fixture
def cognito(moto_local: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Any, str]]:
    """Cognito del moto de la sesión de pruebas (sin `mock_aws`, que reiniciaría su estado)."""
    cliente = boto3.client(
        "cognito-idp",
        region_name="us-east-1",
        endpoint_url=moto_local,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    grupo = cliente.create_user_pool(PoolName=f"atlas-{uuid.uuid4()}")["UserPool"]["Id"]
    monkeypatch.setenv("ATLAS_COGNITO_GRUPO_USUARIOS", grupo)
    monkeypatch.setattr(lambda_cuentas, "_cliente", lambda: cliente)
    yield cliente, grupo
    cliente.delete_user_pool(UserPoolId=grupo)


def _alta(cliente: Any, grupo: str, usuario: str) -> str:
    atributos = cliente.admin_create_user(UserPoolId=grupo, Username=usuario)["User"]
    return next(a["Value"] for a in atributos["Attributes"] if a["Name"] == "sub")


def test_p7_la_lambda_elimina_la_cuenta_por_su_sub(
    cognito: tuple[Any, str], capsys: pytest.CaptureFixture[str]
) -> None:
    cliente, grupo = cognito
    sub = _alta(cliente, grupo, "revisor-ficticio")
    otro = _alta(cliente, grupo, "aprobador-ficticio")
    respuesta = lambda_cuentas.manejar({"accion": "suprimir", "sub": sub}, None)
    assert respuesta == {"resultado": "completada", "eliminada": True}
    restantes = [u["Username"] for u in cliente.list_users(UserPoolId=grupo)["Users"]]
    assert restantes == ["aprobador-ficticio"]
    # Idempotente: una segunda supresión no encuentra la cuenta y no es un error.
    repetida = lambda_cuentas.manejar({"accion": "suprimir", "sub": sub}, None)
    assert repetida == {"resultado": "completada", "eliminada": False}
    salida = capsys.readouterr().out
    assert sub not in salida and otro not in salida and "revisor-ficticio" not in salida


@pytest.mark.parametrize(
    "evento",
    [
        {"accion": "suprimir", "sub": 'x" or sub = "y'},
        {"accion": "suprimir"},
        {"accion": "deshabilitar", "sub": str(uuid.uuid4())},
    ],
)
def test_p7_la_lambda_rechaza_eventos_fuera_de_contrato(
    cognito: tuple[Any, str], evento: dict[str, Any]
) -> None:
    assert lambda_cuentas.manejar(evento, None) == {"resultado": "rechazada"}


def test_p7_la_lambda_informa_la_falla_de_cognito(
    cognito: tuple[Any, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fallar(*_: Any, **__: Any) -> None:
        raise ClientError({"Error": {"Code": "AccessDenied"}}, "ListUsers")

    monkeypatch.setattr(lambda_cuentas, "suprimir", fallar)
    respuesta = lambda_cuentas.manejar({"accion": "suprimir", "sub": str(uuid.uuid4())}, None)
    assert respuesta == {"resultado": "fallida"}


def test_p7_carrera_la_cuenta_desaparece_entre_buscar_y_eliminar() -> None:
    class Cliente:
        def list_users(self, **_: Any) -> dict[str, Any]:
            return {"Users": [{"Username": "x"}]}

        def admin_delete_user(self, **_: Any) -> None:
            raise ClientError({"Error": {"Code": "UserNotFoundException"}}, "AdminDeleteUser")

    assert lambda_cuentas.suprimir(Cliente(), "grupo", "sub") is False

    class Denegado(Cliente):
        def admin_delete_user(self, **_: Any) -> None:
            raise ClientError({"Error": {"Code": "AccessDenied"}}, "AdminDeleteUser")

    with pytest.raises(ClientError):
        lambda_cuentas.suprimir(Denegado(), "grupo", "sub")


def test_p7_cliente_de_cognito_en_la_region_del_despliegue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_AWS_REGION", "us-east-1")
    lambda_cuentas._cliente.cache_clear()
    try:
        assert lambda_cuentas._cliente().meta.region_name == "us-east-1"
    finally:
        lambda_cuentas._cliente.cache_clear()
