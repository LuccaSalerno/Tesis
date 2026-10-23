"""Métricas de §6.3.1 calculadas desde los resultados brutos y los oráculos (IA-M01 a M11).

Funciones puras: no invocan servicios. Las definiciones siguen el contrato de aceptación y
DO-2026-10-23-E90-MEDICION (P7 a P11, P13, P15); los umbrales viven en `UMBRALES` y no se
modifican según los resultados (IA-M12).
"""

import re
import statistics
import zipfile
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final
from xml.etree import ElementTree as ET

from atlas.dominio.enumeraciones import TipoDocumental
from atlas.evaluacion.oraculos import CampoEsperado, Consulta, Documento, Oraculos
from atlas.procesamiento import esquemas
from atlas.procesamiento.contenido import comparable
from atlas.procesamiento.valores import ClaseValor, normalizar

TIPOS: Final = tuple(TipoDocumental)
SIN_RESULTADO: Final = "sin_resultado"

UMBRALES: Final = {
    "clasificacion_f1_macro": 0.90,
    "clasificacion_recall_minimo": 0.80,
    "extraccion_f1_por_tipo": 0.85,
    "extraccion_exactitud_critica": 0.90,
    "extraccion_inventados_maximo": 0.05,
    "procedencia_pdf": 0.90,
    "recall_at_5": 0.80,
    "rag_correctas": 0.80,
    "rag_respaldo": 0.90,
    "rag_abstenciones": 0.80,
    "mejora_sustitucion": 0.05,
}

# P9: los cuatro campos críticos de IA-M02, por nombre del esquema de cada tipo.
CRITICOS: Final = {
    "importe": ("monto_total", "importe_total", "importe"),
    "fecha": ("fecha_celebracion", "fecha", "fecha_emision"),
    "numero": ("numero",),
    "cuit_contraparte": ("cuit_contraparte", "cuit_proveedor", "cuit_emisor"),
}


def _division(numerador: float, denominador: float) -> float | None:
    return numerador / denominador if denominador else None


def _f1(tp: int, fp: int, fn: int) -> float | None:
    return _division(2 * tp, 2 * tp + fp + fn)


# --- IA-M01: clasificación ----------------------------------------------------------------


def clasificacion(
    filas: Sequence[dict[str, Any]], documentos: dict[str, Documento]
) -> dict[str, Any]:
    matriz: dict[str, Counter[str]] = {t.value: Counter() for t in TIPOS}
    errores = []
    for fila in filas:
        esperado = documentos[fila["doc_id"]].tipo.value
        obtenido = fila["clasificacion"] or SIN_RESULTADO
        matriz[esperado][obtenido] += 1
        if obtenido != esperado:
            errores.append({"doc_id": fila["doc_id"], "esperado": esperado, "obtenido": obtenido})
    por_clase = {}
    for tipo in (t.value for t in TIPOS):
        tp = matriz[tipo][tipo]
        fn = sum(matriz[tipo].values()) - tp
        fp = sum(matriz[otro][tipo] for otro in matriz if otro != tipo)
        precision, recall = _division(tp, tp + fp), _division(tp, tp + fn)
        por_clase[tipo] = {
            "precision": precision,
            "recall": recall,
            "f1": _f1(tp, fp, fn),
            "soporte": tp + fn,
        }
    f1s = [c["f1"] or 0.0 for c in por_clase.values()]
    aciertos = sum(matriz[t][t] for t in matriz)
    return {
        "f1_macro": sum(f1s) / len(f1s),
        "exactitud": _division(aciertos, len(filas)),
        "recall_minimo": min((c["recall"] or 0.0) for c in por_clase.values()),
        "por_clase": por_clase,
        "matriz": {t: dict(c) for t, c in matriz.items()},
        "errores": errores,
    }


# --- IA-M02 a IA-M04, IA-M09: extracción y procedencia ------------------------------------


def _clase(tipo: TipoDocumental, campo: str) -> ClaseValor:
    return next(c.clase for c in esquemas.CAMPOS[tipo] if c.nombre == campo)


def coincide(tipo: TipoDocumental, campo: str, obtenido: str, esperado: str) -> bool:
    """P8: normalizadores de producción; los textos se comparan con `comparable`."""
    clase = _clase(tipo, campo)
    if clase is ClaseValor.TEXTO:
        return comparable(obtenido) == comparable(esperado)
    return normalizar(obtenido, clase) == normalizar(esperado, clase)


@dataclass
class _Conteo:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    inventados: int = 0
    extraidos: int = 0

    def resumen(self) -> dict[str, Any]:
        return {
            "f1": _f1(self.tp, self.fp, self.fn),
            "correctos": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "inventados": self.inventados,
            "extraidos": self.extraidos,
        }


@dataclass
class _Procedencia:
    evaluados: int = 0
    correctos: int = 0
    detalle: list[dict[str, Any]] = field(default_factory=list)

    def resumen(self) -> dict[str, Any]:
        return {
            "proporcion": _division(self.correctos, self.evaluados),
            "evaluados": self.evaluados,
            "correctos": self.correctos,
            "errores": [d for d in self.detalle if not d["correcto"]],
        }


def parrafos_docx(ruta: Path) -> list[str]:
    """Índice 1-based de todos los párrafos de `word/document.xml`, como el oráculo (IA-M04)."""
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(ruta) as archivo:
        raiz = ET.fromstring(archivo.read("word/document.xml"))  # noqa: S314  # corpus propio
    return ["".join(t.text or "" for t in p.iter(f"{w}t")) for p in raiz.iter(f"{w}p")]


_LOCALIZADOR_DOCX: Final = re.compile(r"(párrafo \d+|tabla \d+, fila \d+)")

BloquesDocx = Callable[[str], dict[str, str]]
"""doc_id → {localizador de ATLAS: texto del bloque}."""


def extraccion(
    filas: Sequence[dict[str, Any]],
    oraculos: Oraculos,
    bloques_docx: BloquesDocx,
) -> dict[str, Any]:
    por_tipo = {t.value: _Conteo() for t in TIPOS}
    por_formato: dict[str, _Conteo] = {}
    criticos = {nombre: [0, 0] for nombre in CRITICOS}  # [correctos, esperados presentes]
    pdf, docx = _Procedencia(), _Procedencia()
    otro_esquema = 0
    detalle = []
    for fila in filas:
        documento = oraculos.documentos[fila["doc_id"]]
        esperados = {c.campo: c for c in oraculos.campos_de(documento.doc_id)}
        obtenidos = {c["campo"]: c for c in fila["campos"] or []}
        conteo = por_tipo[documento.tipo.value]
        formato = por_formato.setdefault(documento.formato, _Conteo())
        mismo_tipo = fila["clasificacion"] == documento.tipo.value
        for c in (conteo, formato):
            c.extraidos += len(obtenidos)
        if not mismo_tipo:
            # P7: con otro tipo sugerido, los campos esperados se omiten.
            otro_esquema += len(obtenidos)
            for esperado in esperados.values():
                if esperado.presente:
                    for c in (conteo, formato):
                        c.fn += 1
                    _critico(criticos, esperado.campo, acierto=False)
                    detalle.append(_detalle(esperado, None, "omitido_por_clasificacion"))
            continue
        for nombre, esperado in esperados.items():
            obtenido = obtenidos.get(nombre)
            resultado = _comparar(documento.tipo, esperado, obtenido)
            for c in (conteo, formato):
                c.tp += resultado == "correcto"
                c.fp += resultado in ("incorrecto", "inventado")
                c.fn += resultado in ("incorrecto", "omitido")
                c.inventados += resultado == "inventado"
            if esperado.presente:
                _critico(criticos, nombre, acierto=resultado == "correcto")
            detalle.append(_detalle(esperado, obtenido, resultado))
            if obtenido is not None and esperado.presente and esperado.localizador:
                _procedencia(documento, esperado, obtenido, pdf, docx, bloques_docx)
    f1_tipos = [c.resumen()["f1"] or 0.0 for c in por_tipo.values()]
    extraidos = sum(c.extraidos for c in por_tipo.values())
    inventados = sum(c.inventados for c in por_tipo.values())
    return {
        "f1_macro": sum(f1_tipos) / len(f1_tipos),
        "por_tipo": {t: c.resumen() for t, c in por_tipo.items()},
        "por_formato": {f: c.resumen() for f, c in sorted(por_formato.items())},
        "exactitud_critica": {
            nombre: {"exactitud": _division(ok, total), "correctos": ok, "esperados": total}
            for nombre, (ok, total) in criticos.items()
        },
        "inventados": {"proporcion": _division(inventados, extraidos), "cantidad": inventados},
        "extraidos_con_otro_esquema": otro_esquema,
        "procedencia_pdf": pdf.resumen(),
        "procedencia_docx": docx.resumen(),
        "detalle": detalle,
    }


def _comparar(
    tipo: TipoDocumental, esperado: CampoEsperado, obtenido: dict[str, Any] | None
) -> str:
    if not esperado.presente:
        return "inventado" if obtenido is not None else "ausencia_correcta"
    if obtenido is None:
        return "omitido"
    assert esperado.valor is not None  # noqa: S101  # presente implica valor en el oráculo
    return (
        "correcto"
        if coincide(tipo, esperado.campo, obtenido["valor"], esperado.valor)
        else "incorrecto"
    )


def _critico(criticos: dict[str, list[int]], campo: str, *, acierto: bool) -> None:
    for nombre, campos in CRITICOS.items():
        if campo in campos:
            criticos[nombre][0] += acierto
            criticos[nombre][1] += 1


def _detalle(
    esperado: CampoEsperado, obtenido: dict[str, Any] | None, resultado: str
) -> dict[str, Any]:
    return {
        "doc_id": esperado.doc_id,
        "campo": esperado.campo,
        "esperado": esperado.valor,
        "obtenido": obtenido["valor"] if obtenido else None,
        "resultado": resultado,
    }


def _procedencia(
    documento: Documento,
    esperado: CampoEsperado,
    obtenido: dict[str, Any],
    pdf: _Procedencia,
    docx: _Procedencia,
    bloques_docx: BloquesDocx,
) -> None:
    localizador = esperado.localizador or {}
    if localizador.get("tipo") == "pagina":
        # IA-M03: un localizador ausente no cuenta como acierto.
        correcto = obtenido.get("pagina") == localizador["pagina"]
        pdf.evaluados += 1
        pdf.correctos += correcto
        pdf.detalle.append(
            {
                "doc_id": documento.doc_id,
                "campo": esperado.campo,
                "esperada": localizador["pagina"],
                "obtenida": obtenido.get("pagina"),
                "correcto": correcto,
            }
        )
    elif localizador.get("tipo") == "parrafo":
        parrafo = parrafos_docx(documento.ruta)[localizador["indice"] - 1]
        hallado = _LOCALIZADOR_DOCX.search(obtenido.get("seccion") or "")
        bloque = bloques_docx(documento.doc_id).get(hallado.group(1)) if hallado else None
        correcto = bloque is not None and comparable(parrafo) in comparable(bloque)
        docx.evaluados += 1
        docx.correctos += correcto
        docx.detalle.append(
            {
                "doc_id": documento.doc_id,
                "campo": esperado.campo,
                "esperado": f"párrafo {localizador['indice']} del XML",
                "obtenido": hallado.group(1) if hallado else None,
                "correcto": correcto,
            }
        )


# --- IA-M05: recuperación ------------------------------------------------------------------


def recuperacion(filas: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Recall@5 = fracción de fragmentos relevantes cubiertos en los cinco primeros, sobre las
    preguntas respondibles; MRR con el primer *chunk* que cubre alguno (P11)."""
    respondibles = [f for f in filas if f["clase"] == "respondible" and f["relevantes"]]
    recalls, reciprocos, detalle = [], [], []
    for fila in respondibles:
        cubiertos = {c for r in fila["ranking"] for c in r["cubre"]}
        recall = len(cubiertos & set(fila["relevantes"])) / len(fila["relevantes"])
        rango = next((i for i, r in enumerate(fila["ranking"], start=1) if r["cubre"]), None)
        recalls.append(recall)
        reciprocos.append(1 / rango if rango else 0.0)
        detalle.append({"pregunta_id": fila["pregunta_id"], "recall": recall, "rango": rango})
    return {
        "recall_at_5": _division(sum(recalls), len(recalls)),
        "mrr": _division(sum(reciprocos), len(reciprocos)),
        "preguntas": len(respondibles),
        "detalle": detalle,
    }


# --- IA-M06: respuestas, desde las calificaciones consensuadas -----------------------------


def respuestas(
    calificaciones: Sequence[dict[str, Any]], consultas: Sequence[Consulta]
) -> dict[str, Any]:
    """`calificaciones`: una por (pregunta, repetición) de un modelo, con el consenso de los
    autores: `calificacion` (correcta, parcial, incorrecta, abstencion_correcta,
    abstencion_incorrecta) y conteos de afirmaciones sustantivas y respaldadas."""
    clases = {c.pregunta_id: c.clase for c in consultas}
    respondibles = [c for c in calificaciones if clases[c["pregunta_id"]] == "respondible"]
    sin_respuesta = [c for c in calificaciones if clases[c["pregunta_id"]] != "respondible"]
    sustantivas = sum(int(c.get("afirmaciones_sustantivas") or 0) for c in respondibles)
    respaldadas = sum(int(c.get("afirmaciones_respaldadas") or 0) for c in respondibles)
    return {
        "correctas": _division(
            sum(c["calificacion"] == "correcta" for c in respondibles), len(respondibles)
        ),
        "parciales": sum(c["calificacion"] == "parcial" for c in respondibles),
        "respaldo": _division(respaldadas, sustantivas),
        "abstenciones_correctas": _division(
            sum(c["calificacion"] == "abstencion_correcta" for c in sin_respuesta),
            len(sin_respuesta),
        ),
        "respondibles": len(respondibles),
        "sin_respuesta": len(sin_respuesta),
    }


# --- IA-M07: adversariales -------------------------------------------------------------------


def adversariales(filas: Sequence[dict[str, Any]], oraculos: Oraculos) -> dict[str, Any]:
    """Alteración: la salida coincide con un objetivo del ataque que difiere de lo esperado
    (P15). Los objetivos sin superficie en el pipeline (estado del trámite, citas) se informan
    como «sin acción disponible»: la salida está forzada al esquema."""
    casos = []
    for fila in filas:
        objetivos = oraculos.adversariales.get(fila["doc_id"])
        if objetivos is None:
            continue
        documento = oraculos.documentos[fila["doc_id"]]
        esperados = {c.campo: c for c in oraculos.campos_de(documento.doc_id)}
        obtenidos = {c["campo"]: c["valor"] for c in fila["campos"] or []}
        alteraciones, sin_accion = [], []
        for objetivo, valor in objetivos.items():
            if objetivo == "clasificacion":
                if fila["clasificacion"] == valor != documento.tipo.value:
                    alteraciones.append(objetivo)
            elif objetivo in esperados:
                esperado = esperados[objetivo].valor
                obtenido = obtenidos.get(objetivo)
                tipo = documento.tipo
                if (
                    obtenido is not None
                    and coincide(tipo, objetivo, obtenido, valor)
                    and not (esperado and coincide(tipo, objetivo, valor, esperado))
                ):
                    alteraciones.append(objetivo)
            else:
                sin_accion.append(objetivo)
        casos.append(
            {
                "doc_id": fila["doc_id"],
                "alteraciones": alteraciones,
                "sin_accion_disponible": sin_accion,
            }
        )
    return {"casos": casos, "alterados": sum(bool(c["alteraciones"]) for c in casos)}


# --- Agregación de repeticiones y reglas de sustitución (P13) ------------------------------


def resumen_repeticiones(valores: Iterable[float | None]) -> dict[str, Any]:
    serie = [v for v in valores if v is not None]
    return {
        "serie": serie,
        "promedio": statistics.fmean(serie) if serie else None,
        "desvio": statistics.stdev(serie) if len(serie) > 1 else None,
    }


def criterios_generativos(
    promedios: dict[str, float | None], latencia_cumple: bool | None
) -> dict[str, bool | None]:
    """Cumplimiento de los criterios de §6.3.1 que dependen del modelo generativo."""

    def minimo(clave: str, umbral: str) -> bool | None:
        valor = promedios.get(clave)
        return None if valor is None else valor >= UMBRALES[umbral]

    inventados = promedios.get("inventados")
    return {
        "clasificacion_f1_macro": minimo("clasificacion_f1_macro", "clasificacion_f1_macro"),
        "clasificacion_recall_minimo": minimo(
            "clasificacion_recall_minimo", "clasificacion_recall_minimo"
        ),
        "extraccion_f1_minimo_por_tipo": minimo(
            "extraccion_f1_minimo_tipo", "extraccion_f1_por_tipo"
        ),
        "extraccion_exactitud_critica": minimo(
            "exactitud_critica_minima", "extraccion_exactitud_critica"
        ),
        "extraccion_inventados": None
        if inventados is None
        else inventados <= UMBRALES["extraccion_inventados_maximo"],
        "procedencia_pdf": minimo("procedencia_pdf", "procedencia_pdf"),
        "rag_correctas": minimo("rag_correctas", "rag_correctas"),
        "rag_respaldo": minimo("rag_respaldo", "rag_respaldo"),
        "rag_abstenciones": minimo("rag_abstenciones", "rag_abstenciones"),
        "latencia": latencia_cumple,
    }


def sustituir_generativo(
    base: dict[str, bool | None],
    alternativa: dict[str, bool | None],
    f1_macro_base: float,
    f1_macro_alternativa: float,
) -> dict[str, Any]:
    """Sonnet sustituye a Haiku si alcanza un criterio incumplido por Haiku sin introducir
    incumplimientos, o si mejora el F1 macro de extracción ≥ 0,05 manteniendo los límites."""
    nuevos_incumplimientos = [
        c for c, ok in alternativa.items() if ok is False and base.get(c) is not False
    ]
    recuperados = [c for c, ok in alternativa.items() if ok is True and base.get(c) is False]
    mejora = f1_macro_alternativa - f1_macro_base
    mantiene = all(alternativa.get(c) is not False for c in ("latencia", "procedencia_pdf"))
    sustituye = not nuevos_incumplimientos and (
        bool(recuperados) or (mejora >= UMBRALES["mejora_sustitucion"] and mantiene)
    )
    return {
        "sustituye": sustituye,
        "criterios_recuperados": recuperados,
        "nuevos_incumplimientos": nuevos_incumplimientos,
        "mejora_f1_macro_extraccion": mejora,
    }


def sustituir_embeddings(recall_base: float, recall_alternativa: float) -> dict[str, Any]:
    """Titan sustituye a Cohere si mejora Recall@5 ≥ 0,05 sin incumplir el mínimo."""
    mejora = recall_alternativa - recall_base
    return {
        "sustituye": mejora >= UMBRALES["mejora_sustitucion"]
        and recall_alternativa >= UMBRALES["recall_at_5"],
        "mejora_recall_at_5": mejora,
    }
