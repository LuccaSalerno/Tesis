"""Emite un token de acceso local para desarrollo. Nunca en demo.

Uso: `python -m atlas.herramientas.token_local --sub <sub> [--directorio .claves_locales]`

La primera vez genera un par de claves en el directorio (no versionado) y el
JWKS que el servidor local lee con ATLAS_JWT_JWKS_ARCHIVO. El token se imprime
en la salida estándar para usarlo como `Authorization: Bearer <token>`.
"""

import argparse
import sys
from pathlib import Path

from atlas.autenticacion.claves_locales import CLIENTE_LOCAL, EMISOR_LOCAL, ClavesLocales
from atlas.configuracion import obtener_configuracion


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--sub", required=True)
    analizador.add_argument("--directorio", type=Path, default=Path(".claves_locales"))
    analizador.add_argument("--vigencia-s", type=int, default=3600)
    opciones = analizador.parse_args(argumentos)

    if obtener_configuracion().entorno == "demo":
        print("Los tokens locales no se admiten en el entorno demo", file=sys.stderr)
        return 1
    directorio: Path = opciones.directorio
    if (directorio / "privada.pem").exists():
        claves = ClavesLocales.cargar(directorio)
    else:
        ruta = ClavesLocales.generar().guardar(directorio)
        print(f"Claves locales generadas; JWKS en {ruta}", file=sys.stderr)
        claves = ClavesLocales.cargar(directorio)
    print(
        claves.emitir(
            opciones.sub,
            emisor=EMISOR_LOCAL,
            cliente=CLIENTE_LOCAL,
            vigencia_s=opciones.vigencia_s,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
