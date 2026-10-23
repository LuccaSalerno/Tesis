"""Fase 2 del arnés: latencia IA-M08 y carga §6.3.4 contra la API (DO-2026-10-23-E90-API).

Sin AWS: una API simulada en memoria responde las rutas que usan el cargador, la latencia y
la carga, con la forma de las respuestas reales. La instrumentación real de la API
(`Server-Timing`, tiempos del trabajo) se prueba en `test_api_web` y `test_api_tramites`.
"""

import json
import re
import threading
from pathlib import Path
from typing import Any

import pytest

from atlas.evaluacion import campana as cmp
from atlas.evaluacion import carga, cargador, http, latencia, operacion
from atlas.evaluacion.oraculos import Modo, cargar, consultas_de, seleccionar
from atlas.evaluacion.registro import Registro
from atlas.herramientas.cliente_api import ClienteApi
from tests import evaluacion_fijo as fijo

URL = "https://api.ejemplo"


class ApiSimulada:
    """Rutas mínimas de ATLAS. Cada trabajo termina en el segundo listado de archivos."""

    def __init__(self, perfil: str = "perfil-haiku", fallar_doc: str | None = None) -> None:
        self.perfil = perfil
        self.fallar_doc = fallar_doc
        self.ids = 0
        self.archivos: dict[int, dict[str, Any]] = {}
        self.listados: dict[int, int] = {}
        self.consultas = 0
        self._candado = threading.Lock()

    def _id(self) -> int:
        with self._candado:
            self.ids += 1
            return self.ids

    def transporte(
        self, metodo: str, url: str, encabezados: Any, cuerpo: bytes | None
    ) -> tuple[int, bytes]:
        estado, _, respuesta = self.envio(metodo, url, dict(encabezados), cuerpo)
        return estado, respuesta

    def envio(
        self, metodo: str, url: str, encabezados: dict[str, str], cuerpo: bytes | None
    ) -> tuple[int, dict[str, str], bytes]:
        if url.startswith("https://s3/"):  # la URL prefirmada recibe el archivo binario
            return 200, {}, b""
        datos = json.loads(cuerpo) if cuerpo else None
        ruta = url.removeprefix(URL)
        if ruta == "/salud":
            return 200, {}, b'{"estado": "ok"}'
        if metodo == "POST" and ruta == "/tramites":
            return 201, {}, json.dumps({"id": self._id()}).encode()
        if metodo == "POST" and re.fullmatch(r"/tramites/\d+/cargas", ruta):
            carga_id = self._id()
            self.archivos[carga_id] = {"nombre": datos["nombre"], "tramite": ruta.split("/")[2]}
            return (
                201,
                {},
                json.dumps(
                    {"id": carga_id, "url": f"https://s3/{carga_id}", "encabezados": {}}
                ).encode(),
            )
        if metodo == "POST" and (
            m := re.fullmatch(r"/tramites/\d+/cargas/(\d+)/confirmacion", ruta)
        ):
            archivo = self.archivos[int(m.group(1))]
            archivo["id"] = int(m.group(1))
            return (
                200,
                {},
                json.dumps({"id": archivo["id"], "trabajo": {"estado": "pendiente"}}).encode(),
            )
        if metodo == "GET" and (m := re.fullmatch(r"/tramites/(\d+)/archivos", ruta)):
            tramite = m.group(1)
            vez = self.listados[int(tramite)] = self.listados.get(int(tramite), 0) + 1
            salida = []
            for archivo in self.archivos.values():
                if archivo["tramite"] != tramite:
                    continue
                fallido = self.fallar_doc is not None and self.fallar_doc in archivo["nombre"]
                estado = "en_ejecucion" if vez == 1 else ("fallido" if fallido else "completado")
                salida.append(
                    {
                        "id": archivo["id"],
                        "trabajo": {
                            "estado": estado,
                            "creado_en": "2026-10-23T10:00:00+00:00",
                            "actualizado_en": "2026-10-23T10:00:42+00:00",
                        },
                    }
                )
            return 200, {}, json.dumps(salida).encode()
        if metodo == "POST" and re.fullmatch(r"/tramites/\d+/archivos/\d+/incorporacion", ruta):
            return 201, {}, json.dumps({"id": self._id()}).encode()
        if metodo == "POST" and re.fullmatch(r"/tramites/\d+/consultas", ruta):
            with self._candado:
                self.consultas += 1
                primera = self.consultas == 1
            arranque = "frio" if primera else "caliente"
            tiempos = (
                "embeddings;dur=80, recuperacion;dur=20, generacion;dur=900, total;dur=1010, "
                f'arranque;desc="{arranque}"'
            )
            cuerpo_respuesta = {"id": 1, "suficiente": True, "modelo_generacion": self.perfil}
            return 201, {"Server-Timing": tiempos}, json.dumps(cuerpo_respuesta).encode()
        if metodo == "GET" and re.fullmatch(r"/tramites/\d+", ruta):
            return 200, {}, b'{"id": 1}'
        return 404, {}, b""


@pytest.fixture
def raiz(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fijo.construir(tmp_path, congelado=True)
    monkeypatch.setattr(
        cmp, "_commit", lambda _: {"commit": "abc1234", "cambios_sin_commit": False}
    )
    monkeypatch.setattr(operacion, "DIRECTORIO", tmp_path / "evaluacion" / "campanas")
    return tmp_path


def _cliente(api: ApiSimulada) -> ClienteApi:
    return ClienteApi(URL, {"responsable": "token"}, transporte=api.transporte)


# --- Solicitud cronometrada ----------------------------------------------------------------


def test_p4_server_timing_se_lee_por_componente() -> None:
    tiempos = http.leer_server_timing(
        'embeddings;dur=12.5, total;dur=40, arranque;desc="frio", vacio'
    )
    assert tiempos == {"embeddings": 12.5, "total": 40.0, "arranque": "frio"}
    assert http.leer_server_timing(None) == {}


def test_p3_medida_completa_error_de_red_y_cuerpo_invalido() -> None:
    relojes = iter([1.0, 1.25])
    medida = http.medir(
        lambda *_: (201, {"server-timing": "total;dur=9"}, b'{"a": 1}'),
        "POST",
        URL,
        "t",
        {"x": 1},
        lambda: next(relojes),
    )
    assert (
        medida.estado == 201
        and medida.duracion_ms == pytest.approx(250)
        and medida.cuerpo == {"a": 1}
    )
    assert medida.server_timing == {"total": 9.0}

    def sin_red(*_: Any) -> Any:
        raise TimeoutError

    assert http.medir(sin_red, "GET", URL).error == "TimeoutError"
    assert http.medir(lambda *_: (502, {}, b"<html>"), "GET", URL).cuerpo is None
    with pytest.raises(ValueError, match="Solo HTTPS"):
        http.envio_urllib("GET", "http://ejemplo", {}, None)


# --- Cargador del corpus (P2) --------------------------------------------------------------


def test_p2_un_tramite_por_contexto_con_incorporacion(raiz: Path) -> None:
    oraculos = cargar(raiz)
    consultas = consultas_de(oraculos, Modo.OFICIAL)
    grupos = cargador.contextos(consultas)
    assert grupos == {"C01": ("E90-M-CTR-01", "E90-M-FAC-01"), "C02": ("E90-M-FAC-01",)}
    api = ApiSimulada(fallar_doc="doc-aaaa0002")
    documentos = {d.doc_id: d for d in seleccionar(oraculos, Modo.OFICIAL)}
    resultado = cargador.cargar(_cliente(api), documentos, grupos, esperar_s=lambda _: None)
    c01 = resultado["C01"]["documentos"]
    assert c01["E90-M-CTR-01"]["documento_id"] is not None
    # Un trabajo fallido no se incorpora y queda registrado.
    assert (
        c01["E90-M-FAC-01"]["documento_id"] is None
        and c01["E90-M-FAC-01"]["trabajo"]["estado"] == "fallido"
    )


def test_p2_espera_maxima(raiz: Path) -> None:
    api = ApiSimulada()
    api.listados = {}
    tramite = _cliente(api).post("/tramites", "responsable", {"titulo": "x"})
    documento = seleccionar(cargar(raiz), Modo.ENSAYO)[0]
    archivo = cargador.subir(_cliente(api), tramite["id"], documento)
    with pytest.raises(RuntimeError, match="procesamiento_sin_terminar"):
        cargador.esperar(
            _cliente(api), tramite["id"], [archivo["id"]], esperar_s=lambda _: None, maximo_s=-1
        )


# --- Latencia (P3, P6, P7) -----------------------------------------------------------------


def test_p6_percentil_por_rango_mas_cercano() -> None:
    valores = list(range(1, 91))  # 90 observaciones
    assert latencia.percentil_cercano(valores, 95) == 86
    assert (
        latencia.percentil_cercano([7.0], 95) == 7.0 and latencia.percentil_cercano([], 95) is None
    )
    assert latencia.resumen([1.0, 3.0, 2.0])["mediana_ms"] == 2.0


def test_p3_bloques_verifican_perfil_y_no_se_repiten(raiz: Path) -> None:
    api = ApiSimulada(perfil="perfil-haiku")
    registro = Registro(raiz / "latencia.jsonl")
    latencia.linea_base_red(api.envio, URL, registro, muestras=3)
    preguntas = [latencia.Pregunta("Q01", "¿Vigencia?", 1), latencia.Pregunta("Q02", "¿Cuenta?", 2)]
    latencia.medir_bloque(
        api.envio,
        URL,
        "t",
        preguntas,
        modelo="haiku",
        perfil="perfil-haiku",
        repeticion=1,
        registro=registro,
    )
    latencia.medir_bloque(
        api.envio,
        URL,
        "t",
        preguntas,
        modelo="sonnet",
        perfil="perfil-sonnet",
        repeticion=1,
        registro=registro,
    )
    with pytest.raises(ValueError, match="bloque_ya_medido"):
        latencia.medir_bloque(
            api.envio,
            URL,
            "t",
            preguntas,
            modelo="haiku",
            perfil="p",
            repeticion=1,
            registro=registro,
        )
    falla = ApiSimulada()
    falla.envio = lambda *_: (429, {}, b"")  # type: ignore[method-assign]
    latencia.medir_bloque(
        falla.envio,
        URL,
        "t",
        preguntas[:1],
        modelo="haiku",
        perfil="p",
        repeticion=2,
        registro=registro,
    )
    resultado = latencia.metricas(registro.leer())
    assert resultado["red"]["n"] == 3
    haiku, sonnet = resultado["modelos"]["haiku"], resultado["modelos"]["sonnet"]
    assert haiku["n"] == 2 and haiku["cumple"] is True and haiku["arranques_en_frio"] == 1
    assert haiku["errores"] == {"http_429": 1} and haiku["solicitudes"] == 3
    assert haiku["componentes_servidor"]["generacion"]["mediana_ms"] == 900
    assert sonnet["perfil_distinto"] == 2  # la API respondió con otro perfil: despliegue equivocado
    assert latencia.metricas([])["modelos"] == {}


# --- Carga (P8) ----------------------------------------------------------------------------


def test_p8_niveles_interactivos_y_trabajos(raiz: Path) -> None:
    api = ApiSimulada()
    registro = Registro(raiz / "carga.jsonl")
    carga.interactiva(
        api.envio, URL, "t", 1, cargador.PREGUNTAS_GENERICAS, registro, niveles=(1, 5)
    )
    ajuste = seleccionar(cargar(raiz), Modo.ENSAYO)
    carga.asincronica(_cliente(api), ajuste, registro, niveles=(1, 2), esperar_s=lambda _: None)
    resultado = carga.metricas(registro.leer())
    assert resultado["interactiva"]["consulta_5"]["completadas"] == 30
    assert resultado["interactiva"]["lectura_1"]["errores"] == 0
    assert resultado["asincronica"]["2"]["completados"] == 2
    assert resultado["asincronica"]["1"]["mediana_ms"] == 42000.0
    assert carga._segundos({"estado": "fallido"}) is None


# --- Línea de comandos (P1, P11, P12) ------------------------------------------------------


class EntornoSimulado(operacion.Entorno):
    def __init__(self, api: ApiSimulada) -> None:
        self.api = api
        self.envio = api.envio

    def token(self, manifiesto: dict[str, Any]) -> str:
        return "token"

    def cliente(self, manifiesto: dict[str, Any]) -> ClienteApi:
        return _cliente(self.api)


def _iniciar(modo: str, campana: str) -> list[str]:
    return [
        "iniciar", "--campana", campana, "--modo", modo, "--url-api", URL,
        "--version-codigo", "abc", "--cliente-cognito", "cli",
        "--generativos", "haiku=perfil-haiku", "sonnet=perfil-sonnet",
    ]  # fmt: skip


def test_p11_campana_de_ensayo_de_punta_a_punta(
    raiz: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cargador.time, "sleep", lambda _: None)
    api = ApiSimulada()
    entorno = EntornoSimulado(api)

    def correr(*argumentos: str) -> int:
        return _main(list(argumentos), entorno, raiz)

    assert correr(*_iniciar("ensayo", "a1")) == 0
    assert correr(*_iniciar("ensayo", "a1")) == 1  # campaña existente
    base = ["--campana", "a1"]
    for paso in (
        ["cargar"],
        ["red"],
        ["latencia", "--modelo", "haiku", "--repeticion", "1"],
        ["carga"],
    ):
        assert correr(paso[0], *base, *paso[1:]) == 0, paso
    assert correr("cargar", *base) == 1 and correr("carga", *base) == 1  # no se repiten
    assert correr("metricas", *base) == 0
    resultado = json.loads((raiz / "evaluacion/campanas/a1/metricas.json").read_text("utf-8"))
    assert (
        resultado["latencia"]["modelos"]["haiku"]["n"] == 3 and not resultado["reportable_ia_m08"]
    )
    informe = (raiz / "evaluacion/campanas/a1/informe.md").read_text("utf-8")
    assert "ENSAYO" in informe and "consulta_10" in informe and "trabajos_10" in informe
    assert "corpus_ya_cargado" in capsys.readouterr().err


def test_p2_campana_oficial_carga_contextos_y_tramite_de_carga(
    raiz: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cargador.time, "sleep", lambda _: None)
    entorno = EntornoSimulado(ApiSimulada())
    assert _main(_iniciar("oficial", "o1"), entorno, raiz) == 0
    assert _main(["cargar", "--campana", "o1"], entorno, raiz) == 0
    assert (
        _main(
            ["latencia", "--campana", "o1", "--modelo", "haiku", "--repeticion", "1"], entorno, raiz
        )
        == 0
    )
    assert _main(["carga", "--campana", "o1"], entorno, raiz) == 0
    corpus = json.loads((raiz / "evaluacion/campanas/o1/carga_corpus.json").read_text("utf-8"))
    assert set(corpus) == {"C01", "C02", operacion.TRAMITE_CARGA}
    filas = Registro(raiz / "evaluacion/campanas/o1/latencia.jsonl").leer()
    assert [f["pregunta_id"] for f in filas] == ["Q01", "Q02"]
    oraculo = raiz / "oraculos/e90/consultas_candidatas.json"
    oraculo.write_text(oraculo.read_text("utf-8") + " ", "utf-8")
    assert _main(["metricas", "--campana", "o1"], entorno, raiz) == 1  # oráculos cambiados


def test_p1_validaciones_de_la_campana(raiz: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    entorno = EntornoSimulado(ApiSimulada())
    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": None, "cambios_sin_commit": None})
    assert _main(_iniciar("oficial", "o2"), entorno, raiz) == 1
    otra = raiz / "evaluacion/campanas/x"
    otra.mkdir(parents=True)
    (otra / "manifiesto.json").write_text(json.dumps({"tipo": "directo"}), "utf-8")
    assert _main(["red", "--campana", "x"], entorno, raiz) == 1


def test_p1_entorno_real_construye_clientes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        operacion,
        "tokens_cognito",
        lambda region, cliente, usuarios: {"responsable": f"{region}:{cliente}"},
    )
    manifiesto = {
        "region": "us-east-1",
        "cliente_cognito": "c",
        "usuario_responsable": "u",
        "url_api": URL,
    }
    entorno = operacion.Entorno()
    assert entorno.token(manifiesto) == "us-east-1:c"
    assert entorno.cliente(manifiesto).url_base == URL and entorno.envio is http.envio_urllib


def _main(argumentos: list[str], entorno: operacion.Entorno, raiz: Path) -> int:
    monkey = pytest.MonkeyPatch()
    monkey.setattr(cmp, "RAIZ_REPOSITORIO", raiz)
    try:
        return operacion.main(argumentos, entorno)
    finally:
        monkey.undo()


def test_p3_envio_real_contra_un_servidor_local() -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Manejador(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            codigo = 200 if self.path == "/salud" else 404
            self.send_response(codigo)
            self.send_header("Server-Timing", "total;dur=3")
            self.end_headers()
            self.wfile.write(b'{"estado": "ok"}' if codigo == 200 else b"")

        def log_message(self, *_: Any) -> None:
            return None

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        base = f"http://127.0.0.1:{servidor.server_address[1]}"
        bien = http.medir(http.envio_urllib, "GET", f"{base}/salud")
        assert (
            bien.estado == 200
            and bien.cuerpo == {"estado": "ok"}
            and bien.server_timing == {"total": 3.0}
        )
        assert http.medir(http.envio_urllib, "GET", f"{base}/otra").estado == 404
    finally:
        servidor.shutdown()
