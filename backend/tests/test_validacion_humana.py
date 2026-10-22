"""Hito 1.5: validación humana de clasificación y campos (RF-09, RF-10, RF-12, RN-02, RN-03).

DO-2026-10-22-VAL: versión vigente (P1), Borrador o Pendiente de validación (P2), campos
después de la clasificación según el esquema del tipo validado (P3), formatos canónicos
con advertencia por dígito de CUIT (P4). PostgreSQL real y procesamiento con respuestas
fijas (P1 de DO-2026-10-22-PROC).
"""

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, eventos_del_tramite
from tests.flujo_procesamiento import contrato_procesado_e_incorporado

pytestmark = pytest.mark.integracion


@pytest.fixture
def escenario(base_migrada: Configuracion, motor_aplicacion: Engine) -> Iterator[dict[str, Any]]:
    aplicacion = crear_aplicacion(base_migrada)
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        ctx = Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
        yield {"ctx": ctx, **contrato_procesado_e_incorporado(aplicacion, ctx)}
    aplicacion.state.motor.dispose()


def ruta(e: dict[str, Any]) -> str:
    return f"/tramites/{e['tramite']['id']}/documentos/{e['documento']['id']}/validaciones"


def consultar(e: dict[str, Any], encabezados: dict[str, str] | None = None) -> httpx.Response:
    return e["ctx"].cliente.get(ruta(e), headers=encabezados or e["ctx"].encabezados)


def validar(
    e: dict[str, Any], encabezados: dict[str, str] | None = None, **cuerpo: Any
) -> httpx.Response:
    return e["ctx"].cliente.post(ruta(e), json=cuerpo, headers=encabezados or e["ctx"].encabezados)


def confirmar_clasificacion(e: dict[str, Any]) -> dict[str, Any]:
    sugerida = consultar(e).json()["clasificacion"]["sugerencia"]
    respuesta = validar(
        e,
        campo="tipo_documental",
        valor_validado=sugerida["valor"],
        valor_sugerido_id=sugerida["id"],
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def dato(e: dict[str, Any], campo: str) -> dict[str, Any]:
    datos = consultar(e).json()
    return (
        datos["clasificacion"]
        if campo == "tipo_documental"
        else next(c for c in datos["campos"] if c["campo"] == campo)
    )


def cambiar_estado(motor: Engine, tramite_id: int, estado: str) -> None:
    with motor.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE atlas.tramite SET estado = :e, motivo_cancelacion = CASE WHEN"
                " CAST(:e AS varchar) = 'cancelado' THEN 'Escenario de prueba' END WHERE id = :t"
            ),
            {"e": estado, "t": tramite_id},
        )


# --- Clasificación ----------------------------------------------------------------------


def test_rf_09_clasificacion_sugerida_pendiente_y_sin_campos(escenario: dict[str, Any]) -> None:
    datos = consultar(escenario).json()
    assert datos["tipo_validado"] is None
    assert datos["clasificacion"]["sugerencia"]["valor"] == "contrato"
    assert datos["clasificacion"]["vigente"] is None
    assert datos["campos"] == []  # P3: primero la clasificación
    assert datos["version"]["numero"] == 1


def test_rf_09_confirmar_clasificacion_establece_el_tipo_y_se_audita(
    escenario: dict[str, Any],
) -> None:
    validacion = confirmar_clasificacion(escenario)
    assert validacion["tipo"] == "confirmacion"
    assert validacion["valor_validado"] == "contrato"
    assert validacion["validador_id"] == escenario["ctx"].usuario_id
    assert validacion["version_id"] == escenario["documento"]["version_vigente"]["id"]
    detalle = (
        escenario["ctx"]
        .cliente.get(
            f"/tramites/{escenario['tramite']['id']}", headers=escenario["ctx"].encabezados
        )
        .json()
    )
    assert detalle["documentos"][0]["tipo"] == "contrato"
    (evento,) = [
        e
        for e in eventos_del_tramite(escenario["ctx"].motor, escenario["tramite"]["id"])
        if e["accion"] == "clasificacion_confirmada"
    ]
    assert evento["version_id"] == validacion["version_id"]
    assert evento["entidad_id"] == validacion["id"]


def test_rf_09_tipo_fuera_del_catalogo_rechazado(escenario: dict[str, Any]) -> None:
    respuesta = validar(escenario, campo="tipo_documental", valor_validado="acta")
    assert respuesta.status_code == 422


# --- Campos -----------------------------------------------------------------------------


def test_p3_campos_no_se_validan_antes_que_la_clasificacion(escenario: dict[str, Any]) -> None:
    respuesta = validar(escenario, campo="monto_total", valor_validado="1250000.00")
    assert respuesta.status_code == 409
    assert "clasificación" in respuesta.json()["detalle"]


def test_rf_10_campos_del_esquema_del_tipo_validado_con_sugerencia_y_pagina(
    escenario: dict[str, Any],
) -> None:
    confirmar_clasificacion(escenario)
    campos = {c["campo"]: c for c in consultar(escenario).json()["campos"]}
    assert set(campos) == {
        "contraparte",
        "cuit_contraparte",
        "fecha_celebracion",
        "vigencia_desde",
        "vigencia_hasta",
        "monto_total",
        "moneda",
    }
    monto = campos["monto_total"]["sugerencia"]
    assert monto["valor"] == "1250000.00"
    assert monto["localizador"]["pagina"] == 5
    assert monto["localizador"]["seccion"] == "4. Condiciones económicas y forma de pago"


def test_rf_12_confirmar_campo_conserva_sugerencia_actor_fecha_version_y_fuente(
    escenario: dict[str, Any],
) -> None:
    confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "monto_total")["sugerencia"]
    respuesta = validar(
        escenario,
        campo="monto_total",
        valor_validado="1250000.00",
        valor_sugerido_id=sugerida["id"],
    )
    assert respuesta.status_code == 201
    validacion = respuesta.json()
    assert validacion["tipo"] == "confirmacion"
    assert validacion["valor_sugerido_id"] == sugerida["id"]
    assert validacion["localizador"] == sugerida["localizador"]
    assert validacion["validado_en"]
    estado = dato(escenario, "monto_total")
    assert estado["vigente"]["id"] == validacion["id"]
    assert estado["sugerencia"]["valor"] == "1250000.00"


def test_rn_03_correccion_con_otra_fuente_conserva_la_sugerencia(escenario: dict[str, Any]) -> None:
    confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "contraparte")["sugerencia"]
    respuesta = validar(
        escenario,
        campo="contraparte",
        valor_validado="Servicios Integrales del Sur Sociedad Anónima",
        valor_sugerido_id=sugerida["id"],
        fuente={"pagina": 1, "fragmento": "Contraparte: Servicios Integrales del Sur S.A."},
    )
    assert respuesta.status_code == 201
    correccion = respuesta.json()
    assert correccion["tipo"] == "correccion"
    assert correccion["localizador"] == {
        "pagina": 1,
        "seccion": None,
        "fragmento": "Contraparte: Servicios Integrales del Sur S.A.",
    }
    with escenario["ctx"].motor.connect() as conexion:
        fuente = conexion.execute(
            text(
                "SELECT trabajo_id FROM atlas.referencia_fuente WHERE fragmento = :f"
                " AND archivo_id = :a AND trabajo_id IS NULL"
            ),
            {
                "f": "Contraparte: Servicios Integrales del Sur S.A.",
                "a": escenario["archivo"]["id"],
            },
        ).all()
    assert len(fuente) == 1  # la fuente indicada por la persona
    estado = dato(escenario, "contraparte")
    assert estado["sugerencia"]["valor"] == "Servicios Integrales del Sur S.A."  # RN-03


def test_rf_12_correccion_sin_otra_fuente_usa_la_de_la_sugerencia(
    escenario: dict[str, Any],
) -> None:
    confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "moneda")["sugerencia"]
    respuesta = validar(
        escenario, campo="moneda", valor_validado="USD", valor_sugerido_id=sugerida["id"]
    )
    assert respuesta.json()["tipo"] == "correccion"
    assert respuesta.json()["localizador"] == sugerida["localizador"]


def test_dt_val_reemplazo_encadenado_y_validacion_desactualizada(escenario: dict[str, Any]) -> None:
    confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "vigencia_hasta")["sugerencia"]
    primera = validar(
        escenario,
        campo="vigencia_hasta",
        valor_validado="2027-02-28",
        valor_sugerido_id=sugerida["id"],
    ).json()
    # Sin indicar cuál reemplaza: otra validación ya es la vigente.
    assert (
        validar(escenario, campo="vigencia_hasta", valor_validado="2027-03-31").status_code == 409
    )
    segunda = validar(
        escenario, campo="vigencia_hasta", valor_validado="2027-03-31", reemplaza_a_id=primera["id"]
    )
    assert segunda.status_code == 201
    assert segunda.json()["tipo"] == "sin_sugerencia"
    # Reemplazar otra vez la primera ya no es posible: solo un reemplazo se completa.
    tardia = validar(
        escenario, campo="vigencia_hasta", valor_validado="2027-04-30", reemplaza_a_id=primera["id"]
    )
    assert tardia.status_code == 409
    estado = dato(escenario, "vigencia_hasta")
    assert estado["vigente"]["valor_validado"] == "2027-03-31"
    assert [v["valor_validado"] for v in estado["historial"]] == ["2027-02-28", "2027-03-31"]


@pytest.mark.parametrize(
    ("campo", "valor", "mensaje"),
    [
        ("fecha_celebracion", "20/02/2026", "AAAA-MM-DD"),
        ("fecha_celebracion", "2026-02-30", "calendario"),
        ("monto_total", "1.250.000,00", "dos decimales"),
        ("cuit_contraparte", "30964725183", "30-12345678-9"),
        ("moneda", "pesos", "ISO 4217"),
        ("contraparte", "   ", "vacío"),
        ("numero_inexistente", "x", "esquema"),
    ],
)
def test_p4_formatos_canonicos(
    escenario: dict[str, Any], campo: str, valor: str, mensaje: str
) -> None:
    confirmar_clasificacion(escenario)
    respuesta = validar(escenario, campo=campo, valor_validado=valor)
    assert respuesta.status_code == 422
    assert mensaje in respuesta.json()["detalle"]


def test_p4_cuit_con_digito_invalido_se_acepta_con_advertencia(escenario: dict[str, Any]) -> None:
    confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "cuit_contraparte")["sugerencia"]
    respuesta = validar(
        escenario,
        campo="cuit_contraparte",
        valor_validado="30-96472518-4",
        valor_sugerido_id=sugerida["id"],
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["advertencias"] == ["cuit_digito_verificador_invalido"]
    valida = validar(
        escenario,
        campo="cuit_contraparte",
        valor_validado="30-96472518-3",
        reemplaza_a_id=respuesta.json()["id"],
        valor_sugerido_id=sugerida["id"],
    )
    assert (valida.json()["tipo"], valida.json()["advertencias"]) == ("confirmacion", [])


def test_dt_val_sugerencia_de_otro_dato_rechazada(escenario: dict[str, Any]) -> None:
    confirmar_clasificacion(escenario)
    ajena = dato(escenario, "moneda")["sugerencia"]
    respuesta = validar(
        escenario, campo="monto_total", valor_validado="1250000.00", valor_sugerido_id=ajena["id"]
    )
    assert respuesta.status_code == 422


def test_p3_corregir_el_tipo_cambia_el_esquema_y_conserva_el_historial(
    escenario: dict[str, Any],
) -> None:
    clasificacion = confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "monto_total")["sugerencia"]
    validar(
        escenario,
        campo="monto_total",
        valor_validado="1250000.00",
        valor_sugerido_id=sugerida["id"],
    )
    corregida = validar(
        escenario,
        campo="tipo_documental",
        valor_validado="factura",
        reemplaza_a_id=clasificacion["id"],
        valor_sugerido_id=clasificacion["valor_sugerido_id"],
    )
    assert corregida.json()["tipo"] == "correccion"
    datos = consultar(escenario).json()
    assert datos["tipo_validado"] == "factura"
    assert {c["campo"] for c in datos["campos"]} == {
        "numero",
        "fecha_emision",
        "emisor",
        "cuit_emisor",
        "importe_total",
        "moneda",
    }
    # RF-10: las sugerencias se extrajeron con el esquema de contrato.
    assert all(c["sugerencia"] is None and c["vigente"] is None for c in datos["campos"])
    assert [v["campo"] for v in datos["fuera_de_esquema"]] == ["monto_total"]
    registrado = validar(escenario, campo="numero", valor_validado="FC-A-0001-00001234")
    assert registrado.json()["tipo"] == "sin_sugerencia"
    acciones = [
        e["accion"] for e in eventos_del_tramite(escenario["ctx"].motor, escenario["tramite"]["id"])
    ]
    assert acciones[-3:] == ["campo_confirmado", "clasificacion_corregida", "campo_registrado"]


# --- Estados del trámite y acceso -------------------------------------------------------


@pytest.mark.parametrize(
    ("estado", "codigo"),
    [
        ("pendiente_validacion", 201),
        ("observado", 409),
        ("pendiente_aprobacion", 409),
        ("aprobado", 409),
        ("cancelado", 409),
    ],
)
def test_p2_estados_que_admiten_validar(
    escenario: dict[str, Any], estado: str, codigo: int
) -> None:
    cambiar_estado(escenario["ctx"].motor, escenario["tramite"]["id"], estado)
    sugerida = consultar(escenario).json()["clasificacion"]["sugerencia"]
    respuesta = validar(
        escenario,
        campo="tipo_documental",
        valor_validado="contrato",
        valor_sugerido_id=sugerida["id"],
    )
    assert respuesta.status_code == codigo


def test_rnf_01_validacion_solo_para_el_responsable_del_tramite(escenario: dict[str, Any]) -> None:
    motor = escenario["ctx"].motor
    _, otro = crear_cuenta(motor, "responsable_tramite")
    _, revisor = crear_cuenta(motor, "revisor_aprobador")
    _, admin = crear_cuenta(motor, "administrador_operativo")
    cuerpo = {"campo": "tipo_documental", "valor_validado": "contrato"}
    assert validar(escenario, portador(otro), **cuerpo).status_code == 404
    assert validar(escenario, portador(revisor), **cuerpo).status_code == 403
    assert consultar(escenario, portador(otro)).status_code == 404
    assert consultar(escenario, portador(admin)).status_code == 404
    ajeno = escenario["ctx"].cliente.get(
        f"/tramites/{escenario['tramite']['id']}/documentos/999999999/validaciones",
        headers=escenario["ctx"].encabezados,
    )
    assert ajeno.status_code == 404


# --- Garantías en la base ---------------------------------------------------------------


def test_rn_09_validacion_inmutable(escenario: dict[str, Any], motor_migracion: Engine) -> None:
    validacion = confirmar_clasificacion(escenario)
    sentencia = text("UPDATE atlas.validacion_humana SET valor_validado = 'factura' WHERE id = :v")
    with pytest.raises(DBAPIError, match="permission denied"), escenario["ctx"].motor.begin() as c:
        c.execute(sentencia, {"v": validacion["id"]})
    with pytest.raises(IntegrityError, match="es inmutable"), motor_migracion.begin() as c:
        c.execute(sentencia, {"v": validacion["id"]})


@pytest.mark.parametrize(
    ("columnas", "restriccion"),
    [
        ({"reemplaza_a_id": None}, "uq_validacion_humana_primera"),
        ({"reemplaza_a_id": "PRIMERA"}, "uq_validacion_humana_reemplaza_a_id"),
        ({"reemplaza_a_id": "PRIMERA", "campo": "moneda"}, "otra versión o de otro dato"),
        (
            {"reemplaza_a_id": None, "campo": "moneda", "valor_sugerido_id": "SUGERENCIA"},
            "otro archivo o de otro dato",
        ),
    ],
    ids=["dos_primeras", "dos_reemplazos", "reemplazo_de_otro_campo", "sugerencia_de_otro_campo"],
)
def test_dt_val_una_sola_cadena_por_dato_en_la_base(
    escenario: dict[str, Any], columnas: dict[str, Any], restriccion: str
) -> None:
    confirmar_clasificacion(escenario)
    sugerida = dato(escenario, "monto_total")["sugerencia"]
    primera = validar(
        escenario,
        campo="monto_total",
        valor_validado="1250000.00",
        valor_sugerido_id=sugerida["id"],
    ).json()
    validar(
        escenario, campo="monto_total", valor_validado="1250000.01", reemplaza_a_id=primera["id"]
    )
    fila = {
        "version": primera["version_id"],
        "campo": "monto_total",
        "reemplaza": None,
        "validador": escenario["ctx"].usuario_id,
        "sugerencia": None,
        "tipo": "sin_sugerencia",
    }
    for clave, valor in columnas.items():
        destino = {
            "reemplaza_a_id": "reemplaza",
            "campo": "campo",
            "valor_sugerido_id": "sugerencia",
        }[clave]
        fila[destino] = {"PRIMERA": primera["id"], "SUGERENCIA": sugerida["id"]}.get(valor, valor)
    if fila["sugerencia"] is not None:
        fila["tipo"] = "correccion"
    with (
        pytest.raises(IntegrityError, match=restriccion),
        escenario["ctx"].motor.begin() as conexion,
    ):
        conexion.execute(
            text(
                "INSERT INTO atlas.validacion_humana (version_id, clase, campo, reemplaza_a_id,"
                " validador_id, valor_sugerido_id, valor_validado, tipo) VALUES (:version, 'campo',"
                " :campo, :reemplaza, :validador, :sugerencia, '1', :tipo)"
            ),
            fila,
        )
