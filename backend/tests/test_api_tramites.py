"""Trámite, carga prefirmada, confirmación, trabajo y versión inicial.

Contra PostgreSQL real y S3/Step Functions simulados con moto.
RF-02, RF-03, RF-04, RF-05, RF-07, RF-21, RN-15
"""

import hashlib
import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from atlas.configuracion import Configuracion
from atlas.integraciones.aws import crear_cliente, nombre_ejecucion
from atlas.integraciones.puertos import ErrorIntegracion
from tests import archivos
from tests.conftest import ARN_MAQUINA_PRUEBA, lineas_registro
from tests.datos import crear_cuenta, portador
from tests.flujo_api import (
    Contexto,
    autorizar,
    cargar,
    confirmar,
    contar,
    crear_tramite,
    eventos_del_tramite,
    incorporar,
    transferir,
)

pytestmark = pytest.mark.integracion

RESPONSABLE = "responsable_tramite"
REVISOR = "revisor_aprobador"
ADMIN = "administrador_operativo"
TIPO_PDF = "application/pdf"


@pytest.fixture
def ctx(aplicacion: Any, motor_aplicacion: Engine) -> Iterator[Contexto]:
    usuario_id, sub = crear_cuenta(motor_aplicacion, RESPONSABLE)
    with TestClient(aplicacion) as cliente:
        yield Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))


# --- RF-03: crear, listar y abrir --------------------------------------------------


def estado_trabajo(archivo: dict[str, Any]) -> dict[str, Any]:
    """Estado e intento; los tiempos del servidor (OP-02) se comprueban aparte."""
    return {k: archivo["trabajo"][k] for k in ("estado", "intento")}


def test_rf_03_crear_tramite_en_borrador_y_auditado(ctx: Contexto) -> None:
    respuesta = ctx.cliente.post(
        "/tramites",
        json={"titulo": "Mantenimiento 2026", "descripcion": "Escenario ficticio"},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 201
    tramite = respuesta.json()
    assert tramite["estado"] == "borrador"
    assert tramite["responsable_id"] == ctx.usuario_id
    assert tramite["descripcion"] == "Escenario ficticio"
    assert tramite["creado_en"] and tramite["actualizado_en"]
    assert eventos_del_tramite(ctx.motor, tramite["id"]) == [
        {
            "accion": "tramite_creado",
            "entidad_tipo": "tramite",
            "entidad_id": tramite["id"],
            "actor_id": ctx.usuario_id,
            "version_id": None,
        }
    ]


@pytest.mark.parametrize("cuerpo", [{"titulo": ""}, {"titulo": "   "}, {}, {"titulo": "x" * 201}])
def test_rf_03_titulo_obligatorio(ctx: Contexto, cuerpo: dict[str, Any]) -> None:
    assert ctx.cliente.post("/tramites", json=cuerpo, headers=ctx.encabezados).status_code == 422


@pytest.mark.parametrize("roles", [(REVISOR,), (ADMIN,), ()], ids=["revisor", "admin", "sin_rol"])
def test_rnf_01_solo_el_rol_responsable_crea_tramites(
    ctx: Contexto, roles: tuple[str, ...]
) -> None:
    _, sub = crear_cuenta(ctx.motor, *roles)
    respuesta = ctx.cliente.post("/tramites", json={"titulo": "x"}, headers=portador(sub))
    assert respuesta.status_code == 403


def test_rf_03_listar_y_abrir_solo_tramites_con_acceso(ctx: Contexto) -> None:
    propio = crear_tramite(ctx)
    _, sub_otro = crear_cuenta(ctx.motor, RESPONSABLE)
    ajeno = ctx.cliente.post(
        "/tramites", json={"titulo": "Ajeno"}, headers=portador(sub_otro)
    ).json()

    listados = {t["id"] for t in ctx.cliente.get("/tramites", headers=ctx.encabezados).json()}
    assert propio["id"] in listados
    assert ajeno["id"] not in listados

    abierto = ctx.cliente.get(f"/tramites/{propio['id']}", headers=ctx.encabezados).json()
    assert abierto["documentos"] == []
    # Inexistente y sin acceso responden igual.
    for ruta in (f"/tramites/{ajeno['id']}", "/tramites/999999999"):
        assert ctx.cliente.get(ruta, headers=ctx.encabezados).status_code == 404


@pytest.mark.parametrize("roles", [(REVISOR,), (ADMIN,)], ids=["revisor", "admin"])
def test_rnf_01_sin_responsabilidad_ni_tarea_no_hay_acceso(
    ctx: Contexto, roles: tuple[str, ...]
) -> None:
    tramite = crear_tramite(ctx)
    _, sub = crear_cuenta(ctx.motor, *roles)
    encabezados = portador(sub)
    assert ctx.cliente.get(f"/tramites/{tramite['id']}", headers=encabezados).status_code == 404
    assert (
        ctx.cliente.get(f"/tramites/{tramite['id']}/archivos", headers=encabezados).status_code
        == 404
    )
    assert ctx.cliente.get("/tramites", headers=encabezados).json() == []


# --- RF-04, §5.3.1: carga prefirmada, confirmación y trabajo -----------------------


def test_rf_04_carga_confirmada_queda_pendiente_con_trabajo_iniciado(
    ctx: Contexto, configuracion_tests: Configuracion
) -> None:
    tramite = crear_tramite(ctx)
    datos = archivos.CONTRATO_PDF.read_bytes()
    carga = autorizar(ctx, tramite["id"], datos)
    assert carga["metodo"] == "PUT"
    assert carga["encabezados"] == {"Content-Type": TIPO_PDF}

    transferir(carga, datos)
    respuesta = confirmar(ctx, tramite["id"], carga["id"])
    assert respuesta.status_code == 201
    archivo = respuesta.json()
    assert archivo["estado_incorporacion"] == "pendiente"
    assert archivo["huella"] == hashlib.sha256(datos).hexdigest()
    assert archivo["tamano_bytes"] == len(datos)
    assert estado_trabajo(archivo) == {"estado": "en_ejecucion", "intento": 1}
    assert archivo["trabajo"]["creado_en"] and archivo["trabajo"]["ejecucion_iniciada_en"]

    # La carga no modifica el conjunto documental ni el estado del trámite (RF-04).
    abierto = ctx.cliente.get(f"/tramites/{tramite['id']}", headers=ctx.encabezados).json()
    assert abierto["documentos"] == []
    assert abierto["estado"] == "borrador"
    acciones = [e["accion"] for e in eventos_del_tramite(ctx.motor, tramite["id"])]
    assert acciones == ["tramite_creado", "carga_confirmada"]

    # La ejecución lleva el nombre del trabajo e intento y solo identificadores.
    sfn = crear_cliente(configuracion_tests, "stepfunctions")
    with ctx.motor.connect() as conexion:
        trabajo_id = conexion.execute(
            text("SELECT id FROM atlas.trabajo_procesamiento WHERE archivo_id = :a"),
            {"a": archivo["id"]},
        ).scalar_one()
    (ejecucion,) = [
        e
        for e in sfn.list_executions(stateMachineArn=ARN_MAQUINA_PRUEBA)["executions"]
        if e["name"] == nombre_ejecucion(trabajo_id, 1)
    ]
    entrada = json.loads(sfn.describe_execution(executionArn=ejecucion["executionArn"])["input"])
    assert entrada == {"trabajo_id": trabajo_id, "intento": 1}


def test_rf_04_confirmacion_repetida_no_duplica_archivo_ni_trabajo(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    datos = archivos.pdf()
    carga = autorizar(ctx, tramite["id"], datos)
    transferir(carga, datos)
    primera = confirmar(ctx, tramite["id"], carga["id"])
    segunda = confirmar(ctx, tramite["id"], carga["id"])
    assert (primera.status_code, segunda.status_code) == (201, 200)
    assert primera.json()["id"] == segunda.json()["id"]
    assert contar(ctx.motor, "archivo", tramite["id"]) == 1
    assert [e["accion"] for e in eventos_del_tramite(ctx.motor, tramite["id"])].count(
        "carga_confirmada"
    ) == 1


def test_rf_04_docx_del_corpus_se_admite(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_DOCX.read_bytes(), formato="docx")
    assert archivo["formato"] == "docx"


@pytest.mark.parametrize(
    ("datos_declarados", "datos_enviados", "formato", "codigo"),
    [
        (archivos.docx(), archivos.docx(), "pdf", "formato_no_coincide"),
        (archivos.pdf(clave="x"), archivos.pdf(clave="x"), "pdf", "pdf_protegido"),
        (archivos.pdf(), archivos.pdf(paginas=2), "pdf", "tamano_no_coincide"),
        (archivos.pdf(), None, "pdf", "archivo_no_recibido"),
    ],
    ids=["contenido_distinto", "pdf_protegido", "tamano_distinto", "sin_transferencia"],
)
def test_archivo_invalido_rechazado_sin_efectos(
    ctx: Contexto,
    datos_declarados: bytes,
    datos_enviados: bytes | None,
    formato: str,
    codigo: str,
) -> None:
    tramite = crear_tramite(ctx)
    carga = autorizar(ctx, tramite["id"], datos_declarados, formato)
    if datos_enviados is not None:
        transferir(carga, datos_enviados)
    respuesta = confirmar(ctx, tramite["id"], carga["id"])
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == codigo
    assert respuesta.json()["detalle"]
    assert contar(ctx.motor, "archivo", tramite["id"]) == 0
    assert [e["accion"] for e in eventos_del_tramite(ctx.motor, tramite["id"])] == [
        "tramite_creado"
    ]


@pytest.mark.parametrize(
    ("cuerpo", "estado"),
    [
        ({"nombre": "x.pdf", "formato": "pdf", "tamano_bytes": 20 * 1024 * 1024 + 1}, 422),
        ({"nombre": "x.xlsx", "formato": "xlsx", "tamano_bytes": 10}, 422),
        ({"nombre": "", "formato": "pdf", "tamano_bytes": 10}, 422),
        ({"nombre": "x.pdf", "formato": "pdf", "tamano_bytes": 0}, 422),
    ],
    ids=["excede_20mb", "formato_no_admitido", "sin_nombre", "tamano_cero"],
)
def test_comprobaciones_preliminares_antes_de_autorizar(
    ctx: Contexto, cuerpo: dict[str, Any], estado: int
) -> None:
    tramite = crear_tramite(ctx)
    respuesta = ctx.cliente.post(
        f"/tramites/{tramite['id']}/cargas", json=cuerpo, headers=ctx.encabezados
    )
    assert respuesta.status_code == estado
    with ctx.motor.connect() as conexion:
        autorizaciones = conexion.execute(
            text("SELECT count(*) FROM atlas.autorizacion_carga WHERE tramite_id = :t"),
            {"t": tramite["id"]},
        ).scalar_one()
    assert autorizaciones == 0


def test_carga_sin_confirmar_vence_a_las_24_horas(ctx: Contexto, motor_migracion: Engine) -> None:
    tramite = crear_tramite(ctx)
    datos = archivos.pdf()
    carga = autorizar(ctx, tramite["id"], datos)
    transferir(carga, datos)
    with motor_migracion.begin() as conexion:  # la aplicación no puede alterar la creación
        conexion.execute(
            text(
                "UPDATE atlas.autorizacion_carga"
                " SET creada_en = now() - interval '24 hours 1 second' WHERE id = :c"
            ),
            {"c": carga["id"]},
        )
    respuesta = confirmar(ctx, tramite["id"], carga["id"])
    assert respuesta.status_code == 409
    assert "venció" in respuesta.json()["detalle"]
    assert contar(ctx.motor, "archivo", tramite["id"]) == 0


def test_rnf_01_otro_responsable_no_confirma_ni_carga_en_tramite_ajeno(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    datos = archivos.pdf()
    carga = autorizar(ctx, tramite["id"], datos)
    transferir(carga, datos)
    _, sub_otro = crear_cuenta(ctx.motor, RESPONSABLE)
    ajeno = portador(sub_otro)
    ruta = f"/tramites/{tramite['id']}/cargas"
    assert ctx.cliente.post(f"{ruta}/{carga['id']}/confirmacion", headers=ajeno).status_code == 404
    assert (
        ctx.cliente.post(
            ruta, json={"nombre": "x.pdf", "formato": "pdf", "tamano_bytes": 10}, headers=ajeno
        ).status_code
        == 404
    )
    assert contar(ctx.motor, "archivo", tramite["id"]) == 0


def test_inicio_fallido_deja_el_trabajo_pendiente_y_registrado(
    ctx: Contexto, aplicacion: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    visibles: list[bool] = []

    class OrquestadorCaido:
        def iniciar(self, trabajo_id: int, intento: int) -> None:
            # §5.3.1: al iniciar, archivo y trabajo ya están confirmados (visibles desde
            # otra conexión), así el reconciliador puede recuperarlos si esto falla.
            with ctx.motor.connect() as otra:
                visibles.append(
                    otra.execute(
                        text("SELECT count(*) FROM atlas.trabajo_procesamiento WHERE id = :t"),
                        {"t": trabajo_id},
                    ).scalar_one()
                    == 1
                )
            raise ErrorIntegracion("sfn_inicio_incierto")

    orquestador_real = aplicacion.state.orquestador
    aplicacion.state.orquestador = OrquestadorCaido()
    tramite = crear_tramite(ctx)
    datos = archivos.pdf()
    carga = autorizar(ctx, tramite["id"], datos)
    transferir(carga, datos)
    respuesta = confirmar(ctx, tramite["id"], carga["id"])
    assert respuesta.status_code == 201
    assert estado_trabajo(respuesta.json()) == {"estado": "pendiente", "intento": 1}
    assert respuesta.json()["trabajo"]["ejecucion_iniciada_en"] is None
    assert visibles == [True]
    registros = lineas_registro(capsys.readouterr().out)
    assert any(
        r["evento"] == "inicio_procesamiento_pendiente"
        and r["codigo_error"] == "sfn_inicio_incierto"
        for r in registros
    )

    # Repetir la confirmación reintenta el mismo intento, sin duplicar el trabajo.
    aplicacion.state.orquestador = orquestador_real
    repetida = confirmar(ctx, tramite["id"], carga["id"])
    assert repetida.status_code == 200
    assert estado_trabajo(repetida.json()) == {"estado": "en_ejecucion", "intento": 1}


def test_rnf_03_registros_de_la_carga_sin_contenido_ni_urls(
    ctx: Contexto, capsys: pytest.CaptureFixture[str]
) -> None:
    tramite = crear_tramite(ctx, titulo="Título que no debe registrarse")
    datos = archivos.pdf()
    carga = autorizar(ctx, tramite["id"], datos)
    transferir(carga, datos)
    confirmar(ctx, tramite["id"], carga["id"])
    salida = capsys.readouterr().out
    assert "Título que no debe registrarse" not in salida
    assert "C-v1.pdf" not in salida
    assert "X-Amz-Signature" not in salida


# --- RF-05, RF-07: incorporación como documento nuevo --------------------------------


def test_rf_07_incorporar_crea_documento_con_version_inicial_vigente(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_PDF.read_bytes())
    respuesta = incorporar(ctx, tramite["id"], archivo["id"], nombre="Contrato C-v1")
    assert respuesta.status_code == 201
    documento = respuesta.json()
    assert documento["nombre"] == "Contrato C-v1"
    assert documento["tipo"] is None  # Sin tipo hasta validar la clasificación
    assert documento["version_vigente"]["numero"] == 1
    assert documento["version_vigente"]["archivo_id"] == archivo["id"]

    abierto = ctx.cliente.get(f"/tramites/{tramite['id']}", headers=ctx.encabezados).json()
    assert [d["id"] for d in abierto["documentos"]] == [documento["id"]]
    (listado,) = ctx.cliente.get(
        f"/tramites/{tramite['id']}/archivos", headers=ctx.encabezados
    ).json()
    assert listado["estado_incorporacion"] == "incorporado"

    (evento,) = [
        e
        for e in eventos_del_tramite(ctx.motor, tramite["id"])
        if e["accion"] == "documento_incorporado"
    ]
    assert evento["entidad_id"] == documento["id"]
    assert evento["version_id"] == documento["version_vigente"]["id"]
    assert evento["actor_id"] == ctx.usuario_id


def test_rf_07_nombre_por_defecto_es_el_declarado_en_la_carga(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    assert incorporar(ctx, tramite["id"], archivo["id"]).json()["nombre"] == "C-v1.pdf"


def test_rf_07_un_archivo_se_incorpora_una_sola_vez(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 201
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 409
    assert contar(ctx.motor, "documento", tramite["id"]) == 1


def test_rf_07_archivo_de_otro_tramite_no_se_incorpora(ctx: Contexto) -> None:
    uno, otro = crear_tramite(ctx), crear_tramite(ctx)
    archivo = cargar(ctx, otro["id"], archivos.pdf())
    assert incorporar(ctx, uno["id"], archivo["id"]).status_code == 404


def test_tabla_3_vi_incorporacion_devuelve_el_tramite_a_borrador(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    with ctx.motor.begin() as conexion:  # estado alcanzado por hitos posteriores
        conexion.execute(
            text("UPDATE atlas.tramite SET estado = 'pendiente_validacion' WHERE id = :t"),
            {"t": tramite["id"]},
        )
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 201
    abierto = ctx.cliente.get(f"/tramites/{tramite['id']}", headers=ctx.encabezados).json()
    assert abierto["estado"] == "borrador"
    assert [e["accion"] for e in eventos_del_tramite(ctx.motor, tramite["id"])][-2:] == [
        "documento_incorporado",
        "tramite_vuelve_a_borrador",
    ]


def test_rn_15_tramite_cancelado_no_admite_cargas_ni_incorporaciones(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    with ctx.motor.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE atlas.tramite SET estado = 'cancelado',"
                " motivo_cancelacion = 'Escenario de prueba' WHERE id = :t"
            ),
            {"t": tramite["id"]},
        )
    respuesta = ctx.cliente.post(
        f"/tramites/{tramite['id']}/cargas",
        json={"nombre": "x.pdf", "formato": "pdf", "tamano_bytes": 10},
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 409
    assert incorporar(ctx, tramite["id"], archivo["id"]).status_code == 409
    assert contar(ctx.motor, "documento", tramite["id"]) == 0
