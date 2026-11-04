"""Cancelación del trámite (RF-26, RN-14, RN-15, DO-2026-10-23-CIERRE P1 a P3), contra
PostgreSQL real y S3 simulado. Cuentas y documentos sintéticos."""

from typing import Any

import pytest
from sqlalchemy import Engine, text

from atlas.dominio.enumeraciones import TipoDocumental
from atlas.procesamiento import esquemas
from atlas.servicios import reconciliacion
from atlas.servicios.tareas import TRAMITE_CANCELADO
from tests import archivos
from tests.datos import crear_archivo, crear_tramite, crear_usuario
from tests.flujo_api import acciones_del_tramite, cargar, incorporar
from tests.flujo_api import crear_tramite as nuevo_tramite
from tests.flujo_procesamiento import recorrer, trabajo_de
from tests.flujo_revision import (
    Equipo,
    ciclos,
    contexto,
    decidida,
    decidir,
    enviar_a_validacion,
    evidencia,
    iniciar_ciclo,
    obtener,
    tramite,
    tramite_con_conjunto,
)
from tests.flujo_versiones import archivo
from tests.flujo_vinculos import CUIT, documento, vincular
from tests.procesamiento_fijo import ModeloFijo, dato
from tests.test_reconciliador import OrquestadorSimulado

pytestmark = pytest.mark.integracion

MOTIVO = "El proveedor desistió de la contratación"


def cancelar(ctx: Any, tramite_id: int, motivo: str | None = MOTIVO) -> Any:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/cancelacion",
        json={"motivo": motivo},
        headers=ctx.encabezados,
    )


# --- Estados admitidos y rechazados (RF-26, Tabla 3.VI) --------------------------------


def test_rf_26_cancelar_en_borrador_con_motivo(e: Equipo) -> None:
    tramite_id = nuevo_tramite(e.responsable)["id"]
    respuesta = cancelar(e.responsable, tramite_id, f"  {MOTIVO}  ")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert (cuerpo["estado"], cuerpo["motivo_cancelacion"]) == ("cancelado", MOTIVO)
    assert tramite(e.responsable, tramite_id)["motivo_cancelacion"] == MOTIVO
    assert acciones_del_tramite(e.responsable.motor, tramite_id)[-1] == "tramite_cancelado"


def test_rf_26_cancelar_en_pendiente_de_validacion(e: Equipo) -> None:
    tramite_id = nuevo_tramite(e.responsable)["id"]
    documento(e.responsable, tramite_id, "Anexo")
    assert enviar_a_validacion(e.responsable, tramite_id).status_code == 200
    assert cancelar(e.responsable, tramite_id).json()["estado"] == "cancelado"


def test_rn_14_cancelar_en_aprobacion_anula_tareas_y_cancela_el_ciclo(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    tramite_id = ids["tramite"]
    ciclo = iniciar_ciclo(e.responsable, tramite_id)
    legal, final = (t["id"] for t in ciclo["tareas"])
    aprobacion = decidida(e.revisor, legal)
    previa = evidencia(e.responsable, aprobacion["id"])
    assert cancelar(e.responsable, tramite_id).status_code == 200
    (cancelado,) = ciclos(e.responsable, tramite_id)
    assert cancelado["estado"] == "cancelado" and cancelado["concluido_en"] is not None
    assert [t["estado"] for t in cancelado["tareas"]] == ["aprobada", "anulada"]
    respuesta = decidir(e.aprobador, final)
    assert respuesta.status_code == 409 and respuesta.json()["detalle"] == TRAMITE_CANCELADO
    # La historia se conserva y sigue consultable (RN-14, RN-15).
    actual = evidencia(e.responsable, aprobacion["id"])
    assert actual["decision"] == previa["decision"]
    assert actual["validaciones"] == previa["validaciones"]
    assert len(tramite(e.responsable, tramite_id)["documentos"]) == 3
    acciones = acciones_del_tramite(e.responsable.motor, tramite_id)
    assert acciones[-3:] == ["ciclo_cancelado", "tarea_anulada", "tramite_cancelado"]
    assert "tramite_aprobado" not in acciones and "firma_simulada_aplicada" not in acciones


def test_rn_14_cancelar_en_observado_conserva_el_ciclo_observado(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    decidida(e.revisor, ciclo["tareas"][0]["id"], "observacion", "Revisar la orden")
    assert cancelar(e.responsable, ids["tramite"]).status_code == 200
    (observado,) = ciclos(e.responsable, ids["tramite"])
    assert observado["estado"] == "observado"
    assert "ciclo_cancelado" not in acciones_del_tramite(e.responsable.motor, ids["tramite"])


def test_rf_26_no_se_cancela_aprobado_cerrado_ni_cancelado(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    tramite_id = ids["tramite"]
    ciclo = iniciar_ciclo(e.responsable, tramite_id)
    for ctx, tarea in zip((e.revisor, e.aprobador), ciclo["tareas"], strict=True):
        decidida(ctx, tarea["id"])
    assert cancelar(e.responsable, tramite_id).status_code == 409  # Aprobado
    version = ciclo["versiones"][0]["version_id"]
    firma = e.cliente.post(
        f"/tramites/{tramite_id}/firma",
        json={"version_id": version},
        headers=e.aprobador.encabezados,
    )
    assert firma.status_code == 201
    assert cancelar(e.responsable, tramite_id).status_code == 409  # Cerrado
    otro = nuevo_tramite(e.responsable)["id"]
    assert cancelar(e.responsable, otro).status_code == 200
    assert cancelar(e.responsable, otro, "Otro motivo").status_code == 409  # Cancelado
    assert tramite(e.responsable, otro)["motivo_cancelacion"] == MOTIVO


@pytest.mark.parametrize("motivo", [None, "", "   "])
def test_rf_26_el_motivo_es_obligatorio(e: Equipo, motivo: str | None) -> None:
    tramite_id = nuevo_tramite(e.responsable)["id"]
    assert cancelar(e.responsable, tramite_id, motivo).status_code == 422
    assert tramite(e.responsable, tramite_id)["estado"] == "borrador"


def test_rnf_01_solo_el_responsable_del_tramite_cancela(e: Equipo) -> None:
    tramite_id = nuevo_tramite(e.responsable)["id"]
    for ctx in (e.revisor, e.aprobador, e.administrador):
        assert cancelar(ctx, tramite_id).status_code == 403
    ajeno = contexto(e.cliente, e.responsable.motor, "responsable_tramite")
    assert cancelar(ajeno, tramite_id).status_code == 404
    assert tramite(e.responsable, tramite_id)["estado"] == "borrador"


# --- Cancelado es terminal (RN-15) ------------------------------------------------------


def test_rn_15_cancelado_no_admite_cambios_y_conserva_la_historia(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    tramite_id, r = ids["tramite"], e.responsable
    pendiente = cargar(r, tramite_id, archivos.pdf(paginas=2))
    assert cancelar(r, tramite_id).status_code == 200
    base = f"/tramites/{tramite_id}"
    rechazadas = {
        "carga": r.cliente.post(
            f"{base}/cargas",
            json={"nombre": "Anexo.pdf", "formato": "pdf", "tamano_bytes": 1000},
            headers=r.encabezados,
        ),
        "incorporación": incorporar(r, tramite_id, pendiente["id"]),
        "versión": r.cliente.post(
            f"{base}/archivos/{pendiente['id']}/version", headers=r.encabezados
        ),
        "descarte": r.cliente.post(
            f"{base}/archivos/{pendiente['id']}/descarte", headers=r.encabezados
        ),
        "reintento": r.cliente.post(
            f"{base}/archivos/{pendiente['id']}/reintento", headers=r.encabezados
        ),
        "validación": r.cliente.post(
            f"{base}/documentos/{ids['contrato']}/validaciones",
            json={"campo": "moneda", "valor_validado": "USD"},
            headers=r.encabezados,
        ),
        "vínculo": vincular(r, tramite_id, ids["contrato"], ids["factura"]),
        "envío": enviar_a_validacion(r, tramite_id),
        "subsanación": r.cliente.post(f"{base}/subsanacion", headers=r.encabezados),
        "flujo": r.cliente.post(
            f"{base}/ciclos",
            json={"plantilla_id": 1, "version_plantilla": 1},
            headers=r.encabezados,
        ),
        "firma": e.cliente.post(
            f"{base}/firma", json={"version_id": 1}, headers=e.aprobador.encabezados
        ),
    }
    for nombre, respuesta in rechazadas.items():
        assert respuesta.status_code in (404, 409), (nombre, respuesta.text)
        assert respuesta.status_code == 409 or nombre == "firma", (nombre, respuesta.text)
    assert tramite(r, tramite_id)["estado"] == "cancelado"
    assert acciones_del_tramite(r.motor, tramite_id)[-1] == "tramite_cancelado"
    hitos = obtener(r, f"{base}/linea-tiempo")
    assert hitos[-1]["accion"] == "tramite_cancelado"
    assert obtener(r, f"{base}/vinculos")["confirmados"]


# --- Trabajo asíncrono posterior (RN-14, P3) --------------------------------------------


def test_rn_14_un_resultado_tardio_no_modifica_el_cancelado(aplicacion: Any, e: Equipo) -> None:
    """Carrera con el procesamiento: el archivo se cargó antes de cancelar y su resultado
    se persiste después. Se guardan las sugerencias, sin cambiar el estado ni sugerir una
    versión aunque haya un candidato."""
    tramite_id = nuevo_tramite(e.responsable)["id"]
    documento(e.responsable, tramite_id, "Orden", "orden_compra", {"cuit_proveedor": CUIT})
    carga = cargar(e.responsable, tramite_id, archivos.docx(f"cuit_proveedor | {CUIT}"), "docx")
    assert cancelar(e.responsable, tramite_id).status_code == 200
    modelo = ModeloFijo(
        {
            esquemas.HERRAMIENTA_CLASIFICACION: {"tipo": "orden_compra"},
            esquemas.HERRAMIENTA_EXTRACCION: {
                c.nombre: dato(CUIT if c.nombre == "cuit_proveedor" else None)
                for c in esquemas.CAMPOS[TipoDocumental.ORDEN_COMPRA]
            },
        }
    )
    salidas = recorrer(aplicacion, trabajo_de(e.responsable.motor, carga["id"]), modelo)
    assert salidas[-1] == {"resultado": "persistido"}
    assert tramite(e.responsable, tramite_id)["estado"] == "cancelado"
    assert archivo(e.responsable, tramite_id, carga["id"])["sugerencia_version"] is None
    respuesta = e.cliente.get(
        f"/tramites/{tramite_id}/archivos/{carga['id']}/sugerencias",
        headers=e.responsable.encabezados,
    )
    assert respuesta.json()["clasificacion"]["valor"] == "orden_compra"


def test_rn_14_el_reconciliador_no_inicia_trabajos_de_un_cancelado(
    aplicacion: Any, motor_migracion: Engine
) -> None:
    with motor_migracion.begin() as conexion:
        usuario = crear_usuario(conexion)
        cancelado = crear_tramite(conexion, usuario)
        vigente = crear_tramite(conexion, usuario)
        trabajos = []
        for tramite_id in (cancelado, vigente):
            archivo_id = crear_archivo(conexion, tramite_id, usuario, estado="pendiente")
            trabajos.append(
                conexion.execute(
                    text(
                        "INSERT INTO atlas.trabajo_procesamiento (archivo_id, estado)"
                        " VALUES (:a, 'en_espera') RETURNING id"
                    ),
                    {"a": archivo_id},
                ).scalar_one()
            )
        conexion.execute(
            text(
                "UPDATE atlas.tramite SET estado = 'cancelado', motivo_cancelacion = :m"
                " WHERE id = :t"
            ),
            {"m": MOTIVO, "t": cancelado},
        )
    orquestador = OrquestadorSimulado()
    with aplicacion.state.fabrica_sesiones() as sesion:
        resumen = reconciliacion.reconciliar(sesion, orquestador, limite=10_000, alcance=trabajos)
    assert resumen.terminales == [trabajos[0]]
    assert resumen.admitidos == [trabajos[1]]
    assert orquestador.iniciados == [(trabajos[1], 1)]
    with motor_migracion.connect() as conexion:
        estado, codigo = conexion.execute(
            text("SELECT estado, codigo_error FROM atlas.trabajo_procesamiento WHERE id = :t"),
            {"t": trabajos[0]},
        ).one()
        assert (estado, codigo) == ("fallido", "tramite_terminal")
        assert (
            conexion.execute(
                text("SELECT estado FROM atlas.tramite WHERE id = :t"), {"t": cancelado}
            ).scalar_one()
            == "cancelado"
        )
