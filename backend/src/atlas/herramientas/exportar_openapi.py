"""Exporta el contrato OpenAPI de la API para la aplicación web (DO-2026-10-22-WEB F2).

Uso: `python -m atlas.herramientas.exportar_openapi ../frontend/openapi.json`

Luego, en `frontend/`: `npm run tipos` regenera `src/api/esquema.ts`. Una prueba verifica
que el archivo versionado coincide con el contrato del código.
"""

import json
import sys
from pathlib import Path

from atlas.principal import esquema_openapi


def contenido() -> str:
    return json.dumps(esquema_openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main(argumentos: list[str] | None = None) -> int:
    destino = Path((argumentos or sys.argv[1:])[0])
    destino.write_text(contenido(), encoding="utf-8")
    print(f"Contrato OpenAPI exportado en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
