"""Planillas de calificación de las respuestas por los autores (IA-M06, P14, RC-P06.2.7).

Cada respuesta distinta (misma pregunta, afirmaciones, citas y motivo) aparece una sola vez,
con la lista de modelos y repeticiones que la produjeron. Cada autor completa su planilla por
separado; `discrepancias` lista los grupos en que difieren y `consolidar` aplica el consenso
sin sobrescribir las calificaciones individuales. No hay juez automático.
"""

import csv
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from atlas.evaluacion.oraculos import Consulta
from atlas.evaluacion.recuperacion import Indice

CALIFICACIONES: Final = frozenset(
    {"correcta", "parcial", "incorrecta", "abstencion_correcta", "abstencion_incorrecta"}
)
COLUMNAS: Final = (
    "grupo",
    "pregunta_id",
    "clase",
    "pregunta",
    "afirmaciones_esperadas",
    "respuesta",
    "citas",
    "motivo",
    "ocurrencias",
    "calificacion",
    "afirmaciones_sustantivas",
    "afirmaciones_respaldadas",
    "observaciones",
)
A_COMPLETAR: Final = ("calificacion", "afirmaciones_sustantivas", "afirmaciones_respaldadas")


def _grupo(fila: dict[str, Any]) -> str:
    clave = json.dumps(
        [fila["pregunta_id"], fila["afirmaciones"], fila["motivo"], fila["error"]],
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(clave.encode()).hexdigest()[:12]


def generar_planilla(
    filas: Sequence[dict[str, Any]], consultas: Sequence[Consulta], indice: Indice, ruta: Path
) -> int:
    """Escribe la planilla en blanco; devuelve la cantidad de grupos."""
    por_id = {c.pregunta_id: c for c in consultas}
    textos = {c.chunk_id: c for c in indice.chunks}
    grupos: dict[str, dict[str, Any]] = {}
    for fila in sorted(filas, key=lambda f: (f["pregunta_id"], f["modelo"], f["repeticion"])):
        clave = _grupo(fila)
        consulta = por_id[fila["pregunta_id"]]
        if clave not in grupos:
            afirmaciones = fila["afirmaciones"] or []
            citadas = dict.fromkeys(c for a in afirmaciones for c in a["citas"])
            grupos[clave] = {
                "grupo": clave,
                "pregunta_id": consulta.pregunta_id,
                "clase": consulta.clase,
                "pregunta": consulta.pregunta,
                "afirmaciones_esperadas": " | ".join(consulta.afirmaciones_esperadas)
                or (consulta.motivo_abstencion or ""),
                "respuesta": " | ".join(
                    f"{a['texto']} [{', '.join(a['citas'])}]" for a in afirmaciones
                ),
                "citas": "\n\n".join(
                    f"[{c}] (p. {textos[c].pagina}) {textos[c].texto}" for c in citadas
                ),
                "motivo": fila["error"] or fila["motivo"] or "",
                "ocurrencias": [],
                **dict.fromkeys(A_COMPLETAR, ""),
                "observaciones": "",
            }
        grupos[clave]["ocurrencias"].append(f"{fila['modelo']}:{fila['repeticion']}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for grupo in grupos.values():
            escritor.writerow(grupo | {"ocurrencias": " ".join(grupo["ocurrencias"])})
    return len(grupos)


def leer_planilla(ruta: Path) -> dict[str, dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        filas = {f["grupo"]: f for f in csv.DictReader(archivo)}
    for fila in filas.values():
        if fila["calificacion"] not in CALIFICACIONES:
            raise ValueError(f"calificacion_invalida:{ruta.name}:{fila['grupo']}")
        for columna in ("afirmaciones_sustantivas", "afirmaciones_respaldadas"):
            if fila[columna] and not fila[columna].isdigit():
                raise ValueError(f"conteo_invalido:{ruta.name}:{fila['grupo']}")
    return filas


def _juicio(fila: dict[str, str]) -> tuple[str, str, str]:
    return tuple(fila[c] for c in A_COMPLETAR)  # type: ignore[return-value]


def discrepancias(autor_a: Path, autor_b: Path, ruta: Path) -> int:
    """Escribe los grupos con juicios distintos, para el consenso; devuelve cuántos son."""
    a, b = leer_planilla(autor_a), leer_planilla(autor_b)
    if set(a) != set(b):
        raise ValueError("planillas_con_grupos_distintos")
    distintos = [g for g in a if _juicio(a[g]) != _juicio(b[g])]
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for grupo in distintos:
            escritor.writerow(
                a[grupo]
                | dict.fromkeys(A_COMPLETAR, "")
                | {
                    "observaciones": f"autor A: {'/'.join(_juicio(a[grupo]))}; "
                    f"autor B: {'/'.join(_juicio(b[grupo]))}"
                }
            )
    return len(distintos)


def consolidar(
    autor_a: Path, autor_b: Path, consenso: Path | None
) -> tuple[dict[tuple[str, int], list[dict[str, Any]]], dict[str, Any]]:
    """Devuelve las calificaciones finales por (modelo, repetición) y el acuerdo observado."""
    a, b = leer_planilla(autor_a), leer_planilla(autor_b)
    acordados = {g for g in a if _juicio(a[g]) == _juicio(b[g])}
    resueltos = leer_planilla(consenso) if consenso else {}
    faltantes = sorted(set(a) - acordados - set(resueltos))
    if faltantes:
        raise ValueError(f"discrepancias_sin_consenso:{len(faltantes)}")
    finales: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for grupo, fila in a.items():
        final = fila if grupo in acordados else resueltos[grupo]
        for ocurrencia in fila["ocurrencias"].split():
            modelo, repeticion = ocurrencia.rsplit(":", 1)
            finales.setdefault((modelo, int(repeticion)), []).append(
                {
                    "pregunta_id": fila["pregunta_id"],
                    "calificacion": final["calificacion"],
                    "afirmaciones_sustantivas": final["afirmaciones_sustantivas"] or 0,
                    "afirmaciones_respaldadas": final["afirmaciones_respaldadas"] or 0,
                }
            )
    acuerdo = {
        "grupos": len(a),
        "acuerdos": len(acordados),
        "proporcion": len(acordados) / len(a) if a else None,
    }
    return finales, acuerdo
