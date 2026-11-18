"""Admisión de trabajos de procesamiento con límite de concurrencia (8 a 11).

Un *lock* transaccional de PostgreSQL serializa las admisiones:
dentro de la misma transacción se cuentan los trabajos en curso (`pendiente` y
`en_ejecucion`) y el nuevo queda `pendiente` si hay cupo o `en_espera` si no. El lock se
libera al confirmar la transacción, así que dos confirmaciones simultáneas nunca superan el
límite. La espera es un estado técnico: no cambia el trámite ni es un error.
"""

from typing import Final

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import EstadoTrabajo
from atlas.persistencia.modelos import TrabajoProcesamiento

# Clave del lock de aplicación de la admisión; arbitraria y exclusiva de ATLAS.
CLAVE_ADMISION: Final = 6_303_200_801
EN_CURSO: Final = (EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_EJECUCION)


def bloquear(sesion: Session) -> None:
    sesion.execute(text("SELECT pg_advisory_xact_lock(:clave)"), {"clave": CLAVE_ADMISION})


def en_curso(sesion: Session, excepto: int | None = None) -> int:
    consulta = (
        select(func.count())
        .select_from(TrabajoProcesamiento)
        .where(TrabajoProcesamiento.estado.in_(EN_CURSO))
    )
    if excepto is not None:
        consulta = consulta.where(TrabajoProcesamiento.id != excepto)
    return int(sesion.scalar(consulta) or 0)


def admitir(sesion: Session, trabajo: TrabajoProcesamiento, limite: int) -> EstadoTrabajo:
    """Fija `pendiente` o `en_espera` para un trabajo nuevo o reintentado, sin confirmar."""
    bloquear(sesion)
    sesion.flush()
    trabajo.estado = (
        EstadoTrabajo.PENDIENTE
        if en_curso(sesion, excepto=trabajo.id) < limite
        else EstadoTrabajo.EN_ESPERA
    )
    sesion.flush()
    return trabajo.estado
