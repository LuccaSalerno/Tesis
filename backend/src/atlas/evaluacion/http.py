"""Solicitud HTTP cronometrada a la API desplegada.

Mide el tiempo completo desde que el cliente envía la solicitud hasta que recibe la respuesta
entera, y conserva el estado y el encabezado `Server-Timing`. El cuerpo se devuelve a quien
llama, nunca se escribe en registros. Solo HTTPS, salvo un servidor local.
"""

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

TIEMPO_MAXIMO_S = 60.0


@dataclass(frozen=True)
class Medida:
    estado: int
    duracion_ms: float
    server_timing: dict[str, Any]
    cuerpo: Any
    error: str | None = None


def leer_server_timing(valor: str | None) -> dict[str, Any]:
    """`embeddings;dur=12, total;dur=40, arranque;desc="frio"` → {nombre: ms o texto}."""
    salida: dict[str, Any] = {}
    for parte in (valor or "").split(","):
        nombre, *atributos = [a.strip() for a in parte.split(";")]
        if not nombre:
            continue
        for atributo in atributos:
            clave, _, dato = atributo.partition("=")
            if clave == "dur":
                salida[nombre] = float(dato)
            elif clave == "desc":
                salida[nombre] = dato.strip('"')
    return salida


# (método, URL, encabezados, cuerpo) -> (estado, encabezados, cuerpo)
Envio = Callable[[str, str, dict[str, str], bytes | None], tuple[int, dict[str, str], bytes]]


def envio_urllib(
    metodo: str, url: str, encabezados: dict[str, str], cuerpo: bytes | None
) -> tuple[int, dict[str, str], bytes]:
    if not url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        raise ValueError("Solo HTTPS, salvo un servidor local")
    solicitud = urllib.request.Request(url, data=cuerpo, method=metodo, headers=encabezados)  # noqa: S310
    try:
        with urllib.request.urlopen(solicitud, timeout=TIEMPO_MAXIMO_S) as respuesta:  # noqa: S310
            return respuesta.status, dict(respuesta.headers), respuesta.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def medir(
    envio: Envio,
    metodo: str,
    url: str,
    token: str | None = None,
    cuerpo: Any = None,
    reloj: Callable[[], float] = time.perf_counter,
) -> Medida:
    encabezados = {"Accept": "application/json"}
    datos = None
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode()
        encabezados["Content-Type"] = "application/json"
    if token is not None:
        encabezados["Authorization"] = f"Bearer {token}"
    inicio = reloj()
    try:
        estado, cabeceras, respuesta = envio(metodo, url, encabezados, datos)
    except (OSError, TimeoutError) as error:
        # Sin respuesta: se registra como error, no como observación de latencia.
        return Medida(0, (reloj() - inicio) * 1000, {}, None, type(error).__name__)
    duracion = (reloj() - inicio) * 1000
    tiempos = {k.lower(): v for k, v in cabeceras.items()}.get("server-timing")
    try:
        datos_respuesta = json.loads(respuesta) if respuesta else None
    except ValueError:
        datos_respuesta = None
    return Medida(estado, duracion, leer_server_timing(tiempos), datos_respuesta)
