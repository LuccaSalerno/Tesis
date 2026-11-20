"""Versión nueva sugerida y confirmada por el responsable (RF-06, RF-07, RN-11, RN-12),
contra PostgreSQL real y S3 simulado. Datos sintéticos."""

import json
import threading
from typing import Any

import pytest
from sqlalchemy import text

from atlas.servicios import cargas, tramites, versiones
from atlas.servicios.errores import Conflicto
from tests.conftest import lineas_registro
from tests.flujo_api import acciones_del_tramite, contar, crear_tramite, incorporar
from tests.flujo_revision import (
    O_COMPLETO,
    Equipo,
    ciclos,
    contexto,
    decidida,
    iniciar_ciclo,
    tramite,
    tramite_con_conjunto,
)
from tests.flujo_versiones import archivo, como_version, descartar, procesado
from tests.flujo_vinculos import CUIT, OTRO_CUIT, controles, documento, validar

pytestmark = pytest.mark.integracion


def _orden(e: Equipo, tramite_id: int, **campos: str) -> int:
    return documento(e.responsable, tramite_id, "Orden de compra", "orden_compra", campos)


def _sugerencia(e: Equipo, tramite_id: int, archivo_id: int) -> dict[str, Any] | None:
    datos: dict[str, Any] | None = archivo(e.responsable, tramite_id, archivo_id)[
        "sugerencia_version"
    ]
    return datos


# --- Detección (RF-06) ---------------------------------------------------------------


def test_rf_06_coincide_el_numero_documental(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    orden = _orden(e, tramite_id, numero="OC-0001", cuit_proveedor=CUIT)
    nuevo = procesado(
        aplicacion,
        e.responsable,
        tramite_id,
        "orden_compra",
        {"numero": "OC-0001", "cuit_proveedor": OTRO_CUIT},
    )
    assert _sugerencia(e, tramite_id, nuevo["id"]) == {
        "documento_id": orden,
        "documento_nombre": "Orden de compra",
        "criterio": "numero",
        "campo": "numero",
        "estado": "pendiente",
    }


def test_rf_06_sin_numero_coincidente_vale_el_cuit(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    orden = _orden(e, tramite_id, numero="OC-0001", cuit_proveedor=CUIT)
    nuevo = procesado(
        aplicacion,
        e.responsable,
        tramite_id,
        "orden_compra",
        {"numero": "OC-0002", "cuit_proveedor": CUIT.replace("-", "")},
    )
    sugerencia = _sugerencia(e, tramite_id, nuevo["id"])
    assert sugerencia is not None
    assert (sugerencia["documento_id"], sugerencia["criterio"], sugerencia["campo"]) == (
        orden,
        "cuit",
        "cuit_proveedor",
    )


def test_rf_06_el_numero_gana_y_luego_la_version_mas_reciente(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    por_cuit = _orden(e, tramite_id, numero="OC-0009", cuit_proveedor=CUIT)
    por_numero = _orden(e, tramite_id, numero="OC-0001", cuit_proveedor=OTRO_CUIT)
    nuevo = procesado(
        aplicacion,
        e.responsable,
        tramite_id,
        "orden_compra",
        {"numero": "OC-0001", "cuit_proveedor": CUIT},
    )
    assert (_sugerencia(e, tramite_id, nuevo["id"]) or {})["documento_id"] == por_numero
    mas_reciente = _orden(e, tramite_id, numero="OC-0008", cuit_proveedor=CUIT)
    empate = procesado(
        aplicacion, e.responsable, tramite_id, "orden_compra", {"cuit_proveedor": CUIT}
    )
    assert (_sugerencia(e, tramite_id, empate["id"]) or {})["documento_id"] == mas_reciente
    assert por_cuit != mas_reciente


@pytest.mark.parametrize(
    ("tipo", "validados"),
    [
        ("factura", {"cuit_proveedor": CUIT}),  # otro tipo documental
        ("orden_compra", {"cuit_proveedor": OTRO_CUIT, "numero": "OC-0009"}),  # sin coincidencia
        ("orden_compra", None),  # el candidato no tiene valores validados (RN-02)
    ],
)
def test_rf_06_sin_candidato_no_hay_sugerencia(
    aplicacion: Any, e: Equipo, tipo: str, validados: dict[str, str] | None
) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    if validados is None:
        documento(e.responsable, tramite_id, "Orden sin validar")
    else:
        documento(e.responsable, tramite_id, "Orden", "orden_compra", validados)
    campos = {"cuit_emisor" if tipo == "factura" else "cuit_proveedor": CUIT, "numero": "OC-0001"}
    nuevo = procesado(aplicacion, e.responsable, tramite_id, tipo, campos)
    assert _sugerencia(e, tramite_id, nuevo["id"]) is None


def test_rf_06_compara_con_lo_validado_y_no_con_lo_sugerido(aplicacion: Any, e: Equipo) -> None:
    """La sugerencia de la IA del candidato no cuenta: solo su valor validado (RN-02)."""
    tramite_id = crear_tramite(e.responsable)["id"]
    previo = procesado(
        aplicacion, e.responsable, tramite_id, "orden_compra", {"cuit_proveedor": CUIT}
    )
    respuesta = incorporar(e.responsable, tramite_id, previo["id"], nombre="Orden")
    documento_id = respuesta.json()["id"]
    validar(e.responsable, tramite_id, documento_id, "tipo_documental", "orden_compra")
    validar(e.responsable, tramite_id, documento_id, "cuit_proveedor", OTRO_CUIT)
    nuevo = procesado(
        aplicacion, e.responsable, tramite_id, "orden_compra", {"cuit_proveedor": CUIT}
    )
    assert _sugerencia(e, tramite_id, nuevo["id"]) is None


# --- Confirmación, rechazo y descarte (RF-07) -----------------------------------


def test_rf_07_confirmar_la_version_la_hace_vigente(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    orden = _orden(e, tramite_id, numero="OC-0001", cuit_proveedor=CUIT)
    anterior = next(
        d for d in tramite(e.responsable, tramite_id)["documentos"] if d["id"] == orden
    )["version_vigente"]
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "orden_compra", {"numero": "OC-0001"})
    respuesta = como_version(e.responsable, tramite_id, nuevo["id"])
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["id"] == orden and cuerpo["tipo"] is None
    assert cuerpo["version_vigente"]["numero"] == anterior["numero"] + 1
    assert cuerpo["version_vigente"]["archivo_id"] == nuevo["id"]
    assert contar(e.responsable.motor, "documento", tramite_id) == 1
    actual = archivo(e.responsable, tramite_id, nuevo["id"])
    assert actual["estado_incorporacion"] == "incorporado"
    assert actual["sugerencia_version"]["estado"] == "confirmada"
    with e.responsable.motor.connect() as conexion:
        previa = conexion.execute(
            text("SELECT version_previa_id FROM atlas.version_documental WHERE id = :v"),
            {"v": cuerpo["version_vigente"]["id"]},
        ).scalar_one()
    assert previa == anterior["id"]  # RN-11: la anterior sigue en el historial
    acciones = acciones_del_tramite(e.responsable.motor, tramite_id)
    assert "version_incorporada" in acciones
    # Los valores validados son de la versión anterior: la nueva empieza sin validaciones.
    respuesta = e.cliente.get(
        f"/tramites/{tramite_id}/documentos/{orden}/validaciones", headers=e.responsable.encabezados
    )
    assert respuesta.status_code == 200
    validaciones = respuesta.json()
    assert validaciones["version"]["id"] == cuerpo["version_vigente"]["id"]
    assert validaciones["clasificacion"]["vigente"] is None
    assert all(c["vigente"] is None for c in validaciones["campos"])


def test_rf_07_rechazar_la_relacion_crea_un_documento_independiente(
    aplicacion: Any, e: Equipo
) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    _orden(e, tramite_id, numero="OC-0001")
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "orden_compra", {"numero": "OC-0001"})
    respuesta = incorporar(e.responsable, tramite_id, nuevo["id"], nombre="Otra orden")
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["version_vigente"]["numero"] == 1
    assert contar(e.responsable.motor, "documento", tramite_id) == 2
    assert (_sugerencia(e, tramite_id, nuevo["id"]) or {})["estado"] == "rechazada"
    assert "sugerencia_version_rechazada" in acciones_del_tramite(e.responsable.motor, tramite_id)


def test_rf_07_descartar_no_cambia_el_tramite(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    _orden(e, tramite_id, numero="OC-0001")
    antes = tramite(e.responsable, tramite_id)
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "orden_compra", {"numero": "OC-0001"})
    respuesta = descartar(e.responsable, tramite_id, nuevo["id"])
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado_incorporacion"] == "descartado"
    despues = tramite(e.responsable, tramite_id)
    assert (despues["estado"], despues["documentos"]) == (antes["estado"], antes["documentos"])
    assert (_sugerencia(e, tramite_id, nuevo["id"]) or {})["estado"] == "descartada"
    assert acciones_del_tramite(e.responsable.motor, tramite_id)[-1] == "archivo_descartado"
    assert descartar(e.responsable, tramite_id, nuevo["id"]).status_code == 409
    assert como_version(e.responsable, tramite_id, nuevo["id"]).status_code == 409


def test_rf_07_descartar_sin_sugerencia(e: Equipo, aplicacion: Any) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "factura", {"numero": "F-1"})
    assert descartar(e.responsable, tramite_id, nuevo["id"]).status_code == 200
    assert _sugerencia(e, tramite_id, nuevo["id"]) is None


def test_rf_07_sin_sugerencia_pendiente_no_hay_version(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "factura", {"numero": "F-1"})
    respuesta = como_version(e.responsable, tramite_id, nuevo["id"])
    assert respuesta.status_code == 409
    assert archivo(e.responsable, tramite_id, nuevo["id"])["estado_incorporacion"] == "pendiente"


def test_rnf_01_rn_07_solo_el_responsable_con_acceso(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    _orden(e, tramite_id, numero="OC-0001")
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "orden_compra", {"numero": "OC-0001"})
    ajeno = contexto(e.cliente, e.responsable.motor, "responsable_tramite")
    for operacion in (como_version, descartar):
        for ctx in (e.revisor, e.aprobador, e.administrador):
            assert operacion(ctx, tramite_id, nuevo["id"]).status_code == 403
        assert operacion(ajeno, tramite_id, nuevo["id"]).status_code == 404
        assert operacion(e.responsable, tramite_id, 999_999).status_code == 404
    assert archivo(e.responsable, tramite_id, nuevo["id"])["estado_incorporacion"] == "pendiente"


# --- RN-12 con una versión nueva ---------------------------------------------------


def test_rn_12_la_version_desplaza_el_ciclo_y_renueva_los_controles(
    aplicacion: Any, e: Equipo
) -> None:
    ids = tramite_con_conjunto(e)
    tramite_id = ids["tramite"]
    ciclo = iniciar_ciclo(e.responsable, tramite_id)
    decidida(e.revisor, ciclo["tareas"][0]["id"])
    nuevo = procesado(
        aplicacion,
        e.responsable,
        tramite_id,
        "orden_compra",
        {"numero": O_COMPLETO["numero"], "fecha": "2026-09-15"},
    )
    assert (_sugerencia(e, tramite_id, nuevo["id"]) or {})["documento_id"] == ids["orden"]
    respuesta = como_version(e.responsable, tramite_id, nuevo["id"])
    assert respuesta.status_code == 201, respuesta.text
    assert tramite(e.responsable, tramite_id)["estado"] == "borrador"
    (desplazado,) = ciclos(e.responsable, tramite_id)
    assert desplazado["estado"] == "desplazado"
    assert [t["estado"] for t in desplazado["tareas"]] == ["aprobada", "anulada"]
    acciones = acciones_del_tramite(e.responsable.motor, tramite_id)
    inicio = acciones.index("version_incorporada")
    assert acciones[inicio : inicio + 4] == [
        "version_incorporada",
        "ciclo_desplazado",
        "tarea_anulada",
        "tramite_vuelve_a_borrador",
    ]
    # La versión nueva todavía no tiene valores validados (RN-02): ningún control vigente
    # sigue usando la versión anterior de la orden.
    previa = {d["version_vigente"]["id"] for d in tramite(e.responsable, tramite_id)["documentos"]}
    for control in controles(e.responsable, tramite_id)["vigentes"]:
        if control["ejecucion"] is not None:
            assert {v["version_id"] for v in control["ejecucion"]["versiones"]} <= previa
    vigente = respuesta.json()["version_vigente"]["id"]
    validar(e.responsable, tramite_id, ids["orden"], "tipo_documental", "orden_compra")
    for campo, valor in {**O_COMPLETO, "fecha": "2026-09-15"}.items():
        validar(e.responsable, tramite_id, ids["orden"], campo, valor)
    r3 = next(
        c
        for c in controles(e.responsable, tramite_id)["vigentes"]
        if c["codigo_regla"].startswith("R3")
    )
    assert vigente in {v["version_id"] for v in r3["ejecucion"]["versiones"]}
    assert r3["resultado"] == "cumplimiento"


def test_rnf_09_sin_contenido_documental_en_los_registros(
    aplicacion: Any, e: Equipo, capsys: pytest.CaptureFixture[str]
) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    _orden(e, tramite_id, numero="OC-0001", cuit_proveedor=CUIT)
    nuevo = procesado(
        aplicacion,
        e.responsable,
        tramite_id,
        "orden_compra",
        {"numero": "OC-0001", "cuit_proveedor": CUIT},
    )
    assert como_version(e.responsable, tramite_id, nuevo["id"]).status_code == 201
    registro = json.dumps(lineas_registro(capsys.readouterr().out), ensure_ascii=False)
    assert "OC-0001" not in registro and CUIT not in registro


# --- Concurrencia ----------------------------------------------------------


def test_dos_confirmaciones_simultaneas_crean_una_sola_version(aplicacion: Any, e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    orden = _orden(e, tramite_id, numero="OC-0001")
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "orden_compra", {"numero": "OC-0001"})
    barrera = threading.Barrier(2)
    resultados: list[str] = []

    def confirmar() -> None:
        with aplicacion.state.fabrica_sesiones() as sesion:
            barrera.wait()
            try:
                tramite_bloqueado = tramites.obtener_accesible(
                    sesion, tramite_id, e.responsable.usuario_id, bloquear=True
                )
                cargas.incorporar_como_version(
                    sesion,
                    aplicacion.state.almacen,
                    tramite=tramite_bloqueado,
                    archivo_id=nuevo["id"],
                    usuario_id=e.responsable.usuario_id,
                    vigencia_pendiente_s=86_400,
                )
                sesion.commit()
                resultados.append("creada")
            except Conflicto:
                sesion.rollback()
                resultados.append("conflicto")

    hilos = [threading.Thread(target=confirmar) for _ in range(2)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    assert sorted(resultados) == ["conflicto", "creada"]
    with e.responsable.motor.connect() as conexion:
        numeros = conexion.execute(
            text("SELECT numero FROM atlas.version_documental WHERE documento_id = :d"),
            {"d": orden},
        ).scalars()
        assert sorted(numeros) == [1, 2]
    assert acciones_del_tramite(e.responsable.motor, tramite_id).count("version_incorporada") == 1


def test_rf_06_la_deteccion_es_idempotente_y_solo_para_pendientes(
    aplicacion: Any, e: Equipo
) -> None:
    """Un reintento de la persistencia no duplica la sugerencia; un archivo ya resuelto o sin
    tipo sugerido válido no recibe una nueva."""
    tramite_id = crear_tramite(e.responsable)["id"]
    _orden(e, tramite_id, numero="OC-0001")
    nuevo = procesado(aplicacion, e.responsable, tramite_id, "orden_compra", {"numero": "OC-0001"})
    with aplicacion.state.fabrica_sesiones() as sesion:
        primera = versiones.detectar(sesion, nuevo["id"], 1)
        assert primera is not None
        assert versiones.detectar(sesion, nuevo["id"], 1) is primera
        assert versiones.detectar(sesion, nuevo["id"], 99) is primera  # intento sin valores
    assert descartar(e.responsable, tramite_id, nuevo["id"]).status_code == 200
    with aplicacion.state.fabrica_sesiones() as sesion:
        assert versiones.detectar(sesion, nuevo["id"], 1) is None
    otro = procesado(aplicacion, e.responsable, tramite_id, "factura", {"numero": "F-1"})
    with aplicacion.state.fabrica_sesiones() as sesion:
        assert versiones.detectar(sesion, otro["id"], 99) is None  # sin tipo sugerido
