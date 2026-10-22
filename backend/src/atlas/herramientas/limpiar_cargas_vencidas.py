"""Limpia las cargas temporales vencidas (DO-2026-10-22-CARGAS). Operación del operador.

Uso: `python -m atlas.herramientas.limpiar_cargas_vencidas [--lote 100]`

Usa la configuración del proceso. Es idempotente: se puede repetir sin efectos
adicionales. En AWS su ejecución programada requiere IaC y aprobación aparte;
la regla de S3 Lifecycle de 2 días actúa como respaldo.
"""

import argparse
import sys

from atlas.configuracion import obtener_configuracion
from atlas.integraciones.aws import AlmacenS3, crear_cliente
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.servicios.cargas import limpiar_cargas_vencidas


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--lote", type=int, default=100)
    opciones = analizador.parse_args(argumentos)

    configuracion = obtener_configuracion()
    almacen = AlmacenS3(
        crear_cliente(configuracion, "s3"), configuracion.s3_bucket_documentos or ""
    )
    motor = crear_motor(configuracion)
    try:
        with crear_fabrica_sesiones(motor)() as sesion:
            resumen = limpiar_cargas_vencidas(
                sesion,
                almacen,
                vigencia_pendiente_s=configuracion.carga_vigencia_pendiente_s,
                lote=opciones.lote,
            )
    finally:
        motor.dispose()
    print(
        f"Revisadas {resumen.revisadas}, vencidas {resumen.vencidas}, "
        f"objetos limpiados {resumen.objetos_limpiados} "
        f"({resumen.versiones_eliminadas} versiones), "
        f"multipartes abortadas {resumen.multipartes_abortadas}, diferidas {resumen.diferidas}, "
        f"errores {len(resumen.errores)} (entorno {configuracion.entorno})"
    )
    return 1 if resumen.errores else 0


if __name__ == "__main__":
    sys.exit(main())
