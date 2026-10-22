"""Consulta asistida (RF-13, RN-04, DO-2026-10-22-RAG). Rutas: RC-P01-007.

La consulta la realiza el responsable del trámite (Tabla 3.II); el revisor con tarea
asignada se incorpora con las tareas (hito 1.8). El alcance documental lo calcula el
backend: el cuerpo de la solicitud solo trae la pregunta.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from atlas.api.dependencias import UsuarioActual, exigir_rol, obtener_sesion
from atlas.dominio.enumeraciones import MotivoAbstencion, Rol
from atlas.servicios import consultas, tramites

enrutador = APIRouter(prefix="/tramites", tags=["consultas"])

Sesion = Annotated[Session, Depends(obtener_sesion)]
Responsable = Annotated[UsuarioActual, Depends(exigir_rol(Rol.RESPONSABLE_TRAMITE))]


class NuevaConsulta(BaseModel):
    model_config = {"extra": "forbid"}  # nada del cliente amplía el alcance (§5.3.4)

    pregunta: Annotated[str, Field(min_length=1, max_length=2000, pattern=r"\S")]


class Referencia(BaseModel):
    """Documento, versión y localizador más preciso del fragmento citado (RF-13)."""

    fragmento_id: int
    documento_id: int
    documento_nombre: str
    version_id: int
    version_numero: int
    pagina: int | None
    seccion: str | None
    contenido: str


class AfirmacionRespuesta(BaseModel):
    texto: str
    referencias: list[Referencia]


class ConsultaRespuesta(BaseModel):
    id: int
    suficiente: bool
    respuesta: str | None
    afirmaciones: list[AfirmacionRespuesta]
    motivo_abstencion: MotivoAbstencion | None
    fragmentos_recuperados: int
    modelo_generacion: str | None
    version_instrucciones: str | None
    modelo_embeddings: str
    creado_en: datetime


@enrutador.post(
    "/{tramite_id}/consultas",
    response_model=ConsultaRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def consultar(
    tramite_id: int,
    nueva: NuevaConsulta,
    usuario: Responsable,
    sesion: Sesion,
    request: Request,
) -> ConsultaRespuesta:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    resultado = consultas.consultar(
        sesion,
        tramite=tramite,
        usuario_id=usuario.id,
        pregunta=nueva.pregunta.strip(),
        embeddings=request.app.state.embeddings,
        modelo=request.app.state.modelo_generativo,
        limite=request.app.state.consulta_fragmentos_recuperados,
        max_tokens=request.app.state.consulta_max_tokens,
    )
    consulta = resultado.consulta
    sesion.refresh(consulta)
    return ConsultaRespuesta(
        id=consulta.id,
        suficiente=consulta.suficiente,
        respuesta=consulta.respuesta,
        afirmaciones=[
            AfirmacionRespuesta(
                texto=a.texto,
                referencias=[
                    Referencia(
                        fragmento_id=f.fragmento_id,
                        documento_id=f.documento_id,
                        documento_nombre=f.documento_nombre,
                        version_id=f.version_id,
                        version_numero=f.version_numero,
                        pagina=f.pagina,
                        seccion=f.seccion,
                        contenido=f.contenido,
                    )
                    for f in a.referencias
                ],
            )
            for a in resultado.afirmaciones
        ],
        motivo_abstencion=consulta.motivo_abstencion,
        fragmentos_recuperados=len(resultado.recuperados),
        modelo_generacion=consulta.modelo_generacion,
        version_instrucciones=consulta.version_instrucciones,
        modelo_embeddings=consulta.modelo_embeddings,
        creado_en=consulta.creado_en,
    )
