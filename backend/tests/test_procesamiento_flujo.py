"""Recorrido de las etapas contra PostgreSQL real y S3 simulado con moto (hito 1.4).

Textract y el modelo se reemplazan por respuestas fijas (DO-2026-10-22-PROC, P1): se
prueba la lógica propia, no la calidad de los servicios. RF-08, RF-10, RF-11, RN-02,
RC-P08.6, §5.3.1, regla 5 de AGENTS.md.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from atlas.configuracion import Configuracion
from atlas.principal import crear_aplicacion
from atlas.procesamiento import esquemas, etapas, lambdas
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from tests import archivos
from tests.conftest import lineas_registro
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, cargar, contar, crear_tramite
from tests.flujo_procesamiento import (
    AnalizadorFijo,
    en_sesion,
    modelo_contrato,
    recorrer,
    salida_sin_contenido,
    trabajo_de,
)
from tests.procesamiento_fijo import dato, extraccion_c_v1_docx

pytestmark = pytest.mark.integracion


@pytest.fixture
def entorno(
    base_migrada: Configuracion, motor_aplicacion: Engine
) -> Iterator[tuple[Any, Contexto]]:
    aplicacion = crear_aplicacion(base_migrada)
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield aplicacion, Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
    aplicacion.state.motor.dispose()


# --- Recorrido completo -----------------------------------------------------------------


def test_rf_08_rf_10_rf_11_docx_produce_sugerencias_con_procedencia(entorno: Any) -> None:
    aplicacion, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_DOCX.read_bytes(), formato="docx")
    trabajo_id = trabajo_de(ctx.motor, archivo["id"])

    salidas = recorrer(aplicacion, trabajo_id, modelo_contrato(extraccion_c_v1_docx()))
    for salida in salidas:
        salida_sin_contenido(salida)
    assert salidas[-1] == {"resultado": "persistido"}

    respuesta = ctx.cliente.get(
        f"/tramites/{tramite['id']}/archivos/{archivo['id']}/sugerencias", headers=ctx.encabezados
    ).json()
    assert respuesta["trabajo"]["estado"] == "completado" and respuesta["trabajo"]["intento"] == 1
    assert respuesta["trabajo"]["actualizado_en"] >= respuesta["trabajo"]["creado_en"]  # OP-02
    assert respuesta["clasificacion"]["valor"] == "contrato"
    assert respuesta["clasificacion"]["motivo_sin_fuente"] == "no_aplica"
    campos = {c["campo"]: c for c in respuesta["campos"]}
    assert campos["monto_total"]["valor"] == "1250000.00"
    assert campos["monto_total"]["valor_original"] == "ARS 1.250.000,00"
    assert campos["monto_total"]["localizador"] == {
        "pagina": None,
        "seccion": "4. Condiciones económicas y forma de pago (tabla 2, fila 1)",
        "fragmento": "Monto total | ARS 1.250.000,00",
    }
    assert {c["version_instrucciones"] for c in campos.values()} == {"extraccion-v1"}
    assert {c["version_esquema"] for c in campos.values()} == {"esquema-extraccion-contrato-v1"}

    # RN-02: siguen siendo sugerencias; el archivo, el trámite y los documentos no cambian.
    (listado,) = ctx.cliente.get(
        f"/tramites/{tramite['id']}/archivos", headers=ctx.encabezados
    ).json()
    assert listado["estado_incorporacion"] == "pendiente"
    abierto = ctx.cliente.get(f"/tramites/{tramite['id']}", headers=ctx.encabezados).json()
    assert (abierto["estado"], abierto["documentos"]) == ("borrador", [])
    assert contar(ctx.motor, "documento", tramite["id"]) == 0


def test_rf_11_pdf_localiza_por_pagina_y_seccion(entorno: Any) -> None:
    aplicacion, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf(paginas=2))
    trabajo_id = trabajo_de(ctx.motor, archivo["id"])
    analizador = AnalizadorFijo(
        [
            [("titulo", "1. Partes"), ("linea", "Contraparte: Servicios Integrales del Sur S.A.")],
            [("titulo", "4. Precio"), ("tabla", [["Monto total", "ARS 1.250.000,00"]])],
        ]
    )
    extraccion = {c.nombre: dato(None) for c in esquemas.CAMPOS[esquemas.TipoDocumental.CONTRATO]}
    extraccion["monto_total"] = dato("ARS 1.250.000,00", "Monto total | ARS 1.250.000,00", 2)
    extraccion["contraparte"] = dato("Servicios Integrales del Sur S.A.", "Servicios Integrales", 2)

    salidas = recorrer(aplicacion, trabajo_id, modelo_contrato(extraccion), analizador)
    for salida in salidas:
        salida_sin_contenido(salida)
    assert analizador.iniciados == [(salidas[0]["clave_objeto"], trabajo_id, 1)]
    campos = {
        c["campo"]: c
        for c in ctx.cliente.get(
            f"/tramites/{tramite['id']}/archivos/{archivo['id']}/sugerencias",
            headers=ctx.encabezados,
        ).json()["campos"]
    }
    assert campos["monto_total"]["localizador"]["pagina"] == 2
    assert campos["monto_total"]["localizador"]["seccion"] == "4. Precio"
    # La cita existe, pero en la página 1: no se acepta la página informada.
    assert campos["contraparte"]["localizador"] is None
    assert campos["contraparte"]["motivo_sin_fuente"] == "no_verificada"


def test_p3_resultados_intermedios_en_s3_por_trabajo_e_intento(entorno: Any) -> None:
    aplicacion, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_DOCX.read_bytes(), formato="docx")
    trabajo_id = trabajo_de(ctx.motor, archivo["id"])
    recorrer(aplicacion, trabajo_id, modelo_contrato(extraccion_c_v1_docx()))
    s3 = aplicacion.state.almacen._cliente
    claves = {
        o["Key"]
        for o in s3.list_objects_v2(
            Bucket=aplicacion.state.almacen._bucket, Prefix=f"resultados/{trabajo_id}/"
        )["Contents"]
    }
    assert claves == {
        f"resultados/{trabajo_id}/1/{n}"
        for n in ("contenido.json", "clasificacion.json", "extraccion.json", "fragmentos.json")
    }


# --- Intentos, idempotencia y fallos (RC-P08) -------------------------------------------


def test_rc_p08_6_persistencia_idempotente_y_descarte_de_intentos_obsoletos(
    entorno: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    aplicacion, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_DOCX.read_bytes(), formato="docx")
    trabajo_id = trabajo_de(ctx.motor, archivo["id"])
    salidas = recorrer(aplicacion, trabajo_id, modelo_contrato(extraccion_c_v1_docx()))
    referencias = {
        clave: salida[clave]
        for salida in salidas
        for clave in ("clasificacion", "extraccion", "fragmentos")
        if clave in salida
    }
    almacen = aplicacion.state.almacen

    repetida = en_sesion(
        aplicacion,
        etapas.persistir,
        almacen=almacen,
        trabajo_id=trabajo_id,
        intento=1,
        **referencias,
    )
    assert repetida == {"resultado": "ya_persistido"}

    with ctx.motor.begin() as conexion:  # un intento nuevo, iniciado por el responsable
        conexion.execute(
            text(
                "UPDATE atlas.trabajo_procesamiento"
                " SET intento = 2, estado = 'en_ejecucion' WHERE id = :t"
            ),
            {"t": trabajo_id},
        )
    obsoleta = en_sesion(
        aplicacion,
        etapas.persistir,
        almacen=almacen,
        trabajo_id=trabajo_id,
        intento=1,
        **referencias,
    )
    assert obsoleta == {"resultado": "descartado"}
    with ctx.motor.connect() as conexion:
        filas = conexion.execute(
            text("SELECT count(*) FROM atlas.valor_sugerido WHERE trabajo_id = :t"),
            {"t": trabajo_id},
        ).scalar_one()
    assert filas == 8  # 1 clasificación + 7 campos, sin duplicados
    assert any(
        r["evento"] == "resultado_descartado" for r in lineas_registro(capsys.readouterr().out)
    )
    with pytest.raises(ErrorPermanente, match="intento_obsoleto"):
        en_sesion(aplicacion, etapas.preparar, trabajo_id=trabajo_id, intento=1)


def test_dt_proc_fallo_tecnico_no_modifica_el_tramite(entorno: Any) -> None:
    aplicacion, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    trabajo_id = trabajo_de(ctx.motor, archivo["id"])
    registrado = en_sesion(
        aplicacion,
        etapas.registrar_fallo,
        trabajo_id=trabajo_id,
        intento=1,
        codigo="textract_fallido",
    )
    assert registrado == {"registrado": True}
    (listado,) = ctx.cliente.get(
        f"/tramites/{tramite['id']}/archivos", headers=ctx.encabezados
    ).json()
    assert listado["trabajo"]["estado"] == "fallido" and listado["trabajo"]["intento"] == 1
    assert listado["estado_incorporacion"] == "pendiente"
    assert (
        ctx.cliente.get(f"/tramites/{tramite['id']}", headers=ctx.encabezados).json()["estado"]
        == "borrador"
    )
    # Un intento que ya no está en curso no vuelve a registrar fallos ni resultados.
    assert en_sesion(
        aplicacion, etapas.registrar_fallo, trabajo_id=trabajo_id, intento=1, codigo="otro"
    ) == {"registrado": False}


@pytest.mark.parametrize(
    "sentencia",
    ["UPDATE atlas.valor_sugerido SET valor = 'x'", "DELETE FROM atlas.referencia_fuente"],
)
def test_rn_02_sugerencias_inmutables(
    entorno: Any, motor_migracion: Engine, sentencia: str
) -> None:
    aplicacion, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_DOCX.read_bytes(), formato="docx")
    recorrer(
        aplicacion, trabajo_de(ctx.motor, archivo["id"]), modelo_contrato(extraccion_c_v1_docx())
    )
    with pytest.raises(DBAPIError, match="permission denied"), ctx.motor.begin() as conexion:
        conexion.execute(text(sentencia))
    with pytest.raises(IntegrityError, match="es inmutable"), motor_migracion.begin() as conexion:
        conexion.execute(text(sentencia))


def test_rnf_01_sugerencias_solo_con_acceso_al_tramite(entorno: Any) -> None:
    _, ctx = entorno
    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.pdf())
    ruta = f"/tramites/{tramite['id']}/archivos/{archivo['id']}/sugerencias"
    for roles in (("responsable_tramite",), ("administrador_operativo",)):
        _, sub = crear_cuenta(ctx.motor, *roles)
        assert ctx.cliente.get(ruta, headers=portador(sub)).status_code == 404
    sin_resultados = ctx.cliente.get(ruta, headers=ctx.encabezados).json()
    assert sin_resultados["clasificacion"] is None and sin_resultados["campos"] == []
    assert sin_resultados["trabajo"]["estado"] == "en_ejecucion"


# --- Funciones Lambda: errores sin contenido --------------------------------------------


def test_regla_5_error_inesperado_sale_sin_mensaje_ni_causa(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def etapa_rota(**_: Any) -> None:
        raise ValueError("CUIT 30-96472518-3 monto 1.250.000")

    with pytest.raises(ErrorPermanente) as excepcion:
        lambdas.ejecutar({"etapa": "rota", "trabajo_id": 1, "intento": 1}, {"rota": etapa_rota})
    assert str(excepcion.value) == "inesperado_ValueError"
    assert excepcion.value.__cause__ is None and excepcion.value.__suppress_context__
    assert "30-96472518-3" not in capsys.readouterr().out


def test_rc_p08_error_transitorio_conserva_su_tipo_para_reintentar() -> None:
    def etapa(**_: Any) -> None:
        raise ErrorTransitorio("textract_ThrottlingException")

    with pytest.raises(ErrorTransitorio, match="textract_ThrottlingException"):
        lambdas.ejecutar({"etapa": "e", "trabajo_id": 1, "intento": 1}, {"e": etapa})


@pytest.mark.parametrize(
    "evento",
    [{"etapa": "inexistente"}, {"etapa": "e", "texto_documento": "x"}],
    ids=["etapa_desconocida", "clave_no_permitida"],
)
def test_regla_5_eventos_fuera_de_contrato_se_rechazan(evento: dict[str, Any]) -> None:
    with pytest.raises(ErrorPermanente, match="evento_invalido"):
        lambdas.ejecutar(evento, {"e": lambda **_: None})


@pytest.mark.parametrize(
    ("error", "causa", "codigo"),
    [
        (
            "ErrorPermanente",
            json.dumps({"errorMessage": "textract_fallido", "stackTrace": []}),
            "textract_fallido",
        ),
        ("States.Timeout", None, "States.Timeout"),
        (
            "ErrorPermanente",
            json.dumps({"errorMessage": "mensaje con espacios y datos"}),
            "ErrorPermanente",
        ),
        (None, "no es json", "error_desconocido"),
    ],
)
def test_dt_proc_codigo_de_falla_solo_tecnico(
    error: str | None, causa: str | None, codigo: str
) -> None:
    assert lambdas.codigo_de_falla(error, causa) == codigo


@pytest.mark.parametrize("operacion", ["leer", "escribir"])
def test_rc_p08_falla_de_s3_en_una_etapa_es_reintentable(operacion: str) -> None:
    from atlas.integraciones.puertos import ErrorIntegracion

    class AlmacenCaido:
        def leer(self, clave: str) -> bytes:
            raise ErrorIntegracion("s3_lectura_fallida")

        def escribir(self, *_: Any) -> None:
            raise ErrorIntegracion("s3_escritura_fallida")

    if operacion == "leer":
        with pytest.raises(ErrorTransitorio, match="s3_lectura_fallida"):
            etapas.normalizar_docx(AlmacenCaido(), clave_objeto="k", trabajo_id=1, intento=1)  # type: ignore[arg-type]
    else:
        analizador = AnalizadorFijo([[("linea", "texto")]])
        with pytest.raises(ErrorTransitorio, match="s3_escritura_fallida"):
            etapas.normalizar_textract(
                analizador, AlmacenCaido(), job_id="j", trabajo_id=1, intento=1
            )  # type: ignore[arg-type]
