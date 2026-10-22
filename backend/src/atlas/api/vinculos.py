"""Vínculos documentales y controles de consistencia (RF-14, RF-15, RF-16). Rutas: RC-P01-008.

Permisos (Tabla 3.II): crear, confirmar, rechazar y eliminar vínculos requieren el rol de
responsable del trámite y ser su responsable. Consultar vínculos y controles, por ahora,
solo el responsable: el revisor con tarea asignada se incorpora con las tareas (hito 1.8).
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from atlas.api.dependencias import (
    UsuarioActual,
    exigir_rol,
    obtener_sesion,
    obtener_solicitud_id,
    obtener_usuario_actual,
)
from atlas.dominio.enumeraciones import (
    DisparadorRegla,
    EstadoVinculo,
    OrigenVinculo,
    ResultadoRegla,
    Rol,
    TipoDocumental,
    TipoVinculo,
)
from atlas.dominio.fuentes import FuenteIndicada
from atlas.persistencia.modelos import ReferenciaFuente, VinculoDocumental
from atlas.servicios import reglas, tramites, vinculos

enrutador = APIRouter(prefix="/tramites", tags=["vinculos"])

Sesion = Annotated[Session, Depends(obtener_sesion)]
Autenticado = Annotated[UsuarioActual, Depends(obtener_usuario_actual)]
Responsable = Annotated[UsuarioActual, Depends(exigir_rol(Rol.RESPONSABLE_TRAMITE))]
SolicitudId = Annotated[uuid.UUID | None, Depends(obtener_solicitud_id)]


class FuenteVinculo(BaseModel):
    """Localizador en la versión vigente del documento de origen."""

    pagina: int | None = Field(default=None, ge=1)
    seccion: str | None = Field(default=None, max_length=255)
    fragmento: str | None = Field(default=None, max_length=500)


class NuevoVinculo(BaseModel):
    model_config = {"extra": "forbid"}

    documento_origen_id: int
    documento_destino_id: int
    tipo: TipoVinculo
    justificacion: Annotated[str, Field(min_length=1, max_length=2000, pattern=r"\S")]
    fuente: FuenteVinculo | None = None


class VinculoRespuesta(BaseModel):
    id: int
    documento_origen_id: int
    documento_destino_id: int
    tipo: TipoVinculo
    origen: OrigenVinculo
    estado: EstadoVinculo
    justificacion: str
    fuente: FuenteVinculo | None
    creado_por_id: int | None
    creado_en: datetime
    resuelto_por_id: int | None
    resuelto_en: datetime | None

    @classmethod
    def desde(
        cls, vinculo: VinculoDocumental, fuente: ReferenciaFuente | None
    ) -> "VinculoRespuesta":
        return cls(
            id=vinculo.id,
            documento_origen_id=vinculo.documento_origen_id,
            documento_destino_id=vinculo.documento_destino_id,
            tipo=vinculo.tipo,
            origen=vinculo.origen,
            estado=vinculo.estado,
            justificacion=vinculo.justificacion,
            fuente=(
                None
                if fuente is None
                else FuenteVinculo(
                    pagina=fuente.pagina, seccion=fuente.seccion, fragmento=fuente.fragmento
                )
            ),
            creado_por_id=vinculo.creado_por_id,
            creado_en=vinculo.creado_en,
            resuelto_por_id=vinculo.resuelto_por_id,
            resuelto_en=vinculo.resuelto_en,
        )


class VinculosRespuesta(BaseModel):
    """RF-15: los sugeridos se presentan por separado de los que rigen."""

    confirmados: list[VinculoRespuesta]
    sugeridos: list[VinculoRespuesta]
    resueltos: list[VinculoRespuesta] = Field(
        description="Rechazados y eliminados; solo con historial=true"
    )


def _respuesta(sesion: Session, vinculo: VinculoDocumental) -> VinculoRespuesta:
    fuente = sesion.get(ReferenciaFuente, vinculo.fuente_id) if vinculo.fuente_id else None
    return VinculoRespuesta.desde(vinculo, fuente)


@enrutador.get("/{tramite_id}/vinculos", response_model=VinculosRespuesta)
def listar_vinculos(
    tramite_id: int, usuario: Autenticado, sesion: Sesion, historial: bool = False
) -> VinculosRespuesta:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    todos = vinculos.listar(sesion, tramite.id, historial=historial)
    fuentes = vinculos.fuentes(sesion, todos)
    respuestas = [
        VinculoRespuesta.desde(v, fuentes.get(v.fuente_id) if v.fuente_id else None) for v in todos
    ]
    return VinculosRespuesta(
        confirmados=[r for r in respuestas if r.estado == EstadoVinculo.CONFIRMADO],
        sugeridos=[r for r in respuestas if r.estado == EstadoVinculo.PENDIENTE],
        resueltos=[
            r for r in respuestas if r.estado in (EstadoVinculo.RECHAZADO, EstadoVinculo.ELIMINADO)
        ],
    )


@enrutador.post(
    "/{tramite_id}/vinculos",
    response_model=VinculoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_vinculo(
    tramite_id: int,
    nuevo: NuevoVinculo,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> VinculoRespuesta:
    """RF-14 y RN-05: vínculo manual, vigente de inmediato; ejecuta las reglas pertinentes."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    vinculo = vinculos.crear(
        sesion,
        tramite=tramite,
        usuario_id=usuario.id,
        documento_origen_id=nuevo.documento_origen_id,
        documento_destino_id=nuevo.documento_destino_id,
        tipo=nuevo.tipo,
        justificacion=nuevo.justificacion,
        fuente=FuenteIndicada(**nuevo.fuente.model_dump()) if nuevo.fuente else None,
        solicitud_id=solicitud_id,
    )
    return _respuesta(sesion, vinculo)


@enrutador.post("/{tramite_id}/vinculos/{vinculo_id}/confirmacion", response_model=VinculoRespuesta)
def confirmar_vinculo(
    tramite_id: int,
    vinculo_id: int,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> VinculoRespuesta:
    """RF-15: confirma un vínculo sugerido; desde ahí rige y alimenta las reglas."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    vinculo = vinculos.confirmar(
        sesion,
        tramite=tramite,
        vinculo_id=vinculo_id,
        usuario_id=usuario.id,
        solicitud_id=solicitud_id,
    )
    return _respuesta(sesion, vinculo)


@enrutador.post("/{tramite_id}/vinculos/{vinculo_id}/rechazo", response_model=VinculoRespuesta)
def rechazar_vinculo(
    tramite_id: int,
    vinculo_id: int,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> VinculoRespuesta:
    """RF-15: rechaza un vínculo sugerido, sin efecto sobre las reglas."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    vinculo = vinculos.rechazar(
        sesion,
        tramite=tramite,
        vinculo_id=vinculo_id,
        usuario_id=usuario.id,
        solicitud_id=solicitud_id,
    )
    return _respuesta(sesion, vinculo)


@enrutador.delete("/{tramite_id}/vinculos/{vinculo_id}", response_model=VinculoRespuesta)
def eliminar_vinculo(
    tramite_id: int,
    vinculo_id: int,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> VinculoRespuesta:
    """RF-14: baja lógica; el vínculo y sus ejecuciones quedan en el historial."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    vinculo = vinculos.eliminar(
        sesion,
        tramite=tramite,
        vinculo_id=vinculo_id,
        usuario_id=usuario.id,
        solicitud_id=solicitud_id,
    )
    return _respuesta(sesion, vinculo)


# --- Controles de consistencia (RF-16, V3) ---------------------------------------------


class VersionConsideradaRespuesta(BaseModel):
    papel: TipoDocumental
    documento_id: int
    documento_nombre: str
    version_id: int
    version_numero: int


class ValorComparadoRespuesta(BaseModel):
    """Entrada de la regla: una validación humana concreta (RN-02)."""

    papel: TipoDocumental
    campo: str
    valor_validado: str
    validacion_id: int
    version_id: int


class EjecucionRespuesta(BaseModel):
    id: int
    vinculo_id: int
    codigo_regla: str
    version_regla: str
    descripcion: str
    resultado: ResultadoRegla
    explicacion: str
    disparador: DisparadorRegla
    ejecutada_en: datetime
    versiones: list[VersionConsideradaRespuesta]
    valores: list[ValorComparadoRespuesta]

    @classmethod
    def desde(cls, detalle: reglas.DetalleEjecucion) -> "EjecucionRespuesta":
        ejecucion = detalle.ejecucion
        return cls(
            id=ejecucion.id,
            vinculo_id=ejecucion.vinculo_id,
            codigo_regla=ejecucion.codigo_regla,
            version_regla=ejecucion.version_regla,
            descripcion=detalle.regla.descripcion,
            resultado=ejecucion.resultado,
            explicacion=ejecucion.explicacion,
            disparador=ejecucion.disparador,
            ejecutada_en=ejecucion.ejecutada_en,
            versiones=[
                VersionConsideradaRespuesta(
                    papel=v.papel,
                    documento_id=v.documento.id,
                    documento_nombre=v.documento.nombre,
                    version_id=v.version.id,
                    version_numero=v.version.numero,
                )
                for v in detalle.versiones
            ],
            valores=[
                ValorComparadoRespuesta(
                    papel=v.papel,
                    campo=v.validacion.campo,
                    valor_validado=v.validacion.valor_validado,
                    validacion_id=v.validacion.id,
                    version_id=v.validacion.version_id,
                )
                for v in detalle.valores
            ],
        )


class ControlRespuesta(BaseModel):
    """Situación actual de una regla en un vínculo; sin vínculo pertinente, no aplicable."""

    codigo_regla: str
    version_regla: str
    descripcion: str
    vinculo_id: int | None
    resultado: ResultadoRegla
    explicacion: str
    ejecucion: EjecucionRespuesta | None


class ControlesRespuesta(BaseModel):
    vigentes: list[ControlRespuesta]
    historial: list[EjecucionRespuesta] = Field(
        description="Todas las ejecuciones del trámite; solo con historial=true"
    )


@enrutador.get("/{tramite_id}/controles", response_model=ControlesRespuesta)
def consultar_controles(
    tramite_id: int, usuario: Autenticado, sesion: Sesion, historial: bool = False
) -> ControlesRespuesta:
    """RF-16: regla, versiones, valores comparados y resultado de cada control."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    return ControlesRespuesta(
        vigentes=[
            ControlRespuesta(
                codigo_regla=c.regla.codigo,
                version_regla=c.regla.version,
                descripcion=c.regla.descripcion,
                vinculo_id=c.vinculo_id,
                resultado=c.resultado,
                explicacion=c.explicacion,
                ejecucion=None if c.detalle is None else EjecucionRespuesta.desde(c.detalle),
            )
            for c in reglas.vigentes(sesion, tramite.id)
        ],
        historial=(
            [EjecucionRespuesta.desde(d) for d in reglas.historial(sesion, tramite.id)]
            if historial
            else []
        ),
    )


@enrutador.get("/{tramite_id}/controles/{ejecucion_id}", response_model=EjecucionRespuesta)
def consultar_ejecucion(
    tramite_id: int, ejecucion_id: int, usuario: Autenticado, sesion: Sesion
) -> EjecucionRespuesta:
    """V3: una ejecución con sus entradas validadas y versiones de origen."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    return EjecucionRespuesta.desde(reglas.obtener(sesion, tramite.id, ejecucion_id))
