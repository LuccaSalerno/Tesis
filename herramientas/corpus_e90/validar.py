"""IA-D01–08: validar artefactos candidatos existentes; nunca regenerar desde la CI."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import re
from collections import Counter
from pathlib import Path

from .comun import (
    CAMPOS,
    ESTADO,
    ETIQUETAS,
    cuit_valido,
    leer_json,
    normalizar,
    parrafos_docx,
    representacion,
    ruta_segura,
    sha256,
)


def problema(codigo: str, ident: str = "corpus") -> str:
    # RNF-09: códigos e identificadores, nunca valores, preguntas o texto extraído.
    return codigo + ":" + ident


def leer_conjunto(root: Path) -> dict:
    carpeta = root / "oraculos/e90"
    with (carpeta / "inventario_candidato.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        inventory = list(csv.DictReader(stream))
    return {
        "registros": leer_json(root / "corpus/e90/registros_fuente.json"),
        "cuit": leer_json(carpeta / "cuit_candidatos.json"),
        "artefactos": leer_json(carpeta / "artefactos_candidatos.json"),
        "campos": leer_json(carpeta / "campos_candidatos.json"),
        "fragmentos": leer_json(carpeta / "fragmentos_candidatos.json"),
        "consultas": leer_json(carpeta / "consultas_candidatas.json"),
        "plantillas": leer_json(
            root / "herramientas/corpus_e90/plantillas/contratos.json"
        ),
        "inventario": inventory,
    }


def validar_estructura(data: dict) -> list[str]:
    errores = []
    for name in (
        "registros",
        "cuit",
        "artefactos",
        "campos",
        "fragmentos",
        "consultas",
        "plantillas",
    ):
        if data[name].get("estado") != ESTADO:
            errores.append(problema("E90_ESTADO_NO_CANDIDATO", name))
        if data[name].get("revisado_por_autores", False):
            errores.append(problema("E90_REVISION_NO_AUTORIZADA", name))
    records = data["registros"]["registros"]
    byid = {r["doc_id"]: r for r in records}
    if len(byid) != len(records):
        errores.append(problema("E90_ID_DUPLICADO"))
    if Counter(r["grupo"] for r in records) != Counter({"medicion": 50, "ajuste": 15}):
        errores.append(problema("E90_PARTICIONES"))
    for tipo in CAMPOS:
        for grupo, cantidad in [("medicion", 10), ("ajuste", 3)]:
            if (
                sum(r["tipo"] == tipo and r["grupo"] == grupo for r in records)
                != cantidad
            ):
                errores.append(problema("E90_RECUENTO_TIPO", tipo + "_" + grupo))
    adversarios = [r for r in records if r["prompt_injection"]]
    if len(adversarios) != 3 or any(r["grupo"] != "medicion" for r in adversarios):
        errores.append(problema("E90_ADVERSARIALES"))
    pool = data["cuit"]["candidatos"]
    cuitids = {r["id"]: r for r in pool}
    if len(pool) != 12 or len(cuitids) != 12 or len({r["cuit"] for r in pool}) != 12:
        errores.append(problema("E90_CUIT_RECUENTO"))
    for candidate in pool:
        if not cuit_valido(candidate["cuit"]):
            errores.append(problema("E90_CUIT_DIGITO", candidate["id"]))
        if candidate["estado"] != "candidato":
            errores.append(problema("E90_CUIT_ESTADO", candidate["id"]))
    for r in records:
        ident = r["doc_id"]
        if r["tipo"] not in CAMPOS or r["grupo"] not in {"ajuste", "medicion"}:
            errores.append(problema("E90_TIPO_GRUPO", ident))
            continue
        if r["estado"] != ESTADO or r["revisado_por_autores"]:
            errores.append(problema("E90_REVISION_NO_AUTORIZADA", ident))
        family = r["plantilla_id"].split("-", 1)[-1]
        if family not in {"BASE_A", "BASE_B", "MED_C", "MED_D", "ARG_A"} or (
            r["grupo"] == "ajuste" and (family.startswith("MED_") or family == "ARG_A")
        ):
            errores.append(problema("E90_PLANTILLA_AJUSTE", ident))
        if family == "ARG_A" and (
            ident != "E90-M-CTR-03"
            or r["tipo"] != "contrato"
            or r["grupo"] != "medicion"
            or r["formato"] != "pdf_digital"
        ):
            errores.append(problema("E90_ARG_A_ALCANCE", ident))
        expected = set(CAMPOS[r["tipo"]])
        present = set(r["valores"])
        absent = set(r["ausentes"])
        na = set(r["no_aplicables"])
        if (
            present & absent
            or present & na
            or absent & na
            or present | absent | na != expected
        ):
            errores.append(problema("E90_ESQUEMA_CAMPOS", ident))
        candidate = cuitids.get(r["cuit_id"])
        if not candidate or any(
            value != candidate["cuit"]
            for k, value in r["valores"].items()
            if k.startswith("cuit")
        ):
            errores.append(problema("E90_CUIT_REFERENCIA", ident))
        capture = r["captura"]
        if r["formato"] in {"pdf_escaneado", "pdf_fotografiado"}:
            if (
                not capture
                or capture.get("metodo") != "degradacion_digital_simulada"
                or capture.get("captura_fisica") is not False
                or capture.get("semilla") != r["semilla"]
            ):
                errores.append(problema("E90_SIMULACION_NO_DECLARADA", ident))
        elif capture is not None:
            errores.append(problema("E90_CAPTURA_FORMATO", ident))
    for tipo in CAMPOS:
        families = {
            r["plantilla_id"].split("-", 1)[-1]
            for r in records
            if r["tipo"] == tipo and r["grupo"] == "medicion"
        }
        expected_families = {"BASE_A", "BASE_B", "MED_C", "MED_D"}
        if tipo == "contrato":
            expected_families.add("ARG_A")
        if families != expected_families:
            errores.append(problema("E90_PLANTILLAS_MEDICION", tipo))
    sources = data["plantillas"]["fuentes"]
    if (
        set(sources) != {"BASE_A", "BASE_B", "MED_C", "MED_D", "ARG_A"}
        or len({s["url_archivo"] for s in sources.values()}) != 5
    ):
        errores.append(problema("E90_DIVERSIDAD_FUENTES"))
    arg = sources.get("ARG_A", {})
    if (
        arg.get("licencia") != "CC-BY-NC-SA-4.0"
        or arg.get("licencia_adaptacion") != "CC-BY-NC-SA-4.0"
        or arg.get("uso_no_comercial") is not True
        or arg.get("uso_en_ajuste") is not False
    ):
        errores.append(problema("E90_ARG_A_LICENCIA"))
    for family, s in sources.items():
        if (
            s["estado_aprobacion"] != "aprobada"
            or not s["licencia"]
            or not s["version"]
            or not s["atribucion"]
            or not s["clausulas"]
            or not re.fullmatch("[a-f0-9]{64}", s["sha256_archivo_original"])
        ):
            errores.append(problema("E90_PROCEDENCIA_CONTRATO", family))
    for key, values in [
        ("inventario", data["inventario"]),
        ("artefactos", data["artefactos"]["artefactos"]),
    ]:
        ids = [r["doc_id"] for r in values]
        if set(ids) != set(byid) or len(ids) != len(byid):
            errores.append(problema("E90_ARTEFACTOS_RECUENTO", key))
    hashes = [r["sha256"] for r in data["artefactos"]["artefactos"]]
    if len(set(hashes)) != len(hashes):
        errores.append(problema("E90_ARCHIVO_DUPLICADO"))
    artifactmap = {r["doc_id"]: r for r in data["artefactos"]["artefactos"]}
    for row in data["inventario"]:
        ident = row["doc_id"]
        r = byid.get(ident)
        a = artifactmap.get(ident)
        if not r or not a:
            continue
        if (
            any(row[k] != r[k] for k in ("grupo", "tipo", "formato", "plantilla_id"))
            or any(row[k] != a[k] for k in ("ruta", "sha256"))
            or (row["prompt_injection"] == "si") != r["prompt_injection"]
        ):
            errores.append(problema("E90_INVENTARIO_DISCREPANTE", ident))
    seen = set()
    for row in data["campos"]["campos"]:
        ident = row["doc_id"]
        r = byid.get(ident)
        key = (ident, row["campo"])
        if key in seen:
            errores.append(problema("E90_CAMPO_DUPLICADO", ident))
        seen.add(key)
        if not r or row["campo"] not in CAMPOS[r["tipo"]]:
            errores.append(problema("E90_CAMPO_DESCONOCIDO", ident))
            continue
        campo = row["campo"]
        presente = campo in r["valores"]
        if (
            row["presente"] != presente
            or row["aplicable"] != (campo not in r["no_aplicables"])
            or row["valor_esperado"] != r["valores"].get(campo)
        ):
            errores.append(problema("E90_ORACULO_DISCREPANTE", ident))
        if not presente and (
            row["localizador"] is not None or row["representacion"] is not None
        ):
            errores.append(problema("E90_AUSENCIA_CON_LOCALIZADOR", ident))
        if presente and (
            not row["localizador"]
            or row["representacion"] != representacion(campo, r["valores"][campo])
        ):
            errores.append(problema("E90_LOCALIZADOR_FALTANTE", ident))
        if row["estado"] != ESTADO or row["revisado_por_autores"]:
            errores.append(problema("E90_REVISION_NO_AUTORIZADA", ident))
    if seen != {(r["doc_id"], c) for r in records for c in CAMPOS[r["tipo"]]}:
        errores.append(problema("E90_CAMPOS_INCOMPLETOS"))
    fragments = data["fragmentos"]["fragmentos"]
    fragmap = {f["fragmento_id"]: f for f in fragments}
    if len(fragmap) != len(fragments):
        errores.append(problema("E90_FRAGMENTO_DUPLICADO"))
    for frag in fragments:
        if frag["doc_id"] not in byid or not frag["texto"] or not frag["localizador"]:
            errores.append(problema("E90_FRAGMENTO_INVALIDO", frag["fragmento_id"]))
        if frag["estado"] != ESTADO or frag["revisado_por_autores"]:
            errores.append(problema("E90_REVISION_NO_AUTORIZADA", frag["fragmento_id"]))
    queries = data["consultas"]["consultas"]
    if {q["pregunta_id"] for q in queries} != {
        f"Q{i:02d}" for i in range(1, 31)
    } or len(queries) != 30:
        errores.append(problema("E90_CONSULTAS_RECUENTO"))
    if Counter(q["categoria"] for q in queries) != Counter(
        {"directa": 10, "condiciones": 8, "multidocumento": 6, "sin_evidencia": 6}
    ):
        errores.append(problema("E90_CONSULTAS_DISTRIBUCION"))
    for q in queries:
        ident = q["pregunta_id"]
        context = q["documentos_autorizados"]
        if (
            not context
            or len(set(context)) != len(context)
            or any(d not in byid or byid[d]["grupo"] != "medicion" for d in context)
        ):
            errores.append(problema("E90_CONSULTA_CONTEXTO", ident))
        refs = q["fragmentos_relevantes"]
        negative = q["categoria"] == "sin_evidencia"
        if (
            not q["pregunta"].strip()
            or q["revisado_por_autores"]
            or q["estado"] != ESTADO
        ):
            errores.append(problema("E90_CONSULTA_ESTADO", ident))
        if negative and (
            refs or q["respuesta_referencia"] is not None or not q["motivo_abstencion"]
        ):
            errores.append(problema("E90_ABSTENCION_INVALIDA", ident))
        if not negative and (
            not refs or not q["respuesta_referencia"] or not q["afirmaciones_esperadas"]
        ):
            errores.append(problema("E90_RESPUESTA_SIN_FUENTE", ident))
        cited = set()
        for ref in refs:
            f = fragmap.get(ref)
            if not f or f["doc_id"] not in context:
                errores.append(problema("E90_CITA_FUERA_CONTEXTO", ident))
            else:
                cited.add(f["doc_id"])
        if q["categoria"] == "multidocumento" and len(cited) < 2:
            errores.append(problema("E90_MULTIDOCUMENTO_INCOMPLETO", ident))
    return errores


def comprobar_localizador(
    root: Path, row: dict, artifact: dict, caches: dict
) -> list[str]:
    ident = row.get("doc_id", row.get("fragmento_id", "referencia"))
    loc = row["localizador"]
    target = row.get("representacion", row.get("texto"))
    if loc is None:
        return []
    if loc["tipo"] == "parrafo":
        path = ruta_segura(root, artifact["fuente_docx"], "corpus/e90")
        if str(path) not in caches:
            caches[str(path)] = parrafos_docx(path)
        paragraphs = caches[str(path)]
        i = loc["indice"]
        if (
            not isinstance(i, int)
            or isinstance(i, bool)
            or i < 1
            or i > len(paragraphs)
        ):
            return [problema("E90_PARrafo_FUERA_RANGO", ident)]
        if normalizar(target) not in normalizar(paragraphs[i - 1]):
            return [problema("E90_PARrafo_SIN_RESPALDO", ident)]
        if "campo" in row:
            etiqueta = normalizar(ETIQUETAS[row["campo"]])
            if etiqueta + ":" not in normalizar(paragraphs[i - 1]) and (
                i < 2 or normalizar(paragraphs[i - 2]) != etiqueta
            ):
                return [problema("E90_PARrafo_CAMPO_INCORRECTO", ident)]
    elif loc["tipo"] == "pagina":
        i = loc["pagina"]
        if (
            not isinstance(i, int)
            or isinstance(i, bool)
            or not 1 <= i <= artifact["paginas"]
        ):
            return [problema("E90_PAGINA_FUERA_RANGO", ident)]
        from pypdf import PdfReader

        path = ruta_segura(root, artifact["pdf_referencia"], "corpus/e90")
        if str(path) not in caches:
            caches[str(path)] = [p.extract_text() or "" for p in PdfReader(path).pages]
        pages = caches[str(path)]
        if i > len(pages) or normalizar(target) not in normalizar(pages[i - 1]):
            return [problema("E90_PAGINA_SIN_RESPALDO", ident)]
        if (
            "referencia_sha256" in loc
            and loc["referencia_sha256"] != artifact["pdf_referencia_sha256"]
        ):
            return [problema("E90_LOCALIZADOR_HUELLA", ident)]
    else:
        return [problema("E90_TIPO_LOCALIZADOR", ident)]
    return []


def validar_archivos(root: Path, data: dict) -> list[str]:
    errores = []
    caches = {}
    records = {r["doc_id"]: r for r in data["registros"]["registros"]}
    if (
        sha256(root / "corpus/e90/registros_fuente.json")
        != data["artefactos"]["registros_sha256"]
    ):
        errores.append(problema("E90_REGISTROS_HUELLA"))
    if (
        sha256(root / "herramientas/corpus_e90/plantillas/contratos.json")
        != data["artefactos"]["plantillas_sha256"]
    ):
        errores.append(problema("E90_PLANTILLAS_HUELLA"))
    with (root / "docs/evaluacion/plan_diseno_corpus_e90.csv").open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        plan = {r["caso_plan"]: r for r in csv.DictReader(stream)}
    if set(plan) != set(records):
        errores.append(problema("E90_PLAN_IDS"))
    for ident, r in records.items():
        expected = plan.get(ident, {})
        for key, col in [
            ("grupo", "grupo_previsto"),
            ("tipo", "tipo"),
            ("formato", "formato_previsto"),
            ("plantilla_id", "plantilla_prevista"),
        ]:
            if r[key] != expected.get(col):
                errores.append(problema("E90_PLAN_DISCREPANTE", ident))
    proof = leer_json(
        root / "docs/evaluacion/corpus_e90/fuentes/ARG_A_CPAU_verificacion.json"
    )
    arg = data["plantillas"]["fuentes"]["ARG_A"]
    avisos = root / "docs/evaluacion/corpus_e90/fuentes/ARG_A_CPAU_avisos.html"
    if (
        proof["sha256_archivo_original"] != arg["sha256_archivo_original"]
        or proof["licencia"] != arg["licencia"]
        or proof["url_archivo"] != arg["url_archivo"]
        or proof["version"] != arg["version"]
        or sha256(avisos) != proof["sha256_extractos_ficha_conservados"]
    ):
        errores.append(problema("E90_ARG_A_PROCEDENCIA"))
    from pypdf import PdfReader

    byid = {a["doc_id"]: a for a in data["artefactos"]["artefactos"]}
    for ident, a in byid.items():
        for pathkey, hashkey in [
            ("ruta", "sha256"),
            ("fuente_docx", "fuente_docx_sha256"),
            ("pdf_referencia", "pdf_referencia_sha256"),
        ]:
            path = ruta_segura(root, a[pathkey], "corpus/e90")
            if not path.is_file() or sha256(path) != a[hashkey]:
                errores.append(problema("E90_ARCHIVO_HUELLA", ident))
                continue
        final = ruta_segura(root, a["ruta"], "corpus/e90")
        reference = ruta_segura(root, a["pdf_referencia"], "corpus/e90")
        if (
            a["tamano_bytes"] != final.stat().st_size
            or final.stat().st_size > 20 * 1024 * 1024
        ):
            errores.append(problema("E90_TAMANO", ident))
        if a["formato"] == "docx":
            paragraphs = parrafos_docx(final)
            if not any("DOCUMENTO FICTICIO" in p for p in paragraphs):
                errores.append(problema("E90_MARCA_FALTANTE", ident))
            if sum(len(p) for p in paragraphs) > 150000:
                errores.append(problema("E90_LIMITE_DOCX", ident))
        else:
            finalreader = PdfReader(final)
            if (
                finalreader.is_encrypted
                or len(finalreader.pages) != a["paginas"]
                or len(finalreader.pages) > 50
            ):
                errores.append(problema("E90_PDF_PAGINAS", ident))
            if a["captura"] and any(
                p.extract_text().strip() for p in finalreader.pages
            ):
                errores.append(problema("E90_IMAGEN_CON_CAPA_TEXTO", ident))
        if ident == "E90-M-CTR-03":
            texto = normalizar(
                " ".join(p.extract_text() or "" for p in PdfReader(final).pages)
            )
            avisos = (
                "CC BY-NC-SA 4.0",
                "https://creativecommons.org/licenses/by-nc-sa/4.0/",
                "https://repositorio.cpau.org/items/show/823",
                "Consejo Profesional de Arquitectura y Urbanismo",
                "no comercial",
                "Cambios:",
                "sin garantías",
            )
            if any(normalizar(aviso) not in texto for aviso in avisos):
                errores.append(problema("E90_ARG_A_ATRIBUCION", ident))
        referencepages = PdfReader(reference).pages
        if len(referencepages) != a["paginas"]:
            errores.append(problema("E90_PDF_REFERENCIA_PAGINAS", ident))
        if a["captura"] != records[ident]["captura"]:
            errores.append(problema("E90_CAPTURA_DISCREPANTE", ident))
        if records[ident]["caso_dificil"] == "contrato_extenso" and a["paginas"] < 8:
            errores.append(problema("E90_CONTRATO_NO_EXTENSO", ident))
    for row in data["campos"]["campos"] + data["fragmentos"]["fragmentos"]:
        if row["doc_id"] in byid:
            errores.extend(
                comprobar_localizador(root, row, byid[row["doc_id"]], caches)
            )
    return errores


def validar(root: Path, archivos: bool = True) -> list[str]:
    try:
        data = leer_conjunto(root)
        errores = validar_estructura(data)
        if errores:
            return errores
        if archivos:
            if importlib.util.find_spec("pypdf") is None:
                return [problema("E90_LECTOR_PDF_NO_DISPONIBLE")]
            errores.extend(validar_archivos(root, data))
        return errores
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError):
        return [problema("E90_ENTRADAS_INVALIDAS")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raiz", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--solo-estructura", action="store_true")
    parser.add_argument("--evidencia", type=Path)
    args = parser.parse_args()
    errores = validar(args.raiz.resolve(), not args.solo_estructura)
    if args.evidencia:
        from .comun import escribir_json

        escribir_json(
            args.evidencia,
            {
                "estado": ESTADO,
                "alcance": "estructural"
                if args.solo_estructura
                else "artefactos_y_referencias",
                "errores": errores,
                "resultado": "sin_inconsistencias_estructurales"
                if not errores
                else "inconsistencias_detectadas",
                "aceptacion_academica": "no_acreditada",
            },
        )
    print("VALIDACION_CANDIDATA errores=" + str(len(errores)) + " congelado=no")
    for error in errores:
        print(error)
    return bool(errores)


if __name__ == "__main__":
    raise SystemExit(main())
