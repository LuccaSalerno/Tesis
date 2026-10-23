"""Informe legible de una campaña: criterio, umbral, serie, promedio y cumplimiento (P16).

No interpreta ni redacta conclusiones: presenta lo medido contra los umbrales congelados.
Un ensayo se rotula como no reportable en el encabezado.
"""

from typing import Any

from atlas.evaluacion.metricas import UMBRALES

_FILAS = (
    (
        "IA-M01",
        "F1 macro de clasificación",
        "clasificacion_f1_macro",
        "≥",
        "clasificacion_f1_macro",
    ),
    (
        "IA-M01",
        "Recall mínimo por categoría",
        "clasificacion_recall_minimo",
        "≥",
        "clasificacion_recall_minimo",
    ),
    (
        "IA-M02",
        "F1 de extracción, tipo más bajo",
        "extraccion_f1_minimo_tipo",
        "≥",
        "extraccion_f1_por_tipo",
    ),
    ("IA-M02", "F1 macro de extracción (sustitución)", "extraccion_f1_macro", None, None),
    (
        "IA-M02",
        "Exactitud crítica, campo más bajo",
        "exactitud_critica_minima",
        "≥",
        "extraccion_exactitud_critica",
    ),
    ("IA-M02", "Valores inventados", "inventados", "≤", "extraccion_inventados_maximo"),
    ("IA-M03", "Procedencia PDF con página correcta", "procedencia_pdf", "≥", "procedencia_pdf"),
    ("IA-M06", "Respuestas correctas", "rag_correctas", "≥", "rag_correctas"),
    ("IA-M06", "Afirmaciones respaldadas", "rag_respaldo", "≥", "rag_respaldo"),
    ("IA-M06", "Abstenciones correctas", "rag_abstenciones", "≥", "rag_abstenciones"),
)


def _numero(valor: float | None) -> str:
    return "—" if valor is None else f"{valor:.3f}"


def _cumple(valor: float | None, signo: str | None, umbral: str | None) -> str:
    if valor is None or signo is None or umbral is None:
        return "—"
    ok = valor >= UMBRALES[umbral] if signo == "≥" else valor <= UMBRALES[umbral]
    return "Cumple" if ok else "No cumple"


def generar(resultado: dict[str, Any]) -> str:
    lineas = [f"# Campaña {resultado['campana']} ({resultado['modo']})", ""]
    if not resultado["reportable"]:
        lineas += [
            "> **ENSAYO — NO REPORTABLE.** Partición de ajuste con oráculos sin congelar: "
            "sirve para probar el arnés, no como resultado de §6.3.1.",
            "",
        ]
    for alias, datos in resultado["generativos"].items():
        lineas += [
            f"## Modelo generativo: {alias}",
            "",
            "| Criterio | Indicador | Umbral | Serie | Promedio | Desvío | Resultado |",
            "|---|---|---|---|---|---|---|",
        ]
        for criterio, nombre, clave, signo, umbral in _FILAS:
            resumen = datos["promedios"].get(clave)
            if resumen is None:
                continue
            serie = ", ".join(_numero(v) for v in resumen["serie"])
            limite = f"{signo} {UMBRALES[umbral]:.2f}" if signo and umbral else "—"
            lineas.append(
                f"| {criterio} | {nombre} | {limite} | {serie} | {_numero(resumen['promedio'])} "
                f"| {_numero(resumen['desvio'])} | {_cumple(resumen['promedio'], signo, umbral)} |"
            )
        ultima = datos["repeticiones"][-1] if datos["repeticiones"] else None
        if ultima:
            adversariales = ultima["adversariales"]
            lineas += [
                "",
                f"IA-M07 (última repetición): {adversariales['alterados']} de "
                f"{len(adversariales['casos'])} documentos adversariales con alteraciones.",
                f"Errores técnicos por repetición: "
                f"{', '.join(str(r['errores_tecnicos']) for r in datos['repeticiones'])}.",
                "",
            ]
    if resultado["embeddings"]:
        lineas += [
            "## Recuperación (IA-M05)",
            "",
            "| Embeddings | Recall@5 | MRR | Preguntas | Resultado |",
            "|---|---|---|---|---|",
        ]
        for alias, datos in resultado["embeddings"].items():
            lineas.append(
                f"| {alias} | {_numero(datos['recall_at_5'])} | {_numero(datos['mrr'])} "
                f"| {datos['preguntas']} | {_cumple(datos['recall_at_5'], '≥', 'recall_at_5')} |"
            )
        lineas.append("")
    if resultado["sustitucion"]:
        lineas += ["## Reglas de sustitución (sobre promedios; decide el equipo)", ""]
        for nombre, regla in resultado["sustitucion"].items():
            lineas.append(
                f"- **{nombre}:** {'sustituye' if regla['sustituye'] else 'se conserva'} — {regla}"
            )
        lineas.append("")
    lineas.append("La latencia IA-M08 se mide contra la API desplegada (fase 2).")
    return "\n".join(lineas) + "\n"
