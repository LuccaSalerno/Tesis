"""Crea el primer administrador operativo. Operación manual del operador.

Uso: `python -m atlas.herramientas.inicializar_administrador --identificador-externo <sub>`

Usa la configuración del proceso (entorno y base). Se niega si ya existe un
administrador; el alta queda auditada y atribuida al sistema. Las demás cuentas
las da de alta el administrador por la API (RF-25).
"""

import argparse
import sys

from atlas.configuracion import obtener_configuracion
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.servicios.cuentas import crear_administrador_inicial
from atlas.servicios.errores import Conflicto


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--identificador-externo", required=True, help="sub de Cognito")
    opciones = analizador.parse_args(argumentos)

    configuracion = obtener_configuracion()
    motor = crear_motor(configuracion)
    try:
        with crear_fabrica_sesiones(motor)() as sesion, sesion.begin():
            cuenta = crear_administrador_inicial(sesion, opciones.identificador_externo)
    except Conflicto as error:
        print(f"No se creó: {error.detalle} (entorno {configuracion.entorno})", file=sys.stderr)
        return 1
    finally:
        motor.dispose()
    print(f"Administrador inicial creado: usuario {cuenta.id} (entorno {configuracion.entorno})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
