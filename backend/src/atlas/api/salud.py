"""Estado del proceso de la API, sin consultar PostgreSQL (RC-P01-001, RC-P10-09).

No afirma disponibilidad fuera de `active` (DO-2026-10-22-OPS P2).
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from atlas.configuracion import Configuracion, Entorno, obtener_configuracion
from atlas.operacion.mantenimiento import EstadoOperativo

enrutador = APIRouter(tags=["salud"])


class RespuestaSalud(BaseModel):
    estado: Literal["ok", "mantenimiento"]
    entorno: Entorno
    operacion: EstadoOperativo | Literal["desconocido"]


@enrutador.get("/salud", response_model=RespuestaSalud)
def consultar_salud(
    configuracion: Annotated[Configuracion, Depends(obtener_configuracion)], request: Request
) -> RespuestaSalud:
    operacion = request.app.state.mantenimiento.estado()
    return RespuestaSalud(
        estado="ok" if operacion == EstadoOperativo.ACTIVE else "mantenimiento",
        entorno=configuracion.entorno,
        operacion=operacion or "desconocido",
    )
