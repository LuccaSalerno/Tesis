"""Estado del proceso de la API, sin consultar PostgreSQL (RC-P01-001)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from atlas.configuracion import Configuracion, Entorno, obtener_configuracion

enrutador = APIRouter(tags=["salud"])


class RespuestaSalud(BaseModel):
    estado: Literal["ok"]
    entorno: Entorno


@enrutador.get("/salud", response_model=RespuestaSalud)
def consultar_salud(
    configuracion: Annotated[Configuracion, Depends(obtener_configuracion)],
) -> RespuestaSalud:
    return RespuestaSalud(estado="ok", entorno=configuracion.entorno)
