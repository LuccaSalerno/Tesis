"""Estado general del administrador operativo (RF-24, HU-10)."""

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from tests.flujo_api import crear_tramite
from tests.flujo_revision import (
    Equipo,
    contexto,
    decidida,
    equipo,
    iniciar_ciclo,
    obtener,
    plantilla_de_contratos,
    tramite_con_conjunto,
)

pytestmark = pytest.mark.integracion

RUTA = "/administracion/estado-general"
TITULO = "Contrato reservado con Servicios Ficticios SA"


@pytest.fixture
def e(base_migrada: Configuracion, motor_aplicacion: Engine) -> Iterator[Equipo]:
    aplicacion = crear_aplicacion(base_migrada)
    with TestClient(aplicacion) as cliente:
        actual = equipo(cliente, motor_aplicacion)
        plantilla_de_contratos(actual)
        yield actual
    aplicacion.state.motor.dispose()


def test_rf_24_estado_general_con_conteos_y_tramites(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    decidida(e.revisor, ciclo["tareas"][0]["id"])
    vacio = crear_tramite(e.responsable, TITULO)["id"]
    datos = obtener(e.administrador, RUTA)
    filas = {t["id"]: t for t in datos["tramites"]}
    assert filas[ids["tramite"]]["estado"] == "pendiente_aprobacion"
    assert filas[ids["tramite"]]["documentos"] == 3
    assert filas[ids["tramite"]]["tareas_abiertas"] == 1
    assert filas[ids["tramite"]]["responsable_id"] == e.responsable.usuario_id
    assert (filas[vacio]["documentos"], filas[vacio]["tareas_abiertas"]) == (0, 0)
    assert datos["tramites_por_estado"]["pendiente_aprobacion"] >= 1
    assert datos["tareas_por_estado"]["aprobada"] >= 1
    assert sum(datos["trabajos_por_estado"].values()) >= 3
    assert set(datos["tramites"][0]) == {
        "id",
        "estado",
        "responsable_id",
        "creado_en",
        "actualizado_en",
        "documentos",
        "tareas_abiertas",
        "tareas_sin_asignar",
    }


def test_rf_24_sin_titulos_contenido_ni_datos_validados(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    crear_tramite(e.responsable, TITULO)
    serializado = json.dumps(obtener(e.administrador, RUTA), ensure_ascii=False)
    for sensible in (TITULO, "Contrato de mantenimiento", "30-96472518-3", "1250000.00", "ARS"):
        assert sensible not in serializado
    assert ids["contrato"] is not None


def test_rf_24_tareas_asignadas_a_cuentas_no_habilitadas(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    respuesta = e.cliente.put(
        f"/usuarios/{e.revisor.usuario_id}/estado",
        json={"estado": "deshabilitada"},
        headers=e.administrador.encabezados,
    )
    assert respuesta.status_code == 200
    bloqueadas = obtener(e.administrador, RUTA)["tareas_bloqueadas"]
    assert {
        "tarea_id": ciclo["tareas"][0]["id"],
        "tramite_id": ids["tramite"],
        "asignada_a_id": e.revisor.usuario_id,
    } in bloqueadas


def test_rnf_01_solo_el_administrador_ve_el_estado_general(e: Equipo) -> None:
    for ctx in (e.responsable, e.revisor, e.aprobador):
        obtener(ctx, RUTA, 403)
    sin_roles = contexto(e.cliente, e.responsable.motor)
    obtener(sin_roles, RUTA, 403)
    assert e.cliente.get(RUTA).status_code == 401


def test_rf_24_el_administrador_sigue_sin_acceso_al_tramite(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    # Sin acceso al trámite responde como si no existiera.
    base = f"/tramites/{ids['tramite']}"
    obtener(e.administrador, base, 404)
    obtener(e.administrador, f"{base}/documentos/{ids['contrato']}/validaciones", 404)


def test_rf_24_el_listado_respeta_el_limite(e: Equipo, monkeypatch: pytest.MonkeyPatch) -> None:
    from atlas.servicios import estado_general

    for _ in range(3):
        crear_tramite(e.responsable)
    monkeypatch.setattr(estado_general, "LIMITE_TRAMITES", 2)
    assert len(obtener(e.administrador, RUTA)["tramites"]) == 2
