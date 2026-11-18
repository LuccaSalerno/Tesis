"""Exportación de evidencia saneada de una sesión, por la API.

Uso (operador, con la API en `active` o `draining`, antes de retirar la sesión):

    ATLAS_SEED_CLAVE_RESPONSABLE=… python -m atlas.herramientas.exportar_evidencia \\
        --manifiesto operaciones/sesiones/<sesion>/manifiesto_seed.json \\
        --cliente-cognito <id> --usuario-responsable … \\
        --salida operaciones/sesiones/<sesion>/evidencia

Guarda, por trámite del manifiesto, las respuestas de la API (detalle, archivos, sugerencias,
validaciones, vínculos, controles con historial, ciclos, línea de tiempo, la evidencia de
cada decisión y la firma) como JSON, más un índice con la huella SHA-256 de cada archivo.
Los archivos, documentos, decisiones y la firma se descubren en la API, no solo en el
manifiesto: así queda lo que las personas hicieron después de la semilla (por ejemplo, el
recorrido en vivo de la demo). También se exportan los trámites reemplazados del manifiesto
y los que se indiquen con `--tramites-adicionales`. Los datos son sintéticos; no se
exportan tokens ni contraseñas. Se conserva fuera de AWS.
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atlas.herramientas.cliente_api import ClienteApi, ErrorApi, tokens_cognito


def _escribir(salida: Path, nombre: str, datos: Any, indice: dict[str, str]) -> None:
    contenido = (json.dumps(datos, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()
    ruta = salida / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    indice[nombre] = hashlib.sha256(contenido).hexdigest()


def _con_nombre(conocidos: dict[str, int], encontrados: list[int], prefijo: str) -> dict[str, int]:
    """Los del manifiesto conservan su código (C-v1, O-v2…); los demás, `<prefijo>-<id>`."""
    nombres = {i: codigo for codigo, i in conocidos.items()}
    return {
        nombres.get(i, f"{prefijo}-{i}"): i for i in sorted({*conocidos.values(), *encontrados})
    }


def exportar_tramite(
    cliente: ClienteApi, salida: Path, clave: str, registro: dict[str, Any], indice: dict[str, str]
) -> None:
    rol = "responsable"
    t = registro["id"]
    base = f"tramites/{clave}-{t}"
    detalle = cliente.get(f"/tramites/{t}", rol)
    _escribir(salida, f"{base}/tramite.json", detalle, indice)
    archivos = cliente.get(f"/tramites/{t}/archivos", rol)
    _escribir(salida, f"{base}/archivos.json", archivos, indice)
    ciclos = cliente.get(f"/tramites/{t}/ciclos", rol)
    _escribir(salida, f"{base}/ciclos.json", ciclos, indice)
    consultas = {
        "vinculos": f"/tramites/{t}/vinculos?historial=true",
        "controles": f"/tramites/{t}/controles?historial=true",
        "linea_tiempo": f"/tramites/{t}/linea-tiempo",
    }
    for nombre, ruta in consultas.items():
        _escribir(salida, f"{base}/{nombre}.json", cliente.get(ruta, rol), indice)
    for codigo, archivo_id in _con_nombre(
        registro.get("archivos", {}), [a["id"] for a in archivos], "archivo"
    ).items():
        _escribir(
            salida,
            f"{base}/sugerencias/{codigo}.json",
            cliente.get(f"/tramites/{t}/archivos/{archivo_id}/sugerencias", rol),
            indice,
        )
    for codigo, documento_id in _con_nombre(
        registro.get("documentos", {}), [d["id"] for d in detalle["documentos"]], "documento"
    ).items():
        _escribir(
            salida,
            f"{base}/validaciones/{codigo}.json",
            cliente.get(f"/tramites/{t}/documentos/{documento_id}/validaciones", rol),
            indice,
        )
    if "firma" in registro or detalle["estado"] == "cerrado":  # RF-23, V11
        _escribir(salida, f"{base}/firma.json", cliente.get(f"/tramites/{t}/firma", rol), indice)
    decisiones = {
        *registro.get("decisiones", []),
        *registro.get("decisiones_2", []),
        *(
            tarea["decision_id"]
            for ciclo in ciclos
            for tarea in ciclo["tareas"]
            if tarea["decision_id"] is not None
        ),
    }
    for decision_id in sorted(decisiones):
        _escribir(
            salida,
            f"{base}/evidencia/decision-{decision_id}.json",
            cliente.get(f"/decisiones/{decision_id}/evidencia", rol),
            indice,
        )


def exportar(
    cliente: ClienteApi,
    manifiesto: dict[str, Any],
    salida: Path,
    adicionales: list[int] | None = None,
) -> dict[str, Any]:
    salida.mkdir(parents=True, exist_ok=True)
    indice: dict[str, str] = {}
    tramites = [
        *manifiesto["tramites"].items(),
        *(("reemplazado", r) for r in manifiesto.get("reemplazados", [])),
        *(("adicional", {"id": t}) for t in adicionales or []),
    ]
    for clave, registro in tramites:
        exportar_tramite(cliente, salida, clave, registro, indice)
    resumen = {
        "sesion": manifiesto["sesion"],
        "exportado_en": datetime.now(UTC).isoformat(),
        "oraculo": manifiesto["oraculo"],
        "corpus": manifiesto["corpus"],
        "tramites_adicionales": adicionales or [],
        "archivos": dict(sorted(indice.items())),
    }
    (salida / "indice.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False) + "\n")
    return resumen


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--manifiesto", required=True, type=Path)
    analizador.add_argument("--salida", required=True, type=Path)
    analizador.add_argument("--region", default="us-east-1")
    analizador.add_argument("--cliente-cognito", required=True)
    analizador.add_argument("--usuario-responsable", required=True)
    analizador.add_argument(
        "--tramites-adicionales",
        nargs="*",
        type=int,
        default=[],
        help="Trámites fuera del manifiesto, por ejemplo los creados en la demo",
    )
    opciones = analizador.parse_args(argumentos)
    if opciones.salida.exists() and any(opciones.salida.iterdir()):
        print("La carpeta de salida no está vacía: no se sobrescribe evidencia", file=sys.stderr)
        return 1
    manifiesto = json.loads(opciones.manifiesto.read_text(encoding="utf-8"))
    tokens = tokens_cognito(
        opciones.region, opciones.cliente_cognito, {"responsable": opciones.usuario_responsable}
    )
    try:
        resumen = exportar(
            ClienteApi(manifiesto["url_api"], tokens),
            manifiesto,
            opciones.salida,
            opciones.tramites_adicionales,
        )
    except ErrorApi as error:
        print(f"Exportación incompleta: {error}. No retirar la sesión.", file=sys.stderr)
        return 1
    print(f"Evidencia exportada: {len(resumen['archivos'])} archivos en {opciones.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
