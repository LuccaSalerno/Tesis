"""Firma digital simulada y cierre terminal (RF-23, RN-11, RN-15, V11, DO-2026-10-23-VER P5,
P6 y P8), contra PostgreSQL real. Cuentas y documentos sintéticos."""

import hashlib
import json
from typing import Any

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from tests import archivos
from tests.flujo_api import acciones_del_tramite, cargar, incorporar
from tests.flujo_revision import (
    Equipo,
    contexto,
    decidida,
    enviar_a_validacion,
    evidencia,
    iniciar_ciclo,
    obtener,
    tramite,
    tramite_con_conjunto,
)
from tests.flujo_vinculos import validar, vincular

pytestmark = pytest.mark.integracion

LEYENDA = "Firma digital simulada — sin validez jurídica"


@pytest.fixture
def aprobado(e: Equipo) -> dict[str, Any]:
    """Conjunto validado y vinculado con el ciclo 1 aprobado por las dos tareas."""
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    revision, final = (t["id"] for t in ciclo["tareas"])
    decidida(e.revisor, revision)
    decision = decidida(e.aprobador, final)
    assert tramite(e.responsable, ids["tramite"])["estado"] == "aprobado"
    contrato = next(v for v in ciclo["versiones"] if v["documento_id"] == ids["contrato"])
    return {**ids, "ciclo": ciclo, "version": contrato["version_id"], "decision": decision}


def firmar(ctx: Any, tramite_id: int, version_id: int) -> Any:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/firma", json={"version_id": version_id}, headers=ctx.encabezados
    )


# --- Firma y cierre (RF-23, P5, P6) -----------------------------------------------------


def test_rf_23_firma_simulada_cierra_el_tramite(e: Equipo, aprobado: dict[str, Any]) -> None:
    tramite_id = aprobado["tramite"]
    respuesta = firmar(e.aprobador, tramite_id, aprobado["version"])
    assert respuesta.status_code == 201, respuesta.text
    firma = respuesta.json()
    assert firma["leyenda"] == LEYENDA and firma["simulada"] is True
    assert (firma["version_id"], firma["ciclo_revision_id"], firma["firmante_id"]) == (
        aprobado["version"],
        aprobado["ciclo"]["id"],
        e.aprobador.usuario_id,
    )
    assert firma["documento_id"] == aprobado["contrato"]
    # P6: la referencia se recalcula desde el registro canónico expuesto.
    registro = json.loads(firma["registro_canonico"])
    assert registro["version_id"] == aprobado["version"]
    assert registro["huella_archivo"] == firma["huella_archivo"]
    assert registro["firmante_id"] == e.aprobador.usuario_id
    assert (
        hashlib.sha256(firma["registro_canonico"].encode()).hexdigest()
        == firma["referencia_integridad"]
    )
    with e.responsable.motor.connect() as conexion:
        huella = conexion.execute(
            text(
                "SELECT a.huella FROM atlas.version_documental v"
                " JOIN atlas.archivo a ON a.id = v.archivo_id WHERE v.id = :v"
            ),
            {"v": aprobado["version"]},
        ).scalar_one()
    assert firma["huella_archivo"] == huella
    assert tramite(e.responsable, tramite_id)["estado"] == "cerrado"
    assert acciones_del_tramite(e.responsable.motor, tramite_id)[-2:] == [
        "firma_simulada_aplicada",
        "tramite_cerrado",
    ]


def test_rf_23_la_firma_sigue_consultable(e: Equipo, aprobado: dict[str, Any]) -> None:
    tramite_id = aprobado["tramite"]
    firma = firmar(e.aprobador, tramite_id, aprobado["version"]).json()
    for ctx in (e.responsable, e.aprobador, e.revisor):
        assert obtener(ctx, f"/tramites/{tramite_id}/firma") == firma
    ajeno = contexto(e.cliente, e.responsable.motor, "responsable_tramite")
    obtener(ajeno, f"/tramites/{tramite_id}/firma", 404)
    obtener(e.administrador, f"/tramites/{tramite_id}/firma", 404)
    hitos = obtener(e.responsable, f"/tramites/{tramite_id}/linea-tiempo")
    firmado = next(h for h in hitos if h["accion"] == "firma_simulada_aplicada")
    assert firmado["version"]["version_id"] == aprobado["version"]
    assert hitos[-1]["accion"] == "tramite_cerrado"
    # P8: la evidencia de la decisión del ciclo firmado incluye la firma.
    datos = evidencia(e.responsable, aprobado["decision"]["id"])
    assert datos["firma"] == firma
    assert ("firma_simulada", firma["id"]) in {
        (ev["entidad_tipo"], ev["entidad_id"]) for ev in datos["eventos"]
    }


def test_rf_23_sin_firma_la_consulta_responde_404(e: Equipo, aprobado: dict[str, Any]) -> None:
    obtener(e.responsable, f"/tramites/{aprobado['tramite']}/firma", 404)
    assert evidencia(e.responsable, aprobado["decision"]["id"])["firma"] is None


# --- Quién firma (RC-P03.2, RN-07, P5) --------------------------------------------------


def test_rc_p03_2_solo_con_autorizacion_de_cierre(e: Equipo, aprobado: dict[str, Any]) -> None:
    tramite_id, version = aprobado["tramite"], aprobado["version"]
    assert firmar(e.revisor, tramite_id, version).status_code == 403  # sin autorización
    for ctx in (e.responsable, e.administrador):
        assert firmar(ctx, tramite_id, version).status_code == 403  # rol (RN-07)
    # Autorizado pero sin tarea en el ciclo: no tiene acceso al trámite.
    otro = contexto(e.cliente, e.responsable.motor, "revisor_aprobador", autorizacion_cierre=True)
    assert firmar(otro, tramite_id, version).status_code == 404
    assert tramite(e.responsable, tramite_id)["estado"] == "aprobado"
    assert "firma_simulada_aplicada" not in acciones_del_tramite(e.responsable.motor, tramite_id)


def test_v11_solo_una_version_del_ciclo_aprobado(e: Equipo, aprobado: dict[str, Any]) -> None:
    tramite_id = aprobado["tramite"]
    ajeno = tramite_con_conjunto(e)
    otra_version = tramite(e.responsable, ajeno["tramite"])["documentos"][0]["version_vigente"]
    assert firmar(e.aprobador, tramite_id, otra_version["id"]).status_code == 409
    assert firmar(e.aprobador, tramite_id, 999_999_999).status_code == 409
    assert tramite(e.responsable, tramite_id)["estado"] == "aprobado"


def test_rf_23_solo_un_tramite_aprobado(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    version = ciclo["versiones"][0]["version_id"]
    decidida(e.revisor, ciclo["tareas"][0]["id"])
    # Pendiente de aprobación: el aprobador tiene la tarea final abierta.
    assert firmar(e.aprobador, ids["tramite"], version).status_code == 409


def test_rn_12_un_cambio_documental_impide_firmar_la_version_anterior(
    e: Equipo, aprobado: dict[str, Any]
) -> None:
    tramite_id = aprobado["tramite"]
    archivo = cargar(e.responsable, tramite_id, archivos.pdf())
    assert incorporar(e.responsable, tramite_id, archivo["id"]).status_code == 201
    assert tramite(e.responsable, tramite_id)["estado"] == "borrador"
    assert firmar(e.aprobador, tramite_id, aprobado["version"]).status_code == 409


# --- Cierre terminal (RN-15, V11) -------------------------------------------------------


def test_rn_15_cerrado_no_admite_cambios(e: Equipo, aprobado: dict[str, Any]) -> None:
    tramite_id, r = aprobado["tramite"], e.responsable
    pendiente = cargar(r, tramite_id, archivos.pdf(paginas=2))
    assert firmar(e.aprobador, tramite_id, aprobado["version"]).status_code == 201
    base = f"/tramites/{tramite_id}"
    rechazadas = {
        "segunda firma": firmar(e.aprobador, tramite_id, aprobado["version"]),
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
        "envío": enviar_a_validacion(r, tramite_id),
        "subsanación": r.cliente.post(f"{base}/subsanacion", headers=r.encabezados),
        "vínculo": vincular(r, tramite_id, aprobado["contrato"], aprobado["factura"]),
    }
    for nombre, respuesta in rechazadas.items():
        assert respuesta.status_code == 409, (nombre, respuesta.text)
    respuesta = r.cliente.post(
        f"{base}/documentos/{aprobado['contrato']}/validaciones",
        json={"campo": "moneda", "valor_validado": "USD"},
        headers=r.encabezados,
    )
    assert respuesta.status_code == 409
    with pytest.raises(AssertionError):
        validar(r, tramite_id, aprobado["contrato"], "moneda", "USD")
    assert tramite(r, tramite_id)["estado"] == "cerrado"
    assert acciones_del_tramite(r.motor, tramite_id)[-1] == "tramite_cerrado"


def test_rn_11_la_firma_es_inmutable(
    e: Equipo, aprobado: dict[str, Any], motor_aplicacion: Engine
) -> None:
    firma = firmar(e.aprobador, aprobado["tramite"], aprobado["version"]).json()
    for sentencia in (
        "UPDATE atlas.firma_simulada SET firmante_id = firmante_id WHERE id = :f",
        "DELETE FROM atlas.firma_simulada WHERE id = :f",
    ):
        with motor_aplicacion.connect() as conexion, pytest.raises(DBAPIError):
            conexion.execute(text(sentencia), {"f": firma["id"]})
    with motor_aplicacion.connect() as conexion, pytest.raises(DBAPIError):
        conexion.execute(
            text(
                "INSERT INTO atlas.firma_simulada (tramite_id, ciclo_revision_id, version_id,"
                " firmante_id, referencia_integridad, firmada_en)"
                " VALUES (:t, :c, :v, :u, :r, now())"
            ),
            {
                "t": aprobado["tramite"],
                "c": aprobado["ciclo"]["id"],
                "v": aprobado["version"],
                "u": e.aprobador.usuario_id,
                "r": "0" * 64,
            },
        )  # una sola firma por trámite


def test_regla_5_la_firma_no_registra_contenido(
    e: Equipo, aprobado: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    from tests.conftest import lineas_registro

    capsys.readouterr()
    assert firmar(e.aprobador, aprobado["tramite"], aprobado["version"]).status_code == 201
    registro = json.dumps(lineas_registro(capsys.readouterr().out), ensure_ascii=False)
    assert "30-96472518-3" not in registro and "referencia" not in registro
