"""Carga del corpus en ATLAS desplegado, por la API.

Un trámite por contexto autorizado de las preguntas: carga prefirmada, confirmación, espera
del procesamiento real e incorporación, como lo haría el responsable. No valida campos: la
consulta asistida solo necesita los documentos incorporados. El resultado guarda solo
identificadores y estados técnicos (`carga_corpus.json`).
"""

import time
from collections.abc import Callable, Sequence
from typing import Any, Final

from atlas.evaluacion.oraculos import Consulta, Documento
from atlas.herramientas.cliente_api import ClienteApi

ROL: Final = "responsable"
ESPERA_MAXIMA_S: Final = 1800.0

# Preguntas fijas del ensayo y de la carga; no son del oráculo ni se miden en §6.3.1.
PREGUNTAS_GENERICAS: Final = (
    "¿Cuál es el importe total del documento?",
    "¿Quién es el proveedor o la contraparte y cuál es su CUIT?",
    "¿Qué fecha figura en el documento?",
)


def contextos(consultas: Sequence[Consulta]) -> dict[str, tuple[str, ...]]:
    """Contextos distintos en orden de aparición: `C01` → documentos autorizados."""
    salida: dict[tuple[str, ...], str] = {}
    for consulta in consultas:
        clave = tuple(sorted(consulta.documentos))
        salida.setdefault(clave, f"C{len(salida) + 1:02d}")
    return {nombre: documentos for documentos, nombre in salida.items()}


def subir(api: ClienteApi, tramite_id: int, documento: Documento) -> dict[str, Any]:
    """Carga prefirmada y confirmación; devuelve el archivo con su trabajo aceptado."""
    datos = documento.ruta.read_bytes()
    carga = api.post(
        f"/tramites/{tramite_id}/cargas",
        ROL,
        {
            "nombre": documento.ruta.name,
            "formato": "docx" if documento.es_docx else "pdf",
            "tamano_bytes": len(datos),
        },
    )
    api.transferir(carga["url"], carga["encabezados"], datos)
    archivo: dict[str, Any] = api.post(
        f"/tramites/{tramite_id}/cargas/{carga['id']}/confirmacion", ROL
    )
    return archivo


def esperar(
    api: ClienteApi,
    tramite_id: int,
    archivos: Sequence[int],
    *,
    esperar_s: Callable[[float], None] | None = None,
    intervalo_s: float = 10.0,
    maximo_s: float = ESPERA_MAXIMA_S,
) -> dict[int, dict[str, Any]]:
    """Espera a que cada trabajo termine (completado o fallido) y devuelve su estado."""
    inicio = time.monotonic()
    while True:
        estados = {
            a["id"]: a.get("trabajo") or {}
            for a in api.get(f"/tramites/{tramite_id}/archivos", ROL)
            if a["id"] in archivos
        }
        if all(t.get("estado") in ("completado", "fallido") for t in estados.values()):
            return estados
        if time.monotonic() - inicio > maximo_s:
            raise RuntimeError("procesamiento_sin_terminar")
        (esperar_s or time.sleep)(intervalo_s)


def cargar_contexto(
    api: ClienteApi,
    nombre: str,
    documentos: Sequence[Documento],
    *,
    esperar_s: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    tramite = api.post("/tramites", ROL, {"titulo": f"Evaluación E90 {nombre}"})
    archivos = {d.doc_id: subir(api, tramite["id"], d) for d in documentos}
    trabajos = esperar(
        api, tramite["id"], [a["id"] for a in archivos.values()], esperar_s=esperar_s
    )
    registro: dict[str, Any] = {"tramite_id": tramite["id"], "documentos": {}}
    for documento in documentos:
        archivo = archivos[documento.doc_id]
        trabajo = trabajos[archivo["id"]]
        incorporado = None
        if trabajo.get("estado") == "completado":
            incorporado = api.post(
                f"/tramites/{tramite['id']}/archivos/{archivo['id']}/incorporacion",
                ROL,
                {"nombre": documento.ruta.name},
            )["id"]
        registro["documentos"][documento.doc_id] = {
            "archivo_id": archivo["id"],
            "documento_id": incorporado,
            "trabajo": trabajo,
        }
    return registro


def cargar(
    api: ClienteApi,
    documentos: dict[str, Documento],
    grupos: dict[str, tuple[str, ...]],
    *,
    esperar_s: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """`grupos`: nombre del trámite → documentos. Devuelve el contenido de `carga_corpus.json`."""
    return {
        nombre: cargar_contexto(api, nombre, [documentos[d] for d in ids], esperar_s=esperar_s)
        for nombre, ids in grupos.items()
    }
