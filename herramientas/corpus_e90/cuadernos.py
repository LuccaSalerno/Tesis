"""IA-D/RC-P06.2: cuadernos de revisión de autores, derivados de los JSON candidatos.

DO-2026-10-22-CORPUS-REVISION: se regeneran con cada revisión candidata para que los
autores revisen exactamente lo construido. No marcan ninguna revisión como hecha.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .comun import ESTADO, VERSION, leer_json

DESTINO = "docs/evaluacion/corpus_e90"
RELATIVA = "../../../"
FORMATOS = {
    "pdf_digital": "PDF digital",
    "docx": "DOCX",
    "pdf_escaneado": "PDF escaneado simulado",
    "pdf_fotografiado": "PDF fotografiado simulado",
}
FIRMAS = """- [ ] Autor 1 revisó {que}.
- [ ] Autor 2 revisó {que}.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.
"""


def localizador(loc: dict | None, formato: str) -> str:
    if not loc:
        return "—"
    if loc["tipo"] == "parrafo":
        return f"DOCX, párrafo {loc['indice']}"
    return f"PDF, página {loc['pagina']}" + (
        " (referencia previa a la simulación)"
        if formato in {"pdf_escaneado", "pdf_fotografiado"}
        else ""
    )


def celda(texto: str | None) -> str:
    return (texto or "—").replace("|", "\\|").replace("\n", " ")


def generar_cuadernos(root: Path, commit: str) -> None:
    registros = leer_json(root / "corpus/e90/registros_fuente.json")
    artefactos = {
        a["doc_id"]: a
        for a in leer_json(root / "oraculos/e90/artefactos_candidatos.json")[
            "artefactos"
        ]
    }
    campos = leer_json(root / "oraculos/e90/campos_candidatos.json")["campos"]
    fragmentos = leer_json(root / "oraculos/e90/fragmentos_candidatos.json")[
        "fragmentos"
    ]
    consultas = leer_json(root / "oraculos/e90/consultas_candidatas.json")["consultas"]
    fragmap = {f["fragmento_id"]: f for f in fragmentos}
    regs = registros["registros"]
    byid = {r["doc_id"]: r for r in regs}

    def enlace(ident: str) -> str:
        return f"[{ident}]({RELATIVA}{artefactos[ident]['ruta']})"

    cabecera = (
        f"Revisión candidata **{VERSION}** (DO-2026-10-22-CORPUS-REVISION), datos del commit `{commit}`. "
        f"Estado: **{ESTADO}**. Este cuaderno se genera con `python -m herramientas.corpus_e90.cuadernos`; "
        "no cambia documentos ni oráculos. **Todo sigue candidato y pendiente de revisión de autores.** "
        "Las casillas y observaciones se dejan sin completar; no representan una revisión ejecutada.\n"
    )
    out = ["# Cuaderno de revisión de los 65 documentos E90\n", cabecera]
    out.append(
        "Los archivos de entrada tienen nombres neutros (`doc-…`); la correspondencia con el ID de inventario "
        "solo figura aquí y en `oraculos/e90/inventario_candidato.csv`. Para cada ficha: abrir el archivo, "
        "comprobar que el contenido sostiene la clase esperada sin pistas de construcción, y cotejar cada "
        "campo con su etiqueta impresa, representación y localizador. En DOCX, el índice cuenta los "
        "elementos `w:p` de `word/document.xml`, incluidas celdas de tablas.\n"
    )
    out.append("## Índice\n")
    out.append(
        "| ID | Archivo | Grupo | Tipo | Formato | Familia | Páginas | Trámite | Atención especial |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in regs:
        a = artefactos[r["doc_id"]]
        atencion = ", ".join(r["casos_dificiles"]) or "—"
        tramite = (
            r["contexto_rag"][-2:] if r["contexto_rag"][-2:].startswith("T") else "—"
        )
        out.append(
            f"| [{r['doc_id']}](#{r['doc_id'].lower()}) | [{a['archivo_id']}]({RELATIVA}{a['ruta']}) | {r['grupo']} | "
            f"{r['tipo']} | {FORMATOS[r['formato']]} | {r['plantilla_id']} | {a['paginas']} | {tramite} | {atencion} |"
        )
    out.append("")
    for r in regs:
        ident = r["doc_id"]
        a = artefactos[ident]
        out.append(f"## {ident}\n")
        aux = (
            f" · [PDF de referencia]({RELATIVA}{a['pdf_referencia']})"
            if r["formato"] != "pdf_digital"
            else ""
        )
        out.append(
            f"Archivo de entrada: [{a['archivo_id']}]({RELATIVA}{a['ruta']}) ({FORMATOS[r['formato']]}){aux}.\n"
        )
        out.append(
            f"Grupo **{r['grupo']}** · clase esperada **{r['clasificacion_esperada']}** · familia **{r['plantilla_id']}** · "
            f"{a['paginas']} página(s) · servicio: {r['servicio']}.\n"
        )
        if r["ambiguedad"]:
            amb = r["ambiguedad"]
            out.append(
                f"**Ambigüedad diseñada:** {amb['diseno']}; puede parecer **{amb['parece']}**. Justificación previa: {amb['justificacion']}\n"
            )
        if r["adversarial"]:
            adv = r["adversarial"]
            objetivos = ", ".join(f"{k} → {v}" for k, v in adv["objetivos"].items())
            out.append(
                f"**Contenido adversarial** ({adv['vector']}, {adv['ubicacion']}). Objetivos que el sistema no debe adoptar: {objetivos}.\n"
            )
        if r["discrepancia_documentada"]:
            d = r["discrepancia_documentada"]
            out.append(
                f"**Discrepancia deliberada:** {d['tipo']} (orden {d['importe_orden']}, factura {d['importe_factura']}).\n"
            )
        if r["referencias"]:
            refs = "; ".join(
                f"{x['tipo']} {x.get('numero') or x.get('fecha_celebracion')} ({x['doc_id']})"
                for x in r["referencias"]
            )
            out.append(f"Trámite {r['contexto_rag']}; cita: {refs}.\n")
        out.append(
            "| Campo | Valor normalizado | Representación impresa | Etiqueta | Presencia | Localizador |"
        )
        out.append("|---|---|---|---|---|---|")
        for c in (c for c in campos if c["doc_id"] == ident):
            out.append(
                f"| {c['campo']} | {celda(c['valor_esperado'])} | {celda(c['representacion'])} | {celda(c['etiqueta'])} | "
                f"{'Presente' if c['presente'] else 'Ausente (intencional)'} | {localizador(c['localizador'], r['formato'])} |"
            )
        otros = [
            f
            for f in fragmentos
            if f["doc_id"] == ident and not f["clave"].startswith("CAMPO-")
        ]
        if otros:
            out.append("\n**Fragmentos de condiciones, cláusulas y referencias:**\n")
            for f in otros:
                out.append(
                    f"- `{f['clave']}` ({localizador(f['localizador'], r['formato'])}): {celda(f['texto'][:220])}{'…' if len(f['texto']) > 220 else ''}"
                )
        out.append("")
        out.append(
            FIRMAS.format(
                que="clase, campos, ausencias, localizadores y casos difíciles"
            )
        )
    (root / DESTINO / "Cuaderno_Revision_Documentos_E90.md").write_text(
        "\n".join(out), encoding="utf-8"
    )

    out = ["# Cuaderno de revisión de las 30 preguntas RAG E90\n", cabecera]
    out.append(
        "Aquí se revisan preguntas y referencias **antes de ejecutar modelos**. Las evaluaciones de respuestas "
        "de IA (IA-M06) se completarán después de ejecutar. Para cada pregunta: leer el contexto autorizado, "
        "intentar responder desde los documentos y cotejar las afirmaciones esperadas. Aceptar equivalencia "
        "semántica conforme a RC-P06.2; las afirmaciones se limitan a lo preguntado.\n"
    )
    for q in consultas:
        out.append(f"## {q['pregunta_id']}\n")
        out.append(f"Categoría: **{q['categoria']}** · Clase: **{q['clase']}**.\n")
        out.append(f"**Pregunta:** {q['pregunta']}\n")
        contexto = ", ".join(
            f"{enlace(d)} ({byid[d]['tipo']})" for d in q["documentos_autorizados"]
        )
        out.append(
            f"**Contexto autorizado ({len(q['documentos_autorizados'])}):** {contexto}.\n"
        )
        if q["afirmaciones_esperadas"]:
            out.append("**Afirmaciones esperadas:**\n")
            out.extend(f"- {x}" for x in q["afirmaciones_esperadas"])
            out.append("\n**Fragmentos citados:**\n")
            for ref in q["fragmentos_relevantes"]:
                f = fragmap[ref]
                out.append(
                    f"- `{ref}` — {enlace(f['doc_id'])}; {localizador(f['localizador'], byid[f['doc_id']]['formato'])}. Texto: {celda(f['texto'][:220])}"
                )
        else:
            out.append(f"**Abstención esperada.** Motivo: {q['motivo_abstencion']}\n")
        out.append("")
        out.append(
            FIRMAS.format(
                que="pregunta, contexto y afirmaciones o motivo de abstención"
            )
        )
    (root / DESTINO / "Cuaderno_Revision_Consultas_RAG_E90.md").write_text(
        "\n".join(out), encoding="utf-8"
    )
    print("CUADERNOS_GENERADOS documentos=65 consultas=30")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raiz", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--commit", required=True, help="commit de los datos que se revisan"
    )
    args = parser.parse_args()
    generar_cuadernos(args.raiz.resolve(), args.commit)


if __name__ == "__main__":
    main()
