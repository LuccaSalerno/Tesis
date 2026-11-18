"""Lambda del reconciliador, invocada por EventBridge Scheduler cada 5 minutos.

Fuera de `active` no actúa: durante el mantenimiento no se
admiten trabajos nuevos y, al volver a `active`, los pendientes se recuperan en orden
. La respuesta y los registros llevan solo conteos e identificadores.
"""

from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from atlas.configuracion import Configuracion, obtener_configuracion
from atlas.integraciones.aws import OrquestadorStepFunctions, crear_cliente
from atlas.operacion.mantenimiento import EstadoOperativo, LectorMantenimiento
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.registro import configurar_registro
from atlas.servicios import reconciliacion


@lru_cache(maxsize=1)
def _dependencias() -> tuple[Configuracion, sessionmaker[Session], Any, LectorMantenimiento]:
    configuracion = obtener_configuracion()
    configurar_registro(configuracion.nivel_registro)
    orquestador = OrquestadorStepFunctions(
        crear_cliente(configuracion, "stepfunctions"),
        configuracion.sfn_maquina_procesamiento_arn or "",
    )
    lector = (
        LectorMantenimiento.desde_s3(
            crear_cliente(configuracion, "s3"),
            configuracion.s3_bucket_documentos or "",
            configuracion.mantenimiento_cache_s,
        )
        if configuracion.mantenimiento_fuente == "s3"
        else LectorMantenimiento.fijo_active()
    )
    return configuracion, crear_fabrica_sesiones(crear_motor(configuracion)), orquestador, lector


def manejar(_evento: dict[str, Any], _contexto: Any) -> dict[str, Any]:
    configuracion, fabrica, orquestador, lector = _dependencias()
    operacion = lector.estado()
    if operacion != EstadoOperativo.ACTIVE:
        return {
            "resultado": "omitido",
            "operacion": operacion.value if operacion else "desconocida",
        }
    with fabrica() as sesion:
        resumen = reconciliacion.reconciliar(
            sesion, orquestador, limite=configuracion.procesamiento_limite_concurrencia
        )
    return {"resultado": "completado", **resumen.conteos()}
