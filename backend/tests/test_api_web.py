"""Backend que usa la aplicación web (DO-2026-10-22-WEB): campos ausentes (F10), URL de
lectura del original (F4), nombres visibles (F5) e historial de consultas (F6).

Contra la API autenticada, PostgreSQL real y moto; documentos sintéticos (PD-07).
"""

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from tests import archivos
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, cargar, crear_tramite, eventos_del_tramite, incorporar
from tests.flujo_procesamiento import contrato_procesado_e_incorporado
from tests.flujo_revision import (
    C_COMPLETO,
    O_COMPLETO,
    Equipo,
    contexto,
    decidida,
    equipo,
    flujo_sugerido,
    iniciar_ciclo,
    obtener,
    plantilla_de_contratos,
    tramite,
    tramite_con_conjunto,
)
from tests.flujo_vinculos import documento, validar, vincular
from tests.procesamiento_fijo import EmbeddingsFijos, ModeloConsultaFijo

pytestmark = pytest.mark.integracion


@pytest.fixture
def aplicacion(base_migrada: Configuracion) -> Iterator[Any]:
    aplicacion = crear_aplicacion(base_migrada)
    aplicacion.state.embeddings = EmbeddingsFijos()
    aplicacion.state.modelo_generativo = ModeloConsultaFijo(buscar="28/02/2027")
    yield aplicacion
    aplicacion.state.motor.dispose()


@pytest.fixture
def e(aplicacion: Any, motor_aplicacion: Engine) -> Iterator[Equipo]:
    with TestClient(aplicacion) as cliente:
        actual = equipo(cliente, motor_aplicacion)
        plantilla_de_contratos(actual)
        yield actual


def ausentar(
    ctx: Contexto,
    tramite_id: int,
    documento_id: int,
    campo: str,
    motivo: str = "no_consta",
    **extra: Any,
) -> httpx.Response:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones",
        json={"campo": campo, "ausente": motivo, **extra},
        headers=ctx.encabezados,
    )


# --- F10: campos ausentes (DIF-67) -------------------------------------------------------


def test_f10_un_campo_ausente_no_inventa_valor_y_resuelve_el_flujo(e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    sin_fecha = {k: v for k, v in C_COMPLETO.items() if k != "fecha_celebracion"}
    contrato = documento(e.responsable, tramite_id, "Contrato", "contrato", sin_fecha)
    e.cliente.post(f"/tramites/{tramite_id}/envio-a-validacion", headers=e.responsable.encabezados)
    assert flujo_sugerido(e.responsable, tramite_id)["documentos_sin_validar"] == [contrato]
    respuesta = ausentar(e.responsable, tramite_id, contrato, "fecha_celebracion")
    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    assert (datos["tipo"], datos["valor_validado"], datos["motivo_ausencia"]) == (
        "ausente",
        None,
        "no_consta",
    )
    assert flujo_sugerido(e.responsable, tramite_id)["documentos_sin_validar"] == []
    assert "campo_declarado_ausente" in [
        ev["accion"] for ev in eventos_del_tramite(e.responsable.motor, tramite_id)
    ]
    vista = obtener(e.responsable, f"/tramites/{tramite_id}/documentos/{contrato}/validaciones")
    fecha = next(c for c in vista["campos"] if c["campo"] == "fecha_celebracion")
    assert fecha["vigente"]["tipo"] == "ausente"
    # Corregir después: la ausencia queda en el historial (reemplazo, no borrado).
    corregida = validar(
        e.responsable,
        tramite_id,
        contrato,
        "fecha_celebracion",
        "2026-02-20",
        fecha["vigente"]["id"],
    )
    assert (
        corregida["tipo"] == "sin_sugerencia"
        and corregida["reemplaza_a_id"] == fecha["vigente"]["id"]
    )


@pytest.mark.parametrize(
    ("cuerpo", "mensaje"),
    [
        ({"campo": "moneda"}, "valor validado o declaralo ausente"),
        ({"campo": "moneda", "valor_validado": "ARS", "ausente": "no_consta"}, "no ambas"),
        ({"campo": "tipo_documental", "ausente": "no_aplica"}, "clasificación no admite"),
        (
            {"campo": "moneda", "ausente": "no_consta", "fuente": {"pagina": 1}},
            "no lleva fuente",
        ),
    ],
)
def test_f10_rechazos_de_ausencia(e: Equipo, cuerpo: dict[str, Any], mensaje: str) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    contrato = documento(e.responsable, tramite_id, "Contrato", "contrato")
    respuesta = e.cliente.post(
        f"/tramites/{tramite_id}/documentos/{contrato}/validaciones",
        json=cuerpo,
        headers=e.responsable.encabezados,
    )
    assert respuesta.status_code == 422
    assert mensaje in respuesta.json()["detalle"]


def test_f10_las_reglas_explican_la_ausencia_declarada(e: Equipo) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    contrato = documento(e.responsable, tramite_id, "Contrato", "contrato", C_COMPLETO)
    sin_fecha = {k: v for k, v in O_COMPLETO.items() if k != "fecha"}
    orden = documento(e.responsable, tramite_id, "Orden", "orden_compra", sin_fecha)
    assert ausentar(e.responsable, tramite_id, orden, "fecha").status_code == 201
    if vincular(e.responsable, tramite_id, orden, contrato).status_code != 201:
        sugerido = obtener(e.responsable, f"/tramites/{tramite_id}/vinculos")["sugeridos"][0]
        e.cliente.post(
            f"/tramites/{tramite_id}/vinculos/{sugerido['id']}/confirmacion",
            headers=e.responsable.encabezados,
        )
    controles = obtener(e.responsable, f"/tramites/{tramite_id}/controles")["vigentes"]
    r3 = next(c for c in controles if c["codigo_regla"].startswith("R3"))
    assert r3["resultado"] == "falta_de_datos"
    assert "Declarado ausente por una persona: fecha (orden de compra)." in r3["explicacion"]
    entrada = next(v for v in r3["ejecucion"]["valores"] if v["campo"] == "fecha")
    assert (entrada["tipo"], entrada["valor_validado"]) == ("ausente", None)


def test_f10_la_ausencia_puede_descartar_una_sugerencia(
    aplicacion: Any, motor_aplicacion: Engine
) -> None:
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        ctx = Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
        procesado = contrato_procesado_e_incorporado(aplicacion, ctx)
        tramite_id, documento_id = procesado["tramite"]["id"], procesado["documento"]["id"]
        ruta = f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones"
        validar(ctx, tramite_id, documento_id, "tipo_documental", "contrato")
        moneda = next(c for c in obtener(ctx, ruta)["campos"] if c["campo"] == "moneda")
        assert moneda["sugerencia"] is not None
        respuesta = ausentar(
            ctx,
            tramite_id,
            documento_id,
            "moneda",
            "no_aplica",
            valor_sugerido_id=moneda["sugerencia"]["id"],
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["valor_sugerido_id"] == moneda["sugerencia"]["id"]
        assert respuesta.json()["localizador"] is None  # una ausencia no tiene fuente


def test_f10_la_base_impide_ausencias_en_la_clasificacion_o_sin_motivo(
    e: Equipo, conexion_aplicacion: Connection
) -> None:
    tramite_id = crear_tramite(e.responsable)["id"]
    documento(e.responsable, tramite_id, "Contrato")
    version = tramite(e.responsable, tramite_id)["documentos"][0]["version_vigente"]["id"]
    for clase, motivo, restriccion in (
        ("clasificacion", "no_consta", "ausente_es_campo"),
        ("campo", None, "ck_validacion_humana_ausente"),
    ):
        with pytest.raises(IntegrityError, match=restriccion), conexion_aplicacion.begin_nested():
            conexion_aplicacion.execute(
                text(
                    "INSERT INTO atlas.validacion_humana (version_id, clase, campo, validador_id,"
                    " tipo, motivo_ausencia) VALUES (:v, :c, 'x', :u, 'ausente', :m)"
                ),
                {"v": version, "c": clase, "u": e.responsable.usuario_id, "m": motivo},
            )


# --- F4: original de una versión ---------------------------------------------------------


def test_f4_url_de_lectura_con_las_reglas_de_acceso(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    version = ciclo["versiones"][0]["version_id"]
    ruta = f"/tramites/{ids['tramite']}/versiones/{version}/archivo"
    datos = obtener(e.responsable, ruta)
    assert datos["formato"] == "pdf" and datos["nombre"].endswith(".pdf")
    original = httpx.get(datos["url"])
    assert original.status_code == 200 and original.content.startswith(b"%PDF")
    assert obtener(e.revisor, ruta)["version_id"] == version  # versión de su ciclo
    for ctx in (e.administrador, contexto(e.cliente, e.responsable.motor, "revisor_aprobador")):
        obtener(ctx, ruta, esperado=404)
    otro = crear_tramite(e.responsable)["id"]
    obtener(e.responsable, f"/tramites/{otro}/versiones/{version}/archivo", esperado=404)
    # Una versión incorporada después no es del ciclo del revisor.
    archivo = cargar(e.responsable, ids["tramite"], archivos.pdf())
    nueva = incorporar(e.responsable, ids["tramite"], archivo["id"], nombre="Anexo").json()
    ruta_nueva = f"/tramites/{ids['tramite']}/versiones/{nueva['version_vigente']['id']}/archivo"
    obtener(e.revisor, ruta_nueva, esperado=404)
    obtener(e.responsable, ruta_nueva)


# --- F5: nombres visibles ----------------------------------------------------------------


def test_f5_nombre_visible_y_directorio(e: Equipo) -> None:
    ruta = f"/usuarios/{e.revisor.usuario_id}/nombre"
    cambio = e.cliente.put(
        ruta, json={"nombre_visible": "Laura Méndez"}, headers=e.administrador.encabezados
    )
    assert cambio.status_code == 200 and cambio.json()["nombre_visible"] == "Laura Méndez"
    assert (
        e.cliente.put(
            ruta, json={"nombre_visible": "x"}, headers=e.responsable.encabezados
        ).status_code
        == 403
    )
    assert (
        e.cliente.put(
            ruta, json={"nombre_visible": " "}, headers=e.administrador.encabezados
        ).status_code
        == 422
    )
    directorio = obtener(
        e.responsable,
        f"/usuarios/directorio?ids={e.revisor.usuario_id}&ids={e.aprobador.usuario_id}&ids=999999999",
    )
    assert directorio == [
        {"id": e.revisor.usuario_id, "nombre_visible": "Laura Méndez"},
        {"id": e.aprobador.usuario_id, "nombre_visible": None},
    ]
    assert obtener(e.revisor, "/usuarios/yo")["nombre_visible"] == "Laura Méndez"
    alta = e.cliente.post(
        "/usuarios",
        json={
            "identificador_externo": "sub-con-nombre-" + str(e.revisor.usuario_id),
            "nombre_visible": "Ana",
        },
        headers=e.administrador.encabezados,
    )
    assert alta.status_code == 201 and alta.json()["nombre_visible"] == "Ana"
    demasiados = "&".join(f"ids={i}" for i in range(101))
    assert (
        e.cliente.get(
            f"/usuarios/directorio?{demasiados}", headers=e.responsable.encabezados
        ).status_code
        == 422
    )


# --- F6: historial de consultas propias --------------------------------------------------


def test_f6_historial_de_consultas_propias(aplicacion: Any, motor_aplicacion: Engine) -> None:
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        ctx = Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
        procesado = contrato_procesado_e_incorporado(aplicacion, ctx)
        tramite_id = procesado["tramite"]["id"]
        ruta = f"/tramites/{tramite_id}/consultas"
        assert obtener(ctx, ruta) == []
        nueva = cliente.post(
            ruta, json={"pregunta": "¿Vigencia hasta cuándo?"}, headers=ctx.encabezados
        ).json()
        (registrada,) = obtener(ctx, ruta)
        assert (
            registrada["id"] == nueva["id"] and registrada["pregunta"] == "¿Vigencia hasta cuándo?"
        )
        assert registrada["afirmaciones"] == nueva["afirmaciones"]
        assert registrada["fragmentos_recuperados"] == nueva["fragmentos_recuperados"]
        _, sub_admin = crear_cuenta(motor_aplicacion, "administrador_operativo")
        assert cliente.get(ruta, headers=portador(sub_admin)).status_code == 403
        _, sub_otro = crear_cuenta(motor_aplicacion, "responsable_tramite")
        assert cliente.get(ruta, headers=portador(sub_otro)).status_code == 404


def test_f6_el_revisor_ve_solo_sus_consultas(e: Equipo) -> None:
    ids = tramite_con_conjunto(e)
    ciclo = iniciar_ciclo(e.responsable, ids["tramite"])
    decidida(e.revisor, ciclo["tareas"][0]["id"])
    ruta = f"/tramites/{ids['tramite']}/consultas"
    e.cliente.post(ruta, json={"pregunta": "¿Importe?"}, headers=e.responsable.encabezados)
    assert obtener(e.revisor, ruta) == []
    assert len(obtener(e.responsable, ruta)) == 1
