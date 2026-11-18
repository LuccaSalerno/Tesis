"""Estado general para el administrador operativo (RF-24, HU-10).

 Solo metadatos y conteos: el administrador no ve títulos, contenido
documental ni datos validados; los demás roles reciben 403.
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from atlas.api.dependencias import Administrador, Sesion
from atlas.dominio.enumeraciones import EstadoTarea, EstadoTrabajo, EstadoTramite
from atlas.servicios import estado_general

enrutador = APIRouter(prefix="/administracion", tags=["administracion"])


class TramiteGeneral(BaseModel):
    """Sin título ni descripción: pueden contener datos sensibles."""

    id: int
    estado: EstadoTramite
    responsable_id: int
    creado_en: datetime
    actualizado_en: datetime
    documentos: int
    tareas_abiertas: int
    tareas_sin_asignar: int


class TareaBloqueadaRespuesta(BaseModel):
    tarea_id: int
    tramite_id: int
    asignada_a_id: int


class EstadoGeneralRespuesta(BaseModel):
    tramites_por_estado: dict[EstadoTramite, int]
    tareas_por_estado: dict[EstadoTarea, int]
    tareas_sin_asignar: int
    tareas_bloqueadas: list[TareaBloqueadaRespuesta] = Field(
        description="Tareas abiertas asignadas a cuentas deshabilitadas o suprimidas (RF-19)"
    )
    trabajos_por_estado: dict[EstadoTrabajo, int]
    tramites: list[TramiteGeneral] = Field(
        description=f"Los {estado_general.LIMITE_TRAMITES} actualizados más recientemente"
    )


@enrutador.get("/estado-general", response_model=EstadoGeneralRespuesta)
def consultar_estado_general(_: Administrador, sesion: Sesion) -> EstadoGeneralRespuesta:
    actual = estado_general.consultar(sesion)
    return EstadoGeneralRespuesta(
        tramites_por_estado=actual.tramites_por_estado,
        tareas_por_estado=actual.tareas_por_estado,
        tareas_sin_asignar=actual.tareas_sin_asignar,
        tareas_bloqueadas=[
            TareaBloqueadaRespuesta(
                tarea_id=t.tarea_id, tramite_id=t.tramite_id, asignada_a_id=t.asignada_a_id
            )
            for t in actual.tareas_bloqueadas
        ],
        trabajos_por_estado=actual.trabajos_por_estado,
        tramites=[
            TramiteGeneral(
                id=f.id,
                estado=f.estado,
                responsable_id=f.responsable_id,
                creado_en=f.creado_en,
                actualizado_en=f.actualizado_en,
                documentos=f.documentos,
                tareas_abiertas=f.tareas_abiertas,
                tareas_sin_asignar=f.tareas_sin_asignar,
            )
            for f in actual.tramites
        ],
    )
