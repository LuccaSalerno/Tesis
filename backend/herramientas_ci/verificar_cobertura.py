"""Exige una cobertura mínima por módulo, no solo en el total (pedido del equipo, 22/10/2026).

Uso: `python -m herramientas_ci.verificar_cobertura coverage.json --minimo 90`

Lee el informe JSON de coverage.py (`pytest --cov --cov-report=json`). Usa el mismo
porcentaje que informa coverage (líneas y ramas). Falla si algún módulo de `atlas`
queda por debajo del mínimo y lista cuáles. No modifica el umbral según el resultado.
"""

import argparse
import json
import sys
from pathlib import Path


def modulos_bajo_minimo(informe: dict[str, object], minimo: float) -> dict[str, float]:
    archivos = informe.get("files", {})
    if not isinstance(archivos, dict):
        raise ValueError("El informe no tiene el formato JSON de coverage.py")
    bajos = {}
    for ruta, datos in sorted(archivos.items()):
        porcentaje = float(datos["summary"]["percent_covered"])
        if porcentaje < minimo:
            bajos[ruta] = round(porcentaje, 1)
    return bajos


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("informe", type=Path)
    analizador.add_argument("--minimo", type=float, default=90.0)
    opciones = analizador.parse_args(argumentos)

    informe = json.loads(opciones.informe.read_text(encoding="utf-8"))
    bajos = modulos_bajo_minimo(informe, opciones.minimo)
    total = len(informe.get("files", {}))
    if bajos:
        print(f"{len(bajos)} de {total} módulos por debajo del {opciones.minimo:g} %:")
        for ruta, porcentaje in bajos.items():
            print(f"  {porcentaje:5.1f} %  {ruta}")
        return 1
    print(f"Los {total} módulos alcanzan al menos el {opciones.minimo:g} % de cobertura.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
