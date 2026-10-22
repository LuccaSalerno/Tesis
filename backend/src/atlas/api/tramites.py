"""Trámites, cargas e incorporación (RF-03, RF-04, RF-05, RF-07, RC-P04). Rutas: RC-P01-004.

Permisos (Tabla 3.II): crear trámites, cargar e incorporar requieren el rol de
responsable del trámite y ser el responsable de ese trámite. Un trámite sin
acceso responde 404, igual que uno inexistente.
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
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
    EstadoIncorporacion,
    EstadoTrabajo,
    EstadoTramite,
    FormatoArchivo,
    Rol,
    TipoDocumental,
)
from atlas.dominio.validacion_archivo import ArchivoRechazado, LimitesCarga
from atlas.integraciones.puertos import AlmacenDocumental, OrquestadorProcesamiento
from atlas.persistencia.modelos import Archivo, TrabajoProcesamiento, Tramite
from atlas.servicios import cargas, tramites

enrutador = APIRouter(prefix="/tramites", tags=["tramites"])

Sesion = Annotated[Session, Depends(obtener_sesion)]
Autenticado = Annotated[UsuarioActual, Depends(obtener_usuario_actual)]
Responsable = Annotated[UsuarioActual, Depends(exigir_rol(Rol.RESPONSABLE_TRAMITE))]
SolicitudId = Annotated[uuid.UUID | None, Depends(obtener_solicitud_id)]

Texto = Annotated[str, Field(min_length=1, pattern=r"\S")]


def obtener_almacen(request: Request) -> AlmacenDocumental:
    almacen: AlmacenDocumental = request.app.state.almacen
    return almacen


def obtener_orquestador(request: Request) -> OrquestadorProcesamiento:
    orquestador: OrquestadorProcesamiento = request.app.state.orquestador
    return orquestador


def obtener_limites(request: Request) -> LimitesCarga:
    limites: LimitesCarga = request.app.state.limites_carga
    return limites


Almacen = Annotated[AlmacenDocumental, Depends(obtener_almacen)]
Orquestador = Annotated[OrquestadorProcesamiento, Depends(obtener_orquestador)]
Limites = Annotated[LimitesCarga, Depends(obtener_limites)]


class NuevoTramite(BaseModel):
    titulo: Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
    descripcion: str | None = Field(default=None, max_length=5000)


class TramiteRespuesta(BaseModel):
    id: int
    titulo: str
    descripcion: str | None
    estado: EstadoTramite
    responsable_id: int
    creado_en: datetime
    actualizado_en: datetime

    @classmethod
    def desde(cls, tramite: Tramite) -> "TramiteRespuesta":
        return cls(
            id=tramite.id,
            titulo=tramite.titulo,
            descripcion=tramite.descripcion,
            estado=tramite.estado,
            responsable_id=tramite.responsable_id,
            creado_en=tramite.creado_en,
            actualizado_en=tramite.actualizado_en,
        )


class VersionResumen(BaseModel):
    id: int
    numero: int
    archivo_id: int


class DocumentoRespuesta(BaseModel):
    id: int
    nombre: str
    tipo: TipoDocumental | None
    version_vigente: VersionResumen


class TramiteDetalle(TramiteRespuesta):
    documentos: list[DocumentoRespuesta]


class SolicitudCarga(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=255, pattern=r"\S")]
    formato: FormatoArchivo
    tamano_bytes: int = Field(gt=0)


class CargaRespuesta(BaseModel):
    id: int
    url: str
    metodo: str = "PUT"
    encabezados: dict[str, str]
    expira_en: datetime


class TrabajoRespuesta(BaseModel):
    estado: EstadoTrabajo
    intento: int


class ArchivoRespuesta(BaseModel):
    id: int
    nombre: str
    formato: FormatoArchivo
    tamano_bytes: int
    huella: str
    estado_incorporacion: EstadoIncorporacion
    cargado_en: datetime
    trabajo: TrabajoRespuesta | None

    @classmethod
    def desde(cls, archivo: Archivo, trabajo: TrabajoProcesamiento | None) -> "ArchivoRespuesta":
        return cls(
            id=archivo.id,
            nombre=archivo.nombre,
            formato=archivo.formato,
            tamano_bytes=archivo.tamano_bytes,
            huella=archivo.huella,
            estado_incorporacion=archivo.estado_incorporacion,
            cargado_en=archivo.cargado_en,
            trabajo=(
                None
                if trabajo is None
                else TrabajoRespuesta(estado=trabajo.estado, intento=trabajo.intento)
            ),
        )


class Incorporacion(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=255, pattern=r"\S")] | None = None


@enrutador.post("", response_model=TramiteRespuesta, status_code=status.HTTP_201_CREATED)
def crear_tramite(
    nuevo: NuevoTramite, usuario: Responsable, sesion: Sesion, solicitud_id: SolicitudId
) -> TramiteRespuesta:
    tramite = tramites.crear(
        sesion,
        responsable_id=usuario.id,
        titulo=nuevo.titulo,
        descripcion=nuevo.descripcion,
        solicitud_id=solicitud_id,
    )
    return TramiteRespuesta.desde(tramite)


@enrutador.get("", response_model=list[TramiteRespuesta])
def listar_tramites(usuario: Autenticado, sesion: Sesion) -> list[TramiteRespuesta]:
    return [TramiteRespuesta.desde(t) for t in tramites.listar_accesibles(sesion, usuario.id)]


@enrutador.get("/{tramite_id}", response_model=TramiteDetalle)
def abrir_tramite(tramite_id: int, usuario: Autenticado, sesion: Sesion) -> TramiteDetalle:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    documentos = [
        DocumentoRespuesta(
            id=d.id,
            nombre=d.nombre,
            tipo=d.tipo,
            version_vigente=VersionResumen(
                id=d.version_vigente_id, numero=d.numero_version, archivo_id=d.archivo_id
            ),
        )
        for d in tramites.documentos_vigentes(sesion, tramite.id)
    ]
    return TramiteDetalle(**TramiteRespuesta.desde(tramite).model_dump(), documentos=documentos)


@enrutador.post(
    "/{tramite_id}/cargas", response_model=CargaRespuesta, status_code=status.HTTP_201_CREATED
)
def autorizar_carga(
    tramite_id: int,
    solicitud: SolicitudCarga,
    usuario: Responsable,
    sesion: Sesion,
    almacen: Almacen,
    limites: Limites,
    request: Request,
) -> CargaRespuesta:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    autorizada = cargas.autorizar(
        sesion,
        almacen,
        limites,
        tramite=tramite,
        usuario_id=usuario.id,
        nombre=solicitud.nombre,
        formato=solicitud.formato,
        tamano_bytes=solicitud.tamano_bytes,
        vigencia_s=request.app.state.vigencia_url_carga_s,
    )
    return CargaRespuesta(
        id=autorizada.autorizacion.id,
        url=autorizada.url,
        encabezados={"Content-Type": autorizada.tipo_contenido},
        expira_en=autorizada.autorizacion.expira_en,
    )


@enrutador.post(
    "/{tramite_id}/cargas/{carga_id}/confirmacion",
    response_model=ArchivoRespuesta,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"description": "Confirmación repetida: el archivo ya estaba registrado"}},
)
def confirmar_carga(
    tramite_id: int,
    carga_id: int,
    usuario: Responsable,
    sesion: Sesion,
    almacen: Almacen,
    orquestador: Orquestador,
    limites: Limites,
    solicitud_id: SolicitudId,
    response: Response,
) -> ArchivoRespuesta:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    confirmada = cargas.confirmar(
        sesion,
        almacen,
        orquestador,
        limites,
        tramite=tramite,
        autorizacion_id=carga_id,
        usuario_id=usuario.id,
        solicitud_id=solicitud_id,
    )
    if not confirmada.nueva:
        response.status_code = status.HTTP_200_OK
    return ArchivoRespuesta.desde(confirmada.archivo, confirmada.trabajo)


@enrutador.get("/{tramite_id}/archivos", response_model=list[ArchivoRespuesta])
def listar_archivos(
    tramite_id: int, usuario: Autenticado, sesion: Sesion
) -> list[ArchivoRespuesta]:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    return [ArchivoRespuesta.desde(a, t) for a, t in cargas.listar_archivos(sesion, tramite.id)]


@enrutador.post(
    "/{tramite_id}/archivos/{archivo_id}/incorporacion",
    response_model=DocumentoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def incorporar_archivo(
    tramite_id: int,
    archivo_id: int,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
    incorporacion: Incorporacion | None = None,
) -> DocumentoRespuesta:
    """RF-07: confirma el archivo como documento nuevo con su versión inicial vigente."""
    # PD-05.2: las operaciones que cambian el trámite lo bloquean mientras se ejecutan.
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    documento, version = cargas.incorporar_como_documento_nuevo(
        sesion,
        tramite=tramite,
        archivo_id=archivo_id,
        usuario_id=usuario.id,
        nombre=incorporacion.nombre if incorporacion else None,
        solicitud_id=solicitud_id,
    )
    return DocumentoRespuesta(
        id=documento.id,
        nombre=documento.nombre,
        tipo=documento.tipo,
        version_vigente=VersionResumen(
            id=version.id, numero=version.numero, archivo_id=version.archivo_id
        ),
    )


async def responder_archivo_rechazado(_: Request, error: Exception) -> JSONResponse:
    """RC-P04: 422 con la causa y la acción necesaria; el archivo no produce efectos."""
    if not isinstance(error, ArchivoRechazado):
        raise error
    return JSONResponse(
        {"detalle": error.mensaje, "codigo": error.codigo},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
