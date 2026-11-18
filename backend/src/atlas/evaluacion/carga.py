"""Comportamiento con concurrencia (§6.3.4, OP-01 a OP-03).

Interactiva: en cada nivel (1, 5 y 10) se envían 30 consultas y 30 lecturas del trámite con
ese número de solicitudes simultáneas. Asíncrona: en cada nivel se suben k documentos
distintos a la vez y se mide cada trabajo desde su aceptación hasta el resultado técnico,
con los tiempos del servidor. Usa la partición de ajuste: no expone resultados de medición.
"""

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from itertools import cycle, islice
from typing import Any, Final

from atlas.evaluacion import latencia
from atlas.evaluacion.cargador import esperar, subir
from atlas.evaluacion.http import Envio, Medida, medir
from atlas.evaluacion.oraculos import Documento
from atlas.evaluacion.registro import Registro
from atlas.herramientas.cliente_api import ClienteApi

NIVELES: Final = (1, 5, 10)
SOLICITUDES_POR_NIVEL: Final = 30


def interactiva(
    envio: Envio,
    url_api: str,
    token: str,
    tramite_id: int,
    preguntas: Sequence[str],
    registro: Registro,
    niveles: Sequence[int] = NIVELES,
) -> None:
    base = url_api.rstrip("/")
    operaciones: dict[str, Callable[[str], Medida]] = {
        "consulta": lambda texto: medir(
            envio, "POST", f"{base}/tramites/{tramite_id}/consultas", token, {"pregunta": texto}
        ),
        "lectura": lambda _: medir(envio, "GET", f"{base}/tramites/{tramite_id}", token),
    }
    for nivel in niveles:
        for operacion, llamada in operaciones.items():
            textos = list(islice(cycle(preguntas), SOLICITUDES_POR_NIVEL))
            with ThreadPoolExecutor(max_workers=nivel) as hilos:
                medidas = list(hilos.map(llamada, textos))
            for medida in medidas:
                registro.escribir(
                    {
                        "tipo": "interactiva",
                        "nivel": nivel,
                        "operacion": operacion,
                        "estado_http": medida.estado,
                        "completada": medida.estado in (200, 201),
                        "duracion_ms": round(medida.duracion_ms, 1),
                        "arranque": medida.server_timing.get("arranque"),
                        "error": medida.error,
                    }
                )


def _segundos(trabajo: dict[str, Any]) -> float | None:
    if trabajo.get("estado") != "completado":
        return None
    inicio = datetime.fromisoformat(trabajo["creado_en"])
    fin = datetime.fromisoformat(trabajo["actualizado_en"])
    return (fin - inicio).total_seconds()


def asincronica(
    api: ClienteApi,
    documentos: Sequence[Documento],
    registro: Registro,
    niveles: Sequence[int] = NIVELES,
    *,
    esperar_s: Callable[[float], None] | None = None,
) -> None:
    for nivel in niveles:
        tramite = api.post("/tramites", "responsable", {"titulo": f"Carga E90 nivel {nivel}"})
        elegidos = list(islice(cycle(documentos), nivel))
        with ThreadPoolExecutor(max_workers=nivel) as hilos:
            archivos = list(hilos.map(partial(subir, api, tramite["id"]), elegidos))
        trabajos = esperar(api, tramite["id"], [a["id"] for a in archivos], esperar_s=esperar_s)
        for documento, archivo in zip(elegidos, archivos, strict=True):
            trabajo = trabajos[archivo["id"]]
            registro.escribir(
                {
                    "tipo": "asincronica",
                    "nivel": nivel,
                    "doc_id": documento.doc_id,
                    "formato": documento.formato,
                    "estado": trabajo.get("estado"),
                    "duracion_s": _segundos(trabajo),
                }
            )


def metricas(filas: Sequence[dict[str, Any]]) -> dict[str, Any]:
    salida: dict[str, Any] = {"interactiva": {}, "asincronica": {}}
    for nivel in sorted({f["nivel"] for f in filas}):
        for operacion in ("consulta", "lectura"):
            propias = [
                f
                for f in filas
                if f["tipo"] == "interactiva"
                and f["nivel"] == nivel
                and f["operacion"] == operacion
            ]
            if propias:
                completadas = [f["duracion_ms"] for f in propias if f["completada"]]
                salida["interactiva"][f"{operacion}_{nivel}"] = {
                    **latencia.resumen(completadas),
                    "completadas": len(completadas),
                    "errores": len(propias) - len(completadas),
                }
        trabajos = [f for f in filas if f["tipo"] == "asincronica" and f["nivel"] == nivel]
        if trabajos:
            duraciones = [f["duracion_s"] * 1000 for f in trabajos if f["duracion_s"] is not None]
            salida["asincronica"][str(nivel)] = {
                **latencia.resumen(duraciones),
                "completados": len(duraciones),
                "fallidos": len(trabajos) - len(duraciones),
            }
    return salida
