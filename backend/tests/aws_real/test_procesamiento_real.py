"""Nivel B: Textract y Claude Haiku 4.5 reales sobre el contrato sintético C-v1.

Solo las ejecuta un operador del equipo en una sesión AWS autorizada y con costo
aprobado (DO-2026-10-21, DO-2026-10-22-PROC). En la CI se omiten siempre: requieren
`ATLAS_PRUEBAS_AWS_REAL=1` y credenciales de la sesión, que nunca están en GitHub.

Comparan contra el oráculo preliminar PD-07 y fallan ante cualquier diferencia: no se
ajustan umbrales ni oráculos para que pasen (AGENTS.md §2.9). La evidencia saneada
(aciertos, páginas, tokens, duración; sin contenido) se escribe en
`ATLAS_EVIDENCIA_AWS_REAL` si está definida.
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from atlas.configuracion import obtener_configuracion
from atlas.dominio.enumeraciones import TipoDocumental
from atlas.integraciones.aws import AlmacenS3, crear_cliente
from atlas.integraciones.bedrock import ModeloBedrockConverse
from atlas.integraciones.textract import AnalizadorTextract
from atlas.procesamiento.analisis import clasificar, extraer
from atlas.procesamiento.contenido import desde_textract
from tests import archivos

pytestmark = [
    pytest.mark.aws_real,
    pytest.mark.skipif(
        os.environ.get("ATLAS_PRUEBAS_AWS_REAL") != "1",
        reason="Nivel B: requiere una sesión AWS autorizada (ATLAS_PRUEBAS_AWS_REAL=1); "
        "no se ejecuta en la CI",
    ),
]

ORACULO = json.loads(
    (archivos.CORPUS.parent / "oraculos" / "oraculo_PD07_v2_preliminar.json").read_text("utf-8")
)["documentos"]["C-v1"]


def test_aws_real_c_v1_textract_clasificacion_y_extraccion() -> None:
    configuracion = obtener_configuracion()
    assert configuracion.aws_endpoint_url is None, "El nivel B usa servicios reales, no moto"
    almacen = AlmacenS3(
        crear_cliente(configuracion, "s3"), configuracion.s3_bucket_documentos or ""
    )
    analizador = AnalizadorTextract(
        crear_cliente(configuracion, "textract"), configuracion.s3_bucket_documentos or ""
    )
    modelo = ModeloBedrockConverse(
        crear_cliente(configuracion, "bedrock-runtime"), configuracion.bedrock_perfil_generativo
    )
    clave = f"cargas-temporales/pruebas-aws-real/{uuid.uuid4()}"
    almacen.escribir(clave, archivos.CONTRATO_PDF.read_bytes(), "application/pdf")
    inicio = time.monotonic()
    try:
        job_id = analizador.iniciar(clave, trabajo_id=0, intento=int(time.time()))
        while (estado := analizador.estado(job_id)) == "en_curso":
            assert time.monotonic() - inicio < 30 * 60, "Textract superó 30 minutos"
            time.sleep(12)
        assert estado == "completado"
        contenido = desde_textract(analizador.resultado(job_id))
        tipo = clasificar(contenido, modelo, max_tokens=256, caracteres_maximos=400_000)
        campos = extraer(
            contenido, TipoDocumental.CONTRATO, modelo, max_tokens=2048, caracteres_maximos=400_000
        )
    finally:
        almacen.eliminar_definitivamente(clave)

    obtenidos = {c.campo: c for c in campos.campos}
    comparacion: dict[str, Any] = {
        campo: {
            "valor_correcto": campo in obtenidos and obtenidos[campo].valor == ORACULO[campo],
            "pagina_esperada": ORACULO["ubicacion_campos"].get(campo),
            "pagina_obtenida": obtenidos[campo].pagina if campo in obtenidos else None,
            "motivo_sin_fuente": (
                obtenidos[campo].motivo_sin_fuente if campo in obtenidos else "sin_sugerencia"
            ),
        }
        for campo in ORACULO["ubicacion_campos"]
    }
    evidencia = {
        "documento": "C-v1",
        "sha256": "7802ce9a5f065260a0d027ae68dafeab78b2657170725f88fb34a1f2783143d4",
        "tipo_correcto": tipo.tipo is TipoDocumental.CONTRATO,
        "campos": comparacion,
        "modelo": campos.uso.modelo,
        "tokens": {
            "clasificacion": [tipo.uso.tokens_entrada, tipo.uso.tokens_salida],
            "extraccion": [campos.uso.tokens_entrada, campos.uso.tokens_salida],
        },
        "paginas": len(contenido.paginas),
        "duracion_s": round(time.monotonic() - inicio, 1),
    }
    if destino := os.environ.get("ATLAS_EVIDENCIA_AWS_REAL"):
        Path(destino).write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), "utf-8")

    assert evidencia["tipo_correcto"]
    assert all(c["valor_correcto"] for c in comparacion.values()), comparacion
    assert all(c["pagina_obtenida"] == c["pagina_esperada"] for c in comparacion.values()), (
        comparacion
    )


def test_aws_real_c_v1_consulta_asistida_con_cita_y_abstencion() -> None:
    """Punto de demo B con Cohere y Haiku reales, sin base: se indexa C-v1 en memoria y se
    recuperan los 5 fragmentos más cercanos por coseno, como en pgvector (RC-P07.3)."""
    import math

    from atlas.integraciones.bedrock import EmbeddingsCohereBedrock
    from atlas.procesamiento import esquemas
    from atlas.procesamiento.segmentacion import segmentar
    from atlas.servicios.consultas import FragmentoRecuperado, renderizar

    configuracion = obtener_configuracion()
    bucket = configuracion.s3_bucket_documentos or ""
    almacen = AlmacenS3(crear_cliente(configuracion, "s3"), bucket)
    analizador = AnalizadorTextract(crear_cliente(configuracion, "textract"), bucket)
    bedrock = crear_cliente(configuracion, "bedrock-runtime")
    embeddings = EmbeddingsCohereBedrock(bedrock, configuracion.bedrock_modelo_embeddings)
    modelo = ModeloBedrockConverse(bedrock, configuracion.bedrock_perfil_generativo)

    clave = f"cargas-temporales/pruebas-aws-real/{uuid.uuid4()}"
    almacen.escribir(clave, archivos.CONTRATO_PDF.read_bytes(), "application/pdf")
    try:
        job_id = analizador.iniciar(clave, trabajo_id=0, intento=int(time.time()))
        while analizador.estado(job_id) == "en_curso":
            time.sleep(12)
        fragmentos = segmentar(desde_textract(analizador.resultado(job_id)))
    finally:
        almacen.eliminar_definitivamente(clave)
    vectores = embeddings.embeber([f.texto for f in fragmentos], "search_document")

    def responder(pregunta: str) -> dict[str, Any]:
        consulta = embeddings.embeber([pregunta], "search_query")[0]

        def distancia(v: list[float]) -> float:
            producto = sum(a * b for a, b in zip(v, consulta, strict=True))
            return 1 - producto / (
                math.sqrt(sum(a * a for a in v)) * math.sqrt(sum(b * b for b in consulta))
            )

        orden = sorted(range(len(fragmentos)), key=lambda i: distancia(vectores[i]))[:5]
        recuperados = [
            FragmentoRecuperado(
                f"F{p}",
                i,
                fragmentos[i].texto,
                distancia(vectores[i]),
                0,
                "Contrato C-v1",
                0,
                1,
                fragmentos[i].pagina,
                fragmentos[i].seccion,
            )
            for p, i in enumerate(orden, start=1)
        ]
        respuesta = modelo.invocar_herramienta(
            instrucciones=esquemas.instrucciones(esquemas.VERSION_INSTRUCCIONES_CONSULTA),
            contenido=renderizar(pregunta, recuperados),
            herramienta=esquemas.herramienta_consulta(),
            max_tokens=1024,
        )
        por_etiqueta = {f.etiqueta: f for f in recuperados}
        return {
            "suficiente": respuesta.entrada["suficiente"],
            "paginas_citadas": sorted(
                {
                    por_etiqueta[e].pagina
                    for a in respuesta.entrada["afirmaciones"]
                    for e in a["fragmentos"]
                    if e in por_etiqueta
                }
            ),
        }

    vigencia = responder("¿Hasta cuándo está vigente el contrato?")
    sin_evidencia = responder("¿Cuál es el número de cuenta bancaria del proveedor?")
    evidencia = {"vigencia": vigencia, "sin_evidencia": sin_evidencia}
    if destino := os.environ.get("ATLAS_EVIDENCIA_AWS_REAL_RAG"):
        Path(destino).write_text(json.dumps(evidencia, indent=2), "utf-8")
    assert (
        vigencia["suficiente"]
        and ORACULO["ubicacion_campos"]["vigencia_hasta"] in vigencia["paginas_citadas"]
    ), evidencia
    assert sin_evidencia["suficiente"] is False, evidencia
