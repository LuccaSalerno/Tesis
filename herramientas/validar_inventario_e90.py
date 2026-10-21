#!/usr/bin/env python3
"""Validar el inventario de corpus de medición E90 sin usar AWS.

No produce ni edita documentos, ni verifica que los textos contengan las
respuestas de los oráculos. El corpus se debe inspeccionar manualmente además.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

CATEGORIAS = {"contrato", "presupuesto", "orden_compra", "factura", "comprobante"}
FORMATOS = {"pdf_digital", "pdf_escaneado", "pdf_fotografiado", "docx"}
COLUMNAS = {
    "doc_id", "grupo", "tipo", "formato", "plantilla_id", "ruta",
    "sha256", "prompt_injection", "observaciones",
}


def validar_inventario(repositorio: Path, csv_path: Path) -> list[str]:
    """Devolver problemas estructurales; [] si cumple el contrato de cantidades."""
    problemas: list[str] = []
    repositorio = repositorio.resolve()
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
            lector = csv.DictReader(fh)
            faltantes = COLUMNAS - set(lector.fieldnames or ())
            if faltantes:
                return [f"Faltan columnas: {', '.join(sorted(faltantes))}"]
            registros = list(lector)
    except (OSError, UnicodeError, csv.Error) as error:
        return [f"No se pudo leer inventario: {error}"]

    contadores = Counter()
    plantillas = defaultdict(lambda: defaultdict(set))
    rutas: set[Path] = set()
    ids: set[str] = set()
    cantidad_adversariales = 0
    formatos_presentes: set[str] = set()
    for numero, row in enumerate(registros, 2):
        prefijo = f"Fila {numero}"
        ident = row["doc_id"].strip()
        grupo = row["grupo"].strip().lower()
        tipo = row["tipo"].strip().lower()
        formato = row["formato"].strip().lower()
        plantilla = row["plantilla_id"].strip()
        nombre = row["ruta"].strip()
        huella = row["sha256"].strip().lower()
        adversarial = row["prompt_injection"].strip().lower()

        if not ident or ident in ids:
            problemas.append(f"{prefijo}: doc_id vacío o duplicado: {ident!r}")
        ids.add(ident)
        if grupo not in {"medicion", "ajuste"}:
            problemas.append(f"{prefijo}: grupo inválido {grupo!r} (medicion/ajuste)")
        if tipo not in CATEGORIAS:
            problemas.append(f"{prefijo}: tipo inválido {tipo!r}")
        if formato not in FORMATOS:
            problemas.append(f"{prefijo}: formato inválido {formato!r}")
        if not plantilla:
            problemas.append(f"{prefijo}: plantilla_id vacío")
        if adversarial not in {"si", "no"}:
            problemas.append(f"{prefijo}: prompt_injection inválido {adversarial!r} (si/no)")
        if adversarial == "si":
            cantidad_adversariales += 1
            if grupo != "medicion":
                problemas.append(f"{prefijo}: los 3 adversariales deben estar en medicion")

        if tipo in CATEGORIAS and grupo in {"medicion", "ajuste"}:
            contadores[(grupo, tipo)] += 1
            plantillas[tipo][grupo].add(plantilla)
        if grupo == "medicion" and formato in FORMATOS:
            formatos_presentes.add(formato)
        if not nombre:
            problemas.append(f"{prefijo}: ruta vacía")
            continue
        rel = Path(nombre)
        if rel.is_absolute() or ".." in rel.parts:
            problemas.append(f"{prefijo}: ruta no permitida: {nombre!r}")
            continue
        archivo = (repositorio / rel).resolve()
        corpus = (repositorio / "corpus").resolve()
        if not archivo.is_relative_to(corpus):
            problemas.append(f"{prefijo}: documento fuera de corpus/: {nombre!r}")
            continue
        if archivo in rutas:
            problemas.append(f"{prefijo}: archivo duplicado: {nombre!r}")
        rutas.add(archivo)
        if not archivo.is_file():
            problemas.append(f"{prefijo}: archivo inexistente: {nombre!r}")
            continue
        if (formato == "docx") != (archivo.suffix.lower() == ".docx"):
            problemas.append(f"{prefijo}: extensión inconsistente con formato {formato!r}")
        if formato.startswith("pdf_") and archivo.suffix.lower() != ".pdf":
            problemas.append(f"{prefijo}: extensión inconsistente con PDF")
        if not re.fullmatch(r"[a-f0-9]{64}", huella):
            problemas.append(f"{prefijo}: sha256 inválido")
        else:
            with archivo.open("rb") as contenido:
                real = hashlib.file_digest(contenido, "sha256").hexdigest()
            if real != huella:
                problemas.append(f"{prefijo}: sha256 no coincide para {nombre!r}")

    for tipo in sorted(CATEGORIAS):
        total_m = contadores[("medicion", tipo)]
        total_a = contadores[("ajuste", tipo)]
        if total_m != 10:
            problemas.append(f"{tipo}: se necesitan 10 de medicion; encontrados {total_m}")
        if not 2 <= total_a <= 3:
            problemas.append(f"{tipo}: se necesitan 2-3 de ajuste; encontrados {total_a}")
        if not (plantillas[tipo]["medicion"] - plantillas[tipo]["ajuste"]):
            problemas.append(f"{tipo}: falta al menos una plantilla exclusiva de medicion")
    if sum(v for (g, _), v in contadores.items() if g == "medicion") != 50:
        problemas.append("El total de medicion debe ser exactamente 50")
    if not 10 <= sum(v for (g, _), v in contadores.items() if g == "ajuste") <= 15:
        problemas.append("El total de ajuste debe estar entre 10 y 15")
    if cantidad_adversariales != 3:
        problemas.append(f"Se necesitan exactamente 3 adversariales medidos; encontrados {cantidad_adversariales}")
    if not {"pdf_digital", "docx"}.issubset(formatos_presentes) or not (formatos_presentes & {"pdf_escaneado", "pdf_fotografiado"}):
        problemas.append("La medicion debe contener PDF digital, DOCX y PDF escaneado/fotografiado")
    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    repo = Path(__file__).resolve().parents[1]
    parser.add_argument("--inventario", type=Path,
                        default=repo / "docs/evaluacion/plantilla_inventario_e90.csv")
    args = parser.parse_args()
    errores = validar_inventario(repo, args.inventario)
    if errores:
        print(f"INCOMPLETO / INVALIDO ({len(errores)} observaciones)")
        for error in errores:
            print(f"- {error}")
        return 1
    print("INVENTARIO VALIDO: 50 medicion, 10-15 ajuste, 3 adversariales, hashes coincidentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
