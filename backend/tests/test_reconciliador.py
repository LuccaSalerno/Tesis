"""Admisión, reconciliador e intento manual: §6.3.2 nivel A (DO-2026-10-23-REC, RC-P08).

AS-01 a AS-04 con fallos inyectados: un orquestador simulado da el estado «real» de cada
ejecución, salvo donde se usa moto. La base de pruebas es compartida, así que el
reconciliador corre con `alcance` (solo los trabajos de cada prueba) y el cupo se fija
sobre el conteo global del momento.
"""

import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from atlas.configuracion import Configuracion
from atlas.dominio.enumeraciones import EstadoTrabajo
from atlas.integraciones.aws import OrquestadorStepFunctions, crear_cliente
from atlas.integraciones.puertos import ErrorIntegracion
from atlas.operacion import lambda_reconciliador
from atlas.operacion.mantenimiento import LectorMantenimiento
from atlas.persistencia.modelos import TrabajoProcesamiento
from atlas.persistencia.motor import crear_fabrica_sesiones
from atlas.principal import crear_aplicacion
from atlas.servicios import admision, reconciliacion, resultados
from tests import archivos
from tests.conftest import ARN_MAQUINA_PRUEBA, configuracion_sin_base
from tests.datos import crear_archivo, crear_cuenta, crear_tramite, crear_usuario, portador
from tests.flujo_api import Contexto, cargar

pytestmark = pytest.mark.integracion


@dataclass
class OrquestadorSimulado:
    """`estados`: trabajo → estado real de su ejecución; sin entrada, no existe."""

    estados: dict[int, str] = field(default_factory=dict)
    iniciados: list[tuple[int, int]] = field(default_factory=list)
    falla_inicio: bool = False
    falla_consulta: bool = False

    def iniciar(self, trabajo_id: int, intento: int) -> None:
        if self.falla_inicio:
            raise ErrorIntegracion("sfn_inicio_incierto")
        self.iniciados.append((trabajo_id, intento))
        self.estados[trabajo_id] = "RUNNING"

    def estado(self, trabajo_id: int, intento: int) -> str:
        if self.falla_consulta:
            raise ErrorIntegracion("sfn_consulta_incierta")
        return self.estados.get(trabajo_id, "inexistente")


def _trabajos(motor: Engine, *estados: str) -> list[int]:
    """Archivos y trabajos confirmados en la base, con el estado indicado."""
    with motor.begin() as conexion:
        usuario = crear_usuario(conexion)
        tramite = crear_tramite(conexion, usuario)
        ids = []
        for estado in estados:
            archivo = crear_archivo(conexion, tramite, usuario, estado="pendiente")
            ids.append(
                conexion.execute(
                    text(
                        "INSERT INTO atlas.trabajo_procesamiento"
                        " (archivo_id, estado, ejecucion_iniciada_en)"
                        " VALUES (:a, CAST(:e AS varchar),"
                        " CASE WHEN CAST(:e AS varchar) = 'en_ejecucion' THEN now() END)"
                        " RETURNING id"
                    ),
                    {"a": archivo, "e": estado},
                ).scalar_one()
            )
    return ids


def _estado(motor: Engine, trabajo_id: int) -> tuple[str, int, str | None]:
    with motor.connect() as conexion:
        fila = conexion.execute(
            text(
                "SELECT estado, intento, codigo_error"
                " FROM atlas.trabajo_procesamiento WHERE id = :t"
            ),
            {"t": trabajo_id},
        ).one()
    return fila[0], fila[1], fila[2]


@pytest.fixture
def fabrica(base_migrada: Configuracion, motor_migracion: Engine) -> Any:
    return crear_fabrica_sesiones(motor_migracion)


def _en_curso(fabrica: Any) -> int:
    with fabrica() as sesion:
        return admision.en_curso(sesion)


def _reconciliar(
    fabrica: Any, orquestador: Any, alcance: list[int], cupo: int = 0, minutos: int = 3
) -> Any:
    with fabrica() as sesion:
        limite = admision.en_curso(sesion) + cupo
        return reconciliacion.reconciliar(
            sesion,
            orquestador,
            limite=limite,
            ahora=datetime.now(UTC) + timedelta(minutes=minutos),
            alcance=alcance,
        )


# --- RC-P08.9: admisión transaccional sin sobreasignación ----------------------------------


def test_rc_p08_9_doce_confirmaciones_simultaneas_con_cupo_de_diez(
    fabrica: Any, motor_migracion: Engine
) -> None:
    with motor_migracion.begin() as conexion:
        usuario = crear_usuario(conexion)
        tramite = crear_tramite(conexion, usuario)
        archivos_ids = [
            crear_archivo(conexion, tramite, usuario, estado="pendiente") for _ in range(12)
        ]
    limite = _en_curso(fabrica) + 10
    barrera = threading.Barrier(12)
    resultados_hilos: dict[int, EstadoTrabajo] = {}

    def confirmar(archivo_id: int) -> None:
        with fabrica() as sesion:
            trabajo = TrabajoProcesamiento(archivo_id=archivo_id, intento=1)
            sesion.add(trabajo)
            barrera.wait()
            resultados_hilos[archivo_id] = admision.admitir(sesion, trabajo, limite)
            sesion.commit()

    hilos = [threading.Thread(target=confirmar, args=(a,)) for a in archivos_ids]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    estados = list(resultados_hilos.values())
    assert estados.count(EstadoTrabajo.PENDIENTE) == 10
    assert estados.count(EstadoTrabajo.EN_ESPERA) == 2


# --- AS-01: trabajo demorado o en espera, consultable y admitido por antigüedad --------------


def test_as_01_en_espera_se_admite_por_antiguedad_cuando_hay_cupo(
    fabrica: Any, motor_migracion: Engine
) -> None:
    primero, segundo = _trabajos(motor_migracion, "en_espera", "en_espera")
    orquestador = OrquestadorSimulado()
    sin_cupo = _reconciliar(fabrica, orquestador, [primero, segundo], cupo=0)
    assert sin_cupo.admitidos == [] and _estado(motor_migracion, primero)[0] == "en_espera"
    resumen = _reconciliar(fabrica, orquestador, [primero, segundo], cupo=1)
    assert resumen.admitidos == [primero] and orquestador.iniciados == [(primero, 1)]
    assert _estado(motor_migracion, primero)[0] == "en_ejecucion"
    assert _estado(motor_migracion, segundo)[0] == "en_espera"


# --- AS-02: inicio fallido o incierto, recuperado una sola vez -------------------------------


def test_as_02_inicio_incierto_se_recupera_sin_duplicar(
    fabrica: Any, motor_migracion: Engine
) -> None:
    sin_ejecucion, aceptada = _trabajos(motor_migracion, "pendiente", "pendiente")
    orquestador = OrquestadorSimulado(estados={aceptada: "RUNNING"})
    reciente = _reconciliar(fabrica, orquestador, [sin_ejecucion, aceptada], minutos=0)
    assert reciente.iniciados == [] and reciente.reconocidos == []  # dentro de los 2 minutos
    resumen = _reconciliar(fabrica, orquestador, [sin_ejecucion, aceptada])
    assert resumen.iniciados == [sin_ejecucion] and resumen.reconocidos == [aceptada]
    # La solicitud aceptada no se repite: una sola ejecución por intento.
    assert orquestador.iniciados == [(sin_ejecucion, 1)]
    otra = _reconciliar(fabrica, orquestador, [sin_ejecucion, aceptada])
    assert otra.iniciados == [] and orquestador.iniciados == [(sin_ejecucion, 1)]
    assert {_estado(motor_migracion, t)[0] for t in (sin_ejecucion, aceptada)} == {"en_ejecucion"}


def test_as_02_si_el_inicio_vuelve_a_fallar_queda_pendiente(
    fabrica: Any, motor_migracion: Engine
) -> None:
    (trabajo,) = _trabajos(motor_migracion, "pendiente")
    resumen = _reconciliar(fabrica, OrquestadorSimulado(falla_inicio=True), [trabajo])
    assert resumen.sin_resolver == [trabajo] and _estado(motor_migracion, trabajo)[0] == "pendiente"
    consulta = _reconciliar(fabrica, OrquestadorSimulado(falla_consulta=True), [trabajo])
    assert consulta.sin_resolver == [trabajo]


def test_as_02_estado_real_con_step_functions(moto_local: str) -> None:
    configuracion = configuracion_sin_base(aws_endpoint_url=moto_local)
    orquestador = OrquestadorStepFunctions(
        crear_cliente(configuracion, "stepfunctions"), ARN_MAQUINA_PRUEBA
    )
    trabajo = int(uuid.uuid4().int % 10**9)
    assert orquestador.estado(trabajo, 1) == "inexistente"
    orquestador.iniciar(trabajo, 1)
    assert orquestador.estado(trabajo, 1) in ("RUNNING", "SUCCEEDED")
    ajena = OrquestadorStepFunctions(
        crear_cliente(configuracion, "stepfunctions"), "arn:aws:states:us-east-1:1:stateMachine:x"
    )
    with pytest.raises(ErrorIntegracion, match="sfn_consulta_fallida"):
        ajena.estado(trabajo, 1)


# --- AS-03: fallo definitivo, sin reintentos indefinidos ni cambio del trámite --------------


def test_as_03_ejecucion_terminada_o_vencida_pasa_a_fallido(
    fabrica: Any, motor_migracion: Engine
) -> None:
    terminada, vencida, en_curso, pendiente_terminada = _trabajos(
        motor_migracion, "en_ejecucion", "en_ejecucion", "en_ejecucion", "pendiente"
    )
    orquestador = OrquestadorSimulado(
        estados={
            terminada: "FAILED",
            vencida: "RUNNING",
            en_curso: "RUNNING",
            pendiente_terminada: "TIMED_OUT",
        }
    )
    resumen = _reconciliar(fabrica, orquestador, [terminada, en_curso, pendiente_terminada])
    assert sorted(resumen.interrumpidos) == sorted([terminada, pendiente_terminada])
    assert _estado(motor_migracion, terminada) == ("fallido", 1, "ejecucion_interrumpida")
    assert _estado(motor_migracion, en_curso)[0] == "en_ejecucion"
    vencimiento = _reconciliar(fabrica, orquestador, [vencida], minutos=31)
    assert vencimiento.vencidos == [vencida]
    assert _estado(motor_migracion, vencida) == ("fallido", 1, "tiempo_agotado")
    consulta = _reconciliar(fabrica, OrquestadorSimulado(falla_consulta=True), [en_curso])
    assert consulta.sin_resolver == [en_curso] and orquestador.iniciados == []


# --- RNF-06 y AS-04: intento manual, sin huérfanos y con descarte del intento anterior ------


@pytest.fixture
def cliente(base_migrada: Configuracion) -> Iterator[TestClient]:
    aplicacion = crear_aplicacion(base_migrada)
    with TestClient(aplicacion) as cliente:
        yield cliente
    aplicacion.state.motor.dispose()


def test_rnf_06_as_04_intento_manual_tras_fallo(
    cliente: TestClient, motor_aplicacion: Engine, motor_migracion: Engine, fabrica: Any
) -> None:
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    ctx = Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
    tramite = cliente.post(
        "/tramites", json={"titulo": "Reintento"}, headers=ctx.encabezados
    ).json()["id"]
    archivo = cargar(ctx, tramite, archivos.pdf())
    trabajo_id = archivo["trabajo"] and _trabajo_de(motor_migracion, archivo["id"])
    ruta = f"/tramites/{tramite}/archivos/{archivo['id']}/reintento"
    assert cliente.post(ruta, headers=ctx.encabezados).status_code == 409  # no está fallido
    estado_tramite = cliente.get(f"/tramites/{tramite}", headers=ctx.encabezados).json()["estado"]
    with motor_migracion.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE atlas.trabajo_procesamiento"
                " SET estado = 'fallido', codigo_error = 'contenido_vacio' WHERE id = :t"
            ),
            {"t": trabajo_id},
        )
    _, sub_otro = crear_cuenta(motor_aplicacion, "responsable_tramite")
    assert cliente.post(ruta, headers=portador(sub_otro)).status_code == 404
    _, sub_admin = crear_cuenta(motor_aplicacion, "administrador_operativo")
    assert cliente.post(ruta, headers=portador(sub_admin)).status_code == 403
    respuesta = cliente.post(ruta, headers=ctx.encabezados)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["trabajo"]["intento"] == 2
    assert respuesta.json()["trabajo"]["estado"] in ("pendiente", "en_ejecucion")
    # El fallo técnico y el reintento no cambian el estado funcional del trámite.
    assert (
        cliente.get(f"/tramites/{tramite}", headers=ctx.encabezados).json()["estado"]
        == estado_tramite
    )
    with motor_migracion.connect() as conexion:
        eventos = conexion.execute(
            text(
                "SELECT count(*) FROM atlas.evento_auditoria"
                " WHERE tramite_id = :t AND accion = 'procesamiento_reintentado'"
            ),
            {"t": tramite},
        ).scalar_one()
        trabajos = conexion.execute(
            text("SELECT count(*) FROM atlas.trabajo_procesamiento WHERE archivo_id = :a"),
            {"a": archivo["id"]},
        ).scalar_one()
    assert eventos == 1 and trabajos == 1  # sin trabajos huérfanos ni duplicados
    # AS-04: un resultado tardío del intento 1 se descarta.
    with fabrica() as sesion:
        estado = resultados.persistir(
            sesion,
            trabajo_id=trabajo_id,
            intento=1,
            clasificacion=None,
            extraccion=None,
            indexacion=None,  # type: ignore[arg-type]
        )
    assert estado == "descartado"


def _trabajo_de(motor: Engine, archivo_id: int) -> int:
    with motor.connect() as conexion:
        return int(
            conexion.execute(
                text("SELECT id FROM atlas.trabajo_procesamiento WHERE archivo_id = :a"),
                {"a": archivo_id},
            ).scalar_one()
        )


# --- RC-P08.12: el reconciliador no actúa fuera de `active` ----------------------------------


def test_rc_p08_12_lambda_omitida_en_mantenimiento_y_completa_en_active(
    fabrica: Any, motor_migracion: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    configuracion = configuracion_sin_base()
    offline = LectorMantenimiento(lambda: b'{"estado": "offline"}')
    monkeypatch.setattr(
        lambda_reconciliador,
        "_dependencias",
        lambda: (configuracion, fabrica, OrquestadorSimulado(), offline),
    )
    assert lambda_reconciliador.manejar({}, None) == {
        "resultado": "omitido",
        "operacion": "offline",
    }
    roto = LectorMantenimiento(lambda: b"no es json")
    monkeypatch.setattr(
        lambda_reconciliador,
        "_dependencias",
        lambda: (configuracion, fabrica, OrquestadorSimulado(), roto),
    )
    assert lambda_reconciliador.manejar({}, None)["operacion"] == "desconocida"
    alcance_vacio = configuracion.model_copy(update={"procesamiento_limite_concurrencia": 1})
    monkeypatch.setattr(
        reconciliacion, "reconciliar", lambda sesion, o, limite: reconciliacion.Resumen()
    )
    monkeypatch.setattr(
        lambda_reconciliador,
        "_dependencias",
        lambda: (alcance_vacio, fabrica, OrquestadorSimulado(), LectorMantenimiento.fijo_active()),
    )
    respuesta = lambda_reconciliador.manejar({}, None)
    assert respuesta["resultado"] == "completado" and respuesta["admitidos"] == 0


def test_rc_p08_3_dependencias_de_la_lambda(
    moto_local: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    for fuente in ("s3", "fija_active"):
        configuracion = configuracion_sin_base(
            aws_endpoint_url=moto_local, mantenimiento_fuente=fuente
        )
        monkeypatch.setattr(
            lambda_reconciliador, "obtener_configuracion", lambda c=configuracion: c
        )
        lambda_reconciliador._dependencias.cache_clear()
        _, fabrica, orquestador, lector = lambda_reconciliador._dependencias()
        assert isinstance(orquestador, OrquestadorStepFunctions) and callable(fabrica)
        assert (lector._leer is None) is (fuente == "fija_active")
    lambda_reconciliador._dependencias.cache_clear()
