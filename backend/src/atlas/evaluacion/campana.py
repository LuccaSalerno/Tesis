"""Campañas de medición: manifiesto, pasos y cálculo de métricas (P13, P16, RC-P07.7).

Una campaña vive en `evaluacion/campanas/<id>/`. El manifiesto fija antes de medir el commit,
los modelos y perfiles, la configuración y las huellas del corpus, los oráculos, las
instrucciones y la segmentación. Cada paso verifica que nada de eso cambió: una campaña no
se mezcla con otra configuración, y un cambio exige una campaña nueva identificable.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from atlas.configuracion import Configuracion
from atlas.evaluacion import metricas
from atlas.evaluacion.oraculos import Modo, Oraculos, cargar, consultas_de, seleccionar
from atlas.integraciones.textract import FUNCIONES as FUNCIONES_TEXTRACT
from atlas.procesamiento import esquemas
from atlas.procesamiento.segmentacion import CARACTERES_MAXIMOS, VERSION_SEGMENTACION

RAIZ_REPOSITORIO: Final = Path(__file__).resolve().parents[4]
ARCHIVOS: Final = {
    "ocr": "ocr.jsonl",
    "medicion": "clasificacion_extraccion.jsonl",
    "recuperacion": "recuperacion.jsonl",
    "respuestas": "respuestas.jsonl",
}


class ErrorCampana(Exception):
    """La campaña no puede continuar sin cambiar su configuración."""


def _por_defecto(campo: str) -> Any:
    return Configuracion.model_fields[campo].default


@dataclass(frozen=True)
class Campana:
    directorio: Path
    manifiesto: dict[str, Any]

    @property
    def modo(self) -> Modo:
        return Modo(self.manifiesto["modo"])

    def ruta(self, nombre: str) -> Path:
        return self.directorio / ARCHIVOS.get(nombre, nombre)


def huellas_configuracion() -> dict[str, str]:
    versiones = (
        esquemas.VERSION_INSTRUCCIONES_CLASIFICACION,
        esquemas.VERSION_INSTRUCCIONES_EXTRACCION,
        esquemas.VERSION_INSTRUCCIONES_CONSULTA,
    )
    return {v: esquemas.huella(esquemas.instrucciones(v)) for v in versiones} | {
        "segmentacion": f"{VERSION_SEGMENTACION}:{CARACTERES_MAXIMOS}",
        "textract": "-".join(FUNCIONES_TEXTRACT),
        "esquemas": esquemas.huella(
            json.dumps(
                {t.value: esquemas.version_esquema_extraccion(t) for t in metricas.TIPOS},
                sort_keys=True,
            )
        ),
    }


def _commit(raiz: Path) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(  # noqa: S603
            ["git", "-C", str(raiz), *args],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "cambios_sin_commit": bool(git("status", "--porcelain")),
    }


def iniciar(
    directorio: Path,
    *,
    identificador: str,
    modo: Modo,
    generativos: dict[str, str],
    embeddings: dict[str, str],
    repeticiones: int,
    region: str,
    bucket: str | None,
    raiz: Path | None = None,
) -> Campana:
    raiz = raiz or RAIZ_REPOSITORIO
    destino = directorio / identificador
    if destino.exists():
        raise ErrorCampana("campana_existente")
    oraculos = cargar(raiz)
    documentos = seleccionar(oraculos, modo)  # compuerta P4
    consultas = consultas_de(oraculos, modo)
    origen = _commit(raiz)
    if modo is Modo.OFICIAL and origen["cambios_sin_commit"]:
        raise ErrorCampana("cambios_sin_commit")
    manifiesto = {
        "campana": identificador,
        "modo": modo.value,
        "reportable": modo is Modo.OFICIAL,
        "creada_en": datetime.now(UTC).isoformat(),
        **origen,
        "region": region,
        "bucket": bucket,
        "generativos": generativos,
        "embeddings": embeddings,
        "embeddings_principal": next(iter(embeddings)),
        "repeticiones": repeticiones,
        "k": 5,
        "limites": {
            "max_tokens_clasificacion": _por_defecto("procesamiento_max_tokens_clasificacion"),
            "max_tokens_extraccion": _por_defecto("procesamiento_max_tokens_extraccion"),
            "caracteres_maximos": _por_defecto("procesamiento_caracteres_maximos"),
            "max_tokens_consulta": _por_defecto("consulta_max_tokens"),
            "temperatura": 0.0,
        },
        "documentos": {d.doc_id: d.sha256 for d in documentos},
        "consultas": [c.pregunta_id for c in consultas],
        "oraculos": oraculos.hashes,
        "oraculos_congelados": oraculos.congelado,
        "configuracion": huellas_configuracion(),
    }
    destino.mkdir(parents=True)
    (destino / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), "utf-8"
    )
    return Campana(destino, manifiesto)


def abrir(
    directorio: Path, identificador: str, raiz: Path | None = None
) -> tuple[Campana, Oraculos]:
    """Carga la campaña y verifica que corpus, oráculos y configuración no cambiaron."""
    raiz = raiz or RAIZ_REPOSITORIO
    destino = directorio / identificador
    manifiesto = json.loads((destino / "manifiesto.json").read_text("utf-8"))
    oraculos = cargar(raiz)
    campana = Campana(destino, manifiesto)
    if oraculos.hashes != manifiesto["oraculos"]:
        raise ErrorCampana("oraculos_cambiaron")
    if huellas_configuracion() != manifiesto["configuracion"]:
        raise ErrorCampana("configuracion_cambio")
    actuales = {d.doc_id: d.sha256 for d in seleccionar(oraculos, campana.modo)}
    if actuales != manifiesto["documentos"]:
        raise ErrorCampana("documentos_cambiaron")
    return campana, oraculos


# --- Métricas de la campaña ----------------------------------------------------------------


def _promedios(por_repeticion: list[dict[str, Any]]) -> dict[str, Any]:
    claves = sorted({k for r in por_repeticion for k in r["indicadores"]})
    return {
        clave: metricas.resumen_repeticiones(r["indicadores"].get(clave) for r in por_repeticion)
        for clave in claves
    }


def _indicadores(cla: dict[str, Any], ext: dict[str, Any]) -> dict[str, float | None]:
    f1_tipos = [t["f1"] for t in ext["por_tipo"].values()]
    exactitudes = [c["exactitud"] for c in ext["exactitud_critica"].values() if c["esperados"]]
    return {
        "clasificacion_f1_macro": cla["f1_macro"],
        "clasificacion_recall_minimo": cla["recall_minimo"],
        "extraccion_f1_macro": ext["f1_macro"],
        "extraccion_f1_minimo_tipo": min((f or 0.0) for f in f1_tipos),
        "exactitud_critica_minima": min(exactitudes) if exactitudes else None,
        "inventados": ext["inventados"]["proporcion"],
        "procedencia_pdf": ext["procedencia_pdf"]["proporcion"],
    }


def calcular(
    campana: Campana,
    oraculos: Oraculos,
    filas_medicion: list[dict[str, Any]],
    filas_recuperacion: list[dict[str, Any]],
    calificaciones: dict[tuple[str, int], list[dict[str, Any]]] | None,
    bloques_docx: metricas.BloquesDocx,
) -> dict[str, Any]:
    resultado: dict[str, Any] = {
        "campana": campana.manifiesto["campana"],
        "modo": campana.manifiesto["modo"],
        "reportable": campana.manifiesto["reportable"],
        "umbrales": metricas.UMBRALES,
        "generativos": {},
        "embeddings": {},
    }
    for alias in campana.manifiesto["generativos"]:
        por_repeticion = []
        for repeticion in range(1, campana.manifiesto["repeticiones"] + 1):
            filas = [
                f for f in filas_medicion if f["modelo"] == alias and f["repeticion"] == repeticion
            ]
            if not filas:
                continue
            cla = metricas.clasificacion(filas, oraculos.documentos)
            ext = metricas.extraccion(filas, oraculos, bloques_docx)
            indicadores = _indicadores(cla, ext)
            calificadas = (calificaciones or {}).get((alias, repeticion))
            rag = metricas.respuestas(calificadas, oraculos.consultas) if calificadas else None
            if rag:
                indicadores |= {
                    "rag_correctas": rag["correctas"],
                    "rag_respaldo": rag["respaldo"],
                    "rag_abstenciones": rag["abstenciones_correctas"],
                }
            por_repeticion.append(
                {
                    "repeticion": repeticion,
                    "indicadores": indicadores,
                    "clasificacion": cla,
                    "extraccion": ext,
                    "respuestas": rag,
                    "adversariales": metricas.adversariales(filas, oraculos),
                    "errores_tecnicos": sum(
                        bool(f["error_clasificacion"] or f["error_extraccion"]) for f in filas
                    ),
                }
            )
        promedios = _promedios(por_repeticion)
        resultado["generativos"][alias] = {
            "repeticiones": por_repeticion,
            "promedios": promedios,
            # La latencia IA-M08 se mide contra la API desplegada (fase 2, P17).
            "criterios": metricas.criterios_generativos(
                {k: v["promedio"] for k, v in promedios.items()}, None
            ),
        }
    for alias in campana.manifiesto["embeddings"]:
        filas = [f for f in filas_recuperacion if f["embeddings"] == alias]
        if filas:
            resultado["embeddings"][alias] = metricas.recuperacion(filas)
    resultado["sustitucion"] = _sustitucion(campana, resultado)
    return resultado


def _sustitucion(campana: Campana, resultado: dict[str, Any]) -> dict[str, Any]:
    """Reglas de §6.3.1 sobre los promedios; la decisión real la registra el equipo (P13)."""
    salida: dict[str, Any] = {}
    generativos = list(campana.manifiesto["generativos"])
    if len(generativos) == 2 and all(
        resultado["generativos"][g]["repeticiones"] for g in generativos
    ):
        base, alternativa = (resultado["generativos"][g] for g in generativos)
        salida["generativo"] = metricas.sustituir_generativo(
            base["criterios"],
            alternativa["criterios"],
            base["promedios"]["extraccion_f1_macro"]["promedio"],
            alternativa["promedios"]["extraccion_f1_macro"]["promedio"],
        )
    embeddings = list(campana.manifiesto["embeddings"])
    if len(embeddings) == 2 and all(e in resultado["embeddings"] for e in embeddings):
        base_e, alternativa_e = (resultado["embeddings"][e]["recall_at_5"] for e in embeddings)
        if base_e is not None and alternativa_e is not None:
            salida["embeddings"] = metricas.sustituir_embeddings(base_e, alternativa_e)
    return salida
