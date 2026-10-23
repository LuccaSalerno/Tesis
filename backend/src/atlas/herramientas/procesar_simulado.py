"""Procesamiento **simulado** para desarrollo y pruebas E2E locales (DO-2026-10-22-WEB F9).

Uso (solo en desarrollo o pruebas, con S3 y Step Functions de moto):

    python -m atlas.herramientas.procesar_simulado            # trabajos pendientes
    python -m atlas.herramientas.procesar_simulado --archivo 12

Sustituye Textract y Bedrock **solo para los archivos del corpus PD-07**, reconocidos por su
huella: el texto sale del PDF (pypdf) y la clasificación y los campos, del oráculo
preliminar. Las sugerencias quedan registradas con el modelo `simulacion-local-…`, que la
interfaz rotula como simulación. Un archivo fuera del corpus se registra como fallo técnico.

**No es evidencia de la IA ni se usa en la defensa.** Se niega a funcionar en demo o sin un
endpoint local de AWS (DT-AWS-01).
"""

import argparse
import hashlib
import io
import json
import math
import re
import sys
from dataclasses import dataclass
from typing import Any, Final

from pypdf import PdfReader
from sqlalchemy import select

from atlas.configuracion import Configuracion, ErrorConfiguracion, obtener_configuracion
from atlas.dominio.enumeraciones import EstadoTrabajo, TipoDocumental
from atlas.herramientas.sembrar_demo import ORACULO, RAZON_SOCIAL_PROVEEDOR
from atlas.integraciones.aws import AlmacenS3, crear_cliente
from atlas.persistencia.modelos import Archivo, TrabajoProcesamiento
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.procesamiento import esquemas, etapas
from atlas.procesamiento.modelo import RespuestaHerramienta

PREFIJO_MODELO: Final = "simulacion-local"
MODELO_SIMULADO: Final = f"{PREFIJO_MODELO}-oraculo-PD07"
EMBEDDINGS_SIMULADOS: Final = f"{PREFIJO_MODELO}-embeddings"


def verificar_entorno(configuracion: Configuracion) -> None:
    if configuracion.entorno == "demo" or configuracion.aws_endpoint_url is None:
        raise ErrorConfiguracion("La simulación solo corre en desarrollo o pruebas, con moto")


def escenario_completo(oraculo: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Valores esperados de los cinco documentos de PD-07 con los nombres de RC-P04."""
    escenario: dict[str, dict[str, str]] = {}
    for codigo, doc in oraculo["documentos"].items():
        if doc["clase"] == "contrato":
            escenario[codigo] = {
                "tipo_documental": "contrato",
                **{c.nombre: doc[c.nombre] for c in esquemas.CAMPOS[TipoDocumental.CONTRATO]},
            }
        elif doc["clase"] == "orden_compra":
            escenario[codigo] = {
                "tipo_documental": "orden_compra",
                "numero": doc["numero"],
                "fecha": doc["fecha_emision"],
                "proveedor": RAZON_SOCIAL_PROVEEDOR,
                "cuit_proveedor": doc["cuit_proveedor"],
                "importe_total": doc["total"],
                "moneda": doc["moneda"],
            }
        else:
            escenario[codigo] = {
                "tipo_documental": "factura",
                "numero": doc["numero"],
                "fecha_emision": doc["fecha_emision"],
                "emisor": RAZON_SOCIAL_PROVEEDOR,
                "cuit_emisor": doc["cuit_emisor"],
                "importe_total": doc["total"],
                "moneda": doc["moneda"],
            }
    return escenario


def codigo_por_huella(oraculo: dict[str, Any], huella: str) -> str | None:
    for archivo, datos in oraculo["archivos_pdf"].items():
        if datos["sha256"] == huella:
            return str(archivo.split("_", 1)[0])
    return None


def lineas_por_pagina(pdf: bytes) -> list[list[str]]:
    return [
        [linea.strip() for linea in (pagina.extract_text() or "").splitlines() if linea.strip()]
        for pagina in PdfReader(io.BytesIO(pdf)).pages
    ]


def bloques_textract(paginas: list[list[str]]) -> list[dict[str, Any]]:
    """Bloques PAGE, LINE y WORD con la forma de `GetDocumentAnalysis`."""
    bloques: list[dict[str, Any]] = []
    for numero, lineas in enumerate(paginas, start=1):
        bloques.append({"BlockType": "PAGE", "Id": f"p{numero}", "Page": numero})
        for posicion, texto in enumerate(lineas):
            arriba = 0.02 + posicion * 0.02
            caja = {"BoundingBox": {"Top": arriba, "Left": 0.1, "Width": 0.8, "Height": 0.015}}
            palabras = []
            for indice, palabra in enumerate(texto.split()):
                identificador = f"w{numero}-{posicion}-{indice}"
                palabras.append(identificador)
                bloques.append(
                    {
                        "BlockType": "WORD",
                        "Id": identificador,
                        "Page": numero,
                        "Text": palabra,
                        "Geometry": caja,
                    }
                )
            bloques.append(
                {
                    "BlockType": "LINE",
                    "Id": f"l{numero}-{posicion}",
                    "Page": numero,
                    "Text": texto,
                    "Geometry": caja,
                    "Relationships": [{"Type": "CHILD", "Ids": palabras}],
                }
            )
    return [{"Blocks": bloques}]


def _formas(valor: str) -> list[str]:
    """Cómo puede aparecer impreso un valor canónico (fecha, importe o texto)."""
    formas = [valor]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        anio, mes, dia = valor.split("-")
        formas.append(f"{dia}/{mes}/{anio}")
    if re.fullmatch(r"\d+\.\d{2}", valor):
        entero, decimales = valor.split(".")
        formas.append(f"{int(entero):,}".replace(",", ".") + f",{decimales}")
    return formas


def ubicar(paginas: list[list[str]], valor: str) -> tuple[int | None, str | None]:
    for numero, lineas in enumerate(paginas, start=1):
        for linea in lineas:
            if any(forma in linea for forma in _formas(valor)):
                return numero, linea
    return None, None


@dataclass
class AnalizadorSimulado:
    paginas: list[list[str]]

    def iniciar(self, clave: str, trabajo_id: int, intento: int) -> str:
        return f"simulado-{trabajo_id}-{intento}"

    def estado(self, job_id: str) -> str:
        return "completado"

    def resultado(self, job_id: str) -> list[dict[str, Any]]:
        return bloques_textract(self.paginas)


@dataclass
class ModeloSimulado:
    valores: dict[str, str]
    paginas: list[list[str]]
    identificador: str = MODELO_SIMULADO

    def invocar_herramienta(
        self, *, instrucciones: str, contenido: str, herramienta: dict[str, Any], max_tokens: int
    ) -> RespuestaHerramienta:
        if herramienta["name"] == esquemas.HERRAMIENTA_CLASIFICACION:
            entrada: dict[str, Any] = {"tipo": self.valores["tipo_documental"]}
        else:
            entrada = {}
            for campo, valor in self.valores.items():
                if campo == "tipo_documental":
                    continue
                pagina, cita = ubicar(self.paginas, valor)
                entrada[campo] = {"valor": valor, "pagina": pagina, "cita": cita}
        return RespuestaHerramienta(
            entrada=entrada, modelo=self.identificador, tokens_entrada=0, tokens_salida=0
        )


@dataclass
class EmbeddingsSimulados:
    """Bolsa de palabras proyectada en 1024 dimensiones: no simula la calidad de Cohere."""

    identificador: str = EMBEDDINGS_SIMULADOS

    def embeber(self, textos: list[str], tipo: Any) -> list[list[float]]:
        vectores = []
        for texto in textos:
            vector = [0.0] * 1024
            for palabra in re.findall(r"\w{3,}", texto.casefold()):
                vector[int(hashlib.sha256(palabra.encode()).hexdigest(), 16) % 1024] += 1.0
            norma = math.sqrt(sum(x * x for x in vector)) or 1.0
            vectores.append([x / norma for x in vector])
        return vectores


LIMITES: Final = etapas.LimitesProcesamiento(
    max_tokens_clasificacion=256, max_tokens_extraccion=2048, caracteres_maximos=400_000
)


def procesar(configuracion: Configuracion, archivo_id: int | None = None) -> dict[str, list[int]]:
    verificar_entorno(configuracion)
    oraculo = json.loads(ORACULO.read_text(encoding="utf-8"))
    escenario = escenario_completo(oraculo)
    almacen = AlmacenS3(
        crear_cliente(configuracion, "s3"), configuracion.s3_bucket_documentos or ""
    )
    motor = crear_motor(configuracion)
    fabrica = crear_fabrica_sesiones(motor)
    resultado: dict[str, list[int]] = {"procesados": [], "fallidos": []}
    try:
        with fabrica() as sesion:
            consulta = select(TrabajoProcesamiento, Archivo).join(
                Archivo, Archivo.id == TrabajoProcesamiento.archivo_id
            )
            consulta = (
                consulta.where(Archivo.id == archivo_id)
                if archivo_id is not None
                else consulta.where(
                    TrabajoProcesamiento.estado.in_(
                        [EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_EJECUCION]
                    )
                )
            )
            pendientes = [(t.id, t.intento, a.id, a.huella) for t, a in sesion.execute(consulta)]
        for trabajo_id, intento, archivo, huella in pendientes:
            codigo = codigo_por_huella(oraculo, huella)
            with fabrica() as sesion, sesion.begin():
                preparado = etapas.preparar(sesion, trabajo_id, intento)
            if codigo is None or preparado["formato"] != "pdf":
                with fabrica() as sesion, sesion.begin():
                    etapas.registrar_fallo(
                        sesion,
                        trabajo_id=trabajo_id,
                        intento=intento,
                        codigo="simulacion_no_disponible",
                    )
                resultado["fallidos"].append(archivo)
                continue
            paginas = lineas_por_pagina(almacen.leer(preparado["clave_objeto"]))
            analizador = AnalizadorSimulado(paginas)
            modelo = ModeloSimulado(escenario[codigo], paginas)
            job = etapas.iniciar_textract(
                analizador,  # type: ignore[arg-type]
                clave_objeto=preparado["clave_objeto"],
                trabajo_id=trabajo_id,
                intento=intento,
            )["job_id"]
            contenido = etapas.normalizar_textract(
                analizador,  # type: ignore[arg-type]
                almacen,
                job_id=job,
                trabajo_id=trabajo_id,
                intento=intento,
            )["contenido"]
            comunes = {"contenido": contenido, "trabajo_id": trabajo_id, "intento": intento}
            clasificacion = etapas.clasificar(almacen, modelo, LIMITES, **comunes)["clasificacion"]
            extraccion = etapas.extraer(
                almacen, modelo, LIMITES, clasificacion=clasificacion, **comunes
            )["extraccion"]
            fragmentos = etapas.indexar(almacen, EmbeddingsSimulados(), **comunes)["fragmentos"]
            with fabrica() as sesion, sesion.begin():
                etapas.persistir(
                    sesion,
                    almacen,
                    clasificacion=clasificacion,
                    extraccion=extraccion,
                    fragmentos=fragmentos,
                    trabajo_id=trabajo_id,
                    intento=intento,
                )
            resultado["procesados"].append(archivo)
    finally:
        motor.dispose()
    return resultado


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--archivo", type=int)
    opciones = analizador.parse_args(argumentos)
    try:
        resultado = procesar(obtener_configuracion(), opciones.archivo)
    except ErrorConfiguracion as error:
        print(f"No se simula: {error}", file=sys.stderr)
        return 1
    print(
        f"SIMULACIÓN LOCAL: {len(resultado['procesados'])} archivos procesados con el oráculo,"
        f" {len(resultado['fallidos'])} registrados como no simulables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
