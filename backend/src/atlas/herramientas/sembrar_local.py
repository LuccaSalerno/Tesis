"""Semilla de **desarrollo local**: la misma semilla de la demo (cadena
de evidencia o, con `--escenario
surdelta`, la cartera SurDelta), contra la API local, con tokens locales y el procesamiento
simulado. Nunca en demo.

Uso, con la API local corriendo (uvicorn) y moto preparado:

    python -m atlas.herramientas.sembrar_local [--url-api http://127.0.0.1:8000]
    python -m atlas.herramientas.sembrar_local --escenario surdelta

Crea (o reutiliza) cuatro cuentas locales, siembra los trámites y muestra los tokens de cada
rol para ingresar a la aplicación web en modo local. Las sugerencias quedan rotuladas como
simulación: sirven para desarrollar y probar, no son evidencia de la IA.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from atlas.autenticacion.claves_locales import CLIENTE_LOCAL, EMISOR_LOCAL, ClavesLocales
from atlas.configuracion import Configuracion, ErrorConfiguracion, obtener_configuracion
from atlas.herramientas import procesar_simulado
from atlas.herramientas.cliente_api import ClienteApi, Transporte, transporte_urllib
from atlas.herramientas.sembrar_demo import (
    ORACULO,
    ORACULO_SURDELTA,
    RAIZ_REPOSITORIO,
    Manifiesto,
    Sembrador,
    SembradorSurDelta,
    verificar_corpus,
    verificar_corpus_surdelta,
)
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.servicios import cuentas
from atlas.servicios.errores import Conflicto

SUBS: Final = {
    "administrador": "local-administrador",
    "responsable": "local-responsable",
    "revisor": "local-revisor",
    "aprobador": "local-aprobador",
}
VIGENCIA_TOKENS_S: Final = 8 * 3600


def sub_administrador(configuracion: Configuracion) -> str:
    """Crea el administrador local si no hay ninguno; si ya hay uno habilitado (por ejemplo,
    de un desarrollo anterior), la semilla actúa con esa misma identidad, sin crear otro."""
    motor = crear_motor(configuracion)
    try:
        with crear_fabrica_sesiones(motor)() as sesion, sesion.begin():
            try:
                cuentas.crear_administrador_inicial(sesion, SUBS["administrador"])
                return SUBS["administrador"]
            except Conflicto:
                existentes = [
                    c
                    for c in cuentas.listar(sesion)
                    if "administrador_operativo" in c.roles
                    and c.estado == "habilitada"
                    and c.identificador_externo
                ]
                if not existentes:
                    raise ErrorConfiguracion("No hay un administrador habilitado") from None
                return str(existentes[0].identificador_externo)
    finally:
        motor.dispose()


def claves_locales(directorio: Path) -> ClavesLocales:
    if not (directorio / "privada.pem").exists():
        ClavesLocales.generar().guardar(directorio)
    return ClavesLocales.cargar(directorio)


def tokens_locales(claves: ClavesLocales, sub_admin: str) -> dict[str, str]:
    return {
        rol: claves.emitir(
            sub, emisor=EMISOR_LOCAL, cliente=CLIENTE_LOCAL, vigencia_s=VIGENCIA_TOKENS_S
        )
        for rol, sub in {**SUBS, "administrador": sub_admin}.items()
    }


def sembrar(
    configuracion: Configuracion,
    url_api: str,
    claves: ClavesLocales,
    transporte: Transporte = transporte_urllib,
    escenario: str = "cadena",
) -> tuple[Manifiesto, dict[str, str]]:
    procesar_simulado.verificar_entorno(configuracion)
    tokens = tokens_locales(claves, sub_administrador(configuracion))
    surdelta = escenario == "surdelta"
    oraculo = json.loads((ORACULO_SURDELTA if surdelta else ORACULO).read_text(encoding="utf-8"))
    manifiesto = Manifiesto(
        sesion=f"local-{datetime.now(UTC):%Y%m%d-%H%M%S}",
        url_api=url_api,
        oraculo=f"{oraculo['id']} ({oraculo['estado']}) — procesamiento SIMULADO",
        corpus=verificar_corpus_surdelta(oraculo) if surdelta else verificar_corpus(oraculo),
    )

    def esperar(_: ClienteApi, __: int, archivos: list[int]) -> None:
        for archivo in archivos:
            procesar_simulado.procesar(configuracion, archivo)

    clase = SembradorSurDelta if surdelta else Sembrador
    clase(ClienteApi(url_api, tokens, transporte), manifiesto, oraculo, esperar).ejecutar()
    return manifiesto, tokens


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--url-api", default="http://127.0.0.1:8000")
    analizador.add_argument("--claves", type=Path, default=Path(".claves_locales"))
    analizador.add_argument(
        "--escenario",
        choices=("cadena", "surdelta"),
        default="cadena",
        help="cadena de evidencia (predeterminado) o la cartera SurDelta",
    )
    opciones = analizador.parse_args(argumentos)
    try:
        configuracion = obtener_configuracion()
        procesar_simulado.verificar_entorno(configuracion)
        manifiesto, tokens = sembrar(
            configuracion,
            opciones.url_api,
            claves_locales(opciones.claves),
            transporte_urllib,
            opciones.escenario,
        )
    except ErrorConfiguracion as error:
        print(f"No se sembró: {error}", file=sys.stderr)
        return 1
    destino = (
        RAIZ_REPOSITORIO / "operaciones" / "sesiones" / manifiesto.sesion / "manifiesto_seed.json"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(manifiesto.__dict__, indent=2, ensure_ascii=False) + "\n")
    print(f"Semilla LOCAL (simulada) en {destino}")
    for rol, token in tokens.items():
        print(f"\n[{rol}] token para ingresar en modo local (vence en 8 h):\n{token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
