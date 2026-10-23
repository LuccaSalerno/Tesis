"""Congelación de la candidata revisada por los autores (DO-2026-10-23-E90-CONGELACION).

Se ejecuta una sola vez, sobre una candidata que valida sin errores: marca los oráculos de
campos, fragmentos y consultas como congelados, con la revisión por muestreo de los autores
(DO-2026-10-23-E90-MUESTREO), y escribe `oraculos/e90/congelamiento.json` con las huellas
de todo lo que la medición usa. No modifica documentos, registros ni el inventario.

    python -m herramientas.corpus_e90.congelar --fecha 2026-10-23 \\
        --autores "Ivo Gonsé" "Lucca Salerno" --commit-datos <commit>
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .comun import ESTADO_CONGELADO, ORACULOS_CONGELABLES, VERSION, escribir_json, leer_json
from .validar import huellas_congeladas, validar

DECISION = "DO-2026-10-23-E90-CONGELACION"
DECISION_MUESTREO = "DO-2026-10-23-E90-MUESTREO"
REGISTRO_REVISION = "docs/evaluacion/corpus_e90/Revision_Autores_Muestreo_V3.md"
# Parte 3 del muestreo: los campos de estos documentos se cotejaron contra el original.
DOCUMENTOS_REVISADOS = (
    "E90-M-PRE-05",
    "E90-M-PRE-09",
    "E90-M-OC-01",
    "E90-M-PRE-06",
    "E90-M-OC-02",
    "E90-M-CTR-06",
    "E90-M-CTR-08",
    "E90-M-FAC-10",
    "E90-M-FAC-02",
    "E90-A-PRE-03",
)
# Parte 2: la clase esperada de los casos difíciles (sin cotejo de campos).
CASOS_DIFICILES = (
    "E90-M-CTR-10",
    "E90-M-FAC-06",
    "E90-M-COM-08",
    "E90-M-PRE-07",
    "E90-M-OC-07",
    "E90-M-FAC-08",
)
ARCHIVOS = {
    "campos": "campos_candidatos.json",
    "fragmentos": "fragmentos_candidatos.json",
    "consultas": "consultas_candidatas.json",
}
CLAVES = {"campos": "campos", "fragmentos": "fragmentos", "consultas": "consultas"}


def revision(fecha: str, autores: list[str], commit_datos: str) -> dict:
    return {
        "modalidad": "muestreo",
        "decision": DECISION_MUESTREO,
        "registro": REGISTRO_REVISION,
        "fecha": fecha,
        "autores": autores,
        "commit_datos": commit_datos,
        "consultas": [f"Q{i:02d}" for i in range(1, 31)],
        "casos_dificiles": list(CASOS_DIFICILES),
        "documentos": list(DOCUMENTOS_REVISADOS),
        "alcance_restante": "Validado con controles automáticos y con la revisión de contraste "
        "de otro agente sobre 25 documentos; se declara como limitación en §6.6.",
    }


def congelar(root: Path, *, fecha: str, autores: list[str], commit_datos: str) -> dict:
    carpeta = root / "oraculos/e90"
    if (carpeta / "congelamiento.json").exists():
        raise ValueError("e90_ya_congelado")
    if len(autores) != 2:
        raise ValueError("e90_congelar_exige_ambos_autores")
    errores = validar(root)
    if errores:
        raise ValueError("e90_candidata_con_errores:" + ",".join(errores[:5]))
    datos_revision = revision(fecha, autores, commit_datos)
    revisados = {
        "consultas": set(datos_revision["consultas"]),
        "campos": set(datos_revision["documentos"]),
        "fragmentos": set(),
    }
    for nombre in ORACULOS_CONGELABLES:
        ruta = carpeta / ARCHIVOS[nombre]
        oraculo = leer_json(ruta)
        oraculo["estado"] = ESTADO_CONGELADO
        oraculo["revisado_por_autores"] = True
        oraculo["revision_autores"] = datos_revision
        for elemento in oraculo[CLAVES[nombre]]:
            clave = elemento["pregunta_id"] if nombre == "consultas" else elemento["doc_id"]
            elemento["estado"] = ESTADO_CONGELADO
            elemento["revisado_por_autores"] = clave in revisados[nombre]
        escribir_json(ruta, oraculo)
    registro = {
        "decision": DECISION,
        "version": VERSION,
        "estado": ESTADO_CONGELADO,
        "fecha": fecha,
        "autores": autores,
        "revision": datos_revision,
        "sha256": huellas_congeladas(root),
    }
    escribir_json(carpeta / "congelamiento.json", registro)
    errores = validar(root)
    if errores:
        raise ValueError("e90_congelado_no_valida:" + ",".join(errores[:5]))
    return registro


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--fecha", required=True)
    parser.add_argument("--autores", nargs=2, required=True)
    parser.add_argument("--commit-datos", required=True)
    args = parser.parse_args()
    registro = congelar(
        args.raiz.resolve(),
        fecha=args.fecha,
        autores=list(args.autores),
        commit_datos=args.commit_datos,
    )
    print(f"CORPUS_CONGELADO version={registro['version']} archivos={len(registro['sha256'])}")


if __name__ == "__main__":
    main()
