"""§6.3.2 nivel B contra la API desplegada (DO-2026-10-23-REC P9, P11). La corre el operador.

Dos escenarios con documentos sintéticos, en una sesión E90A de ensayo:

- **espera:** se suben `limite + 3` documentos a la vez; se registra cuántos quedan «En
  espera» al confirmar y, con consultas cada 30 s, cómo el reconciliador los admite sin que
  haya más de `limite` en curso, hasta que todos terminan. El pico de trabajos simultáneos
  se calcula con los tiempos del servidor de cada trabajo (`ejecucion_iniciada_en` hasta
  `actualizado_en` en estado terminal), además de los sondeos. Los estados devueltos al
  confirmar se registran pero no cuentan para el pico: se toman en instantes distintos
  (campaña e90-confiabilidad-1).
- **fallo:** un DOCX vacío falla de forma definitiva; el responsable pide un intento nuevo,
  que vuelve a fallar sin reintentos indefinidos y sin cambiar el estado del trámite.

El inicio fallido de Step Functions no se puede provocar sin tocar la infraestructura: se
cubre en el nivel A (`tests/test_reconciliador.py`). Se registran estados, intentos y tiempos.

    python -m atlas.evaluacion.confiabilidad --campana <id> --url-api … --cliente-cognito … \\
        --limite 10 [--escenarios espera fallo]
"""

import argparse
import json
import sys
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, Final

from atlas.evaluacion import campana as cmp
from atlas.evaluacion.registro import Registro
from atlas.evaluacion.seguridad import documentos
from atlas.herramientas.cliente_api import ClienteApi, tokens_cognito

ROL: Final = "responsable"
TERMINALES: Final = frozenset({"completado", "fallido"})
ESPERA_MAXIMA_S: Final = 3000.0


def subir(api: ClienteApi, tramite_id: int, nombre: str, datos: bytes) -> dict[str, Any]:
    carga = api.post(
        f"/tramites/{tramite_id}/cargas",
        ROL,
        {"nombre": nombre, "formato": "docx", "tamano_bytes": len(datos)},
    )
    api.transferir(carga["url"], carga["encabezados"], datos)
    archivo: dict[str, Any] = api.post(
        f"/tramites/{tramite_id}/cargas/{carga['id']}/confirmacion", ROL
    )
    return archivo


def observar(
    api: ClienteApi,
    tramite_id: int,
    archivos: list[int],
    registro: Registro,
    escenario: str,
    *,
    dormir: Callable[[float], None] = time.sleep,
    intervalo_s: float = 30.0,
    maximo_s: float = ESPERA_MAXIMA_S,
) -> dict[int, dict[str, Any]]:
    """Consulta los trabajos hasta que todos terminen y registra cada observación."""
    inicio = time.monotonic()
    while True:
        trabajos = {
            a["id"]: a.get("trabajo") or {}
            for a in api.get(f"/tramites/{tramite_id}/archivos", ROL)
            if a["id"] in archivos
        }
        estados = [t.get("estado") for t in trabajos.values()]
        registro.escribir(
            {
                "escenario": escenario,
                "momento": datetime.now(UTC).isoformat(),
                "estados": {str(k): v.get("estado") for k, v in trabajos.items()},
                "en_curso": sum(e in ("pendiente", "en_ejecucion") for e in estados),
                "en_espera": estados.count("en_espera"),
            }
        )
        if all(e in TERMINALES for e in estados):
            return trabajos
        if time.monotonic() - inicio > maximo_s:
            raise RuntimeError(f"trabajos_sin_terminar:{escenario}")
        dormir(intervalo_s)


def pico_simultaneo(trabajos: Iterable[dict[str, Any]]) -> int | None:
    """Máximo de trabajos en ejecución a la vez según los tiempos del servidor. Cada trabajo
    terminado ocupa un cupo desde `ejecucion_iniciada_en` hasta `actualizado_en`; en un
    empate, el que termina libera el cupo antes de que empiece el otro. Sin tiempos del
    servidor no se puede verificar: devuelve None."""
    eventos: list[tuple[datetime, int]] = []
    for trabajo in trabajos:
        inicio = trabajo.get("ejecucion_iniciada_en")
        if trabajo.get("estado") not in TERMINALES or not trabajo.get("actualizado_en"):
            return None
        if inicio:
            eventos += [
                (datetime.fromisoformat(inicio), 1),
                (datetime.fromisoformat(trabajo["actualizado_en"]), -1),
            ]
    actual = pico = 0
    for _, delta in sorted(eventos):
        actual += delta
        pico = max(pico, actual)
    return pico


def escenario_espera(
    api: ClienteApi, limite: int, registro: Registro, **espera: Any
) -> dict[str, Any]:
    tramite = api.post("/tramites", ROL, {"titulo": "Confiabilidad: espera por capacidad"})["id"]
    cantidad = limite + 3
    lotes = [(f"espera-{n}.docx", documentos.contrato(f"CONF{n:03d}")) for n in range(cantidad)]
    with ThreadPoolExecutor(max_workers=cantidad) as hilos:
        confirmados = list(hilos.map(lambda par: subir(api, tramite, *par), lotes))
    al_confirmar = [a["trabajo"]["estado"] for a in confirmados]
    finales = observar(api, tramite, [a["id"] for a in confirmados], registro, "espera", **espera)
    observaciones = [f for f in registro.leer() if f.get("escenario") == "espera"]
    return {
        "documentos": cantidad,
        "en_espera_al_confirmar": al_confirmar.count("en_espera"),
        # Informativo: suma de estados de instantes distintos, no es un pico simultáneo.
        "en_curso_al_confirmar": sum(e in ("pendiente", "en_ejecucion") for e in al_confirmar),
        "max_en_curso_sondeos": max(f["en_curso"] for f in observaciones),
        "max_en_curso_servidor": pico_simultaneo(finales.values()),
        "limite": limite,
        "completados": sum(t.get("estado") == "completado" for t in finales.values()),
        "fallidos": sum(t.get("estado") == "fallido" for t in finales.values()),
    }


def escenario_fallo(api: ClienteApi, registro: Registro, **espera: Any) -> dict[str, Any]:
    tramite = api.post("/tramites", ROL, {"titulo": "Confiabilidad: fallo definitivo"})["id"]
    estado_tramite = api.get(f"/tramites/{tramite}", ROL)["estado"]
    archivo = subir(api, tramite, "vacio.docx", documentos.vacio())
    primero = observar(api, tramite, [archivo["id"]], registro, "fallo", **espera)[archivo["id"]]
    reintento = api.post(f"/tramites/{tramite}/archivos/{archivo['id']}/reintento", ROL)
    segundo = observar(api, tramite, [archivo["id"]], registro, "fallo", **espera)[archivo["id"]]
    return {
        "primer_intento": primero.get("estado"),
        "intento_nuevo": reintento["trabajo"]["intento"],
        "segundo_intento": segundo.get("estado"),
        "tramite_sin_cambios": api.get(f"/tramites/{tramite}", ROL)["estado"] == estado_tramite,
    }


def criterios(resultado: dict[str, Any]) -> dict[str, bool]:
    salida: dict[str, bool] = {}
    if espera := resultado.get("espera"):
        servidor = espera["max_en_curso_servidor"]
        salida["espera_sin_sobreasignacion"] = (
            servidor is not None
            and max(servidor, espera["max_en_curso_sondeos"]) <= espera["limite"]
        )
        salida["espera_admitida_y_terminada"] = (
            espera["completados"] + espera["fallidos"] == espera["documentos"]
        )
        salida["espera_observada"] = espera["en_espera_al_confirmar"] > 0
    if fallo := resultado.get("fallo"):
        salida["fallo_definitivo_sin_reintentos_indefinidos"] = (
            fallo["primer_intento"] == "fallido" and fallo["segundo_intento"] == "fallido"
        )
        salida["intento_nuevo_manual"] = fallo["intento_nuevo"] == 2
        salida["tramite_sin_cambios"] = fallo["tramite_sin_cambios"]
    return salida


def ejecutar(argumentos: argparse.Namespace, api: ClienteApi | None = None, **espera: Any) -> str:
    destino: Path = cmp.RAIZ_REPOSITORIO / "evaluacion" / "campanas" / str(argumentos.campana)
    if destino.exists():
        raise cmp.ErrorCampana("campana_existente")
    destino.mkdir(parents=True)
    if api is None:
        token = tokens_cognito(
            argumentos.region, argumentos.cliente_cognito, {ROL: argumentos.usuario}
        )
        api = ClienteApi(argumentos.url_api, token)
    registro = Registro(destino / "confiabilidad.jsonl")
    resultado: dict[str, Any] = {
        "campana": argumentos.campana,
        "tipo": "confiabilidad",
        "creada_en": datetime.now(UTC).isoformat(),
        **cmp._commit(cmp.RAIZ_REPOSITORIO),
    }
    acciones = {
        "espera": partial(escenario_espera, api, argumentos.limite, registro, **espera),
        "fallo": partial(escenario_fallo, api, registro, **espera),
    }
    for nombre in argumentos.escenarios:
        resultado[nombre] = acciones[nombre]()
    resultado["criterios"] = criterios(resultado)
    (destino / "resultado.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), "utf-8"
    )
    cumplen = sum(resultado["criterios"].values())
    return f"confiabilidad:{cumplen}/{len(resultado['criterios'])}_cumplen"


def analizador() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    raiz.add_argument("--campana", required=True)
    raiz.add_argument("--url-api", required=True)
    raiz.add_argument("--cliente-cognito", required=True)
    raiz.add_argument("--usuario", default="atlas-responsable")
    raiz.add_argument("--region", default="us-east-1")
    raiz.add_argument(
        "--limite", type=int, default=10, help="Límite de concurrencia del despliegue"
    )
    raiz.add_argument(
        "--escenarios", nargs="+", choices=("espera", "fallo"), default=["espera", "fallo"]
    )
    return raiz


def main(argumentos: list[str] | None = None) -> int:
    try:
        print(ejecutar(analizador().parse_args(argumentos)))
    except (cmp.ErrorCampana, RuntimeError, KeyError) as error:
        print(f"Verificación detenida: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
