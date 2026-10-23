"""Latencia de la consulta asistida contra la API (IA-M08, DO-2026-10-23-E90-API P3, P6, P7).

Las 30 preguntas se envían de a una, en orden fijo, por bloque de (modelo, repetición): el
cambio de modelo exige reaplicar `demo` entre bloques (P5). Cada respuesta se verifica contra
el perfil declarado. Mediana y p95 por rango más cercano sobre todas las respuestas
completadas, sin excluir arranques en frío ni observaciones lentas (P6).
"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

from atlas.evaluacion.http import Envio, medir
from atlas.evaluacion.registro import Registro

MEDIANA_MAXIMA_MS: Final = 5000.0
P95_MAXIMO_MS: Final = 10000.0
MUESTRAS_RED: Final = 30


@dataclass(frozen=True)
class Pregunta:
    pregunta_id: str
    texto: str
    tramite_id: int


def percentil_cercano(valores: Sequence[float], percentil: float) -> float | None:
    """Rango más cercano: el valor ordenado en la posición ⌈p·n⌉ (siempre una observación)."""
    if not valores:
        return None
    ordenados = sorted(valores)
    return ordenados[max(1, math.ceil(percentil / 100 * len(ordenados))) - 1]


def resumen(valores: Sequence[float]) -> dict[str, Any]:
    return {
        "n": len(valores),
        "mediana_ms": statistics.median(valores) if valores else None,
        "p95_ms": percentil_cercano(valores, 95),
        "maximo_ms": max(valores) if valores else None,
    }


def linea_base_red(
    envio: Envio, url_api: str, registro: Registro, muestras: int = MUESTRAS_RED
) -> None:
    """P7: `GET /salud` no consulta la base ni Bedrock; aproxima el tiempo de red y de API."""
    for numero in range(1, muestras + 1):
        medida = medir(envio, "GET", url_api.rstrip("/") + "/salud")
        registro.escribir(
            {
                "tipo": "red",
                "muestra": numero,
                "estado_http": medida.estado,
                "duracion_ms": round(medida.duracion_ms, 1),
                "error": medida.error,
            }
        )


def medir_bloque(
    envio: Envio,
    url_api: str,
    token: str,
    preguntas: Sequence[Pregunta],
    *,
    modelo: str,
    perfil: str,
    repeticion: int,
    registro: Registro,
) -> int:
    """Un bloque (modelo, repetición). Se niega a repetir un bloque ya registrado."""
    if (modelo, repeticion) in registro.claves(("modelo", "repeticion")):
        raise ValueError(f"bloque_ya_medido:{modelo}:{repeticion}")
    for orden, pregunta in enumerate(preguntas, start=1):
        enviada = datetime.now(UTC).isoformat()
        medida = medir(
            envio,
            "POST",
            f"{url_api.rstrip('/')}/tramites/{pregunta.tramite_id}/consultas",
            token,
            {"pregunta": pregunta.texto},
        )
        cuerpo = medida.cuerpo if isinstance(medida.cuerpo, dict) else {}
        completada = medida.estado == 201
        registro.escribir(
            {
                "tipo": "consulta",
                "modelo": modelo,
                "repeticion": repeticion,
                "orden": orden,
                "pregunta_id": pregunta.pregunta_id,
                "enviada_en": enviada,
                "estado_http": medida.estado,
                "completada": completada,
                "duracion_ms": round(medida.duracion_ms, 1),
                "servidor": medida.server_timing,
                "modelo_generacion": cuerpo.get("modelo_generacion"),
                # Una respuesta de otro perfil indica un despliegue equivocado (P3).
                "perfil_coincide": cuerpo.get("modelo_generacion") in (perfil, None)
                if completada
                else None,
                "suficiente": cuerpo.get("suficiente"),
                "error": medida.error or (None if completada else f"http_{medida.estado}"),
            }
        )
    return len(preguntas)


def metricas(filas: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """IA-M08 por modelo: sobre las consultas completadas; errores, aparte."""
    red = [f["duracion_ms"] for f in filas if f["tipo"] == "red" and f["estado_http"] == 200]
    salida: dict[str, Any] = {"red": resumen(red), "modelos": {}}
    consultas = [f for f in filas if f["tipo"] == "consulta"]
    for modelo in sorted({f["modelo"] for f in consultas}):
        propias = [f for f in consultas if f["modelo"] == modelo]
        completadas = [f for f in propias if f["completada"]]
        tiempos = [f["duracion_ms"] for f in completadas]
        general = resumen(tiempos)
        componentes = {
            nombre: resumen([f["servidor"][nombre] for f in completadas if nombre in f["servidor"]])
            for nombre in ("embeddings", "recuperacion", "generacion", "total")
        }
        salida["modelos"][modelo] = {
            **general,
            "cumple": None
            if general["mediana_ms"] is None
            else general["mediana_ms"] <= MEDIANA_MAXIMA_MS and general["p95_ms"] <= P95_MAXIMO_MS,
            "solicitudes": len(propias),
            "errores": {
                codigo: sum(f["error"] == codigo for f in propias)
                for codigo in sorted({f["error"] for f in propias if f["error"]})
            },
            "arranques_en_frio": sum(f["servidor"].get("arranque") == "frio" for f in completadas),
            "perfil_distinto": sum(f["perfil_coincide"] is False for f in completadas),
            "por_repeticion": {
                str(r): resumen([f["duracion_ms"] for f in completadas if f["repeticion"] == r])
                for r in sorted({f["repeticion"] for f in propias})
            },
            "componentes_servidor": componentes,
            "orden_bloques": list(dict.fromkeys(f["repeticion"] for f in propias)),
        }
    return salida
