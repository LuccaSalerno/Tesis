"""Procesamiento simulado para desarrollo y E2E locales.

Comprueba que solo corre fuera de demo, que reconoce los documentos de la demo
por su huella, que las
sugerencias quedan rotuladas como simulación y que lo ajeno al corpus se registra como fallo.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from atlas.configuracion import Configuracion, ErrorConfiguracion
from atlas.herramientas import procesar_simulado
from atlas.principal import crear_aplicacion
from tests import archivos
from tests.conftest import configuracion_sin_base
from tests.datos import crear_cuenta, portador
from tests.flujo_api import Contexto, cargar, crear_tramite

pytestmark = pytest.mark.integracion


@pytest.fixture
def ctx(base_migrada: Configuracion, motor_aplicacion: Engine) -> Iterator[Contexto]:
    aplicacion = crear_aplicacion(base_migrada)
    usuario_id, sub = crear_cuenta(motor_aplicacion, "responsable_tramite")
    with TestClient(aplicacion) as cliente:
        yield Contexto(cliente, motor_aplicacion, usuario_id, portador(sub))
    aplicacion.state.motor.dispose()


def _archivo(ctx: Contexto, tramite_id: int, archivo_id: int) -> dict[str, Any]:
    respuesta = ctx.cliente.get(f"/tramites/{tramite_id}/archivos", headers=ctx.encabezados)
    return next(a for a in respuesta.json() if a["id"] == archivo_id)


def test_f9_simula_el_corpus_y_rotula_las_sugerencias(
    ctx: Contexto, base_migrada: Configuracion
) -> None:
    tramite_id = crear_tramite(ctx)["id"]
    contrato = cargar(ctx, tramite_id, archivos.CONTRATO_PDF.read_bytes())
    ajeno = cargar(ctx, tramite_id, archivos.pdf())
    assert procesar_simulado.procesar(base_migrada, contrato["id"]) == {
        "procesados": [contrato["id"]],
        "fallidos": [],
    }
    assert procesar_simulado.procesar(base_migrada, ajeno["id"])["fallidos"] == [ajeno["id"]]
    assert _archivo(ctx, tramite_id, contrato["id"])["trabajo"]["estado"] == "completado"
    assert _archivo(ctx, tramite_id, ajeno["id"])["trabajo"]["estado"] == "fallido"
    sugerencias = ctx.cliente.get(
        f"/tramites/{tramite_id}/archivos/{contrato['id']}/sugerencias", headers=ctx.encabezados
    ).json()
    assert sugerencias["clasificacion"]["valor"] == "contrato"
    assert sugerencias["clasificacion"]["modelo"].startswith(procesar_simulado.PREFIJO_MODELO)
    vigencia = next(c for c in sugerencias["campos"] if c["campo"] == "vigencia_hasta")
    assert vigencia["valor"] == "2027-02-28"
    assert vigencia["localizador"]["pagina"] is not None  # fragmento ubicado en el PDF


def test_f9_se_niega_en_demo_o_sin_moto(monkeypatch: pytest.MonkeyPatch) -> None:
    for configuracion in (
        configuracion_sin_base(entorno="demo"),
        configuracion_sin_base(aws_endpoint_url=None),
    ):
        with pytest.raises(ErrorConfiguracion, match="desarrollo o pruebas"):
            procesar_simulado.verificar_entorno(configuracion)
    monkeypatch.setattr(
        procesar_simulado, "obtener_configuracion", lambda: configuracion_sin_base(entorno="demo")
    )
    assert procesar_simulado.main([]) == 1


def test_f9_main_procesa_los_pendientes(
    ctx: Contexto, base_migrada: Configuracion, monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    tramite_id = crear_tramite(ctx)["id"]
    archivo = cargar(ctx, tramite_id, archivos.CONTRATO_PDF.read_bytes())
    monkeypatch.setattr(procesar_simulado, "obtener_configuracion", lambda: base_migrada)
    assert procesar_simulado.main([]) == 0
    assert "SIMULACIÓN LOCAL" in capsys.readouterr().out
    assert _archivo(ctx, tramite_id, archivo["id"])["trabajo"]["estado"] == "completado"


def test_f9_formas_impresas_de_los_valores() -> None:
    assert procesar_simulado._formas("2027-02-28") == ["2027-02-28", "28/02/2027"]
    assert procesar_simulado._formas("1250000.00") == ["1250000.00", "1.250.000,00"]
    assert procesar_simulado.ubicar([["Sin datos"]], "ARS") == (None, None)


def test_demo_surdelta_simula_sus_documentos(ctx: Contexto, base_migrada: Configuracion) -> None:
    """Los PDF de SurDelta también se simulan, con su rótulo."""
    from atlas.herramientas import sembrar_demo

    tramite_id = crear_tramite(ctx)["id"]
    factura = cargar(
        ctx,
        tramite_id,
        (sembrar_demo.CORPUS_SURDELTA / "SD-F1_Factura_0004-00001248.pdf").read_bytes(),
    )
    assert procesar_simulado.procesar(base_migrada, factura["id"])["procesados"] == [factura["id"]]
    sugerencias = ctx.cliente.get(
        f"/tramites/{tramite_id}/archivos/{factura['id']}/sugerencias", headers=ctx.encabezados
    ).json()
    assert sugerencias["clasificacion"]["valor"] == "factura"
    assert sugerencias["clasificacion"]["modelo"] == procesar_simulado.MODELO_SIMULADO_SURDELTA
    total = next(c for c in sugerencias["campos"] if c["campo"] == "importe_total")
    assert total["valor"] == "9200000.00" and total["localizador"]["pagina"] == 1
