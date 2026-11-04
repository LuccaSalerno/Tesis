"""Consulta asistida (RF-13, RN-04, DO-2026-10-22-RAG). Rutas: RC-P01-007.

La consulta la realiza el responsable del trámite o el revisor/aprobador con una tarea
asignada (Tabla 3.II); para este, el alcance son las versiones vigentes de sus ciclos
(DO-2026-10-22-TAR, P8). El alcance documental lo calcula el backend: el cuerpo de la
solicitud solo trae la pregunta.
"""

import time
from collections.abc import Iterable
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from atlas.api import arranque
from atlas.api.dependencias import Autenticado, Sesion, UsuarioActual, acceso_de_consulta
from atlas.dominio.enumeraciones import MotivoAbstencion, Rol
from atlas.servicios import consultas, tramites
from atlas.servicios.errores import NoPermitido

enrutador = APIRouter(prefix="/tramites", tags=["consultas"])


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
    pregunta: str
    suficiente: bool
    respuesta: str | None
    afirmaciones: list[AfirmacionRespuesta]
    motivo_abstencion: MotivoAbstencion | None
    fragmentos_recuperados: int
    modelo_generacion: str | None
    version_instrucciones: str | None
    modelo_embeddings: str
    creado_en: datetime


def _referencia(f: consultas.FragmentoRecuperado) -> Referencia:
    return Referencia(
        fragmento_id=f.fragmento_id,
        documento_id=f.documento_id,
        documento_nombre=f.documento_nombre,
        version_id=f.version_id,
        version_numero=f.version_numero,
        pagina=f.pagina,
        seccion=f.seccion,
        contenido=f.contenido,
    )


def _respuesta(
    consulta: Any, afirmaciones: Iterable[consultas.Afirmacion], recuperados: int
) -> ConsultaRespuesta:
    return ConsultaRespuesta(
        id=consulta.id,
        pregunta=consulta.pregunta,
        suficiente=consulta.suficiente,
        respuesta=consulta.respuesta,
        afirmaciones=[
            AfirmacionRespuesta(texto=a.texto, referencias=[_referencia(f) for f in a.referencias])
            for a in afirmaciones
        ],
        motivo_abstencion=consulta.motivo_abstencion,
        fragmentos_recuperados=recuperados,
        modelo_generacion=consulta.modelo_generacion,
        version_instrucciones=consulta.version_instrucciones,
        modelo_embeddings=consulta.modelo_embeddings,
        creado_en=consulta.creado_en,
    )


def _acceso(sesion: Session, tramite_id: int, usuario: UsuarioActual) -> tramites.Acceso:
    # Tabla 3.II: responsable del trámite o revisor/aprobador con tarea asignada.
    if not ({Rol.RESPONSABLE_TRAMITE, Rol.REVISOR_APROBADOR} & usuario.roles):
        raise NoPermitido("Operación no permitida")
    return acceso_de_consulta(sesion, tramite_id, usuario)


@enrutador.get("/{tramite_id}/consultas", response_model=list[ConsultaRespuesta])
def listar_consultas(
    tramite_id: int, usuario: Autenticado, sesion: Sesion
) -> list[ConsultaRespuesta]:
    """Historial de las consultas propias en el trámite (DO-2026-10-22-WEB F6)."""
    acceso = _acceso(sesion, tramite_id, usuario)
    return [
        _respuesta(r.consulta, r.afirmaciones, r.recuperados)
        for r in consultas.historial(sesion, acceso.tramite.id, usuario.id)
    ]


@enrutador.post(
    "/{tramite_id}/consultas",
    response_model=ConsultaRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def consultar(
    tramite_id: int,
    nueva: NuevaConsulta,
    usuario: Autenticado,
    sesion: Sesion,
    request: Request,
    response: Response,
) -> ConsultaRespuesta:
    inicio = time.perf_counter()
    acceso = _acceso(sesion, tramite_id, usuario)
    resultado = consultas.consultar(
        sesion,
        tramite=acceso.tramite,
        versiones=acceso.versiones,
        usuario_id=usuario.id,
        pregunta=nueva.pregunta.strip(),
        embeddings=request.app.state.embeddings,
        modelo=request.app.state.modelo_generativo,
        limite=request.app.state.consulta_fragmentos_recuperados,
        max_tokens=request.app.state.consulta_max_tokens,
    )
    consulta = resultado.consulta
    sesion.refresh(consulta)
    response.headers["Server-Timing"] = server_timing(
        resultado.tiempos, round((time.perf_counter() - inicio) * 1000)
    )
    return _respuesta(consulta, resultado.afirmaciones, len(resultado.recuperados))


def server_timing(tiempos: dict[str, int], total_ms: int) -> str:
    """Solo duraciones y la marca de arranque (DO-2026-10-23-E90-API P4): sin contenido."""
    partes = [f"{nombre};dur={ms}" for nombre, ms in tiempos.items()]
    return ", ".join([*partes, f"total;dur={total_ms}", f'arranque;desc="{arranque.estado()}"'])
