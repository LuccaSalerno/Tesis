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
from sqlalchemy import Engine

from atlas.configuracion import Configuracion
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
from tests.conftest import CLAVES_PRUEBA, configuracion_sin_base
from tests.datos import crear_cuenta
from tests.flujo_procesamiento import (
    PAGINAS_C_V1,
    AnalizadorFijo,
    extraccion_c_v1_pdf,
    modelo_contrato,
    recorrer,
    trabajo_de,
)

ORACULO = json.loads(sembrar_demo.ORACULO.read_text(encoding="utf-8"))


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

        def procesar(_: ClienteApi, __: int, archivos: list[int]) -> None:
            # Todo se procesa con el contrato fijo: O-v1 y F-v2 quedan sugeridos como
            # contrato y la semilla los corrige al tipo del oráculo.
            for archivo in archivos:
                recorrer(
                    aplicacion,
                    trabajo_de(motor_aplicacion, archivo),
                    modelo_contrato(extraccion_c_v1_pdf()),
                    AnalizadorFijo(PAGINAS_C_V1),
                )

        yield {"api": api, "procesar": procesar, "aplicacion": aplicacion}
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

    resumen = exportar_evidencia.exportar(entorno["api"], manifiesto.__dict__, tmp_path)
    evidencias = [n for n in resumen["archivos"] if "/evidencia/" in n]
    assert len(evidencias) == 2
    indice = json.loads((tmp_path / "indice.json").read_text())
    assert indice["sesion"] == "e90-pruebas"
    primera, segunda = (json.loads((tmp_path / n).read_text()) for n in sorted(evidencias))
    assert primera["decision"]["tipo"] == "aprobacion"
    assert segunda["decision"]["tipo"] == "observacion"
    assert segunda["decision"]["motivo"] == sembrar_demo.MOTIVO_OBSERVACION
    assert {c["codigo_regla"][:2] for c in primera["controles"]} == {"R1", "R2", "R3", "R4"}


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
