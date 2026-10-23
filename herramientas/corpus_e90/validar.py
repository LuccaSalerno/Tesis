"""IA-D01–08: validar artefactos candidatos existentes; nunca regenerar desde la CI."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import re
import zipfile
from collections import Counter
from pathlib import Path

from .comun import (
    CAMPOS,
    ESTADO,
    PATRON_ID,
    PISTAS_PROHIBIDAS,
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
    if (
        len(pool) != 18
        or len(cuitids) != 18
        or len({r["cuit"] for r in pool}) != 18
        or Counter(r.get("particion") for r in pool)
        != Counter({"medicion": 12, "ajuste": 6})
    ):
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
        elif candidate.get("particion") != r["grupo"]:
            # REV-E90-15: sujetos disjuntos entre ajuste y medición.
            errores.append(problema("E90_SUJETOS_PARTICION", ident))
        if r["tipo"] == "contrato" and r.get("fuente_contractual") != family:
            errores.append(problema("E90_FUENTE_CONTRACTUAL", ident))
        if "ambiguo_entre_categorias" in r.get("casos_dificiles", []) and not (
            r.get("ambiguedad") or {}
        ).get("justificacion"):
            errores.append(problema("E90_AMBIGUO_SIN_JUSTIFICACION", ident))
        adv = r.get("adversarial")
        if r["prompt_injection"]:
            objetivos = (adv or {}).get("objetivos") or {}
            esperado = dict(r["valores"], clasificacion=r["clasificacion_esperada"])
            if not objetivos or any(
                k in esperado and esperado[k] == valor for k, valor in objetivos.items()
            ):
                # REV-E90-10: el ataque debe pedir algo que contradiga el oráculo.
                errores.append(problema("E90_ADVERSARIAL_NO_CONTRASTABLE", ident))
            if any(p in (adv or {}).get("texto", "") for p in PISTAS_PROHIBIDAS):
                errores.append(problema("E90_ADVERSARIAL_NEUTRALIZADO", ident))
        elif adv:
            errores.append(problema("E90_ADVERSARIALES", ident))
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
    partes = {
        grupo: {
            v
            for r in records
            if r["grupo"] == grupo
            for k, v in r["valores"].items()
            if k in {"contraparte", "proveedor", "emisor"}
        }
        for grupo in ("medicion", "ajuste")
    }
    if partes["medicion"] & partes["ajuste"]:
        errores.append(problema("E90_SUJETOS_PARTICION"))
    errores.extend(validar_tramites(data["registros"].get("contextos", {}), byid))
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
    for a in data["artefactos"]["artefactos"]:
        rutas = (a["ruta"], a["fuente_docx"], a["pdf_referencia"])
        if any(PATRON_ID.search(ruta) for ruta in rutas) or any(
            a.get("archivo_id", "\0") not in ruta for ruta in rutas
        ):
            # P7: nombres de archivo neutros.
            errores.append(problema("E90_ID_EN_NOMBRE_ARCHIVO", a["doc_id"]))
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
        familia = r["plantilla_id"].split("-", 1)[-1]
        if presente and (
            not row["localizador"]
            or not row.get("etiqueta")
            or row.get("modo_localizacion") not in {"contiguo", "tabla"}
            or row["representacion"]
            != representacion(
                campo, r["valores"][campo], familia, r["valores"].get("moneda")
            )
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
        if PATRON_ID.search(q["pregunta"]) or "E90" in q["pregunta"]:
            errores.append(problema("E90_CONSULTA_CON_ID", ident))
        textos = {fragmap[ref]["texto"] for ref in refs if ref in fragmap}
        if not negative and any(
            not a.strip() or a in textos for a in q["afirmaciones_esperadas"]
        ):
            # REV-E90-01/05: afirmaciones propias, no el fragmento completo.
            errores.append(problema("E90_AFIRMACION_NO_ATOMICA", ident))
    adversariales = {r["doc_id"] for r in records if r["prompt_injection"]}
    if not any(adversariales & set(q["documentos_autorizados"]) for q in queries):
        errores.append(problema("E90_ADVERSARIAL_FUERA_DE_RAG"))
    abstenciones = {
        tuple(q["documentos_autorizados"])
        for q in queries
        if q["categoria"] == "sin_evidencia"
    }
    if len(abstenciones) < 4:
        errores.append(problema("E90_ABSTENCIONES_CONCENTRADAS"))
    clausulas = [
        q
        for q in queries
        if q["categoria"] == "condiciones"
        and any("-CLAUSULA-" in ref for ref in q["fragmentos_relevantes"])
    ]
    if len(clausulas) < 5:
        errores.append(problema("E90_CONDICIONES_SIN_CLAUSULAS"))
    medidos = [
        row
        for row in data["campos"]["campos"]
        if row["presente"] and byid.get(row["doc_id"], {}).get("grupo") == "medicion"
    ]
    for campo, minimo in (("fecha", 3), ("importe_total", 2), ("moneda", 3)):
        patrones = {
            re.sub(r"\d", "9", row["representacion"] or "")
            for row in medidos
            if row["campo"].startswith(campo)
        }
        if len(patrones) < minimo:
            # REV-E90-07: formatos variados dentro de la medición.
            errores.append(problema("E90_FORMATOS_UNIFORMES", campo))
    return errores


def validar_tramites(contextos: dict, byid: dict) -> list[str]:
    """P13 / REV-E90-12: trámites con el mismo sujeto, moneda e importes relacionados."""
    errores = []
    for nombre, ctx in contextos.items():
        docs = [byid.get(d) for d in ctx["docs"]]
        if (
            len(docs) < 3
            or any(r is None or r["grupo"] != "medicion" for r in docs)
            or any(r["contexto_rag"] != nombre for r in docs)
        ):
            errores.append(problema("E90_TRAMITE_INCOHERENTE", nombre))
            continue
        cuits = {
            v for r in docs for k, v in r["valores"].items() if k.startswith("cuit")
        }
        monedas = {r["valores"]["moneda"] for r in docs}
        importes = {
            r["tipo"]: r["valores"].get("importe_total", r["valores"].get("importe"))
            for r in docs
            if r["tipo"] != "contrato"
        }
        orden = importes.get("orden_compra")
        factura = next(r for r in docs if r["tipo"] == "factura")
        coherente = len(cuits) == 1 and len(monedas) == 1
        if "presupuesto" in importes and importes["presupuesto"] != orden:
            coherente = False
        if factura["discrepancia_documentada"] is None and importes["factura"] != orden:
            coherente = False
        if "comprobante" in importes and importes["comprobante"] != importes["factura"]:
            coherente = False
        if not coherente:
            errores.append(problema("E90_TRAMITE_INCOHERENTE", nombre))
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
            etiqueta = normalizar(row["etiqueta"])
            texto = normalizar(paragraphs[i - 1])
            if row["modo_localizacion"] == "tabla":
                correcto = (
                    i > 1
                    and texto == normalizar(target)
                    and normalizar(paragraphs[i - 2]) == etiqueta
                )
            else:
                correcto = etiqueta + normalizar(target) in texto
            if not correcto:
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
        objetivo = normalizar(target)
        if "campo" in row:
            objetivo = normalizar(row["etiqueta"]) + objetivo
        else:
            # Un fragmento extenso puede continuar en la página siguiente: se ubica su inicio.
            objetivo = objetivo[:60]
        if i > len(pages) or objetivo not in normalizar(pages[i - 1]):
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
        auxiliar = ruta_segura(root, a["fuente_docx"], "corpus/e90")
        contenido = " ".join(parrafos_docx(auxiliar)) + " ".join(
            p.extract_text() or "" for p in PdfReader(reference).pages
        )
        if PATRON_ID.search(contenido):
            errores.append(problema("E90_ID_EN_CONTENIDO", ident))
        if any(pista in contenido for pista in PISTAS_PROHIBIDAS):
            errores.append(problema("E90_PISTA_DE_CONSTRUCCION", ident))
        titulos = [str((PdfReader(reference).metadata or {}).get("/Title", ""))]
        if a["formato"] != "docx":
            titulos.append(str((PdfReader(final).metadata or {}).get("/Title", "")))
        with zipfile.ZipFile(auxiliar) as z:
            titulos.append(z.read("docProps/core.xml").decode("utf-8"))
        if any(PATRON_ID.search(t) for t in titulos):
            errores.append(problema("E90_ID_EN_METADATOS", ident))
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
    multipagina = sum(
        records[a["doc_id"]]["tipo"] != "contrato"
        and records[a["doc_id"]]["grupo"] == "medicion"
        and a["paginas"] >= 2
        for a in byid.values()
    )
    if multipagina < 15:
        # REV-E90-13: procedencia por página no trivial.
        errores.append(problema("E90_PAGINAS_INSUFICIENTES"))
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
