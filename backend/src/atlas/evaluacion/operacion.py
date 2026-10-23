"""Campañas contra la API desplegada: latencia IA-M08 y carga §6.3.4 (DO-2026-10-23-E90-API).

La ejecuta el operador con la sesión E90A en `active` y las cuentas de la semilla. Pasos sobre
`evaluacion/campanas/<id>/`:

    iniciar → cargar → red → latencia (un bloque por modelo y repetición) → carga → metricas

Entre bloques de distinto modelo, el operador reaplica `demo` con `perfil_generativo` y
`modelo_generativo` (P5), en el orden H, S │ S, H │ H, S. La clave del responsable sale de
`ATLAS_SEED_CLAVE_RESPONSABLE`; los tokens viven en memoria.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from atlas.evaluacion import campana as cmp
from atlas.evaluacion import carga, cargador, latencia
from atlas.evaluacion.http import Envio, envio_urllib
from atlas.evaluacion.oraculos import Modo, cargar, consultas_de, seleccionar
from atlas.evaluacion.registro import Registro
from atlas.herramientas.cliente_api import ClienteApi, tokens_cognito

DIRECTORIO: Final = cmp.RAIZ_REPOSITORIO / "evaluacion" / "campanas"
TRAMITE_CARGA: Final = "CARGA"


class Entorno:
    """Dependencias externas, reemplazables en las pruebas."""

    def __init__(self) -> None:
        self.envio: Envio = envio_urllib

    def token(self, manifiesto: dict[str, Any]) -> str:
        tokens = tokens_cognito(
            manifiesto["region"],
            manifiesto["cliente_cognito"],
            {"responsable": manifiesto["usuario_responsable"]},
        )
        return tokens["responsable"]

    def cliente(self, manifiesto: dict[str, Any]) -> ClienteApi:
        return ClienteApi(manifiesto["url_api"], {"responsable": self.token(manifiesto)})


def _leer(ruta: Path) -> dict[str, Any]:
    datos: dict[str, Any] = json.loads(ruta.read_text("utf-8"))
    return datos


def _escribir(ruta: Path, datos: Any) -> None:
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), "utf-8")


def iniciar(argumentos: argparse.Namespace, raiz: Path | None = None) -> Path:
    raiz = raiz or cmp.RAIZ_REPOSITORIO
    destino: Path = DIRECTORIO / str(argumentos.campana)
    if destino.exists():
        raise cmp.ErrorCampana("campana_existente")
    modo = Modo(argumentos.modo)
    oraculos = cargar(raiz)
    documentos = seleccionar(oraculos, modo)  # compuerta P4 de E90-MEDICION
    origen = cmp._commit(raiz)
    if modo is Modo.OFICIAL and (not origen["commit"] or origen["cambios_sin_commit"] is not False):
        raise cmp.ErrorCampana("commit_no_identificado_o_con_cambios")
    generativos = dict(par.split("=", 1) for par in argumentos.generativos)
    manifiesto = {
        "campana": argumentos.campana,
        "tipo": "api",
        "modo": modo.value,
        "reportable_ia_m08": modo is Modo.OFICIAL,
        "creada_en": datetime.now(UTC).isoformat(),
        **origen,
        "url_api": argumentos.url_api,
        "version_codigo": argumentos.version_codigo,
        "region": argumentos.region,
        "cliente_cognito": argumentos.cliente_cognito,
        "usuario_responsable": argumentos.usuario_responsable,
        "generativos": generativos,
        "documentos": {d.doc_id: d.sha256 for d in documentos},
        "oraculos": oraculos.hashes,
    }
    destino.mkdir(parents=True)
    _escribir(destino / "manifiesto.json", manifiesto)
    return destino


def _preguntas(
    manifiesto: dict[str, Any], carga_corpus: dict[str, Any], raiz: Path
) -> list[latencia.Pregunta]:
    modo = Modo(manifiesto["modo"])
    if modo is Modo.ENSAYO:
        tramite = carga_corpus["E01"]["tramite_id"]
        return [
            latencia.Pregunta(f"G{n}", texto, tramite)
            for n, texto in enumerate(cargador.PREGUNTAS_GENERICAS, start=1)
        ]
    consultas = consultas_de(cargar(raiz), modo)
    por_documentos = {docs: nombre for nombre, docs in cargador.contextos(consultas).items()}
    return [
        latencia.Pregunta(
            c.pregunta_id,
            c.pregunta,
            carga_corpus[por_documentos[tuple(sorted(c.documentos))]]["tramite_id"],
        )
        for c in consultas
    ]


def ejecutar(argumentos: argparse.Namespace, entorno: Entorno, raiz: Path | None = None) -> str:
    raiz = raiz or cmp.RAIZ_REPOSITORIO
    if argumentos.paso == "iniciar":
        return f"campana_creada:{iniciar(argumentos, raiz)}"
    destino: Path = DIRECTORIO / str(argumentos.campana)
    manifiesto = _leer(destino / "manifiesto.json")
    if manifiesto.get("tipo") != "api":
        raise cmp.ErrorCampana("no_es_campana_api")
    oraculos = cargar(raiz)
    if oraculos.hashes != manifiesto["oraculos"]:
        raise cmp.ErrorCampana("oraculos_cambiaron")
    modo = Modo(manifiesto["modo"])
    ruta_corpus = destino / "carga_corpus.json"
    registro_latencia = Registro(destino / "latencia.jsonl")

    if argumentos.paso == "cargar":
        if ruta_corpus.exists():
            raise cmp.ErrorCampana("corpus_ya_cargado")
        documentos = {d.doc_id: d for d in seleccionar(oraculos, modo)}
        grupos = (
            {"E01": tuple(documentos)}
            if modo is Modo.ENSAYO
            else cargador.contextos(consultas_de(oraculos, modo))
        )
        resultado = cargador.cargar(entorno.cliente(manifiesto), documentos, grupos)
        _escribir(ruta_corpus, resultado)
        fallidos = sum(
            d["documento_id"] is None for t in resultado.values() for d in t["documentos"].values()
        )
        return f"corpus_cargado:{len(resultado)}_tramites:{fallidos}_sin_incorporar"
    if argumentos.paso == "red":
        latencia.linea_base_red(entorno.envio, manifiesto["url_api"], registro_latencia)
        return "red_medida"
    if argumentos.paso == "latencia":
        perfil = manifiesto["generativos"][argumentos.modelo]
        preguntas = _preguntas(manifiesto, _leer(ruta_corpus), raiz)
        cantidad = latencia.medir_bloque(
            entorno.envio,
            manifiesto["url_api"],
            entorno.token(manifiesto),
            preguntas,
            modelo=argumentos.modelo,
            perfil=perfil,
            repeticion=argumentos.repeticion,
            registro=registro_latencia,
        )
        return f"bloque_medido:{argumentos.modelo}:{argumentos.repeticion}:{cantidad}"
    if argumentos.paso == "carga":
        corpus = _leer(ruta_corpus) if ruta_corpus.exists() else {}
        ajuste = seleccionar(oraculos, Modo.ENSAYO)  # P8: siempre la partición de ajuste
        api = entorno.cliente(manifiesto)
        if "E01" in corpus:
            tramite_id = corpus["E01"]["tramite_id"]
        else:
            if TRAMITE_CARGA not in corpus:
                corpus[TRAMITE_CARGA] = cargador.cargar_contexto(api, TRAMITE_CARGA, ajuste[:3])
                _escribir(ruta_corpus, corpus)
            tramite_id = corpus[TRAMITE_CARGA]["tramite_id"]
        registro = Registro(destino / "carga.jsonl")
        if registro.leer():
            raise cmp.ErrorCampana("carga_ya_medida")
        carga.interactiva(
            entorno.envio,
            manifiesto["url_api"],
            entorno.token(manifiesto),
            tramite_id,
            cargador.PREGUNTAS_GENERICAS,
            registro,
        )
        carga.asincronica(api, ajuste, registro)
        return "carga_medida"
    resultado = {
        "campana": manifiesto["campana"],
        "modo": manifiesto["modo"],
        "reportable_ia_m08": manifiesto["reportable_ia_m08"],
        "latencia": latencia.metricas(registro_latencia.leer()),
        "carga": carga.metricas(Registro(destino / "carga.jsonl").leer()),
    }
    _escribir(destino / "metricas.json", resultado)
    (destino / "informe.md").write_text(informe(resultado), "utf-8")
    return f"metricas_listas:{destino / 'informe.md'}"


def _ms(valor: float | None) -> str:
    return "—" if valor is None else f"{valor / 1000:.2f} s"


def informe(resultado: dict[str, Any]) -> str:
    lineas = [f"# Campaña API {resultado['campana']} ({resultado['modo']})", ""]
    if not resultado["reportable_ia_m08"]:
        lineas += [
            "> **ENSAYO:** la latencia usa preguntas genéricas sobre el ajuste; no es IA-M08.",
            "",
        ]
    red = resultado["latencia"]["red"]
    lineas += [
        "## Latencia de la consulta (IA-M08: mediana ≤ 5 s, p95 ≤ 10 s)",
        "",
        f"Línea de base de red (`GET /salud`): mediana {_ms(red['mediana_ms'])}, "
        f"p95 {_ms(red['p95_ms'])}.",
        "",
        "| Modelo | n | Mediana | p95 | Máximo | Errores | Arranques en frío "
        "| Perfil distinto | Resultado |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for modelo, datos in resultado["latencia"]["modelos"].items():
        estado = "—" if datos["cumple"] is None else ("Cumple" if datos["cumple"] else "No cumple")
        lineas.append(
            f"| {modelo} | {datos['n']} | {_ms(datos['mediana_ms'])} | {_ms(datos['p95_ms'])} "
            f"| {_ms(datos['maximo_ms'])} | {sum(datos['errores'].values())} "
            f"| {datos['arranques_en_frio']} | {datos['perfil_distinto']} | {estado} |"
        )
    lineas += [
        "",
        "## Concurrencia (§6.3.4)",
        "",
        "| Operación y nivel | n | Mediana | p95 | Errores |",
        "|---|---|---|---|---|",
    ]
    for clave, datos in resultado["carga"]["interactiva"].items():
        lineas.append(
            f"| {clave} | {datos['n']} | {_ms(datos['mediana_ms'])} "
            f"| {_ms(datos['p95_ms'])} | {datos['errores']} |"
        )
    for nivel, datos in resultado["carga"]["asincronica"].items():
        lineas.append(
            f"| trabajos_{nivel} | {datos['n']} | {_ms(datos['mediana_ms'])} "
            f"| {_ms(datos['p95_ms'])} | {datos['fallidos']} |"
        )
    return "\n".join(lineas) + "\n"


def analizador() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    pasos = raiz.add_subparsers(dest="paso", required=True)
    nuevo = pasos.add_parser("iniciar")
    nuevo.add_argument("--campana", required=True)
    nuevo.add_argument("--modo", choices=[m.value for m in Modo], required=True)
    nuevo.add_argument("--url-api", required=True)
    nuevo.add_argument("--version-codigo", required=True)
    nuevo.add_argument("--cliente-cognito", required=True)
    nuevo.add_argument("--usuario-responsable", default="atlas-responsable")
    nuevo.add_argument("--region", default="us-east-1")
    nuevo.add_argument("--generativos", nargs="+", required=True, metavar="ALIAS=PERFIL")
    for paso in ("cargar", "red", "carga", "metricas"):
        pasos.add_parser(paso).add_argument("--campana", required=True)
    bloque = pasos.add_parser("latencia")
    bloque.add_argument("--campana", required=True)
    bloque.add_argument("--modelo", required=True)
    bloque.add_argument("--repeticion", type=int, choices=(1, 2, 3), required=True)
    return raiz


def main(argumentos: list[str] | None = None, entorno: Entorno | None = None) -> int:
    try:
        print(ejecutar(analizador().parse_args(argumentos), entorno or Entorno()))
    except (cmp.ErrorCampana, ValueError, RuntimeError, KeyError) as error:
        print(f"Campaña detenida: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
