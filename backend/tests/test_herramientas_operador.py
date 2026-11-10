"""Herramientas del operador: seed, exportación de evidencia y vaciado de buckets.

DO-2026-10-22-OPS (P8, P11, P12), PD-07. Contra la API local real (PostgreSQL y moto), con
el procesamiento de respuestas fijas (DIF-43): no contactan AWS.
"""

import json
import uuid
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from atlas.configuracion import Configuracion
from atlas.dominio.enumeraciones import TipoDocumental
from atlas.herramientas import exportar_evidencia, sembrar_demo, vaciar_bucket_versionado
from atlas.herramientas.cliente_api import (
    ClienteApi,
    ErrorApi,
    sub_del_token,
    tokens_cognito,
    transporte_urllib,
)
from atlas.integraciones.aws import crear_cliente
from atlas.principal import crear_aplicacion
from atlas.procesamiento import esquemas
from atlas.servicios import resultados
from tests.conftest import CLAVES_PRUEBA, configuracion_sin_base
from tests.datos import crear_cuenta
from tests.flujo_procesamiento import (
    PAGINAS_C_V1,
    AnalizadorFijo,
    en_sesion,
    extraccion_c_v1_pdf,
    modelo_contrato,
    recorrer,
    trabajo_de,
)
from tests.procesamiento_fijo import ModeloFijo, dato

ORACULO = json.loads(sembrar_demo.ORACULO.read_text(encoding="utf-8"))
O_V2 = {c: ORACULO["documentos"]["O-v2"][c] for c in ("numero", "cuit_proveedor", "moneda")}
ORACULO_SD = json.loads(sembrar_demo.ORACULO_SURDELTA.read_text(encoding="utf-8"))


def transporte_de(cliente: TestClient) -> Any:
    """La API por TestClient; las URL prefirmadas, por HTTP real contra moto."""

    def transportar(
        metodo: str, url: str, encabezados: Mapping[str, str], cuerpo: bytes | None
    ) -> tuple[int, bytes]:
        if url.startswith("http://testserver"):
            r = cliente.request(metodo, url, headers=dict(encabezados), content=cuerpo)
        else:
            r = httpx.request(metodo, url, headers=dict(encabezados), content=cuerpo)
        return r.status_code, r.content

    return transportar


@pytest.fixture
def entorno(base_migrada: Configuracion, motor_aplicacion: Engine) -> Iterator[dict[str, Any]]:
    aplicacion = crear_aplicacion(base_migrada)
    _, sub_admin = crear_cuenta(motor_aplicacion, "administrador_operativo")
    tokens = {"administrador": CLAVES_PRUEBA.emitir(sub_admin)}
    for rol in ("responsable", "revisor", "aprobador"):
        tokens[rol] = CLAVES_PRUEBA.emitir(f"sub-{rol}-{uuid.uuid4()}")
    with TestClient(aplicacion) as cliente:
        api = ClienteApi("http://testserver", tokens, transporte_de(cliente))
        # (fragmento del título del trámite, prefijo del archivo): falla una vez, como el
        # token repetido de Textract de la sesión del 24/10.
        fallos: set[tuple[str, str]] = set()

        def procesar(_: ClienteApi, __: int, archivos: list[int]) -> None:
            # Todo se procesa con el contrato fijo: O-v1 y F-v2 quedan sugeridos como
            # contrato y la semilla los corrige al tipo del oráculo. O-v2 se sugiere como
            # orden con el número estable del oráculo v2, para que RF-06 la relacione con
            # O-v1 por su número (DIF-84).
            for archivo in archivos:
                with motor_aplicacion.connect() as conexion:
                    nombre, titulo, estado, intento = conexion.execute(
                        text(
                            "SELECT a.nombre, t.titulo, p.estado, p.intento"
                            " FROM atlas.archivo a JOIN atlas.tramite t ON t.id = a.tramite_id"
                            " JOIN atlas.trabajo_procesamiento p ON p.archivo_id = a.id"
                            " WHERE a.id = :a"
                        ),
                        {"a": archivo},
                    ).one()
                if estado in ("completado", "fallido"):
                    continue
                trabajo = trabajo_de(motor_aplicacion, archivo)
                fallo = next(
                    (f for f in fallos if f[0] in titulo and nombre.startswith(f[1])), None
                )
                if fallo is not None:
                    fallos.discard(fallo)
                    en_sesion(
                        aplicacion,
                        resultados.registrar_fallo,
                        trabajo_id=trabajo,
                        intento=intento,
                        codigo="textract_IdempotentParameterMismatchException",
                    )
                    continue
                modelo = modelo_contrato(extraccion_c_v1_pdf())
                if nombre.startswith("SD-"):
                    # SurDelta: la IA sugiere lo que dice el documento (oráculo), así RF-06
                    # relaciona la factura v2 con la v1 por el CUIT del emisor.
                    doc = ORACULO_SD["documentos"][nombre.split("_")[0]]
                    tipo = TipoDocumental(doc["tipo_documental"])
                    modelo = ModeloFijo(
                        {
                            esquemas.HERRAMIENTA_CLASIFICACION: {"tipo": tipo.value},
                            esquemas.HERRAMIENTA_EXTRACCION: {
                                c.nombre: dato(doc["campos"][c.nombre])
                                for c in esquemas.CAMPOS[tipo]
                            },
                        }
                    )
                elif nombre.startswith("O-v2"):
                    modelo = ModeloFijo(
                        {
                            esquemas.HERRAMIENTA_CLASIFICACION: {"tipo": "orden_compra"},
                            esquemas.HERRAMIENTA_EXTRACCION: {
                                c.nombre: dato(O_V2.get(c.nombre))
                                for c in esquemas.CAMPOS[TipoDocumental.ORDEN_COMPRA]
                            },
                        }
                    )
                recorrer(aplicacion, trabajo, modelo, AnalizadorFijo(PAGINAS_C_V1), intento=intento)

        yield {"api": api, "procesar": procesar, "aplicacion": aplicacion, "fallos": fallos}
    aplicacion.state.motor.dispose()


def _manifiesto() -> sembrar_demo.Manifiesto:
    return sembrar_demo.Manifiesto(
        sesion="e90-pruebas",
        url_api="http://testserver",
        oraculo=f"{ORACULO['id']} ({ORACULO['estado']})",
        corpus=sembrar_demo.verificar_corpus(ORACULO),
    )


@pytest.mark.integracion
def test_p11_semilla_completa_por_api_y_p12_exportacion(
    entorno: dict[str, Any], tmp_path: Path
) -> None:
    manifiesto = sembrar_demo.Sembrador(
        entorno["api"], _manifiesto(), ORACULO, entorno["procesar"]
    ).ejecutar()
    assert manifiesto.resultado == "completado"
    observado, en_vivo = manifiesto.tramites["observado"], manifiesto.tramites["en_vivo"]
    assert observado["estado"] == "observado" and len(observado["decisiones"]) == 2
    assert en_vivo["estado"] == "borrador" and set(en_vivo["documentos"]) == {"C-v1"}
    # DO-2026-10-23-VER P9: EVD-B completo hasta la firma.
    cerrado = manifiesto.tramites["cerrado"]
    assert cerrado["estado"] == "cerrado" and cerrado["criterio_version"] == "numero"
    assert cerrado["controles"]["R3"] == "advertencia"
    assert cerrado["controles_corregidos"]["R3"] == "cumplimiento"
    assert cerrado["validaciones"]["O-v2"]["fecha"] == "sin_sugerencia"
    assert cerrado["firma"]["version_id"] != cerrado["version_nueva"]
    assert len(cerrado["decisiones_2"]) == 2
    assert manifiesto.tramites["cancelado"]["estado"] == "cancelado"  # RF-26 (CIERRE P11)
    # PD-07, conjunto C-v1 + O-v1 + F-v2: solo R3 advierte.
    assert observado["controles"] == {
        "R1": "cumplimiento",
        "R2": "cumplimiento",
        "R3": "advertencia",
        "R4": "cumplimiento",
    }
    validaciones = observado["validaciones"]
    assert validaciones["C-v1"]["tipo_documental"] == "confirmacion"
    assert validaciones["O-v1"]["tipo_documental"] == "correccion"
    assert validaciones["C-v1"]["cuit_contraparte"] == "confirmacion"
    assert validaciones["F-v2"]["numero"] == "sin_sugerencia"
    assert set(manifiesto.cuentas) == set(sembrar_demo.ROLES)
    assert "token" not in json.dumps(manifiesto.__dict__).lower()

    # El exportador descubre en la API lo que el manifiesto no lista: sin las decisiones del
    # ciclo 2 ni los archivos del trámite en vivo, igual quedan exportados.
    datos = json.loads(json.dumps(manifiesto.__dict__))
    del datos["tramites"]["cerrado"]["decisiones_2"]
    datos["tramites"]["en_vivo"]["archivos"] = {}
    resumen = exportar_evidencia.exportar(
        entorno["api"], datos, tmp_path, [manifiesto.tramites["cancelado"]["id"]]
    )
    evidencias = [n for n in resumen["archivos"] if "/evidencia/" in n and "observado-" in n]
    assert len(evidencias) == 2
    assert len([n for n in resumen["archivos"] if "/evidencia/" in n]) == 6
    en_vivo = f"tramites/en_vivo-{manifiesto.tramites['en_vivo']['id']}"
    archivo_c = manifiesto.tramites["en_vivo"]["archivos"]["C-v1"]
    assert f"{en_vivo}/sugerencias/archivo-{archivo_c}.json" in resumen["archivos"]
    assert f"{en_vivo}/validaciones/C-v1.json" in resumen["archivos"]
    adicional = f"tramites/adicional-{manifiesto.tramites['cancelado']['id']}/tramite.json"
    assert adicional in resumen["archivos"]
    assert resumen["tramites_adicionales"] == [manifiesto.tramites["cancelado"]["id"]]
    firma = next(n for n in resumen["archivos"] if n.endswith("/firma.json"))
    assert json.loads((tmp_path / firma).read_text())["leyenda"].startswith(
        "Firma digital simulada"
    )
    indice = json.loads((tmp_path / "indice.json").read_text())
    assert indice["sesion"] == "e90-pruebas"
    primera, segunda = (json.loads((tmp_path / n).read_text()) for n in sorted(evidencias))
    assert primera["decision"]["tipo"] == "aprobacion"
    assert segunda["decision"]["tipo"] == "observacion"
    assert segunda["decision"]["motivo"] == sembrar_demo.MOTIVO_OBSERVACION
    assert {c["codigo_regla"][:2] for c in primera["controles"]} == {"R1", "R2", "R3", "R4"}


@pytest.mark.integracion
def test_p11_un_fallo_detiene_la_semilla_y_reanudar_completa_sin_ocultarlo(
    entorno: dict[str, Any], tmp_path: Path
) -> None:
    """Sesión del 24/10: Textract rechazó el token de trabajos del trámite en vivo y del
    cerrado. La semilla se detiene antes de validar a mano; `reanudar` reintenta el en vivo
    por la API y reemplaza el cerrado incompleto, que queda cancelado con su motivo."""
    fallos = entorno["fallos"]
    fallos.add(("(en vivo)", "C-v1"))
    semilla = sembrar_demo.Sembrador(entorno["api"], _manifiesto(), ORACULO, entorno["procesar"])
    with pytest.raises(RuntimeError, match="Procesamiento fallido"):
        semilla.ejecutar()
    en_vivo = semilla.m.tramites["en_vivo"]
    assert en_vivo["documentos"] == {}  # no se incorpora un archivo sin procesar
    assert semilla.m.tramites["observado"]["estado"] == "observado"

    fallos.add(("(historia completa)", "O-v2"))
    with pytest.raises(RuntimeError, match="Procesamiento fallido"):
        semilla.reanudar()
    assert en_vivo["reintentos"] == [en_vivo["archivos"]["C-v1"]]
    assert en_vivo["estado"] == "borrador" and set(en_vivo["documentos"]) == {"C-v1"}
    incompleto = semilla.m.tramites["cerrado"]
    assert incompleto["estado"] == "observado" and "O-v2" not in incompleto["validaciones"]

    manifiesto = semilla.reanudar()
    assert manifiesto.resultado == "completado" and len(manifiesto.reanudaciones) == 2
    [reemplazado] = manifiesto.reemplazados
    assert reemplazado["id"] == incompleto["id"] and reemplazado["estado"] == "cancelado"
    tramite = entorno["api"].get(f"/tramites/{incompleto['id']}", "responsable")
    assert tramite["motivo_cancelacion"] == sembrar_demo.MOTIVO_REEMPLAZO
    cerrado = manifiesto.tramites["cerrado"]
    assert cerrado["id"] != incompleto["id"] and cerrado["estado"] == "cerrado"
    assert cerrado["criterio_version"] == "numero"
    assert manifiesto.tramites["cancelado"]["estado"] == "cancelado"
    assert not fallos
    # P12: el reemplazado también se exporta, con su cancelación.
    resumen = exportar_evidencia.exportar(entorno["api"], manifiesto.__dict__, tmp_path)
    exportado = tmp_path / f"tramites/reemplazado-{incompleto['id']}/tramite.json"
    assert json.loads(exportado.read_text())["estado"] == "cancelado"
    assert f"tramites/reemplazado-{incompleto['id']}/tramite.json" in resumen["archivos"]


def _manifiesto_surdelta() -> sembrar_demo.Manifiesto:
    return sembrar_demo.Manifiesto(
        sesion="surdelta-pruebas",
        url_api="http://testserver",
        oraculo=f"{ORACULO_SD['id']} ({ORACULO_SD['estado']})",
        corpus=sembrar_demo.verificar_corpus_surdelta(ORACULO_SD),
    )


@pytest.mark.integracion
def test_demo_surdelta_semilla_completa_por_api(entorno: dict[str, Any]) -> None:
    """DO-2026-11-09-DEMO-SURDELTA: la cartera de SurDelta con las reglas reales."""
    sembrador = sembrar_demo.SembradorSurDelta(
        entorno["api"], _manifiesto_surdelta(), ORACULO_SD, entorno["procesar"]
    )
    manifiesto = sembrador.ejecutar()
    assert manifiesto.resultado == "completado"
    assert manifiesto.plantilla_id and manifiesto.plantilla_general_id
    # La cartera no incluye el mantenimiento de planta: se crea en vivo en la grabación.
    assert set(manifiesto.tramites) == {"suministro", "observado", "pendiente", "cancelado"}
    # Provisión de acero: el caso habitual, sin advertencias, aprobado y firmado.
    suministro = manifiesto.tramites["suministro"]
    assert suministro["controles"] == dict.fromkeys(("R1", "R2", "R3", "R4"), "cumplimiento")
    assert suministro["estado"] == "cerrado" and suministro["firma"]["version_id"]
    # El recorrido de los videos, por la API: la factura v1 supera la orden (R4) y la fecha
    # de la orden es anterior a la vigencia (R3); la v2 corrige R4, entra por el CUIT del
    # emisor (RF-06) y R3 sigue.
    sembrador.sembrar_historia()
    historia = manifiesto.tramites["cerrado"]
    assert historia["controles"] == {
        "R1": "cumplimiento",
        "R2": "cumplimiento",
        "R3": "advertencia",
        "R4": "advertencia",
    }
    assert historia["controles_corregidos"]["R4"] == "cumplimiento"
    assert historia["controles_corregidos"]["R3"] == "advertencia"
    assert historia["criterio_version"] == "cuit"
    assert len(historia["decisiones"]) == 1 and len(historia["decisiones_2"]) == 2
    assert historia["estado"] == "cerrado"
    assert historia["firma"]["version_id"] != historia["version_nueva"]
    evidencia = entorno["api"].get(
        f"/decisiones/{historia['decisiones'][0]}/evidencia", "responsable"
    )
    assert evidencia["decision"]["motivo"] == sembrar_demo.MOTIVO_OBSERVACION_SURDELTA
    # Compra: la factura de otra empresa no se vincula sola; R1 advierte y se observa.
    compra = manifiesto.tramites["observado"]
    assert compra["estado"] == "observado"
    assert compra["controles"] == {
        "R1": "advertencia",
        "R2": "no_aplicable",  # sin contrato en el trámite
        "R3": "no_aplicable",
        "R4": "cumplimiento",
    }
    assert manifiesto.tramites["pendiente"]["estado"] == "pendiente_aprobacion"
    assert manifiesto.tramites["cancelado"]["estado"] == "cancelado"
    assert "token" not in json.dumps(manifiesto.__dict__).lower()


def test_demo_surdelta_corpus_y_escenario() -> None:
    for codigo, valores in sembrar_demo.escenario_surdelta(ORACULO_SD).items():
        tipo = TipoDocumental(valores["tipo_documental"])
        assert set(valores) - {"tipo_documental"} == {c.nombre for c in esquemas.CAMPOS[tipo]}, (
            codigo
        )
    alterado = json.loads(json.dumps(ORACULO_SD))
    alterado["documentos"]["SD-F1"]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="SD-F1"):
        sembrar_demo.verificar_corpus_surdelta(alterado)
    with pytest.raises(RuntimeError, match="no se reanuda"):
        sembrar_demo.SembradorSurDelta(None, _manifiesto_surdelta(), ORACULO_SD).reanudar()  # type: ignore[arg-type]


def test_demo_surdelta_main_elige_el_escenario(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = ["--url-api", "http://x", "--sesion", "s", "--cliente-cognito", "c"]
    usuarios = ["--usuarios", *(f"{r}={r}" for r in sembrar_demo.ROLES)]
    escenario = ["--escenario", "surdelta"]
    salida = tmp_path / "m.json"
    assert (
        sembrar_demo.main([*base, *usuarios, *escenario, "--reanudar", "--manifiesto", str(salida)])
        == 2
    )
    monkeypatch.setattr(sembrar_demo, "tokens_cognito", lambda *_: {})
    usados: list[type] = []

    def ejecutar(self: sembrar_demo.Sembrador) -> sembrar_demo.Manifiesto:
        usados.append(type(self))
        return self.m

    monkeypatch.setattr(sembrar_demo.Sembrador, "ejecutar", ejecutar)
    monkeypatch.setattr(sembrar_demo.SembradorSurDelta, "ejecutar", ejecutar)
    assert sembrar_demo.main([*base, *usuarios, *escenario, "--manifiesto", str(salida)]) == 0
    assert usados == [sembrar_demo.SembradorSurDelta]
    guardado = json.loads(salida.read_text())
    assert guardado["oraculo"] == "oraculo_surdelta_v1 (demostracion)"
    assert guardado["corpus"] == sembrar_demo.huellas_surdelta(ORACULO_SD)


def test_p11_reanudar_exige_el_observado_completo() -> None:
    class Api:
        def get(self, ruta: str, *_: Any) -> dict[str, str]:
            return {"operacion": "active"}

    with pytest.raises(RuntimeError, match="observado"):
        sembrar_demo.Sembrador(Api(), _manifiesto(), ORACULO).reanudar()  # type: ignore[arg-type]


def test_p11_no_siembra_fuera_de_active() -> None:
    def transporte(*_: Any) -> tuple[int, bytes]:
        return 200, json.dumps({"operacion": "offline"}).encode()

    api = ClienteApi("http://testserver", {}, transporte)
    with pytest.raises(RuntimeError, match="no está en active"):
        sembrar_demo.Sembrador(api, _manifiesto(), ORACULO).ejecutar()


def test_pd_07_la_semilla_rechaza_un_corpus_alterado() -> None:
    alterado = json.loads(json.dumps(ORACULO))
    alterado["archivos_pdf"]["F-v2_Factura.pdf"]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match=r"F-v2_Factura\.pdf"):
        sembrar_demo.verificar_corpus(alterado)


def test_p11_escenario_cubre_todos_los_campos_del_esquema() -> None:
    from atlas.dominio.enumeraciones import TipoDocumental
    from atlas.procesamiento import esquemas

    for codigo, valores in sembrar_demo.escenario(ORACULO).items():
        tipo = TipoDocumental(valores["tipo_documental"])
        assert set(valores) - {"tipo_documental"} == {c.nombre for c in esquemas.CAMPOS[tipo]}, (
            codigo
        )


def test_p11_esperar_procesamiento_termina_o_vence(monkeypatch: pytest.MonkeyPatch) -> None:
    respuestas = iter(
        [
            [{"id": 1, "trabajo": {"estado": "en_ejecucion"}}],
            [{"id": 1, "trabajo": {"estado": "completado"}}],
        ]
    )

    class Api:
        def get(self, _: str, __: str) -> Any:
            return next(respuestas)

    monkeypatch.setattr(sembrar_demo.time, "sleep", lambda _: None)
    sembrar_demo.esperar_procesamiento(Api(), 1, [1], intervalo_s=0)  # type: ignore[arg-type]

    class Trabado:
        def get(self, _: str, __: str) -> Any:
            return [{"id": 1, "trabajo": {"estado": "pendiente"}}]

    with pytest.raises(RuntimeError, match="tiempo máximo"):
        sembrar_demo.esperar_procesamiento(Trabado(), 1, [1], maximo_s=0)  # type: ignore[arg-type]


def test_p11_main_valida_argumentos_y_guarda_el_resultado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = ["--url-api", "https://api.ejemplo", "--sesion", "s", "--cliente-cognito", "c"]
    usuarios = ["--usuarios", "administrador=a", "responsable=r", "revisor=v", "aprobador=p"]
    existente = tmp_path / "existe.json"
    existente.write_text("{}")
    assert sembrar_demo.main([*base, *usuarios, "--manifiesto", str(existente)]) == 1
    faltan = ["--usuarios", "administrador=a", "responsable=r", "revisor=v", "otro=p"]
    assert sembrar_demo.main([*base, *faltan, "--manifiesto", str(tmp_path / "m.json")]) == 2

    monkeypatch.setattr(sembrar_demo, "tokens_cognito", lambda *_: {})

    def falla(self: Any) -> Any:
        raise ErrorApi("POST", "/tramites", 503)

    monkeypatch.setattr(sembrar_demo.Sembrador, "ejecutar", falla)
    fallido = tmp_path / "fallido.json"
    assert sembrar_demo.main([*base, *usuarios, "--manifiesto", str(fallido)]) == 1
    assert json.loads(fallido.read_text())["resultado"].startswith("fallido: POST /tramites")

    monkeypatch.setattr(sembrar_demo.Sembrador, "ejecutar", lambda self: self.m)
    correcto = tmp_path / "correcto.json"
    assert sembrar_demo.main([*base, *usuarios, "--manifiesto", str(correcto)]) == 0
    assert json.loads(correcto.read_text())["corpus"] == sembrar_demo.huellas_corpus()

    # --reanudar: solo sobre una semilla interrumpida de la misma sesión, API y corpus.
    reanudar = ["--reanudar", "--manifiesto"]
    assert sembrar_demo.main([*base, *usuarios, *reanudar, str(tmp_path / "no.json")]) == 1
    assert sembrar_demo.main([*base, *usuarios, *reanudar, str(correcto)]) == 1
    otra = ["--url-api", "https://otra.ejemplo", *base[2:]]
    assert sembrar_demo.main([*otra, *usuarios, *reanudar, str(fallido)]) == 1

    def reanuda(self: Any) -> Any:
        self.m.reanudaciones.append("ahora")
        return self.m

    monkeypatch.setattr(sembrar_demo.Sembrador, "reanudar", reanuda)
    assert sembrar_demo.main([*base, *usuarios, *reanudar, str(fallido)]) == 0
    assert json.loads(fallido.read_text())["reanudaciones"] == ["ahora"]


# --- Cliente HTTP y tokens ---------------------------------------------------------------


def test_p10_tokens_de_cognito_desde_la_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    class Idp:
        def __init__(self) -> None:
            self.llamadas: list[dict[str, Any]] = []

        def initiate_auth(self, **parametros: Any) -> dict[str, Any]:
            self.llamadas.append(parametros)
            return {"AuthenticationResult": {"AccessToken": "token-" + parametros["ClientId"]}}

    idp = Idp()
    monkeypatch.delenv("ATLAS_SEED_CLAVE_RESPONSABLE", raising=False)
    with pytest.raises(RuntimeError, match="ATLAS_SEED_CLAVE_RESPONSABLE"):
        tokens_cognito("us-east-1", "cli", {"responsable": "r"}, idp)
    monkeypatch.setenv("ATLAS_SEED_CLAVE_RESPONSABLE", "ficticia")
    assert tokens_cognito("us-east-1", "cli", {"responsable": "r"}, idp) == {
        "responsable": "token-cli"
    }
    assert idp.llamadas[0]["AuthFlow"] == "USER_PASSWORD_AUTH"


def test_p11_sub_del_token() -> None:
    assert sub_del_token(CLAVES_PRUEBA.emitir("sub-ficticio")) == "sub-ficticio"


def test_p11_transporte_solo_https_o_local(moto_local: str) -> None:
    with pytest.raises(ValueError, match="Solo HTTPS"):
        transporte_urllib("GET", "http://api.ejemplo/salud", {}, None)
    estado, _ = transporte_urllib(
        "GET", f"{moto_local}/bucket-inexistente-{uuid.uuid4()}", {}, None
    )
    assert estado == 404


def test_p11_cliente_informa_metodo_ruta_y_estado_sin_cuerpo() -> None:
    def transporte(*_: Any) -> tuple[int, bytes]:
        return 409, b'{"detalle": "dato documental"}'

    api = ClienteApi("http://testserver", {"r": "t"}, transporte)
    with pytest.raises(ErrorApi) as error:
        api.put("/tareas/1/asignacion", "r", {"usuario_id": 2})
    assert str(error.value) == "PUT /tareas/1/asignacion respondió 409"
    with pytest.raises(ErrorApi, match="url prefirmada"):
        api.transferir("http://127.0.0.1:9/x", {}, b"")


def test_p12_main_de_exportacion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifiesto = tmp_path / "m.json"
    manifiesto.write_text(
        json.dumps(
            {"url_api": "https://x", "sesion": "s", "oraculo": "o", "corpus": {}, "tramites": {}}
        )
    )
    ocupada = tmp_path / "ocupada"
    ocupada.mkdir()
    (ocupada / "algo").write_text("x")
    base = ["--manifiesto", str(manifiesto), "--cliente-cognito", "c", "--usuario-responsable", "r"]
    assert exportar_evidencia.main([*base, "--salida", str(ocupada)]) == 1
    monkeypatch.setattr(exportar_evidencia, "tokens_cognito", lambda *_: {"responsable": "t"})
    assert exportar_evidencia.main([*base, "--salida", str(tmp_path / "vacia")]) == 0
    recibidos: list[Any] = []

    def exporta(cliente: Any, manifiesto_: Any, salida: Path, adicionales: Any) -> Any:
        recibidos.append(adicionales)
        return {"archivos": {}}

    monkeypatch.setattr(exportar_evidencia, "exportar", exporta)
    adicionales = ["--tramites-adicionales", "7", "8"]
    assert exportar_evidencia.main([*base, *adicionales, "--salida", str(tmp_path / "mas")]) == 0
    assert recibidos == [[7, 8]]

    def falla(*_: Any) -> Any:
        raise ErrorApi("GET", "/tramites/1", 503)

    monkeypatch.setattr(exportar_evidencia, "exportar", falla)
    assert exportar_evidencia.main([*base, "--salida", str(tmp_path / "otra")]) == 1


# --- Vaciado de buckets versionados (P8) -------------------------------------------------


@pytest.fixture
def s3(moto_local: str) -> Any:
    return crear_cliente(configuracion_sin_base(aws_endpoint_url=moto_local), "s3")


def _bucket(s3: Any, etiquetas: dict[str, str] | None) -> str:
    nombre = f"atlas-demo-vaciado-{uuid.uuid4().hex[:8]}"
    s3.create_bucket(Bucket=nombre)
    s3.put_bucket_versioning(Bucket=nombre, VersioningConfiguration={"Status": "Enabled"})
    if etiquetas:
        s3.put_bucket_tagging(
            Bucket=nombre,
            Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in etiquetas.items()]},
        )
    for _ in range(2):
        s3.put_object(Bucket=nombre, Key="documentos/a.pdf", Body=b"x")
    s3.delete_object(Bucket=nombre, Key="documentos/a.pdf")  # marcador de eliminación
    return nombre


def test_p8_simula_por_defecto_y_borra_todas_las_versiones(s3: Any) -> None:
    bucket = _bucket(s3, {"proyecto": "atlas", "entorno": "demo", "raiz": "persistent"})
    simulado = vaciar_bucket_versionado.vaciar(s3, bucket, ejecutar=False)
    assert (simulado.versiones, simulado.marcadores, simulado.eliminados) == (2, 1, 0)
    assert vaciar_bucket_versionado.main(["--bucket", bucket, "--ejecutar"], s3=s3) == 2
    assert (
        vaciar_bucket_versionado.main(
            ["--bucket", bucket, "--confirmar", bucket, "--ejecutar"], s3=s3
        )
        == 0
    )
    restante = s3.list_object_versions(Bucket=bucket)
    assert not restante.get("Versions") and not restante.get("DeleteMarkers")
    s3.delete_bucket(Bucket=bucket)  # vacío de verdad: se puede retirar


@pytest.mark.parametrize(
    "etiquetas",
    [None, {"proyecto": "atlas", "raiz": "bootstrap"}, {"proyecto": "otro", "entorno": "demo"}],
)
def test_p8_se_niega_fuera_de_la_demo_y_con_el_estado_remoto(
    s3: Any, etiquetas: dict[str, str] | None
) -> None:
    bucket = _bucket(s3, etiquetas)
    assert vaciar_bucket_versionado.main(["--bucket", bucket], s3=s3) == 1
    assert len(s3.list_object_versions(Bucket=bucket)["Versions"]) == 2


# --- Semilla local de desarrollo (WEB F8, F9) --------------------------------------------


@pytest.mark.integracion
def test_f9_semilla_local_con_procesamiento_simulado(
    base_migrada: Configuracion, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from atlas.herramientas import sembrar_local

    aplicacion = crear_aplicacion(base_migrada)
    with TestClient(aplicacion) as cliente:
        manifiesto, tokens = sembrar_local.sembrar(
            base_migrada, "http://testserver", CLAVES_PRUEBA, transporte_de(cliente)
        )
    aplicacion.state.motor.dispose()
    assert manifiesto.resultado == "completado"
    assert "SIMULADO" in manifiesto.oraculo
    assert set(tokens) == set(sembrar_demo.ROLES)
    observado = manifiesto.tramites["observado"]
    # Con la simulación del oráculo, la IA «acierta»: todo se confirma y queda rotulado.
    assert observado["validaciones"]["O-v1"]["tipo_documental"] == "confirmacion"
    assert observado["controles"]["R3"] == "advertencia"
    monkeypatch.setattr(
        sembrar_local, "obtener_configuracion", lambda: configuracion_sin_base(entorno="demo")
    )
    assert sembrar_local.main([]) == 1


@pytest.mark.integracion
def test_demo_surdelta_semilla_local_simulada(base_migrada: Configuracion) -> None:
    """La cartera SurDelta también se siembra en local para ensayar la demo sin AWS."""
    from atlas.herramientas import sembrar_local

    aplicacion = crear_aplicacion(base_migrada)
    with TestClient(aplicacion) as cliente:
        manifiesto, _ = sembrar_local.sembrar(
            base_migrada, "http://testserver", CLAVES_PRUEBA, transporte_de(cliente), "surdelta"
        )
    aplicacion.state.motor.dispose()
    assert manifiesto.resultado == "completado"
    assert manifiesto.oraculo.startswith("oraculo_surdelta_v1")
    assert set(manifiesto.tramites) == {"suministro", "observado", "pendiente", "cancelado"}
    assert manifiesto.tramites["suministro"]["estado"] == "cerrado"
    assert manifiesto.tramites["observado"]["controles"]["R1"] == "advertencia"


@pytest.mark.integracion
def test_f9_semilla_local_usa_o_crea_el_administrador(base_reiniciada: Configuracion) -> None:
    from atlas.herramientas import sembrar_local

    assert sembrar_local.sub_administrador(base_reiniciada) == sembrar_local.SUBS["administrador"]
    # Con un administrador ya creado, la semilla actúa con esa misma identidad.
    assert sembrar_local.sub_administrador(base_reiniciada) == sembrar_local.SUBS["administrador"]


def test_f9_main_de_la_semilla_local_guarda_el_manifiesto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from atlas.herramientas import sembrar_local

    generadas = sembrar_local.claves_locales(tmp_path / "nuevas")
    assert sembrar_local.claves_locales(tmp_path / "nuevas").jwks() == generadas.jwks()
    monkeypatch.setattr(sembrar_local, "obtener_configuracion", configuracion_sin_base)
    monkeypatch.setattr(sembrar_local, "RAIZ_REPOSITORIO", tmp_path)
    monkeypatch.setattr(sembrar_local, "claves_locales", lambda _: CLAVES_PRUEBA)
    monkeypatch.setattr(
        sembrar_local, "sembrar", lambda *_: (_manifiesto(), {"responsable": "token-local"})
    )
    assert sembrar_local.main(["--claves", str(tmp_path / "claves")]) == 0
    salida = capsys.readouterr().out
    assert "Semilla LOCAL (simulada)" in salida and "[responsable]" in salida
    assert list((tmp_path / "operaciones" / "sesiones").glob("*/manifiesto_seed.json"))
