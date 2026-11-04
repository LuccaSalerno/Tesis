"""Hito 1.8: plantillas, ciclos de revisión, tareas, decisiones, línea de tiempo y evidencia.

RF-17 a RF-22, RN-07, RN-08, RN-09, RN-12, RN-13, PD-02, PD-03, PD-05, RC-P03,
DO-2026-10-22-TAR (P1 a P12). Contra la API autenticada y PostgreSQL real.
"""

from typing import Any

import pytest
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from atlas.servicios.tareas import TAREA_DESACTUALIZADA
from tests import archivos
from tests.flujo_api import cargar, crear_tramite, eventos_del_tramite, incorporar
from tests.flujo_revision import (
    C_COMPLETO,
    Equipo,
    ciclos,
    confirmar_flujo,
    contexto,
    crear_plantilla,
    decidida,
    decidir,
    enviar_a_validacion,
    evidencia,
    flujo_sugerido,
    iniciar_ciclo,
    obtener,
    plantilla,
    plantilla_de_contratos,
    tramite,
    tramite_con_conjunto,
    tramite_con_contrato,
)
from tests.flujo_vinculos import documento, validar
from tests.procesamiento_fijo import EmbeddingsFijos

pytestmark = pytest.mark.integracion


@pytest.fixture
def en_aprobacion(e: Equipo) -> dict[str, Any]:
    """Contrato, orden y factura vinculados, con el ciclo 1 confirmado (dos tareas)."""
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    return {**ids, "ciclo": ciclo, "tareas": [t["id"] for t in ciclo["tareas"]]}


def acciones(motor: Engine, tramite_id: int) -> list[str]:
    return [ev["accion"] for ev in eventos_del_tramite(motor, tramite_id)]


def estado(e: Equipo, tramite_id: int) -> str:
    return str(tramite(e.responsable, tramite_id)["estado"])


def tarea(e: Equipo, tarea_id: int, quien: Any = None) -> dict[str, Any]:
    datos: dict[str, Any] = obtener(quien or e.responsable, f"/tareas/{tarea_id}")
    return datos


# --- Plantillas (RC-P03.1, P1) ----------------------------------------------------------


def test_rc_p03_1_plantilla_versionada_reemplaza_a_la_activa(e: Equipo) -> None:
    primera = plantilla(e.administrador, "general", [e.aprobador.usuario_id])
    segunda = plantilla(e.administrador, "general", [e.revisor.usuario_id, e.aprobador.usuario_id])
    assert segunda["version"] == primera["version"] + 1
    assert [p["orden"] for p in segunda["pasos"]] == [1, 2]
    assert {p["rol_requerido"] for p in segunda["pasos"]} == {"revisor_aprobador"}
    listadas = {p["id"]: p for p in obtener(e.administrador, "/plantillas-flujo")}
    assert listadas[primera["id"]]["activa"] is False
    assert listadas[primera["id"]]["desactivada_en"] is not None
    assert listadas[segunda["id"]]["activa"] is True


def test_rc_p03_1_desactivar_plantilla_una_sola_vez(e: Equipo) -> None:
    creada = plantilla(e.administrador, "general", [e.aprobador.usuario_id])
    ruta = f"/plantillas-flujo/{creada['id']}/desactivacion"
    primera = e.cliente.post(ruta, headers=e.administrador.encabezados)
    assert primera.status_code == 200 and primera.json()["activa"] is False
    assert e.cliente.post(ruta, headers=e.administrador.encabezados).status_code == 409
    inexistente = e.cliente.post(
        "/plantillas-flujo/999999999/desactivacion", headers=e.administrador.encabezados
    )
    assert inexistente.status_code == 404


def test_rc_p03_2_5_el_ultimo_paso_exige_autorizacion_de_cierre(e: Equipo) -> None:
    respuesta = crear_plantilla(e.administrador, "general", [e.revisor.usuario_id])
    assert respuesta.status_code == 422
    assert "autorización de cierre" in respuesta.json()["detalle"]


@pytest.mark.parametrize("quien", ["responsable", "administrador"])
def test_rf_19_el_revisor_por_defecto_debe_ser_revisor_habilitado(e: Equipo, quien: str) -> None:
    ajeno = getattr(e, quien).usuario_id
    respuesta = crear_plantilla(e.administrador, "general", [ajeno, e.aprobador.usuario_id])
    assert respuesta.status_code == 422


def test_rc_p03_1_de_uno_a_tres_pasos(e: Equipo) -> None:
    revisores = [e.revisor.usuario_id] * 3 + [e.aprobador.usuario_id]
    assert crear_plantilla(e.administrador, "general", revisores).status_code == 422
    assert crear_plantilla(e.administrador, "general", []).status_code == 422


@pytest.mark.parametrize("quien", ["responsable", "revisor"])
def test_rf_02_solo_el_administrador_configura_plantillas(e: Equipo, quien: str) -> None:
    ctx = getattr(e, quien)
    assert crear_plantilla(ctx, "general", [e.aprobador.usuario_id]).status_code == 403
    assert e.cliente.get("/plantillas-flujo", headers=ctx.encabezados).status_code == 403


# --- Envío a validación (Tabla 3.VI, P3) ------------------------------------------------


def test_tabla_3_vi_enviar_a_validacion_exige_un_documento(e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    assert enviar_a_validacion(e.responsable, tramite_id).status_code == 409
    documento(e.responsable, tramite_id, "Contrato")
    respuesta = enviar_a_validacion(e.responsable, tramite_id)
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "pendiente_validacion"
    assert enviar_a_validacion(e.responsable, tramite_id).status_code == 409
    assert acciones(e.responsable.motor, tramite_id)[-1] == "tramite_enviado_a_validacion"


def test_rn_07_solo_el_responsable_envia_a_validacion(e: Equipo) -> None:
    tramite_id = tramite_con_contrato(e)["tramite"]
    assert enviar_a_validacion(e.revisor, tramite_id).status_code == 403
    otro = contexto(e.cliente, e.responsable.motor, "responsable_tramite")
    assert enviar_a_validacion(otro, tramite_id).status_code == 404


# --- Flujo sugerido y confirmación (RF-17, RF-18, P2, P4) -------------------------------


def test_rf_17_sugerencia_inactiva_hasta_confirmar(e: Equipo) -> None:
    tramite_id = tramite_con_contrato(e)["tramite"]
    sugerido = flujo_sugerido(e.responsable, tramite_id)
    assert sugerido["alcance"] == "contrato"
    assert [p["asignada_a_id"] for p in sugerido["pasos"]] == [
        e.revisor.usuario_id,
        e.aprobador.usuario_id,
    ]
    assert sugerido["documentos_sin_validar"] == []
    assert ciclos(e.responsable, tramite_id) == []
    assert e.cliente.get("/tareas", headers=e.revisor.encabezados).json() == []


def test_rc_p03_1_4_sin_contrato_se_sugiere_la_plantilla_general(e: Equipo) -> None:
    general = plantilla(e.administrador, "general", [e.aprobador.usuario_id])
    tramite_id = crear_tramite(e.responsable)["id"]
    documento(e.responsable, tramite_id, "Orden", "orden_compra")
    sugerido = flujo_sugerido(e.responsable, tramite_id)
    assert (sugerido["alcance"], sugerido["plantilla_id"]) == ("general", general["id"])
    e.cliente.post(
        f"/plantillas-flujo/{general['id']}/desactivacion", headers=e.administrador.encabezados
    )
    sin_plantilla = flujo_sugerido(e.responsable, tramite_id)
    assert sin_plantilla["plantilla_id"] is None and sin_plantilla["pasos"] == []
    assert enviar_a_validacion(e.responsable, tramite_id).status_code == 200
    desactivada = confirmar_flujo(e.responsable, tramite_id, general["id"], general["version"])
    assert desactivada.status_code == 409


def test_rf_18_confirmar_crea_ciclo_con_versiones_y_tareas_asignadas(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    ciclo = en_aprobacion["ciclo"]
    tramite_id = en_aprobacion["tramite"]
    assert (ciclo["numero"], ciclo["estado"]) == (1, "en_curso")
    vigentes = {
        d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]
    }
    assert {v["version_id"] for v in ciclo["versiones"]} == vigentes
    assert [(t["orden"], t["estado"], t["asignada_a_id"]) for t in ciclo["tareas"]] == [
        (1, "pendiente", e.revisor.usuario_id),
        (2, "en_espera", e.aprobador.usuario_id),
    ]
    assert estado(e, tramite_id) == "pendiente_aprobacion"
    assert acciones(e.responsable.motor, tramite_id)[-3:] == [
        "flujo_confirmado",
        "tarea_asignada",
        "tarea_asignada",
    ]
    asignaciones = tarea(e, ciclo["tareas"][0]["id"])["asignaciones"]
    assert asignaciones == [
        {
            "anterior_id": None,
            "asignada_a_id": e.revisor.usuario_id,
            "asignada_por_id": None,
            "asignada_en": asignaciones[0]["asignada_en"],
        }
    ]
    assert confirmar_flujo(e.responsable, tramite_id).status_code == 409  # ya no está en PV


def test_tabla_3_vi_confirmar_exige_datos_validados(e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    incompleto = documento(e.responsable, tramite_id, "Contrato", "contrato", {"moneda": "ARS"})
    sin_tipo = documento(e.responsable, tramite_id, "Sin clasificar")
    enviar_a_validacion(e.responsable, tramite_id)
    assert flujo_sugerido(e.responsable, tramite_id)["documentos_sin_validar"] == [
        incompleto,
        sin_tipo,
    ]
    respuesta = confirmar_flujo(e.responsable, tramite_id)
    assert respuesta.status_code == 409
    assert f"{incompleto}, {sin_tipo}" in respuesta.json()["detalle"]
    assert ciclos(e.responsable, tramite_id) == []


def test_rf_17_confirmar_con_otra_plantilla_o_version_responde_409(e: Equipo) -> None:
    tramite_id = tramite_con_contrato(e)["tramite"]
    enviar_a_validacion(e.responsable, tramite_id)
    sugerido = flujo_sugerido(e.responsable, tramite_id)
    otra_version = confirmar_flujo(
        e.responsable, tramite_id, sugerido["plantilla_id"], sugerido["version_plantilla"] + 1
    )
    assert otra_version.status_code == 409
    nueva = plantilla_de_contratos(e)  # reemplaza a la sugerida antes de confirmar
    vieja = confirmar_flujo(
        e.responsable, tramite_id, sugerido["plantilla_id"], sugerido["version_plantilla"]
    )
    assert vieja.status_code == 409
    assert (
        confirmar_flujo(e.responsable, tramite_id, nueva["id"], nueva["version"]).status_code == 201
    )


def test_rc_p03_3_tarea_del_responsable_queda_sin_asignar_y_senalada(e: Equipo) -> None:
    doble = contexto(e.cliente, e.responsable.motor, "responsable_tramite", "revisor_aprobador")
    plantilla(e.administrador, "contrato", [doble.usuario_id, e.aprobador.usuario_id])
    tramite_id = crear_tramite(doble)["id"]
    documento(doble, tramite_id, "Contrato", "contrato", C_COMPLETO)
    ciclo = iniciar_ciclo(doble, tramite_id)
    primera, segunda = ciclo["tareas"]
    assert primera["asignada_a_id"] is None and segunda["asignada_a_id"] == e.aprobador.usuario_id
    assert "tarea_sin_asignar" in acciones(doble.motor, tramite_id)
    sin_asignar = obtener(e.administrador, "/tareas/sin-asignar")
    assert primera["id"] in {t["id"] for t in sin_asignar}
    # DO-2026-10-23-DIF (DIF-119): el administrador ve el identificador, no el título.
    assert all(t["tramite"]["titulo"] is None for t in sin_asignar)
    assert e.cliente.get("/tareas/sin-asignar", headers=doble.encabezados).status_code == 403
    # El administrador asigna; el responsable nunca puede recibirla.
    ruta = f"/tareas/{primera['id']}/asignacion"
    propia = e.cliente.put(
        ruta, json={"usuario_id": doble.usuario_id}, headers=e.administrador.encabezados
    )
    assert propia.status_code == 422
    asignada = e.cliente.put(
        ruta, json={"usuario_id": e.revisor.usuario_id}, headers=e.administrador.encabezados
    )
    assert asignada.status_code == 200 and asignada.json()["asignada_a_id"] == e.revisor.usuario_id
    assert asignada.json()["tramite"] == {
        "id": tramite_id,
        "titulo": None,
        "estado": "pendiente_aprobacion",
    }
    assert decidir(e.revisor, primera["id"]).status_code == 201


# --- Asignación (RF-19, P7) -------------------------------------------------------------


def test_rf_19_reasignar_registra_cada_cambio(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    tarea_id = en_aprobacion["tareas"][0]
    otro = contexto(e.cliente, e.responsable.motor, "revisor_aprobador")
    ruta = f"/tareas/{tarea_id}/asignacion"
    respuesta = e.cliente.put(
        ruta, json={"usuario_id": otro.usuario_id}, headers=e.administrador.encabezados
    )
    assert respuesta.status_code == 200
    repetida = e.cliente.put(
        ruta, json={"usuario_id": otro.usuario_id}, headers=e.administrador.encabezados
    )
    assert repetida.status_code == 200  # sin cambios: no registra nada
    historial = tarea(e, tarea_id)["asignaciones"]
    assert [(a["anterior_id"], a["asignada_a_id"], a["asignada_por_id"]) for a in historial] == [
        (None, e.revisor.usuario_id, None),
        (e.revisor.usuario_id, otro.usuario_id, e.administrador.usuario_id),
    ]
    assert acciones(e.responsable.motor, en_aprobacion["tramite"]).count("tarea_reasignada") == 1
    # P8: quien deja de tener la tarea pierde el acceso al trámite.
    assert (
        e.cliente.get(
            f"/tramites/{en_aprobacion['tramite']}", headers=e.revisor.encabezados
        ).status_code
        == 404
    )
    assert decidir(e.revisor, tarea_id).status_code == 404
    assert decidir(otro, tarea_id).status_code == 201


def test_rf_19_rechazos_de_asignacion(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    tarea_id = en_aprobacion["tareas"][0]
    ruta = f"/tareas/{tarea_id}/asignacion"
    sin_rol = contexto(e.cliente, e.responsable.motor, "responsable_tramite")
    assert (
        e.cliente.put(
            ruta, json={"usuario_id": sin_rol.usuario_id}, headers=e.administrador.encabezados
        ).status_code
        == 422
    )
    assert (
        e.cliente.put(
            ruta, json={"usuario_id": e.aprobador.usuario_id}, headers=e.revisor.encabezados
        ).status_code
        == 403
    )
    assert (
        e.cliente.put(
            "/tareas/999999999/asignacion",
            json={"usuario_id": e.aprobador.usuario_id},
            headers=e.administrador.encabezados,
        ).status_code
        == 404
    )
    decidida(e.revisor, tarea_id)
    concluida = e.cliente.put(
        ruta, json={"usuario_id": e.aprobador.usuario_id}, headers=e.administrador.encabezados
    )
    assert concluida.status_code == 409


# --- Decisión (RF-20, RN-08, P5, P6) ----------------------------------------------------


def test_rf_20_aprobar_todas_las_tareas_aprueba_el_tramite(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    primera, segunda = en_aprobacion["tareas"]
    tramite_id = en_aprobacion["tramite"]
    assert decidir(e.aprobador, segunda).status_code == 409  # en espera
    dec_1 = decidida(e.revisor, primera)
    assert (dec_1["tipo"], dec_1["motivo"], dec_1["actor_id"]) == (
        "aprobacion",
        None,
        e.revisor.usuario_id,
    )
    assert tarea(e, segunda)["estado"] == "pendiente"
    assert estado(e, tramite_id) == "pendiente_aprobacion"
    assert decidir(e.revisor, primera).status_code == 409  # ya decidida
    dec_2 = decidida(e.aprobador, segunda, motivo="Conforme")
    assert dec_2["motivo"] == "Conforme"
    assert estado(e, tramite_id) == "aprobado"
    (ciclo,) = ciclos(e.responsable, tramite_id)
    assert ciclo["estado"] == "aprobado" and ciclo["concluido_en"] is not None
    assert acciones(e.responsable.motor, tramite_id)[-4:] == [
        "tarea_aprobada",
        "tarea_habilitada",
        "tarea_aprobada",
        "tramite_aprobado",
    ]


def test_pd_02_la_decision_registra_los_controles_mostrados(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tarea_id = en_aprobacion["tareas"][0]
    vista = tarea(e, tarea_id, e.revisor)
    mostrados = {c["ejecucion"]["id"] for c in vista["controles"] if c["ejecucion"]}
    assert len(mostrados) == 4  # R1 a R4 con vínculos pertinentes
    assert vista["controles_pendientes"] is False
    dec = decidida(e.revisor, tarea_id)
    assert set(dec["controles_considerados"]) == mostrados
    despues = tarea(e, tarea_id, e.revisor)
    assert {c["ejecucion"]["id"] for c in despues["controles"]} == mostrados
    assert despues["decision"]["id"] == dec["id"]


def test_pd_02_4_sin_reglas_aplicables_decide_sin_controles(e: Equipo) -> None:
    tramite_id = tramite_con_contrato(e)["tramite"]
    ciclo = iniciar_ciclo(e.responsable, tramite_id)
    dec = decidida(e.revisor, ciclo["tareas"][0]["id"])
    assert dec["controles_considerados"] == []


def test_rn_08_la_observacion_exige_motivo_y_deja_el_tramite_observado(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    primera, segunda = en_aprobacion["tareas"]
    assert decidir(e.revisor, primera, "observacion").status_code == 422
    assert decidir(e.revisor, primera, "observacion", "   ").status_code == 422
    dec = decidida(e.revisor, primera, "observacion", "Falta el anexo de precios")
    assert dec["motivo"] == "Falta el anexo de precios"
    tramite_id = en_aprobacion["tramite"]
    assert estado(e, tramite_id) == "observado"
    assert tarea(e, segunda)["estado"] == "descartada"
    (ciclo,) = ciclos(e.responsable, tramite_id)
    assert ciclo["estado"] == "observado"
    assert acciones(e.responsable.motor, tramite_id)[-3:] == [
        "tarea_observada",
        "tarea_descartada",
        "tramite_observado",
    ]
    assert decidir(e.aprobador, segunda).status_code == 409


def test_rn_08_solo_el_asignado_decide(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    primera = en_aprobacion["tareas"][0]
    assert decidir(e.aprobador, primera).status_code == 403  # tiene tarea en el ciclo
    ajeno = contexto(e.cliente, e.responsable.motor, "revisor_aprobador")
    assert decidir(ajeno, primera).status_code == 404  # sin acceso: como si no existiera
    assert decidir(e.administrador, primera).status_code == 403  # RN-08: nunca el administrador
    assert decidir(e.responsable, primera).status_code == 403
    assert decidir(e.revisor, 999999999).status_code == 404
    assert estado(e, en_aprobacion["tramite"]) == "pendiente_aprobacion"


def test_rn_08_una_cuenta_deshabilitada_no_decide(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    e.cliente.put(
        f"/usuarios/{e.revisor.usuario_id}/estado",
        json={"estado": "deshabilitada"},
        headers=e.administrador.encabezados,
    )
    assert decidir(e.revisor, en_aprobacion["tareas"][0]).status_code == 403


def test_rf_18_mis_tareas_y_vista_de_tarea(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    mias = obtener(e.revisor, "/tareas")
    assert [t["id"] for t in mias] == [en_aprobacion["tareas"][0]]
    assert mias[0]["tramite"]["estado"] == "pendiente_aprobacion"
    assert mias[0]["ciclo"]["numero"] == 1
    vista = tarea(e, en_aprobacion["tareas"][1], e.revisor)  # misma tarea de ciclo: visible
    assert len(vista["versiones"]) == 3
    obtener(e.administrador, f"/tareas/{en_aprobacion['tareas'][0]}", esperado=404)  # RF-24
    obtener(e.revisor, "/tareas/999999999", esperado=404)


# --- Acceso del revisor (P8, V10) -------------------------------------------------------


def test_p8_el_revisor_consulta_las_versiones_de_su_ciclo(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tramite_id = en_aprobacion["tramite"]
    r = e.revisor
    assert tramite_id in {t["id"] for t in obtener(r, "/tramites")}
    assert len(tramite(r, tramite_id)["documentos"]) == 3
    assert len(obtener(r, f"/tramites/{tramite_id}/archivos")) == 3
    obtener(r, f"/tramites/{tramite_id}/documentos/{en_aprobacion['contrato']}/validaciones")
    assert len(obtener(r, f"/tramites/{tramite_id}/vinculos")["confirmados"]) == 2
    controles = obtener(r, f"/tramites/{tramite_id}/controles?historial=true")
    ejecucion = next(c["ejecucion"] for c in controles["vigentes"] if c["ejecucion"])
    obtener(r, f"/tramites/{tramite_id}/controles/{ejecucion['id']}")
    assert len(ciclos(r, tramite_id)) == 1
    # Solo lectura: las operaciones del responsable siguen rechazadas.
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/documentos/{en_aprobacion['contrato']}/validaciones",
        json={"campo": "moneda", "valor_validado": "USD"},
        headers=r.encabezados,
    )
    assert respuesta.status_code == 403


def test_p8_el_revisor_no_ve_documentos_fuera_de_su_ciclo(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tramite_id = en_aprobacion["tramite"]
    archivo = cargar(e.responsable, tramite_id, archivos.pdf())
    nuevo = incorporar(e.responsable, tramite_id, archivo["id"], nombre="Anexo")
    assert nuevo.status_code == 201
    nuevo_id = nuevo.json()["id"]
    r = e.revisor
    assert nuevo_id not in {d["id"] for d in tramite(r, tramite_id)["documentos"]}
    assert archivo["id"] not in {a["id"] for a in obtener(r, f"/tramites/{tramite_id}/archivos")}
    obtener(r, f"/tramites/{tramite_id}/documentos/{nuevo_id}/validaciones", esperado=404)
    obtener(r, f"/tramites/{tramite_id}/archivos/{archivo['id']}/sugerencias", esperado=404)
    linea = obtener(r, f"/tramites/{tramite_id}/linea-tiempo")
    del_anexo = [
        h for h in linea if h["accion"] == "documento_incorporado" and h["entidad_id"] == nuevo_id
    ]
    assert del_anexo and del_anexo[0]["version"] is None  # ve el evento, no abre la versión
    linea_responsable = obtener(e.responsable, f"/tramites/{tramite_id}/linea-tiempo")
    assert (
        next(h for h in linea_responsable if h["id"] == del_anexo[0]["id"])["version"][
            "documento_id"
        ]
        == nuevo_id
    )


def test_v10_sin_tarea_no_hay_acceso(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    tramite_id = en_aprobacion["tramite"]
    ajeno = contexto(e.cliente, e.responsable.motor, "revisor_aprobador")
    for ruta in (
        f"/tramites/{tramite_id}",
        f"/tramites/{tramite_id}/ciclos",
        f"/tramites/{tramite_id}/linea-tiempo",
        f"/tramites/{tramite_id}/controles",
        f"/tramites/{tramite_id}/vinculos",
    ):
        obtener(ajeno, ruta, esperado=404)
        obtener(e.administrador, ruta, esperado=404)
    assert tramite_id not in {t["id"] for t in obtener(ajeno, "/tramites")}


def test_p8_el_revisor_consulta_solo_sus_versiones(
    e: Equipo, en_aprobacion: dict[str, Any], aplicacion: Any
) -> None:
    aplicacion.state.embeddings = EmbeddingsFijos()
    respuesta = e.cliente.post(
        f"/tramites/{en_aprobacion['tramite']}/consultas",
        json={"pregunta": "¿Hasta cuándo está vigente?"},
        headers=e.revisor.encabezados,
    )
    assert respuesta.status_code == 201
    # Sin procesamiento no hay fragmentos indexados: abstención sin invocar el modelo.
    assert respuesta.json()["motivo_abstencion"] == "sin_fragmentos"


# --- Subsanación (RN-13, P9) y RN-12 con documento nuevo (P10) --------------------------


def test_rn_13_subsanar_vuelve_a_validacion_sin_nueva_version(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tramite_id = en_aprobacion["tramite"]
    ruta = f"/tramites/{tramite_id}/subsanacion"
    assert e.cliente.post(ruta, headers=e.responsable.encabezados).status_code == 409
    decidida(e.revisor, en_aprobacion["tareas"][0], "observacion", "Revisar el importe")
    versiones_antes = {
        d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]
    }
    assert e.cliente.post(ruta, headers=e.revisor.encabezados).status_code == 403
    respuesta = e.cliente.post(ruta, headers=e.responsable.encabezados)
    assert respuesta.status_code == 200 and respuesta.json()["estado"] == "pendiente_validacion"
    assert {
        d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]
    } == versiones_antes
    assert acciones(e.responsable.motor, tramite_id)[-1] == "tramite_subsanado"
    segundo = iniciar_ciclo(e.responsable, tramite_id)
    assert segundo["numero"] == 2
    assert {v["version_id"] for v in segundo["versiones"]} == versiones_antes
    assert [t["estado"] for t in segundo["tareas"]] == ["pendiente", "en_espera"]


def test_rn_12_documento_nuevo_desplaza_el_ciclo_y_anula_tareas(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tramite_id = en_aprobacion["tramite"]
    primera, segunda = en_aprobacion["tareas"]
    decidida(e.revisor, primera)
    archivo = cargar(e.responsable, tramite_id, archivos.pdf())
    assert incorporar(e.responsable, tramite_id, archivo["id"], nombre="Anexo").status_code == 201
    assert estado(e, tramite_id) == "borrador"
    (ciclo,) = ciclos(e.responsable, tramite_id)
    assert ciclo["estado"] == "desplazado"
    assert [t["estado"] for t in ciclo["tareas"]] == ["aprobada", "anulada"]
    respuesta = decidir(e.aprobador, segunda)
    assert respuesta.status_code == 409 and respuesta.json()["detalle"] == TAREA_DESACTUALIZADA
    assert tarea(e, segunda)["decision"] is None
    assert acciones(e.responsable.motor, tramite_id)[-4:] == [
        "documento_incorporado",
        "ciclo_desplazado",
        "tarea_anulada",
        "tramite_vuelve_a_borrador",
    ]


def test_rn_12_un_ciclo_aprobado_conserva_su_estado(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tramite_id = en_aprobacion["tramite"]
    for ctx, tarea_id in zip((e.revisor, e.aprobador), en_aprobacion["tareas"], strict=True):
        decidida(ctx, tarea_id)
    archivo = cargar(e.responsable, tramite_id, archivos.pdf())
    incorporar(e.responsable, tramite_id, archivo["id"])
    assert estado(e, tramite_id) == "borrador"
    assert ciclos(e.responsable, tramite_id)[0]["estado"] == "aprobado"


# --- Evidencia de la decisión (PD-03, P12, V1 a V4) -------------------------------------


def test_pd_03_evidencia_reconstruye_la_cadena(e: Equipo, en_aprobacion: dict[str, Any]) -> None:
    tramite_id = en_aprobacion["tramite"]
    dec = decidida(e.revisor, en_aprobacion["tareas"][0], "observacion", "Revisar R3")
    datos = evidencia(e.responsable, dec["id"])
    assert datos["decision"]["id"] == dec["id"]
    assert (datos["tarea"]["id"], datos["ciclo"]["numero"], datos["tramite"]["id"]) == (
        en_aprobacion["tareas"][0],
        1,
        tramite_id,
    )
    assert {v["version_id"] for v in datos["versiones"]} == {
        v["version_id"] for v in en_aprobacion["ciclo"]["versiones"]
    }
    contrato = [v for v in datos["validaciones"] if v["documento_id"] == en_aprobacion["contrato"]]
    assert {v["campo"] for v in contrato} == {"tipo_documental", *C_COMPLETO}
    moneda = next(v for v in contrato if v["campo"] == "moneda")
    assert (moneda["valor_validado"], moneda["tipo"], moneda["validador_id"]) == (
        "ARS",
        "sin_sugerencia",
        e.responsable.usuario_id,
    )
    assert moneda["valor_sugerido"] is None and moneda["localizador_sugerido"] is None
    assert {c["id"] for c in datos["controles"]} == set(dec["controles_considerados"])
    entradas = {v["validacion_id"] for c in datos["controles"] for v in c["valores"]}
    assert entradas <= {v["validacion_id"] for v in datos["validaciones"]}
    acciones_evidencia = [ev["accion"] for ev in datos["eventos"]]
    assert {"flujo_confirmado", "tarea_observada", "regla_ejecutada", "campo_registrado"} <= set(
        acciones_evidencia
    )
    assert evidencia(e.revisor, dec["id"])["decision"]["id"] == dec["id"]
    assert evidencia(e.aprobador, dec["id"])["decision"]["id"] == dec["id"]


def test_v4_la_evidencia_conserva_los_controles_originales(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    """Una corrección posterior (subsanación) crea ejecuciones nuevas; la decisión anterior
    conserva las suyas y sus validaciones de entonces."""
    tramite_id = en_aprobacion["tramite"]
    dec_1 = decidida(e.revisor, en_aprobacion["tareas"][0], "observacion", "Importe")
    antes = evidencia(e.responsable, dec_1["id"])
    e.cliente.post(f"/tramites/{tramite_id}/subsanacion", headers=e.responsable.encabezados)
    validaciones = obtener(
        e.responsable, f"/tramites/{tramite_id}/documentos/{en_aprobacion['factura']}/validaciones"
    )
    importe = next(c for c in validaciones["campos"] if c["campo"] == "importe_total")
    validar(
        e.responsable,
        tramite_id,
        en_aprobacion["factura"],
        "importe_total",
        "1250000.00",
        importe["vigente"]["id"],
    )
    segundo = iniciar_ciclo(e.responsable, tramite_id)
    dec_2 = decidida(e.revisor, segundo["tareas"][0]["id"])
    despues = evidencia(e.responsable, dec_1["id"])
    assert despues["controles"] == antes["controles"]
    assert despues["validaciones"] == antes["validaciones"]
    nueva = evidencia(e.responsable, dec_2["id"])
    assert set(dec_2["controles_considerados"]) != set(dec_1["controles_considerados"])
    assert nueva["ciclo"]["numero"] == 2
    importes = {v["valor_validado"] for v in nueva["validaciones"] if v["campo"] == "importe_total"}
    assert "1250000.00" in importes


def test_p8_sin_el_rol_de_revisor_se_pierde_el_acceso_derivado(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    dec = decidida(e.revisor, en_aprobacion["tareas"][0])
    retiro = e.cliente.delete(
        f"/usuarios/{e.revisor.usuario_id}/roles/revisor_aprobador",
        headers=e.administrador.encabezados,
    )
    assert retiro.status_code == 200
    obtener(e.revisor, f"/tareas/{en_aprobacion['tareas'][0]}", esperado=404)
    obtener(e.revisor, f"/decisiones/{dec['id']}/evidencia", esperado=404)
    obtener(e.revisor, f"/tramites/{en_aprobacion['tramite']}", esperado=404)


def test_v10_evidencia_solo_para_quien_corresponde(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    dec = decidida(e.revisor, en_aprobacion["tareas"][0])
    ajeno = contexto(e.cliente, e.responsable.motor, "revisor_aprobador")
    for ctx in (ajeno, e.administrador):
        obtener(ctx, f"/decisiones/{dec['id']}/evidencia", esperado=404)
    obtener(e.responsable, "/decisiones/999999999/evidencia", esperado=404)


def test_rf_22_linea_de_tiempo_ordenada_con_versiones(
    e: Equipo, en_aprobacion: dict[str, Any]
) -> None:
    tramite_id = en_aprobacion["tramite"]
    decidida(e.revisor, en_aprobacion["tareas"][0])
    linea = obtener(e.responsable, f"/tramites/{tramite_id}/linea-tiempo")
    assert [h["id"] for h in linea] == sorted(h["id"] for h in linea)
    assert linea[0]["accion"] == "tramite_creado"
    assert linea[-1]["accion"] == "tarea_habilitada" and linea[-1]["actor_tipo"] == "sistema"
    incorporaciones = [h for h in linea if h["accion"] == "documento_incorporado"]
    assert len(incorporaciones) == 3
    assert all(h["version"]["version_numero"] == 1 for h in incorporaciones)
    aprobacion = next(h for h in linea if h["accion"] == "tarea_aprobada")
    assert (aprobacion["actor_id"], aprobacion["entidad_tipo"]) == (
        e.revisor.usuario_id,
        "decision",
    )


# --- Garantías en la base (RNF-04, RC-P03.3, PD-04-011) ---------------------------------


def _ids(motor: Engine, tarea_id: int) -> dict[str, int]:
    with motor.connect() as conexion:
        fila = conexion.execute(
            text(
                "SELECT t.ciclo_revision_id AS ciclo, c.tramite_id AS tramite,"
                " tr.responsable_id AS responsable, c.plantilla_flujo_id AS plantilla"
                " FROM atlas.tarea t JOIN atlas.ciclo_revision c ON c.id = t.ciclo_revision_id"
                " JOIN atlas.tramite tr ON tr.id = c.tramite_id WHERE t.id = :t"
            ),
            {"t": tarea_id},
        ).one()
    return dict(fila._mapping)


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE atlas.tarea SET nombre = 'otra' WHERE id = :t",
        "DELETE FROM atlas.tarea WHERE id = :t",
        "UPDATE atlas.ciclo_revision SET numero = 9 WHERE id = :c",
        "DELETE FROM atlas.ciclo_revision_version WHERE ciclo_revision_id = :c",
        "UPDATE atlas.decision SET motivo = 'x' WHERE tarea_id = :t",
        "DELETE FROM atlas.decision_control",
        "UPDATE atlas.asignacion_tarea SET asignada_a_id = asignada_a_id WHERE tarea_id = :t",
        "UPDATE atlas.plantilla_flujo SET nombre = 'x' WHERE id = :p",
        "DELETE FROM atlas.plantilla_flujo_paso WHERE plantilla_flujo_id = :p",
    ],
)
def test_rnf_04_la_aplicacion_no_altera_ciclos_tareas_ni_decisiones(
    e: Equipo,
    en_aprobacion: dict[str, Any],
    conexion_aplicacion: Connection,
    sentencia: str,
) -> None:
    tarea_id = en_aprobacion["tareas"][0]
    decidida(e.revisor, tarea_id)
    ids = _ids(e.responsable.motor, tarea_id)
    with pytest.raises(DBAPIError, match="permission denied"):
        conexion_aplicacion.execute(
            text(sentencia), {"t": tarea_id, "c": ids["ciclo"], "p": ids["plantilla"]}
        )


@pytest.mark.parametrize(
    ("sentencia", "mensaje"),
    [
        ("UPDATE atlas.tarea SET nombre = 'otra' WHERE id = :t", "solo cambian"),
        ("UPDATE atlas.tarea SET estado = 'pendiente' WHERE id = :t", "no admitida"),
        ("UPDATE atlas.tarea SET asignada_a_id = NULL WHERE id = :t", "no se reasigna"),
        (
            "INSERT INTO atlas.tarea (ciclo_revision_id, orden, nombre, rol_requerido, estado,"
            " asignada_a_id) VALUES (:c, 3, 'x', 'revisor_aprobador', 'en_espera', :r)",
            "responsable",
        ),
        ("DELETE FROM atlas.tarea WHERE id = :t", "es inmutable"),
        ("UPDATE atlas.ciclo_revision SET estado = 'aprobado' WHERE id = :c", "no admitida"),
        ("UPDATE atlas.ciclo_revision SET numero = 9 WHERE id = :c", "no admitida"),
        ("DELETE FROM atlas.ciclo_revision WHERE id = :c", "es inmutable"),
        ("UPDATE atlas.decision SET motivo = 'otro' WHERE tarea_id = :t", "es inmutable"),
        ("DELETE FROM atlas.ciclo_revision_version WHERE ciclo_revision_id = :c", "es inmutable"),
        ("UPDATE atlas.plantilla_flujo SET nombre = 'x' WHERE id = :p", "desactivación"),
        ("DELETE FROM atlas.plantilla_flujo WHERE id = :p", "es inmutable"),
    ],
)
def test_rnf_04_ciclos_y_decisiones_protegidos_incluso_para_el_propietario(
    e: Equipo,
    en_aprobacion: dict[str, Any],
    conexion_migracion: Connection,
    sentencia: str,
    mensaje: str,
) -> None:
    primera = en_aprobacion["tareas"][0]
    decidida(e.revisor, primera, "observacion", "Motivo")  # ciclo observado, primera decidida
    ids = _ids(e.responsable.motor, primera)
    with pytest.raises(IntegrityError, match=mensaje):
        conexion_migracion.execute(
            text(sentencia),
            {"t": primera, "c": ids["ciclo"], "p": ids["plantilla"], "r": ids["responsable"]},
        )


def test_rf_18_la_base_rechaza_versiones_de_otro_tramite_en_el_ciclo(
    e: Equipo, en_aprobacion: dict[str, Any], conexion_aplicacion: Connection
) -> None:
    otro = tramite_con_contrato(e)
    version = tramite(e.responsable, otro["tramite"])["documentos"][0]["version_vigente"]["id"]
    with pytest.raises(IntegrityError, match="no pertenece al trámite"):
        conexion_aplicacion.execute(
            text(
                "INSERT INTO atlas.ciclo_revision_version (ciclo_revision_id, version_id)"
                " VALUES (:c, :v)"
            ),
            {"c": en_aprobacion["ciclo"]["id"], "v": version},
        )


def test_rf_20_la_base_exige_motivo_en_la_observacion(
    e: Equipo, en_aprobacion: dict[str, Any], conexion_aplicacion: Connection
) -> None:
    with pytest.raises(IntegrityError, match="ck_decision_observacion_con_motivo"):
        conexion_aplicacion.execute(
            text(
                "INSERT INTO atlas.decision (tarea_id, actor_id, tipo)"
                " VALUES (:t, :a, 'observacion')"
            ),
            {"t": en_aprobacion["tareas"][0], "a": e.revisor.usuario_id},
        )
