"""RC-P06.2: redactar referencias RAG candidatas solo después de construir documentos."""

from __future__ import annotations

import argparse
from pathlib import Path

from .comun import CAMPOS, ESTADO, escribir_json, leer_json, sha256


def preparar_consultas(root: Path) -> None:
    destino = root / "oraculos/e90/consultas_candidatas.json"
    if destino.exists():
        raise FileExistsError("consultas_ya_preparadas_no_sobrescribir")
    registros = leer_json(root / "corpus/e90/registros_fuente.json")["registros"]
    artifacts = leer_json(root / "oraculos/e90/artefactos_candidatos.json")[
        "artefactos"
    ]
    available = {a["doc_id"]: a for a in artifacts}
    for a in artifacts:
        p = root / a["ruta"]
        if not p.is_file() or sha256(p) != a["sha256"]:
            raise ValueError("documentos_no_construidos_o_modificados")
    docs = [
        r for r in registros if r["grupo"] == "medicion" and r["doc_id"] in available
    ]
    fragments = leer_json(root / "oraculos/e90/fragmentos_candidatos.json")[
        "fragmentos"
    ]
    campos = leer_json(root / "oraculos/e90/campos_candidatos.json")["campos"]
    byfield = {(r["doc_id"], r["campo"]): r for r in campos if r["presente"]}
    byfrag = {f["fragmento_id"]: f for f in fragments}
    result = []

    def add(categoria, pregunta, contexto, answer, refs, motivo=None):
        if any(ref not in byfrag for ref in refs):
            raise ValueError("fragmento_referencia_no_construido")
        result.append(
            {
                "pregunta_id": f"Q{len(result) + 1:02d}",
                "categoria": categoria,
                "clase": "sin_evidencia"
                if categoria == "sin_evidencia"
                else "respondible",
                "pregunta": pregunta,
                "documentos_autorizados": contexto,
                "respuesta_referencia": answer,
                "afirmaciones_esperadas": [answer] if answer else [],
                "fragmentos_relevantes": refs,
                "motivo_abstencion": motivo,
                "estado": ESTADO,
                "revisado_por_autores": False,
                "evaluaciones_autores": [],
                "consenso": None,
            }
        )

    for tipo in CAMPOS:
        selected = next(
            r for r in docs if r["tipo"] == tipo and r["doc_id"].endswith("-01")
        )
        ident = selected["doc_id"]
        amount = next(
            c for c in CAMPOS[tipo] if c in {"monto_total", "importe_total", "importe"}
        )
        moneda = selected["valores"]["moneda"]
        add(
            "directa",
            f"¿Cuál es el total y en qué moneda está expresado en {ident}?",
            [ident],
            byfield[(ident, amount)]["representacion"] + " " + moneda,
            [ident + "-CAMPO-" + amount, ident + "-CAMPO-moneda"],
        )
        persona = next(
            c for c in ("contraparte", "proveedor", "emisor") if c in CAMPOS[tipo]
        )
        add(
            "directa",
            f"¿Qué entidad interviene como {persona} en {ident}?",
            [ident],
            selected["valores"][persona],
            [ident + "-CAMPO-" + persona],
        )
    selection = [r for r in docs if r["doc_id"].endswith(("-02", "-03"))][:8]
    for r in selection:
        ident = r["doc_id"]
        frag = next(
            f
            for f in fragments
            if f["doc_id"] == ident and f["texto"].startswith("El plazo de entrega")
        )
        add(
            "condiciones",
            f"Para coordinar la prestación de {ident}, ¿qué plazo y modalidad hay que tener en cuenta?",
            [ident],
            frag["texto"],
            [frag["fragmento_id"]],
        )
    for numero in ("01", "03"):
        group = [r for r in docs if r["contexto_rag"] == "E90-CONTEXTO-" + numero]
        if len(group) != 3:
            raise ValueError("contexto_multidocumento_no_construido")
        for first, second in (
            (group[0], group[1]),
            (group[1], group[2]),
            (group[0], group[2]),
        ):
            ids = [first["doc_id"], second["doc_id"]]
            refs = []
            answers = []
            for r in (first, second):
                campo = next(
                    c
                    for c in CAMPOS[r["tipo"]]
                    if c in {"importe", "importe_total", "monto_total"}
                )
                refs.extend(
                    [r["doc_id"] + "-CAMPO-" + campo, r["doc_id"] + "-CAMPO-moneda"]
                )
                answers.append(
                    r["doc_id"]
                    + ": "
                    + byfield[(r["doc_id"], campo)]["representacion"]
                    + " "
                    + r["valores"]["moneda"]
                )
            add(
                "multidocumento",
                f"¿Qué importes y monedas figuran en {ids[0]} y {ids[1]}?",
                [r["doc_id"] for r in group],
                "; ".join(answers),
                refs,
            )
    negatives = [
        (
            "¿Qué tasa de interés anual se pactó para financiar esta operación?",
            "No se declara financiación ni una tasa anual en el contexto autorizado.",
        ),
        (
            "¿Qué persona física es beneficiaria final de la contraparte?",
            "El documento solo identifica una entidad ficticia, no beneficiarios finales.",
        ),
        (
            "¿Cuál es el número de la cuenta bancaria para realizar el pago?",
            "No hay cuenta bancaria en el contexto autorizado.",
        ),
        (
            "¿Quién autorizó el gasto en representación del cliente y con qué poder?",
            "No se identifica un representante con un poder verificable.",
        ),
        (
            "¿Qué domicilio particular tiene quien supervisa la entrega?",
            "No se incluyen personas ni domicilios particulares.",
        ),
        (
            "¿Cuál es el precio que se acordó en el contrato relacionado que no está incluido aquí?",
            "Un contrato ajeno al contexto autorizado no es fuente disponible; no inferir su precio.",
        ),
    ]
    context = next(
        r for r in docs if r["tipo"] == "presupuesto" and r["doc_id"].endswith("-03")
    )
    for pregunta, motivo in negatives:
        add("sin_evidencia", pregunta, [context["doc_id"]], None, [], motivo)
    if len(result) != 30:
        raise ValueError("recuento_consultas")
    escribir_json(
        destino,
        {
            "estado": ESTADO,
            "revisado_por_autores": False,
            "consultas": result,
            "nota": "Borradores de referencias previas a modelos; no son evaluaciones ni revisión humana. Los fragmentos primarios se mapearán a chunks de cada indexación congelada después.",
        },
    )
    print(
        "CONSULTAS_CANDIDATAS total=30 directas=10 condiciones=8 multidocumento=6 sin_evidencia=6"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raiz", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args()
    preparar_consultas(args.raiz.resolve())


if __name__ == "__main__":
    main()
