"""Línea de comandos del arnés (DO-2026-10-23-E90-MEDICION). La ejecuta el operador.

Pasos, en orden, sobre `evaluacion/campanas/<id>/`:

    iniciar → ocr → medir → indexar → recuperar → responder → planillas
    → (autores) discrepancias → (consenso) metricas

`ocr`, `medir`, `indexar`, `recuperar` y `responder` invocan Textract y Bedrock reales con
las credenciales del operador. Los demás pasos son locales.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any, Final

from atlas.evaluacion import campana as cmp
from atlas.evaluacion import informe, planillas, recuperacion
from atlas.evaluacion.contenidos import FuenteContenidos
from atlas.evaluacion.ejecucion import medir_documentos
from atlas.evaluacion.oraculos import Modo, consultas_de, seleccionar
from atlas.evaluacion.registro import Registro
from atlas.integraciones.aws import AlmacenS3, crear_cliente_region
from atlas.integraciones.bedrock import (
    EmbeddingsCohereBedrock,
    EmbeddingsTitanBedrock,
    ModeloBedrockConverse,
)
from atlas.integraciones.textract import AnalizadorTextract
from atlas.procesamiento.embeddings import ModeloEmbeddings

DIRECTORIO: Final = cmp.RAIZ_REPOSITORIO / "evaluacion" / "campanas"
CACHE_OCR: Final = cmp.RAIZ_REPOSITORIO / "evaluacion" / "cache_ocr"


def _pares(valores: Sequence[str]) -> dict[str, str]:
    salida = {}
    for valor in valores:
        alias, _, identificador = valor.partition("=")
        if not alias or not identificador:
            raise ValueError(f"se_espera_alias=identificador:{valor}")
        salida[alias] = identificador
    return salida


def _embeddings(cliente: Any, modelo: str) -> ModeloEmbeddings:
    if modelo.startswith("amazon.titan-embed"):
        return EmbeddingsTitanBedrock(cliente, modelo)
    return EmbeddingsCohereBedrock(cliente, modelo)


def _fuente(c: cmp.Campana, con_servicios: bool) -> FuenteContenidos:
    registro = Registro(c.ruta("ocr"))
    if not con_servicios:
        return FuenteContenidos(CACHE_OCR, registrar=registro.escribir)
    bucket = c.manifiesto["bucket"]
    if not bucket:
        raise cmp.ErrorCampana("falta_bucket")
    region = c.manifiesto["region"]
    return FuenteContenidos(
        CACHE_OCR,
        AnalizadorTextract(crear_cliente_region("textract", region), bucket),
        AlmacenS3(crear_cliente_region("s3", region), bucket),
        registrar=registro.escribir,
    )


def _bloques_docx(fuente: FuenteContenidos, oraculos: Any) -> Any:
    def resolver(doc_id: str) -> dict[str, str]:
        contenido = fuente.obtener(oraculos.documentos[doc_id])
        return {b.localizador: b.texto for p in contenido.paginas for b in p.bloques}

    return resolver


def _rankings(c: cmp.Campana) -> dict[str, list[str]]:
    principal = c.manifiesto["embeddings_principal"]
    return {
        f["pregunta_id"]: [r["chunk_id"] for r in f["ranking"]]
        for f in Registro(c.ruta("recuperacion")).leer()
        if f["embeddings"] == principal
    }


def ejecutar(argumentos: argparse.Namespace) -> str:
    if argumentos.paso == "iniciar":
        nueva = cmp.iniciar(
            DIRECTORIO,
            identificador=argumentos.campana,
            modo=Modo(argumentos.modo),
            generativos=_pares(argumentos.generativos),
            embeddings=_pares(argumentos.embeddings),
            repeticiones=argumentos.repeticiones,
            region=argumentos.region,
            bucket=argumentos.bucket,
        )
        return f"campana_creada:{nueva.directorio}"
    c, oraculos = cmp.abrir(DIRECTORIO, argumentos.campana)
    m = c.manifiesto
    documentos = seleccionar(oraculos, c.modo)
    consultas = consultas_de(oraculos, c.modo)
    region = m["region"]
    if argumentos.paso == "ocr":
        fuente = _fuente(c, con_servicios=True)
        for documento in documentos:
            fuente.obtener(documento)
        return f"ocr_listo:{len(documentos)}"
    if argumentos.paso == "medir":
        bedrock = crear_cliente_region("bedrock-runtime", region)
        nuevas = medir_documentos(
            documentos,
            _fuente(c, con_servicios=False),
            {a: ModeloBedrockConverse(bedrock, p) for a, p in m["generativos"].items()},
            Registro(c.ruta("medicion")),
            repeticiones=m["repeticiones"],
            max_tokens_clasificacion=m["limites"]["max_tokens_clasificacion"],
            max_tokens_extraccion=m["limites"]["max_tokens_extraccion"],
            caracteres_maximos=m["limites"]["caracteres_maximos"],
        )
        return f"mediciones_nuevas:{nuevas}"
    if argumentos.paso == "indexar":
        bedrock = crear_cliente_region("bedrock-runtime", region)
        chunks = recuperacion.chunks_de(documentos, _fuente(c, con_servicios=False))
        for alias, modelo in m["embeddings"].items():
            ruta = c.ruta(f"indices/{alias}.json")
            if not ruta.exists():
                indice = recuperacion.construir_indice(chunks, _embeddings(bedrock, modelo))
                recuperacion.guardar_indice(indice, ruta)
        return f"indices_listos:{len(m['embeddings'])}:{len(chunks)}_chunks"
    if argumentos.paso == "recuperar":
        bedrock = crear_cliente_region("bedrock-runtime", region)
        indices = {
            a: recuperacion.cargar_indice(c.ruta(f"indices/{a}.json")) for a in m["embeddings"]
        }
        nuevas = recuperacion.medir_recuperacion(
            consultas,
            indices,
            {a: _embeddings(bedrock, modelo) for a, modelo in m["embeddings"].items()},
            oraculos.fragmentos,
            Registro(c.ruta("recuperacion")),
        )
        return f"recuperaciones_nuevas:{nuevas}"
    if argumentos.paso == "responder":
        bedrock = crear_cliente_region("bedrock-runtime", region)
        indice = recuperacion.cargar_indice(c.ruta(f"indices/{m['embeddings_principal']}.json"))
        nuevas = recuperacion.medir_respuestas(
            consultas,
            indice,
            _rankings(c),
            {a: ModeloBedrockConverse(bedrock, p) for a, p in m["generativos"].items()},
            Registro(c.ruta("respuestas")),
            repeticiones=m["repeticiones"],
            max_tokens=m["limites"]["max_tokens_consulta"],
        )
        return f"respuestas_nuevas:{nuevas}"
    if argumentos.paso == "planillas":
        indice = recuperacion.cargar_indice(c.ruta(f"indices/{m['embeddings_principal']}.json"))
        filas = Registro(c.ruta("respuestas")).leer()
        for autor in ("autor_a", "autor_b"):
            destino = c.ruta(f"planillas/{autor}.csv")
            if destino.exists():
                raise cmp.ErrorCampana(f"planilla_existente:{autor}")
            grupos = planillas.generar_planilla(filas, consultas, indice, destino)
        return f"planillas_listas:{grupos}_grupos"
    if argumentos.paso == "discrepancias":
        cantidad = planillas.discrepancias(
            c.ruta("planillas/autor_a.csv"),
            c.ruta("planillas/autor_b.csv"),
            c.ruta("planillas/discrepancias.csv"),
        )
        return f"discrepancias:{cantidad}"
    # metricas
    calificaciones = None
    acuerdo = None
    if argumentos.con_calificaciones:
        consenso = c.ruta("planillas/consenso.csv")
        calificaciones, acuerdo = planillas.consolidar(
            c.ruta("planillas/autor_a.csv"),
            c.ruta("planillas/autor_b.csv"),
            consenso if consenso.exists() else None,
        )
    resultado = cmp.calcular(
        c,
        oraculos,
        Registro(c.ruta("medicion")).leer(),
        Registro(c.ruta("recuperacion")).leer(),
        calificaciones,
        _bloques_docx(_fuente(c, con_servicios=False), oraculos),
    )
    resultado["acuerdo_autores"] = acuerdo
    c.ruta("metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), "utf-8")
    c.ruta("informe.md").write_text(informe.generar(resultado), "utf-8")
    return f"metricas_listas:{c.ruta('informe.md')}"


def analizador() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    pasos = raiz.add_subparsers(dest="paso", required=True)
    nuevo = pasos.add_parser("iniciar")
    nuevo.add_argument("--campana", required=True)
    nuevo.add_argument("--modo", choices=[m.value for m in Modo], required=True)
    nuevo.add_argument("--generativos", nargs="+", required=True, metavar="ALIAS=PERFIL")
    nuevo.add_argument("--embeddings", nargs="+", required=True, metavar="ALIAS=MODELO")
    nuevo.add_argument("--repeticiones", type=int, default=3)
    nuevo.add_argument("--region", default="us-east-1")
    nuevo.add_argument("--bucket")
    for paso in (
        "ocr",
        "medir",
        "indexar",
        "recuperar",
        "responder",
        "planillas",
        "discrepancias",
    ):
        pasos.add_parser(paso).add_argument("--campana", required=True)
    final = pasos.add_parser("metricas")
    final.add_argument("--campana", required=True)
    final.add_argument(
        "--con-calificaciones",
        action="store_true",
        help="Incluir IA-M06 desde las planillas completas de ambos autores y el consenso",
    )
    return raiz


def main(argumentos: list[str] | None = None) -> int:
    try:
        print(ejecutar(analizador().parse_args(argumentos)))
    except (cmp.ErrorCampana, ValueError, RuntimeError) as error:
        print(f"Campaña detenida: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
