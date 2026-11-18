"""Verificación de seguridad en una sesión AWS (nivel B). La corre el operador.

Pasos sobre `evaluacion/campanas/<id>/`:

    iniciar → escenario → matriz → configuracion → marcadores → informe

Requiere la sesión E90A en `active` y siete cuentas ficticias de Cognito; la clave de cada
una sale de `ATLAS_SEED_CLAVE_<CUENTA>` (RESPONSABLE, RESPONSABLE_2, REVISOR, REVISOR_2,
APROBADOR, ADMINISTRADOR, DESHABILITADA). Agrega trámites y cuentas a la sesión: correrla en
una sesión de ensayo, no antes de una demo.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from atlas.evaluacion import campana as cmp
from atlas.evaluacion.http import Envio, envio_urllib, medir
from atlas.evaluacion.seguridad import aws, matriz
from atlas.evaluacion.seguridad import escenario as esc
from atlas.herramientas.cliente_api import ClienteApi, tokens_cognito

DIRECTORIO: Final = cmp.RAIZ_REPOSITORIO / "evaluacion" / "campanas"
CUENTAS: Final = {
    esc.DUENO: ("responsable", "atlas-responsable"),
    esc.AJENO: ("responsable_2", "atlas-responsable-2"),
    esc.REVISOR: ("revisor", "atlas-revisor"),
    esc.REVISOR_SIN_TAREA: ("revisor_2", "atlas-revisor-2"),
    esc.APROBADOR: ("aprobador", "atlas-aprobador"),
    esc.ADMINISTRADOR: ("administrador", "atlas-admin"),
    esc.DESHABILITADA: ("deshabilitada", "atlas-deshabilitada"),
}


class Entorno:
    """Dependencias externas, reemplazables en las pruebas."""

    def __init__(self) -> None:
        self.envio: Envio = envio_urllib
        self.esperar: esc.Esperar | None = esc.esperar_trabajo

    def tokens(self, m: dict[str, Any]) -> dict[str, str | None]:
        por_clave = tokens_cognito(m["region"], m["cliente_cognito"], dict(CUENTAS.values()))
        salida: dict[str, str | None] = {a: por_clave[c] for a, (c, _) in CUENTAS.items()}
        return salida | {esc.SIN_TOKEN: None}

    def api(self, m: dict[str, Any], tokens: dict[str, str | None]) -> ClienteApi:
        return ClienteApi(m["url_api"], {k: v for k, v in tokens.items() if v})

    def cliente_aws(self, servicio: str, region: str) -> Any:
        from atlas.integraciones.aws import crear_cliente_region

        return crear_cliente_region(servicio, region)


def _solicitar(envio: Envio, url_api: str) -> matriz.Solicitar:
    base = url_api.rstrip("/")

    def solicitar(metodo: str, ruta: str, token: str | None, cuerpo: Any) -> tuple[int, str]:
        medida = medir(envio, metodo, base + ruta, token, cuerpo)
        texto = json.dumps(medida.cuerpo, ensure_ascii=False) if medida.cuerpo is not None else ""
        return medida.estado, texto

    return solicitar


def _escribir(ruta: Path, datos: Any) -> None:
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), "utf-8")


def _leer(ruta: Path) -> Any:
    return json.loads(ruta.read_text("utf-8"))


def ejecutar(argumentos: argparse.Namespace, entorno: Entorno) -> str:
    destino: Path = DIRECTORIO / str(argumentos.campana)
    if argumentos.paso == "iniciar":
        if destino.exists():
            raise cmp.ErrorCampana("campana_existente")
        destino.mkdir(parents=True)
        _escribir(
            destino / "manifiesto.json",
            {
                "campana": argumentos.campana,
                "tipo": "seguridad",
                "creada_en": datetime.now(UTC).isoformat(),
                **cmp._commit(cmp.RAIZ_REPOSITORIO),
                "url_api": argumentos.url_api,
                "cliente_cognito": argumentos.cliente_cognito,
                "region": argumentos.region,
                "prefijo": argumentos.prefijo,
                "bucket": argumentos.bucket,
                "rds": argumentos.rds,
                "maquina": argumentos.maquina,
            },
        )
        return f"campana_creada:{destino}"
    m = _leer(destino / "manifiesto.json")
    if m.get("tipo") != "seguridad":
        raise cmp.ErrorCampana("no_es_campana_de_seguridad")
    ruta_escenario = destino / "escenario.json"

    if argumentos.paso == "escenario":
        if ruta_escenario.exists():
            raise cmp.ErrorCampana("escenario_existente")
        armado = esc.construir(entorno.api(m, entorno.tokens(m)), esperar=entorno.esperar)
        _escribir(ruta_escenario, armado.__dict__)
        return f"escenario_armado:{len(armado.ids)}_identificadores"
    if argumentos.paso == "matriz":
        datos = _leer(ruta_escenario)
        escenario = esc.Escenario(**datos)
        ejecucion = matriz.Ejecucion(
            _solicitar(entorno.envio, m["url_api"]), entorno.tokens(m), escenario
        )
        filas = ejecucion.todo()
        _escribir(destino / "seguridad.json", filas)
        resultado = matriz.resumen(filas)
        return f"matriz:{resultado['cumplen']}/{resultado['casos']}_cumplen"
    if argumentos.paso == "configuracion":
        verificaciones = aws.configuracion(
            lambda s: entorno.cliente_aws(s, m["region"]),
            prefijo=m["prefijo"],
            bucket=m["bucket"],
            rds=m["rds"],
        )
        _escribir(destino / "configuracion.json", verificaciones)
        cumplen = sum(v["cumple"] for v in verificaciones)
        return f"configuracion:{cumplen}/{len(verificaciones)}_cumplen"
    if argumentos.paso == "marcadores":
        escenario_datos = _leer(ruta_escenario)
        verificaciones = aws.buscar_marcadores(
            lambda s: entorno.cliente_aws(s, m["region"]),
            prefijo=m["prefijo"],
            maquina_arn=m["maquina"],
            marcadores=escenario_datos["marcadores"].values(),
            desde=datetime.fromisoformat(m["creada_en"]),
        )
        _escribir(destino / "marcadores.json", verificaciones)
        return (
            f"marcadores:{sum(v['cumple'] for v in verificaciones)}/{len(verificaciones)}_cumplen"
        )
    informe = _informe(destino)
    (destino / "informe.md").write_text(informe, "utf-8")
    return f"informe_listo:{destino / 'informe.md'}"


def _informe(destino: Path) -> str:
    lineas = [f"# Verificación de seguridad {destino.name} (§6.3.3)", ""]
    if (destino / "seguridad.json").exists():
        resultado = matriz.resumen(_leer(destino / "seguridad.json"))
        estado = "Cumple" if resultado["cumple"] else "No cumple"
        lineas += [
            f"## SEG-01, SEG-03 y RNF-08: {estado}",
            "",
            f"{resultado['cumplen']} de {resultado['casos']} casos con el resultado esperado.",
            "No implementadas (no se cuentan como cumplidas): "
            f"{', '.join(resultado['no_implementadas']) or 'ninguna'}.",
            "",
        ]
        for falla in resultado["fallas"]:
            lineas.append(
                f"- **{falla['caso']}** {falla['operacion']} — {falla.get('actor')}: "
                f"esperado {falla.get('esperado', '—')}, obtenido {falla.get('obtenido', '—')}"
            )
        lineas.append("")
    for archivo, titulo in (
        ("configuracion.json", "SEG-02 — configuración"),
        ("marcadores.json", "SEG-04 — registros"),
    ):
        if (destino / archivo).exists():
            verificaciones = _leer(destino / archivo)
            lineas += [
                f"## {titulo}",
                "",
                "| Verificación | Resultado | Detalle |",
                "|---|---|---|",
            ]
            lineas += [
                f"| {v['verificacion']} | {'Cumple' if v['cumple'] else 'No cumple'} "
                f"| {v['detalle']} |"
                for v in verificaciones
            ]
            lineas.append("")
    return "\n".join(lineas)


def analizador() -> argparse.ArgumentParser:
    raiz = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    pasos = raiz.add_subparsers(dest="paso", required=True)
    nuevo = pasos.add_parser("iniciar")
    nuevo.add_argument("--campana", required=True)
    nuevo.add_argument("--url-api", required=True)
    nuevo.add_argument("--cliente-cognito", required=True)
    nuevo.add_argument("--region", default="us-east-1")
    nuevo.add_argument("--prefijo", default="atlas-demo")
    nuevo.add_argument("--bucket", required=True)
    nuevo.add_argument("--rds", default="atlas-demo-postgres")
    nuevo.add_argument("--maquina", required=True, help="ARN de la máquina de procesamiento")
    for paso in ("escenario", "matriz", "configuracion", "marcadores", "informe"):
        pasos.add_parser(paso).add_argument("--campana", required=True)
    return raiz


def main(argumentos: list[str] | None = None, entorno: Entorno | None = None) -> int:
    try:
        print(ejecutar(analizador().parse_args(argumentos), entorno or Entorno()))
    except (cmp.ErrorCampana, ValueError, RuntimeError, KeyError) as error:
        print(f"Verificación detenida: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
