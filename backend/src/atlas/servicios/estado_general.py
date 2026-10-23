"""Estado general de trámites, tareas y procesamiento para el administrador operativo (RF-24,
HU-10, DO-2026-10-23-CIERRE P4).

Solo metadatos y conteos: ni títulos ni descripciones de trámites, ni contenido documental,
ni datos validados. Sirve para coordinar (asignar y reasignar tareas, RF-19) sin sustituir las
decisiones de los revisores.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    EstadoTarea,
    EstadoTrabajo,
    EstadoTramite,
    EstadoUsuario,
)
from atlas.persistencia.modelos import (
    CicloRevision,
    Documento,
    Tarea,
    TrabajoProcesamiento,
    Tramite,
    Usuario,
)
from atlas.servicios import ciclos

LIMITE_TRAMITES: Final = 500


@dataclass(frozen=True)
class FilaTramite:
    id: int
    estado: EstadoTramite
    responsable_id: int
    creado_en: datetime
    actualizado_en: datetime
    documentos: int
    tareas_abiertas: int
    tareas_sin_asignar: int


@dataclass(frozen=True)
class TareaBloqueada:
    """Tarea abierta asignada a una cuenta deshabilitada o suprimida: hay que reasignarla."""

    tarea_id: int
    tramite_id: int
    asignada_a_id: int


@dataclass(frozen=True)
class EstadoGeneral:
    tramites_por_estado: dict[EstadoTramite, int]
    tareas_por_estado: dict[EstadoTarea, int]
    tareas_sin_asignar: int
    tareas_bloqueadas: list[TareaBloqueada]
    trabajos_por_estado: dict[EstadoTrabajo, int]
    tramites: list[FilaTramite]


def _conteo(sesion: Session, columna: Any) -> dict[str, int]:
    return {e: n for e, n in sesion.execute(select(columna, func.count()).group_by(columna))}


def consultar(sesion: Session) -> EstadoGeneral:
    abiertas = Tarea.estado.in_(ciclos.ABIERTAS)
    documentos = (
        select(Documento.tramite_id, func.count().label("n"))
        .group_by(Documento.tramite_id)
        .subquery()
    )
    tareas = (
        select(
            CicloRevision.tramite_id,
            func.count().filter(abiertas).label("abiertas"),
            func.count().filter(abiertas, Tarea.asignada_a_id.is_(None)).label("sin_asignar"),
        )
        .join(Tarea, Tarea.ciclo_revision_id == CicloRevision.id)
        .group_by(CicloRevision.tramite_id)
        .subquery()
    )
    filas = sesion.execute(
        select(
            Tramite.id,
            Tramite.estado,
            Tramite.responsable_id,
            Tramite.creado_en,
            Tramite.actualizado_en,
            func.coalesce(documentos.c.n, 0),
            func.coalesce(tareas.c.abiertas, 0),
            func.coalesce(tareas.c.sin_asignar, 0),
        )
        .outerjoin(documentos, documentos.c.tramite_id == Tramite.id)
        .outerjoin(tareas, tareas.c.tramite_id == Tramite.id)
        .order_by(Tramite.actualizado_en.desc(), Tramite.id.desc())
        .limit(LIMITE_TRAMITES)
    ).all()
    bloqueadas = sesion.execute(
        select(Tarea.id, CicloRevision.tramite_id, Tarea.asignada_a_id)
        .join(CicloRevision, CicloRevision.id == Tarea.ciclo_revision_id)
        .join(Usuario, Usuario.id == Tarea.asignada_a_id)
        .where(abiertas, Usuario.estado != EstadoUsuario.HABILITADA)
        .order_by(Tarea.id)
    ).all()
    sin_asignar = sesion.scalar(
        select(func.count()).select_from(Tarea).where(abiertas, Tarea.asignada_a_id.is_(None))
    )
    return EstadoGeneral(
        tramites_por_estado={
            EstadoTramite(e): n for e, n in _conteo(sesion, Tramite.estado).items()
        },
        tareas_por_estado={EstadoTarea(e): n for e, n in _conteo(sesion, Tarea.estado).items()},
        tareas_sin_asignar=int(sin_asignar or 0),
        # La unión con la cuenta garantiza la asignación.
        tareas_bloqueadas=[TareaBloqueada(t, r, cast(int, u)) for t, r, u in bloqueadas],
        trabajos_por_estado={
            EstadoTrabajo(e): n for e, n in _conteo(sesion, TrabajoProcesamiento.estado).items()
        },
        tramites=[FilaTramite(*f) for f in filas],
    )
