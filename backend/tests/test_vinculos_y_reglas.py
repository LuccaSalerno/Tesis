"""Vínculos documentales y reglas de consistencia R1 a R4.

RF-14, RF-15, RF-16, RN-02, RN-05, RN-06.
Contra PostgreSQL real; los documentos son PDF sintéticos con valores del oráculo de
la cadena de evidencia
registrados por una persona (las reglas solo usan valores validados).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, crear_tramite, eventos_del_tramite
from tests.flujo_procesamiento import contrato_procesado_e_incorporado
from tests.flujo_vinculos import (
    C_V1,
    CUIT,
    F_V1,
    F_V2,
    O_V1,
    O_V2,
    OTRO_CUIT,
    conjunto,
    control,
    controles,
    documento,
    resolver,
    resultados,
    validar,
    vincular,
    vinculos,
)

pytestmark = pytest.mark.integracion

RESPONSABLE = "responsable_tramite"


@pytest.fixture
def ctx(aplicacion: Any, motor_aplicacion: Engine) -> Iterator[Contexto]:
    usuario_id, sub = crear_cuenta(motor_aplicacion, RESPONSABLE)
    with TestClient(aplicacion) as cliente:
        yield Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))


@pytest.fixture
def par(ctx: Contexto) -> dict[str, int]:
    """Trámite con una orden y un contrato validados, sin vincular (CUIT distintos)."""
    tramite = crear_tramite(ctx)["id"]
    contrato = documento(ctx, tramite, "Contrato", "contrato", C_V1)
    orden = documento(ctx, tramite, "Orden", "orden_compra", {**O_V1, "cuit_proveedor": OTRO_CUIT})
    return {"tramite": tramite, "contrato": contrato, "orden": orden}


def cambiar_estado(motor: Engine, tramite_id: int, estado: str) -> None:
    with motor.begin() as conexion:
        conexion.execute(
            text("UPDATE atlas.tramite SET estado = :e WHERE id = :t"),
            {"e": estado, "t": tramite_id},
        )


def estado_tramite(motor: Engine, tramite_id: int) -> str:
    with motor.connect() as conexion:
        return str(
            conexion.execute(
                text("SELECT estado FROM atlas.tramite WHERE id = :t"), {"t": tramite_id}
            ).scalar_one()
        )


def acciones(motor: Engine, tramite_id: int) -> list[str]:
    return [e["accion"] for e in eventos_del_tramite(motor, tramite_id)]


# --- RF-14 y RN-05: vínculo manual ----------------------------------------------------


def test_rf_14_rn_05_vinculo_manual_rige_de_inmediato_y_se_audita(
    ctx: Contexto, par: dict[str, int]
) -> None:
    respuesta = vincular(ctx, par["tramite"], par["orden"], par["contrato"])
    assert respuesta.status_code == 201, respuesta.text
    vinculo = respuesta.json()
    assert vinculo["estado"] == "confirmado" and vinculo["origen"] == "manual"
    assert vinculo["tipo"] == "campos" and vinculo["creado_por_id"] == ctx.usuario_id
    assert vinculo["justificacion"] == "Comparten el CUIT del proveedor"
    assert vinculos(ctx, par["tramite"])["confirmados"] == [vinculo]
    eventos = eventos_del_tramite(ctx.motor, par["tramite"])
    creado = next(e for e in eventos if e["accion"] == "vinculo_creado")
    assert (creado["entidad_id"], creado["actor_id"]) == (vinculo["id"], ctx.usuario_id)


def test_rf_14_vinculo_por_referencia_registra_la_fuente_en_el_origen(
    ctx: Contexto, par: dict[str, int]
) -> None:
    fuente = {"pagina": 1, "seccion": "Encabezado", "fragmento": "Contrato marco"}
    respuesta = vincular(
        ctx,
        par["tramite"],
        par["orden"],
        par["contrato"],
        tipo="referencia",
        justificacion="La orden cita el contrato marco",
        fuente=fuente,
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["fuente"] == fuente
    with ctx.motor.connect() as conexion:
        archivo_fuente, archivo_origen = conexion.execute(
            text(
                "SELECT f.archivo_id, v.archivo_id FROM atlas.vinculo_documental l"
                " JOIN atlas.referencia_fuente f ON f.id = l.fuente_id"
                " JOIN atlas.documento d ON d.id = l.documento_origen_id"
                " JOIN atlas.version_documental v ON v.id = d.version_vigente_id"
                " WHERE l.id = :l"
            ),
            {"l": respuesta.json()["id"]},
        ).one()
    assert archivo_fuente == archivo_origen


@pytest.mark.parametrize(
    ("cuerpo", "codigo"),
    [
        ({"tipo": "campos", "fuente": {"pagina": 1}}, 422),  # solo la referencia indica fuente
        ({"tipo": "referencia", "fuente": {}}, 422),  # fuente sin localizador
        ({"justificacion": "   "}, 422),
        ({"tipo": "otro"}, 422),
        ({"extra": 1}, 422),
    ],
)
def test_rf_14_datos_del_vinculo_invalidos(
    ctx: Contexto, par: dict[str, int], cuerpo: dict[str, Any], codigo: int
) -> None:
    respuesta = vincular(ctx, par["tramite"], par["orden"], par["contrato"], **cuerpo)
    assert respuesta.status_code == codigo, respuesta.text
    assert vinculos(ctx, par["tramite"])["confirmados"] == []


def test_rf_14_un_documento_no_se_vincula_consigo_mismo(ctx: Contexto, par: dict[str, int]) -> None:
    assert vincular(ctx, par["tramite"], par["orden"], par["orden"]).status_code == 422


def test_rf_14_vinculos_entre_tramites_se_rechazan(ctx: Contexto, par: dict[str, int]) -> None:
    otro = crear_tramite(ctx, "Otro trámite")["id"]
    ajeno = documento(ctx, otro, "Ajeno", "contrato", C_V1)
    assert vincular(ctx, par["tramite"], par["orden"], ajeno).status_code == 404
    assert vincular(ctx, otro, par["orden"], ajeno).status_code == 404
    assert vincular(ctx, par["tramite"], par["orden"], 999_999_999).status_code == 404


def test_rf_14_un_solo_vinculo_activo_por_par_en_cualquier_direccion(
    ctx: Contexto, par: dict[str, int]
) -> None:
    assert vincular(ctx, par["tramite"], par["orden"], par["contrato"]).status_code == 201
    assert vincular(ctx, par["tramite"], par["orden"], par["contrato"]).status_code == 409
    assert vincular(ctx, par["tramite"], par["contrato"], par["orden"]).status_code == 409


def test_rf_14_p2_eliminar_es_baja_logica_y_conserva_el_historial(
    ctx: Contexto, par: dict[str, int]
) -> None:
    vinculo = vincular(ctx, par["tramite"], par["orden"], par["contrato"]).json()
    antes = controles(ctx, par["tramite"], historial=True)["historial"]
    assert len(antes) == 2  # R2 y R3
    respuesta = resolver(ctx, par["tramite"], vinculo["id"], "eliminacion")
    assert respuesta.status_code == 200, respuesta.text
    eliminado = respuesta.json()
    assert eliminado["estado"] == "eliminado"
    assert eliminado["resuelto_por_id"] == ctx.usuario_id and eliminado["resuelto_en"]
    lista = vinculos(ctx, par["tramite"])
    assert lista["confirmados"] == [] and lista["resueltos"] == []
    assert vinculos(ctx, par["tramite"], historial=True)["resueltos"] == [eliminado]
    despues = controles(ctx, par["tramite"], historial=True)
    assert despues["historial"] == antes  # las ejecuciones no se borran ni cambian
    assert {c["resultado"] for c in despues["vigentes"]} == {"no_aplicable"}
    assert "vinculo_eliminado" in acciones(ctx.motor, par["tramite"])
    # El par queda libre para un vínculo nuevo, que vuelve a ejecutar las reglas.
    assert vincular(ctx, par["tramite"], par["orden"], par["contrato"]).status_code == 201
    assert len(controles(ctx, par["tramite"], historial=True)["historial"]) == 4


def test_rf_14_un_vinculo_eliminado_no_vuelve_a_eliminarse(
    ctx: Contexto, par: dict[str, int]
) -> None:
    vinculo = vincular(ctx, par["tramite"], par["orden"], par["contrato"]).json()
    assert resolver(ctx, par["tramite"], vinculo["id"], "eliminacion").status_code == 200
    assert resolver(ctx, par["tramite"], vinculo["id"], "eliminacion").status_code == 409
    assert resolver(ctx, par["tramite"], vinculo["id"], "confirmacion").status_code == 409


def test_rf_14_vinculo_inexistente_o_de_otro_tramite(ctx: Contexto, par: dict[str, int]) -> None:
    vinculo = vincular(ctx, par["tramite"], par["orden"], par["contrato"]).json()
    otro = crear_tramite(ctx, "Otro")["id"]
    assert resolver(ctx, otro, vinculo["id"], "eliminacion").status_code == 404
    assert resolver(ctx, par["tramite"], 999_999_999, "rechazo").status_code == 404


# --- RF-15 y RN-05: vínculos sugeridos ------------------------------------------------


def test_rf_15_cuit_validado_coincidente_genera_una_sugerencia_pendiente(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    contrato = documento(ctx, tramite, "Contrato", "contrato", C_V1)
    orden = documento(ctx, tramite, "Orden", "orden_compra", O_V2)
    lista = vinculos(ctx, tramite)
    assert lista["confirmados"] == []
    (sugerido,) = lista["sugeridos"]
    assert (sugerido["documento_origen_id"], sugerido["documento_destino_id"]) == (orden, contrato)
    assert sugerido["origen"] == "automatico" and sugerido["estado"] == "pendiente"
    assert sugerido["tipo"] == "campos" and sugerido["creado_por_id"] is None
    assert CUIT in sugerido["justificacion"]
    # RN-05: pendiente, sin efecto: no hay ejecuciones de reglas.
    assert controles(ctx, tramite, historial=True)["historial"] == []
    evento = next(
        e for e in eventos_del_tramite(ctx.motor, tramite) if e["accion"] == "vinculo_sugerido"
    )
    assert evento["actor_id"] is None  # lo sugiere el sistema


def test_rf_15_confirmar_la_sugerencia_la_aplica_y_ejecuta_las_reglas(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    documento(ctx, tramite, "Contrato", "contrato", C_V1)
    documento(ctx, tramite, "Orden", "orden_compra", O_V1)
    (sugerido,) = vinculos(ctx, tramite)["sugeridos"]
    respuesta = resolver(ctx, tramite, sugerido["id"], "confirmacion")
    assert respuesta.status_code == 200, respuesta.text
    confirmado = respuesta.json()
    assert confirmado["estado"] == "confirmado" and confirmado["resuelto_por_id"] == ctx.usuario_id
    assert vinculos(ctx, tramite) == {"confirmados": [confirmado], "sugeridos": [], "resueltos": []}
    assert resultados(ctx, tramite) == {
        "R1": "no_aplicable",
        "R2": "cumplimiento",
        "R3": "advertencia",
        "R4": "no_aplicable",
    }
    assert "vinculo_confirmado" in acciones(ctx.motor, tramite)
    # Confirmado no se confirma ni se rechaza otra vez.
    assert resolver(ctx, tramite, sugerido["id"], "confirmacion").status_code == 409
    assert resolver(ctx, tramite, sugerido["id"], "rechazo").status_code == 409


def test_rf_15_rechazar_la_sugerencia_no_tiene_efecto_ni_se_repite(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    documento(ctx, tramite, "Contrato", "contrato", C_V1)
    orden = documento(ctx, tramite, "Orden", "orden_compra", O_V1)
    (sugerido,) = vinculos(ctx, tramite)["sugeridos"]
    respuesta = resolver(ctx, tramite, sugerido["id"], "rechazo")
    assert respuesta.status_code == 200 and respuesta.json()["estado"] == "rechazado"
    assert vinculos(ctx, tramite)["sugeridos"] == []
    assert controles(ctx, tramite, historial=True)["historial"] == []
    # Revalidar el CUIT no vuelve a sugerir un par rechazado.
    vigente = ctx.cliente.get(
        f"/tramites/{tramite}/documentos/{orden}/validaciones", headers=ctx.encabezados
    ).json()
    anterior = next(c for c in vigente["campos"] if c["campo"] == "cuit_proveedor")["vigente"]
    validar(ctx, tramite, orden, "cuit_proveedor", CUIT, reemplaza_a_id=anterior["id"])
    assert vinculos(ctx, tramite)["sugeridos"] == []
    assert "vinculo_rechazado" in acciones(ctx.motor, tramite)


def test_rf_15_una_sugerencia_se_rechaza_no_se_elimina(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    documento(ctx, tramite, "Factura", "factura", F_V1)
    documento(ctx, tramite, "Orden", "orden_compra", O_V1)
    (sugerido,) = vinculos(ctx, tramite)["sugeridos"]
    assert resolver(ctx, tramite, sugerido["id"], "eliminacion").status_code == 409


def test_rf_15_sin_cuit_coincidente_o_sin_validar_no_se_sugiere(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    documento(ctx, tramite, "Contrato", "contrato", C_V1)
    documento(ctx, tramite, "Orden", "orden_compra", {**O_V1, "cuit_proveedor": OTRO_CUIT})
    documento(ctx, tramite, "Factura sin CUIT", "factura", {"moneda": "ARS"})
    documento(ctx, tramite, "Sin clasificar")
    documento(ctx, tramite, "Presupuesto", "presupuesto", {"cuit_proveedor": CUIT})
    assert vinculos(ctx, tramite)["sugeridos"] == []


def test_rf_15_no_se_sugiere_un_par_ya_vinculado(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    contrato = documento(ctx, tramite, "Contrato", "contrato")
    orden = documento(ctx, tramite, "Orden", "orden_compra")
    assert vincular(ctx, tramite, orden, contrato).status_code == 201
    validar(ctx, tramite, contrato, "cuit_contraparte", CUIT)
    validar(ctx, tramite, orden, "cuit_proveedor", CUIT)
    assert vinculos(ctx, tramite)["sugeridos"] == []


# --- RF-16, RN-02 y RN-06: reglas de consistencia -------------------------------------


@pytest.mark.parametrize(
    ("orden", "factura", "esperado"),
    [
        (O_V1, F_V2, ["cumplimiento", "cumplimiento", "advertencia", "cumplimiento"]),
        (O_V2, F_V1, ["cumplimiento", "cumplimiento", "cumplimiento", "advertencia"]),
        (O_V2, F_V2, ["cumplimiento", "cumplimiento", "cumplimiento", "cumplimiento"]),
    ],
    ids=["C-v1+O-v1+F-v2", "C-v1+O-v2+F-v1", "C-v1+O-v2+F-v2"],
)
def test_rf_16_resultados_del_oraculo_por_la_api(
    ctx: Contexto, orden: dict[str, str], factura: dict[str, str], esperado: list[str]
) -> None:
    tramite = crear_tramite(ctx)["id"]
    conjunto(ctx, tramite, orden, factura)
    assert list(resultados(ctx, tramite).values()) == esperado
    # RN-06: las advertencias no aprueban, no observan ni cambian el estado del trámite.
    assert estado_tramite(ctx.motor, tramite) == "borrador"


def test_rf_16_v3_ejecucion_con_regla_versiones_valores_validados_y_resultado(
    ctx: Contexto,
) -> None:
    tramite = crear_tramite(ctx)["id"]
    ids = conjunto(ctx, tramite, O_V1, F_V2)
    r3 = control(ctx, tramite, "R3")
    assert (r3["codigo_regla"], r3["version_regla"]) == ("R3-VIGENCIA-OC-CONTRATO", "v1")
    assert r3["resultado"] == "advertencia"
    assert r3["explicacion"] == (
        "La fecha de la orden de compra (2027-03-15) está fuera de la vigencia del contrato"
        " (del 2026-03-01 al 2027-02-28)."
    )
    ejecucion = r3["ejecucion"]
    assert {v["papel"]: v["documento_id"] for v in ejecucion["versiones"]} == {
        "contrato": ids["contrato"],
        "orden_compra": ids["orden"],
    }
    valores = {(v["papel"], v["campo"]): v["valor_validado"] for v in ejecucion["valores"]}
    assert valores == {
        ("contrato", "vigencia_desde"): "2026-03-01",
        ("contrato", "vigencia_hasta"): "2027-02-28",
        ("orden_compra", "fecha"): "2027-03-15",
    }
    # Las entradas son las validaciones vigentes de esas versiones (RN-02).
    with ctx.motor.connect() as conexion:
        esperadas = set(
            conexion.execute(
                text(
                    "SELECT v.id FROM atlas.validacion_humana v"
                    " JOIN atlas.documento d ON d.version_vigente_id = v.version_id"
                    " WHERE d.id IN (:c, :o)"
                    " AND v.campo IN ('vigencia_desde', 'vigencia_hasta', 'fecha')"
                ),
                {"c": ids["contrato"], "o": ids["orden"]},
            ).scalars()
        )
    assert {v["validacion_id"] for v in ejecucion["valores"]} == esperadas
    detalle = ctx.cliente.get(
        f"/tramites/{tramite}/controles/{ejecucion['id']}", headers=ctx.encabezados
    )
    assert detalle.status_code == 200 and detalle.json() == ejecucion


def test_rf_16_ejecucion_de_otro_tramite_no_se_consulta(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    conjunto(ctx, tramite, O_V2, F_V2)
    ejecucion = control(ctx, tramite, "R1")["ejecucion"]["id"]
    otro = crear_tramite(ctx, "Otro")["id"]
    ruta = f"/tramites/{otro}/controles/{ejecucion}"
    assert ctx.cliente.get(ruta, headers=ctx.encabezados).status_code == 404


def test_rf_16_v3_sugerencias_sin_validar_no_alimentan_las_reglas(
    aplicacion: Any, ctx: Contexto
) -> None:
    """El contrato procesado tiene los siete campos sugeridos, pero ninguno validado."""
    procesado = contrato_procesado_e_incorporado(aplicacion, ctx)
    tramite, contrato = procesado["tramite"]["id"], procesado["documento"]["id"]
    validar(ctx, tramite, contrato, "tipo_documental", "contrato")
    orden = documento(ctx, tramite, "Orden", "orden_compra", O_V2)
    assert vincular(ctx, tramite, orden, contrato).status_code == 201
    for prefijo in ("R2", "R3"):
        c = control(ctx, tramite, prefijo)
        assert c["resultado"] == "falta_de_datos"
        assert {v["papel"] for v in c["ejecucion"]["valores"]} == {"orden_compra"}
        assert "(contrato)" in c["explicacion"]


def test_rf_16_falta_de_datos_conserva_versiones_y_se_reejecuta_al_validar(
    ctx: Contexto,
) -> None:
    tramite = crear_tramite(ctx)["id"]
    contrato = documento(ctx, tramite, "Contrato", "contrato")
    orden = documento(ctx, tramite, "Orden", "orden_compra")
    assert vincular(ctx, tramite, orden, contrato).status_code == 201
    r3 = control(ctx, tramite, "R3")
    assert r3["resultado"] == "falta_de_datos" and r3["ejecucion"]["valores"] == []
    assert len(r3["ejecucion"]["versiones"]) == 2  # versiones consideradas aunque falten datos
    assert r3["explicacion"] == (
        "Falta validar: fecha (orden de compra), vigencia desde (contrato),"
        " vigencia hasta (contrato)."
    )
    for campo in ("vigencia_desde", "vigencia_hasta"):
        validar(ctx, tramite, contrato, campo, C_V1[campo])
    validar(ctx, tramite, orden, "fecha", "2026-09-15")
    nuevo = control(ctx, tramite, "R3")
    assert nuevo["resultado"] == "cumplimiento" and nuevo["ejecucion"]["disparador"] == "validacion"


def test_rf_16_p4_corregir_un_valor_crea_una_ejecucion_nueva_y_conserva_la_anterior(
    ctx: Contexto,
) -> None:
    """EVD-C: corrección de un valor validado sin versión nueva."""
    tramite = crear_tramite(ctx)["id"]
    ids = conjunto(ctx, tramite, O_V1, F_V2)
    anterior = control(ctx, tramite, "R3")["ejecucion"]
    validaciones = ctx.cliente.get(
        f"/tramites/{tramite}/documentos/{ids['orden']}/validaciones", headers=ctx.encabezados
    ).json()
    fecha = next(c for c in validaciones["campos"] if c["campo"] == "fecha")["vigente"]
    validar(ctx, tramite, ids["orden"], "fecha", "2026-09-15", reemplaza_a_id=fecha["id"])
    actual = control(ctx, tramite, "R3")["ejecucion"]
    assert actual["id"] != anterior["id"] and actual["resultado"] == "cumplimiento"
    historial = controles(ctx, tramite, historial=True)["historial"]
    assert next(e for e in historial if e["id"] == anterior["id"]) == anterior
    # R2 compara otros campos: sus entradas no cambiaron y no se vuelve a ejecutar.
    r2 = [e for e in historial if e["codigo_regla"].startswith("R2")]
    assert len(r2) == 1


def test_rf_16_p4_validar_un_campo_ajeno_a_las_reglas_no_crea_ejecuciones(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    ids = conjunto(ctx, tramite, O_V2, F_V2)
    antes = len(controles(ctx, tramite, historial=True)["historial"])
    validar(ctx, tramite, ids["orden"], "numero", "OC-0001")
    assert len(controles(ctx, tramite, historial=True)["historial"]) == antes


def test_rf_16_p5_sin_vinculos_todas_las_reglas_son_no_aplicables(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    vigentes = controles(ctx, tramite)["vigentes"]
    assert [c["codigo_regla"] for c in vigentes] == [
        "R1-CUIT-FACTURA-OC",
        "R2-CUIT-OC-CONTRATO",
        "R3-VIGENCIA-OC-CONTRATO",
        "R4-IMPORTE-FACTURA-OC",
    ]
    for c in vigentes:
        assert c["resultado"] == "no_aplicable" and c["ejecucion"] is None
        assert c["vinculo_id"] is None
        assert (
            c["explicacion"] == "No hay documentos vinculados con los tipos que compara la regla."
        )


def test_rf_16_p5_r4_con_monedas_distintas_registra_no_aplicable(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    conjunto(ctx, tramite, O_V2, {**F_V2, "moneda": "USD"})
    r4 = control(ctx, tramite, "R4")
    assert r4["resultado"] == "no_aplicable" and r4["ejecucion"] is not None


def test_rf_16_p5_vinculo_sin_tipos_validados_se_ejecuta_al_clasificar(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    factura = documento(ctx, tramite, "Factura")
    orden = documento(ctx, tramite, "Orden", "orden_compra", O_V2)
    assert vincular(ctx, tramite, factura, orden).status_code == 201
    assert controles(ctx, tramite, historial=True)["historial"] == []
    validar(ctx, tramite, factura, "tipo_documental", "factura")
    assert {
        e["codigo_regla"][:2] for e in controles(ctx, tramite, historial=True)["historial"]
    } == {
        "R1",
        "R4",
    }


def test_rf_16_p5_vinculo_entre_tipos_sin_regla_no_ejecuta(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    factura = documento(ctx, tramite, "Factura", "factura", F_V2)
    contrato = documento(ctx, tramite, "Contrato", "contrato", C_V1)
    assert vincular(ctx, tramite, factura, contrato).status_code == 201
    assert controles(ctx, tramite, historial=True)["historial"] == []


def test_rf_21_ejecuciones_auditadas_como_acciones_del_sistema(ctx: Contexto) -> None:
    tramite = crear_tramite(ctx)["id"]
    conjunto(ctx, tramite, O_V2, F_V2)
    ejecutadas = [
        e for e in eventos_del_tramite(ctx.motor, tramite) if e["accion"] == "regla_ejecutada"
    ]
    historial = controles(ctx, tramite, historial=True)["historial"]
    assert sorted(e["entidad_id"] for e in ejecutadas) == sorted(e["id"] for e in historial)
    assert all(e["actor_id"] is None for e in ejecutadas)


# --- P7: estados del trámite y permisos (Tabla 3.II) ----------------------------------


@pytest.mark.parametrize("estado", ["pendiente_aprobacion", "observado", "aprobado", "cerrado"])
def test_estados_que_no_admiten_cambiar_vinculos(
    ctx: Contexto, par: dict[str, int], estado: str
) -> None:
    vinculo = vincular(ctx, par["tramite"], par["orden"], par["contrato"]).json()
    factura = documento(ctx, par["tramite"], "Factura")
    cambiar_estado(ctx.motor, par["tramite"], estado)
    assert resolver(ctx, par["tramite"], vinculo["id"], "eliminacion").status_code == 409
    assert vincular(ctx, par["tramite"], factura, par["orden"]).status_code == 409
    # Consultar vínculos y controles sigue permitido.
    assert vinculos(ctx, par["tramite"])["confirmados"] == [vinculo]
    assert controles(ctx, par["tramite"])["vigentes"]


def test_pendiente_de_validacion_admite_vincular(ctx: Contexto, par: dict[str, int]) -> None:
    cambiar_estado(ctx.motor, par["tramite"], "pendiente_validacion")
    assert vincular(ctx, par["tramite"], par["orden"], par["contrato"]).status_code == 201


@pytest.mark.parametrize(
    ("roles", "codigo"),
    [
        (("revisor_aprobador",), 403),
        (("administrador_operativo",), 403),
        ((RESPONSABLE,), 404),  # responsable de otro trámite: no revela que existe
    ],
)
def test_tabla_3_ii_solo_el_responsable_del_tramite_vincula(
    ctx: Contexto, par: dict[str, int], roles: tuple[str, ...], codigo: int
) -> None:
    _, sub = crear_cuenta(ctx.motor, *roles)
    ajeno = portador(sub)
    respuesta = vincular(ctx, par["tramite"], par["orden"], par["contrato"], encabezados=ajeno)
    assert respuesta.status_code == codigo
    vinculo = vincular(ctx, par["tramite"], par["orden"], par["contrato"]).json()
    ruta = f"/tramites/{par['tramite']}/vinculos/{vinculo['id']}"
    assert ctx.cliente.delete(ruta, headers=ajeno).status_code == codigo
    assert ctx.cliente.post(f"{ruta}/rechazo", headers=ajeno).status_code == codigo
    assert ctx.cliente.post(f"{ruta}/confirmacion", headers=ajeno).status_code == codigo


@pytest.mark.parametrize(
    "roles", [("revisor_aprobador",), ("administrador_operativo",), (RESPONSABLE,)]
)
def test_tabla_3_ii_vinculos_y_controles_solo_los_consulta_el_responsable(
    ctx: Contexto, par: dict[str, int], roles: tuple[str, ...]
) -> None:
    """El revisor con tarea asignada se incorpora con los ciclos de revisión."""
    _, sub = crear_cuenta(ctx.motor, *roles)
    for ruta in ("vinculos", "controles", "controles/1"):
        url = f"/tramites/{par['tramite']}/{ruta}"
        assert ctx.cliente.get(url, headers=portador(sub)).status_code == 404


def test_rf_01_sin_token_no_se_vincula(ctx: Contexto, par: dict[str, int]) -> None:
    respuesta = ctx.cliente.post(f"/tramites/{par['tramite']}/vinculos", json={})
    assert respuesta.status_code == 401


# --- Integridad en la base ------------------------------------------------


def _vinculo_en_base(ctx: Contexto, par: dict[str, int]) -> int:
    return int(vincular(ctx, par["tramite"], par["orden"], par["contrato"]).json()["id"])


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE atlas.vinculo_documental SET justificacion = 'otra' WHERE id = :v",
        "UPDATE atlas.vinculo_documental SET documento_destino_id = documento_origen_id"
        " WHERE id = :v",
        "DELETE FROM atlas.vinculo_documental WHERE id = :v",
        "UPDATE atlas.ejecucion_regla SET resultado = 'cumplimiento' WHERE vinculo_id = :v",
        "DELETE FROM atlas.ejecucion_regla WHERE vinculo_id = :v",
        "DELETE FROM atlas.entrada_regla",
        "UPDATE atlas.ejecucion_regla_version SET papel = 'factura'",
    ],
)
def test_rnf_04_la_aplicacion_no_altera_vinculos_ni_ejecuciones(
    ctx: Contexto, par: dict[str, int], conexion_aplicacion: Connection, sentencia: str
) -> None:
    vinculo = _vinculo_en_base(ctx, par)
    with pytest.raises(DBAPIError, match="permission denied"):
        conexion_aplicacion.execute(text(sentencia), {"v": vinculo})


@pytest.mark.parametrize(
    ("sentencia", "mensaje"),
    [
        (
            "UPDATE atlas.vinculo_documental SET justificacion = 'otra' WHERE id = :v",
            "solo cambian",
        ),
        ("UPDATE atlas.vinculo_documental SET estado = 'pendiente' WHERE id = :v", "no admitida"),
        ("DELETE FROM atlas.vinculo_documental WHERE id = :v", "es inmutable"),
        (
            "UPDATE atlas.ejecucion_regla SET explicacion = 'x' WHERE vinculo_id = :v",
            "es inmutable",
        ),
        (
            "DELETE FROM atlas.entrada_regla WHERE ejecucion_regla_id IN"
            " (SELECT id FROM atlas.ejecucion_regla WHERE vinculo_id = :v)",
            "es inmutable",
        ),
        (
            "DELETE FROM atlas.ejecucion_regla_version WHERE ejecucion_regla_id IN"
            " (SELECT id FROM atlas.ejecucion_regla WHERE vinculo_id = :v)",
            "es inmutable",
        ),
    ],
)
def test_rf_16_vinculos_y_ejecuciones_protegidos_incluso_para_el_propietario(
    ctx: Contexto,
    par: dict[str, int],
    conexion_migracion: Connection,
    sentencia: str,
    mensaje: str,
) -> None:
    vinculo = _vinculo_en_base(ctx, par)
    with pytest.raises(IntegrityError, match=mensaje):
        conexion_migracion.execute(text(sentencia), {"v": vinculo})


def test_rf_14_la_base_rechaza_vinculos_entre_tramites(
    ctx: Contexto, par: dict[str, int], conexion_aplicacion: Connection
) -> None:
    otro = crear_tramite(ctx, "Otro")["id"]
    ajeno = documento(ctx, otro, "Ajeno")
    with pytest.raises(IntegrityError, match="fk_vinculo_documental_destino"):
        conexion_aplicacion.execute(
            text(
                "INSERT INTO atlas.vinculo_documental (tramite_id, documento_origen_id,"
                " documento_destino_id, tipo, origen, estado, justificacion, creado_por_id)"
                " VALUES (:t, :o, :d, 'campos', 'manual', 'confirmado', 'x', :u)"
            ),
            {"t": par["tramite"], "o": par["orden"], "d": ajeno, "u": ctx.usuario_id},
        )


def test_rf_14_la_base_admite_un_solo_vinculo_activo_por_par(
    ctx: Contexto, par: dict[str, int], conexion_aplicacion: Connection
) -> None:
    _vinculo_en_base(ctx, par)
    with pytest.raises(IntegrityError, match="uq_vinculo_documental_par_activo"):
        conexion_aplicacion.execute(
            text(
                "INSERT INTO atlas.vinculo_documental (tramite_id, documento_origen_id,"
                " documento_destino_id, tipo, origen, estado, justificacion)"
                " VALUES (:t, :d, :o, 'campos', 'automatico', 'pendiente', 'x')"
            ),
            {"t": par["tramite"], "o": par["orden"], "d": par["contrato"]},
        )
