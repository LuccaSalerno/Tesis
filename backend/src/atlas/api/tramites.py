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
    ClaseSugerencia,
    EstadoIncorporacion,
    EstadoTrabajo,
    EstadoTramite,
    FormatoArchivo,
    MotivoSinFuente,
    Rol,
    TipoDocumental,
    TipoValidacion,
)
from atlas.dominio.fuentes import FuenteIndicada
from atlas.dominio.validacion_archivo import ArchivoRechazado, LimitesCarga
from atlas.integraciones.puertos import AlmacenDocumental, OrquestadorProcesamiento
from atlas.persistencia.modelos import (
    Archivo,
    ReferenciaFuente,
    TrabajoProcesamiento,
    Tramite,
    ValidacionHumana,
    ValorSugerido,
)
from atlas.servicios import cargas, resultados, tramites, validaciones
from atlas.servicios.errores import NoEncontrado

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


def obtener_vigencia_pendiente(request: Request) -> int:
    vigencia: int = request.app.state.vigencia_carga_pendiente_s
    return vigencia


Almacen = Annotated[AlmacenDocumental, Depends(obtener_almacen)]
Orquestador = Annotated[OrquestadorProcesamiento, Depends(obtener_orquestador)]
Limites = Annotated[LimitesCarga, Depends(obtener_limites)]
VigenciaPendiente = Annotated[int, Depends(obtener_vigencia_pendiente)]


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
    vence_en: datetime | None = Field(
        description="Límite para incorporar una carga pendiente (DO-2026-10-22-CARGAS)"
    )
    trabajo: TrabajoRespuesta | None

    @classmethod
    def desde(
        cls, archivo: Archivo, trabajo: TrabajoProcesamiento | None, vigencia_s: int
    ) -> "ArchivoRespuesta":
        pendiente = archivo.estado_incorporacion == EstadoIncorporacion.PENDIENTE
        return cls(
            vence_en=cargas.vencimiento(archivo.cargado_en, vigencia_s) if pendiente else None,
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


class Localizador(BaseModel):
    pagina: int | None
    seccion: str | None
    fragmento: str | None


class SugerenciaRespuesta(BaseModel):
    """Resultado automático: es una sugerencia hasta su validación humana (RN-02)."""

    id: int
    campo: str
    valor: str
    valor_original: str
    localizador: Localizador | None
    motivo_sin_fuente: MotivoSinFuente | None
    modelo: str
    version_instrucciones: str
    version_esquema: str


class SugerenciasRespuesta(BaseModel):
    trabajo: TrabajoRespuesta | None
    clasificacion: SugerenciaRespuesta | None
    campos: list[SugerenciaRespuesta]


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
    vigencia: VigenciaPendiente,
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
        vigencia_pendiente_s=vigencia,
        solicitud_id=solicitud_id,
    )
    if not confirmada.nueva:
        response.status_code = status.HTTP_200_OK
    return ArchivoRespuesta.desde(confirmada.archivo, confirmada.trabajo, vigencia)


@enrutador.get("/{tramite_id}/archivos", response_model=list[ArchivoRespuesta])
def listar_archivos(
    tramite_id: int, usuario: Autenticado, sesion: Sesion, vigencia: VigenciaPendiente
) -> list[ArchivoRespuesta]:
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    return [
        ArchivoRespuesta.desde(a, t, vigencia)
        for a, t in cargas.listar_archivos(sesion, tramite.id)
    ]


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
    almacen: Almacen,
    vigencia: VigenciaPendiente,
    solicitud_id: SolicitudId,
    incorporacion: Incorporacion | None = None,
) -> DocumentoRespuesta:
    """RF-07: confirma el archivo como documento nuevo con su versión inicial vigente.

    La carga debe estar vigente (24 h, DO-2026-10-22-CARGAS); el original se traslada
    al prefijo definitivo de S3 antes de registrar la versión.
    """
    # PD-05.2: las operaciones que cambian el trámite lo bloquean mientras se ejecutan.
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    documento, version = cargas.incorporar_como_documento_nuevo(
        sesion,
        almacen,
        tramite=tramite,
        archivo_id=archivo_id,
        usuario_id=usuario.id,
        nombre=incorporacion.nombre if incorporacion else None,
        vigencia_pendiente_s=vigencia,
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


@enrutador.get(
    "/{tramite_id}/archivos/{archivo_id}/sugerencias", response_model=SugerenciasRespuesta
)
def consultar_sugerencias(
    tramite_id: int, archivo_id: int, usuario: Autenticado, sesion: Sesion
) -> SugerenciasRespuesta:
    """RF-08, RF-10, RF-11: clasificación y campos sugeridos con su localizador, o el
    motivo por el que no hay uno verificable."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    archivo = sesion.get(Archivo, archivo_id)
    if archivo is None or archivo.tramite_id != tramite.id:
        raise NoEncontrado("El archivo no existe en este trámite")
    trabajo, filas = resultados.sugerencias_vigentes(sesion, archivo.id)
    sugerencias = {valor.id: _sugerencia(valor, fuente) for valor, fuente in filas}
    clases = {valor.id: valor.clase for valor, _ in filas}
    return SugerenciasRespuesta(
        trabajo=(
            None
            if trabajo is None
            else TrabajoRespuesta(estado=trabajo.estado, intento=trabajo.intento)
        ),
        clasificacion=next(
            (s for i, s in sugerencias.items() if clases[i] == ClaseSugerencia.CLASIFICACION), None
        ),
        campos=[s for i, s in sugerencias.items() if clases[i] == ClaseSugerencia.CAMPO],
    )


def _localizador(fuente: ReferenciaFuente | None) -> Localizador | None:
    if fuente is None:
        return None
    return Localizador(pagina=fuente.pagina, seccion=fuente.seccion, fragmento=fuente.fragmento)


def _sugerencia(valor: ValorSugerido, fuente: ReferenciaFuente | None) -> SugerenciaRespuesta:
    return SugerenciaRespuesta(
        id=valor.id,
        campo=valor.campo,
        valor=valor.valor,
        valor_original=valor.valor_original,
        localizador=_localizador(fuente),
        motivo_sin_fuente=valor.motivo_sin_fuente,
        modelo=valor.modelo,
        version_instrucciones=valor.version_instrucciones,
        version_esquema=valor.version_esquema,
    )


# --- Validación humana (hito 1.5, RF-09, RF-12, DO-2026-10-22-VAL) --------------------


class FuenteEntrada(BaseModel):
    pagina: int | None = Field(default=None, ge=1)
    seccion: str | None = Field(default=None, max_length=255)
    fragmento: str | None = Field(default=None, max_length=500)


class NuevaValidacion(BaseModel):
    campo: Annotated[str, Field(min_length=1, max_length=60)]
    valor_validado: Annotated[str, Field(min_length=1, max_length=500)]
    valor_sugerido_id: int | None = None
    reemplaza_a_id: int | None = Field(
        default=None, description="Validación vigente del dato que se reemplaza, si la hay"
    )
    fuente: FuenteEntrada | None = None


class ValidacionRespuesta(BaseModel):
    """RN-03: valor validado, actor, fecha, versión, fuente y la sugerencia de origen."""

    id: int
    version_id: int
    campo: str
    valor_validado: str
    tipo: TipoValidacion
    valor_sugerido_id: int | None
    reemplaza_a_id: int | None
    validador_id: int
    validado_en: datetime
    localizador: Localizador | None

    @classmethod
    def desde(
        cls, validacion: ValidacionHumana, fuente: ReferenciaFuente | None
    ) -> "ValidacionRespuesta":
        return cls(
            id=validacion.id,
            version_id=validacion.version_id,
            campo=validacion.campo,
            valor_validado=validacion.valor_validado,
            tipo=validacion.tipo,
            valor_sugerido_id=validacion.valor_sugerido_id,
            reemplaza_a_id=validacion.reemplaza_a_id,
            validador_id=validacion.validador_id,
            validado_en=validacion.validado_en,
            localizador=_localizador(fuente),
        )


class ValidacionRegistradaRespuesta(ValidacionRespuesta):
    advertencias: list[str]


class DatoValidacion(BaseModel):
    campo: str
    sugerencia: SugerenciaRespuesta | None
    vigente: ValidacionRespuesta | None
    historial: list[ValidacionRespuesta]


class ValidacionesRespuesta(BaseModel):
    documento_id: int
    version: VersionResumen
    tipo_validado: TipoDocumental | None
    clasificacion: DatoValidacion
    campos: list[DatoValidacion]
    fuera_de_esquema: list[ValidacionRespuesta] = Field(
        description="Validaciones de campos que no pertenecen al esquema del tipo validado"
    )


@enrutador.get(
    "/{tramite_id}/documentos/{documento_id}/validaciones", response_model=ValidacionesRespuesta
)
def consultar_validaciones(
    tramite_id: int, documento_id: int, usuario: Autenticado, sesion: Sesion
) -> ValidacionesRespuesta:
    """Versión vigente: sugerencias, validaciones vigentes e historial de cada dato."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    actual = validaciones.consultar(sesion, tramite, documento_id)

    def respuesta(validacion: ValidacionHumana) -> ValidacionRespuesta:
        fuente = actual.fuentes.get(validacion.fuente_id) if validacion.fuente_id else None
        return ValidacionRespuesta.desde(validacion, fuente)

    def dato(estado: validaciones.EstadoDato) -> DatoValidacion:
        return DatoValidacion(
            campo=estado.campo,
            sugerencia=_sugerencia(*estado.sugerencia) if estado.sugerencia else None,
            vigente=respuesta(estado.vigente) if estado.vigente else None,
            historial=[respuesta(v) for v in estado.historial],
        )

    return ValidacionesRespuesta(
        documento_id=actual.documento.id,
        version=VersionResumen(
            id=actual.version.id, numero=actual.version.numero, archivo_id=actual.version.archivo_id
        ),
        tipo_validado=actual.tipo_validado,
        clasificacion=dato(actual.clasificacion),
        campos=[dato(c) for c in actual.campos],
        fuera_de_esquema=[respuesta(v) for v in actual.fuera_de_esquema],
    )


@enrutador.post(
    "/{tramite_id}/documentos/{documento_id}/validaciones",
    response_model=ValidacionRegistradaRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def registrar_validacion(
    tramite_id: int,
    documento_id: int,
    nueva: NuevaValidacion,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> ValidacionRegistradaRespuesta:
    """RF-09 y RF-12: confirma o corrige la clasificación o un campo de la versión vigente."""
    # PD-05.2: las operaciones que cambian el trámite lo bloquean mientras se ejecutan.
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    registrada = validaciones.registrar(
        sesion,
        tramite=tramite,
        documento_id=documento_id,
        usuario_id=usuario.id,
        campo=nueva.campo,
        valor_validado=nueva.valor_validado,
        valor_sugerido_id=nueva.valor_sugerido_id,
        reemplaza_a_id=nueva.reemplaza_a_id,
        fuente=FuenteIndicada(**nueva.fuente.model_dump()) if nueva.fuente else None,
        solicitud_id=solicitud_id,
    )
    return ValidacionRegistradaRespuesta(
        **ValidacionRespuesta.desde(registrada.validacion, registrada.fuente).model_dump(),
        advertencias=registrada.advertencias,
    )
