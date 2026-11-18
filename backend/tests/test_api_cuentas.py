"""Hito 1.2: autenticación, autorización por rol y cuentas con auditoría, contra PostgreSQL real.

RF-01, RF-02, RF-21, RF-25, RN-01, RNF-01.
"""

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from atlas.api.middleware import CABECERA_SOLICITUD
from atlas.configuracion import Configuracion
from atlas.herramientas import inicializar_administrador
from atlas.principal import crear_aplicacion
from tests.conftest import CLAVES_PRUEBA, lineas_registro
from tests.datos import crear_cuenta, portador

pytestmark = pytest.mark.integracion

ADMIN = "administrador_operativo"
RESPONSABLE = "responsable_tramite"
REVISOR = "revisor_aprobador"


def eventos(motor: Engine, usuario_id: int) -> list[dict[str, Any]]:
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT accion, actor_id, actor_tipo, resultado, solicitud_id, tramite_id"
                " FROM atlas.evento_auditoria WHERE entidad_tipo = 'usuario' AND entidad_id = :u"
                " ORDER BY id"
            ),
            {"u": usuario_id},
        ).mappings()
        return [dict(f) for f in filas]


@pytest.fixture
def administrador(motor_aplicacion: Engine) -> tuple[int, dict[str, str]]:
    usuario_id, sub = crear_cuenta(motor_aplicacion, ADMIN)
    return usuario_id, portador(sub)


# --- RF-01, RN-01: autenticación y habilitación en cada solicitud -------------------


@pytest.mark.parametrize(
    "encabezados",
    [
        {},
        {"Authorization": "Bearer no-es-un-jwt"},
        {"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="},
    ],
    ids=["sin_token", "token_invalido", "esquema_basic"],
)
def test_rf_01_sin_token_valido_responde_401(
    cliente: TestClient, encabezados: dict[str, str]
) -> None:
    respuesta = cliente.get("/usuarios/yo", headers=encabezados)
    assert respuesta.status_code == 401
    assert respuesta.json() == {"detalle": "No autenticado"}
    assert respuesta.headers["www-authenticate"] == "Bearer"


def test_rnf_03_rechazo_registra_motivo_sin_el_token(
    cliente: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    token = CLAVES_PRUEBA.emitir("sub-vencido", vigencia_s=-5)
    cliente.get("/usuarios/yo", headers={"Authorization": f"Bearer {token}"})
    salida = capsys.readouterr().out
    (rechazo,) = [r for r in lineas_registro(salida) if r["evento"] == "autenticacion_rechazada"]
    assert rechazo["codigo_error"] == "token_vencido"
    assert token not in salida
    assert "sub-vencido" not in salida


def test_rn_01_token_valido_de_cuenta_no_registrada_responde_403(cliente: TestClient) -> None:
    respuesta = cliente.get("/usuarios/yo", headers=portador(f"sub-{uuid.uuid4()}"))
    assert respuesta.status_code == 403
    assert respuesta.json() == {"detalle": "Operación no permitida"}


@pytest.mark.parametrize("estado", ["deshabilitada", "suprimida"])
def test_rn_01_cuenta_no_habilitada_responde_403_con_token_vigente(
    cliente: TestClient, motor_aplicacion: Engine, estado: str
) -> None:
    _, sub = crear_cuenta(motor_aplicacion, ADMIN)
    encabezados = portador(sub)  # token emitido mientras la cuenta estaba habilitada
    with motor_aplicacion.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE atlas.usuario SET estado = :e, identificador_externo ="
                " CASE WHEN CAST(:e AS varchar) = 'suprimida' THEN NULL"
                " ELSE identificador_externo END"
                " WHERE identificador_externo = :s"
            ),
            {"e": estado, "s": sub},
        )
    assert cliente.get("/usuarios/yo", headers=encabezados).status_code == 403


def test_rf_01_cuenta_propia(cliente: TestClient, motor_aplicacion: Engine) -> None:
    usuario_id, sub = crear_cuenta(motor_aplicacion, REVISOR, autorizacion_cierre=True)
    respuesta = cliente.get("/usuarios/yo", headers=portador(sub))
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": usuario_id,
        "roles": [REVISOR],
        "autorizacion_cierre": True,
        "nombre_visible": None,
    }


# --- RF-02, RNF-01: matriz de autorización de las operaciones de cuentas -----------

OPERACIONES_DE_ADMINISTRACION = [
    ("GET", "/usuarios", None),
    ("POST", "/usuarios", {"identificador_externo": "sub-matriz"}),
    ("GET", "/usuarios/{id}", None),
    ("PUT", "/usuarios/{id}/estado", {"estado": "deshabilitada"}),
    ("PUT", "/usuarios/{id}/roles/responsable_tramite", None),
    ("DELETE", "/usuarios/{id}/roles/revisor_aprobador", None),
    ("PUT", "/usuarios/{id}/autorizacion-cierre", {"otorgada": True}),
]


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), OPERACIONES_DE_ADMINISTRACION)
@pytest.mark.parametrize(
    "roles",
    [(), (RESPONSABLE,), (REVISOR,), (RESPONSABLE, REVISOR)],
    ids=["sin_roles", "responsable", "revisor", "responsable_y_revisor"],
)
def test_rnf_01_administracion_de_cuentas_denegada_sin_rol_de_administrador(
    cliente: TestClient,
    motor_aplicacion: Engine,
    metodo: str,
    ruta: str,
    cuerpo: dict[str, Any] | None,
    roles: tuple[str, ...],
) -> None:
    objetivo, _ = crear_cuenta(motor_aplicacion, REVISOR)
    _, sub = crear_cuenta(motor_aplicacion, *roles)
    antes = eventos(motor_aplicacion, objetivo)
    respuesta = cliente.request(
        metodo, ruta.format(id=objetivo), json=cuerpo, headers=portador(sub)
    )
    assert respuesta.status_code == 403
    assert eventos(motor_aplicacion, objetivo) == antes


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), OPERACIONES_DE_ADMINISTRACION)
def test_rnf_01_administracion_de_cuentas_permitida_al_administrador(
    cliente: TestClient,
    motor_aplicacion: Engine,
    administrador: tuple[int, dict[str, str]],
    metodo: str,
    ruta: str,
    cuerpo: dict[str, Any] | None,
) -> None:
    objetivo, _ = crear_cuenta(motor_aplicacion, REVISOR)
    if cuerpo and "identificador_externo" in cuerpo:
        cuerpo = {"identificador_externo": f"sub-{uuid.uuid4()}"}
    respuesta = cliente.request(
        metodo, ruta.format(id=objetivo), json=cuerpo, headers=administrador[1]
    )
    assert respuesta.status_code in (200, 201)


# --- RF-25, RF-21: alta, habilitación, roles y autorización de cierre ---------------


def test_rf_25_alta_por_sub_sin_roles_ni_acceso_y_auditada(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    admin_id, encabezados = administrador
    sub = f"sub-{uuid.uuid4()}"
    respuesta = cliente.post("/usuarios", json={"identificador_externo": sub}, headers=encabezados)
    assert respuesta.status_code == 201
    cuenta = respuesta.json()
    assert cuenta == {
        "id": cuenta["id"],
        "identificador_externo": sub,
        "estado": "habilitada",
        "roles": [],
        "autorizacion_cierre": False,
        "nombre_visible": None,
    }
    (evento,) = eventos(motor_aplicacion, cuenta["id"])
    assert evento["accion"] == "cuenta_alta"
    assert evento["actor_id"] == admin_id
    assert evento["actor_tipo"] == "usuario"
    assert evento["resultado"] == "exito"
    assert evento["tramite_id"] is None
    assert str(evento["solicitud_id"]) == respuesta.headers[CABECERA_SOLICITUD]


def test_rf_25_alta_duplicada_responde_409_sin_efectos(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    existente, sub = crear_cuenta(motor_aplicacion)
    respuesta = cliente.post(
        "/usuarios", json={"identificador_externo": sub}, headers=administrador[1]
    )
    assert respuesta.status_code == 409
    assert eventos(motor_aplicacion, existente) == []


@pytest.mark.parametrize("identificador", ["", "con espacios", "x" * 129])
def test_rf_25_alta_con_identificador_invalido_responde_422(
    cliente: TestClient, administrador: tuple[int, dict[str, str]], identificador: str
) -> None:
    respuesta = cliente.post(
        "/usuarios", json={"identificador_externo": identificador}, headers=administrador[1]
    )
    assert respuesta.status_code == 422


def test_rf_25_deshabilitar_impide_operar_y_rehabilitar_restituye(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    objetivo, sub = crear_cuenta(motor_aplicacion, RESPONSABLE)
    ruta = f"/usuarios/{objetivo}/estado"
    assert cliente.get("/usuarios/yo", headers=portador(sub)).status_code == 200

    assert (
        cliente.put(ruta, json={"estado": "deshabilitada"}, headers=administrador[1]).json()[
            "estado"
        ]
        == "deshabilitada"
    )
    assert cliente.get("/usuarios/yo", headers=portador(sub)).status_code == 403
    # Repetir el mismo cambio no genera otro evento.
    cliente.put(ruta, json={"estado": "deshabilitada"}, headers=administrador[1])
    cliente.put(ruta, json={"estado": "habilitada"}, headers=administrador[1])
    assert cliente.get("/usuarios/yo", headers=portador(sub)).status_code == 200
    assert [e["accion"] for e in eventos(motor_aplicacion, objetivo)] == [
        "cuenta_deshabilitada",
        "cuenta_habilitada",
    ]


def test_rf_25_supresion_no_se_admite_como_cambio_de_estado(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    objetivo, _ = crear_cuenta(motor_aplicacion)
    respuesta = cliente.put(
        f"/usuarios/{objetivo}/estado", json={"estado": "suprimida"}, headers=administrador[1]
    )
    assert respuesta.status_code == 422


def test_rf_25_cuenta_suprimida_no_admite_cambios(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    objetivo, _ = crear_cuenta(motor_aplicacion, estado="suprimida")
    respuesta = cliente.put(f"/usuarios/{objetivo}/roles/{RESPONSABLE}", headers=administrador[1])
    assert respuesta.status_code == 409
    assert eventos(motor_aplicacion, objetivo) == []


def test_rf_25_roles_otorgados_y_retirados_quedan_auditados(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    objetivo, sub = crear_cuenta(motor_aplicacion)
    base = f"/usuarios/{objetivo}/roles"
    assert cliente.put(f"{base}/{REVISOR}", headers=administrador[1]).json()["roles"] == [REVISOR]
    cliente.put(f"{base}/{REVISOR}", headers=administrador[1])  # sin cambio, sin evento
    cliente.put(f"{base}/{RESPONSABLE}", headers=administrador[1])
    assert cliente.get("/usuarios/yo", headers=portador(sub)).json()["roles"] == [
        RESPONSABLE,
        REVISOR,
    ]
    assert cliente.delete(f"{base}/{REVISOR}", headers=administrador[1]).json()["roles"] == [
        RESPONSABLE
    ]
    assert [e["accion"] for e in eventos(motor_aplicacion, objetivo)] == [
        "rol_otorgado",
        "rol_otorgado",
        "rol_retirado",
    ]


def test_rf_25_rol_fuera_del_catalogo_responde_422(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    objetivo, _ = crear_cuenta(motor_aplicacion)
    respuesta = cliente.put(f"/usuarios/{objetivo}/roles/firmante", headers=administrador[1])
    assert respuesta.status_code == 422


def test_autorizacion_de_cierre_otorgada_y_retirada_auditada(
    cliente: TestClient, motor_aplicacion: Engine, administrador: tuple[int, dict[str, str]]
) -> None:
    objetivo, _ = crear_cuenta(motor_aplicacion, REVISOR)
    ruta = f"/usuarios/{objetivo}/autorizacion-cierre"
    otorgada = cliente.put(ruta, json={"otorgada": True}, headers=administrador[1]).json()
    assert otorgada["autorizacion_cierre"] is True
    assert otorgada["roles"] == [REVISOR]  # no agrega roles ni acceso a trámites
    cliente.put(ruta, json={"otorgada": False}, headers=administrador[1])
    acciones = [(e["accion"], e["actor_id"]) for e in eventos(motor_aplicacion, objetivo)]
    assert acciones == [
        ("autorizacion_cierre_otorgada", administrador[0]),
        ("autorizacion_cierre_retirada", administrador[0]),
    ]


def test_rf_25_cuenta_inexistente_responde_404(
    cliente: TestClient, administrador: tuple[int, dict[str, str]]
) -> None:
    assert cliente.get("/usuarios/999999999", headers=administrador[1]).status_code == 404


# --- Primer administrador y escenario de los tres usuarios ficticios -----


def test_inicializacion_manual_unica(
    base_reiniciada: Configuracion,
    motor_aplicacion: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(inicializar_administrador, "obtener_configuracion", lambda: base_reiniciada)
    assert inicializar_administrador.main(["--identificador-externo", "sub-admin-inicial"]) == 0
    assert inicializar_administrador.main(["--identificador-externo", "sub-otro"]) == 1
    with motor_aplicacion.connect() as conexion:
        cuentas = conexion.execute(
            text("SELECT identificador_externo FROM atlas.usuario ORDER BY id")
        ).scalars()
        assert list(cuentas) == ["sub-admin-inicial"]
        acciones = conexion.execute(
            text("SELECT accion, actor_tipo FROM atlas.evento_auditoria ORDER BY id")
        ).all()
    assert [tuple(a) for a in acciones] == [("cuenta_alta", "sistema"), ("rol_otorgado", "sistema")]


def test_hito_1_2_tres_usuarios_ficticios_por_api(
    base_reiniciada: Configuracion, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Responsable, revisor/aprobador con autorización de cierre y administrador operativo."""
    monkeypatch.setattr(inicializar_administrador, "obtener_configuracion", lambda: base_reiniciada)
    assert inicializar_administrador.main(["--identificador-externo", "sub-admin"]) == 0

    aplicacion = crear_aplicacion(base_reiniciada)
    with TestClient(aplicacion) as cliente:
        admin = portador("sub-admin")
        responsable = cliente.post(
            "/usuarios", json={"identificador_externo": "sub-responsable"}, headers=admin
        ).json()
        revisor = cliente.post(
            "/usuarios", json={"identificador_externo": "sub-revisor"}, headers=admin
        ).json()
        cliente.put(f"/usuarios/{responsable['id']}/roles/{RESPONSABLE}", headers=admin)
        cliente.put(f"/usuarios/{revisor['id']}/roles/{REVISOR}", headers=admin)
        cliente.put(
            f"/usuarios/{revisor['id']}/autorizacion-cierre", json={"otorgada": True}, headers=admin
        )
        perfiles = {
            sub: cliente.get("/usuarios/yo", headers=portador(sub)).json()
            for sub in ("sub-admin", "sub-responsable", "sub-revisor")
        }
    aplicacion.state.motor.dispose()

    assert perfiles["sub-admin"]["roles"] == [ADMIN]
    assert perfiles["sub-responsable"] == {
        "id": responsable["id"],
        "roles": [RESPONSABLE],
        "autorizacion_cierre": False,
        "nombre_visible": None,
    }
    assert perfiles["sub-revisor"] == {
        "id": revisor["id"],
        "roles": [REVISOR],
        "autorizacion_cierre": True,
        "nombre_visible": None,
    }
