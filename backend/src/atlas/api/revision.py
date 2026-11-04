"""Flujo de revisión: plantillas, ciclos, tareas, decisiones, línea de tiempo y evidencia.

RF-17 a RF-22, RN-07, RN-08, RN-09, RN-13, PD-02, PD-03, RC-P03, DO-2026-10-22-TAR.
Rutas: RC-P01-009 y PD-06-001.

Permisos (Tabla 3.II): el administrador operativo configura plantillas y asigna tareas,
sin acceso al contenido documental (RF-24); el responsable envía a validación, confirma
el flujo y subsana; solo el revisor/aprobador asignado decide (RN-08). Lo que no se puede
ver responde 404, igual que lo inexistente.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from atlas.api.dependencias import (
    Administrador,
    Autenticado,
    Nombre,
    Responsable,
    Revisor,
    Sesion,
    SolicitudId,
    acceso_de_consulta,
    es_revisor,
)
from atlas.api.tramites import Localizador, TramiteRespuesta, localizador_de
from atlas.api.vinculos import ControlRespuesta, EjecucionRespuesta
from atlas.dominio.enumeraciones import (
    AlcancePlantilla,
    ClaseSugerencia,
    EstadoCiclo,
    EstadoTarea,
    EstadoTramite,
    MotivoAusencia,
    ResultadoAuditoria,
    Rol,
    TipoActor,
    TipoDecision,
    TipoValidacion,
)
from atlas.persistencia.modelos import (
    AsignacionTarea,
    CicloRevision,
    Decision,
    EventoAuditoria,
    FirmaSimulada,
    Tarea,
    VersionDocumental,
)
from atlas.servicios import (
    cancelacion,
    ciclos,
    evidencia,
    firma,
    plantillas,
    reglas,
    tareas,
    tramites,
)
from atlas.servicios.errores import NoEncontrado

enrutador = APIRouter(tags=["revision"])


# --- Plantillas (RC-P03.1, P1) ----------------------------------------------------------


class PasoEntrada(BaseModel):
    nombre: Nombre
    revisor_por_defecto_id: int


class NuevaPlantilla(BaseModel):
    model_config = {"extra": "forbid"}

    nombre: Nombre
    alcance: AlcancePlantilla
    pasos: list[PasoEntrada] = Field(min_length=1, max_length=plantillas.MAX_PASOS)


class PasoRespuesta(BaseModel):
    orden: int
    nombre: str
    rol_requerido: Rol
    revisor_por_defecto_id: int


class PlantillaRespuesta(BaseModel):
    id: int
    nombre: str
    alcance: AlcancePlantilla
    version: int
    activa: bool
    creada_por_id: int
    creada_en: datetime
    desactivada_en: datetime | None
    pasos: list[PasoRespuesta]

    @classmethod
    def desde(cls, actual: plantillas.Plantilla) -> "PlantillaRespuesta":
        p = actual.plantilla
        return cls(
            id=p.id,
            nombre=p.nombre,
            alcance=p.alcance,
            version=p.version,
            activa=p.activa,
            creada_por_id=p.creada_por_id,
            creada_en=p.creada_en,
            desactivada_en=p.desactivada_en,
            pasos=[
                PasoRespuesta(
                    orden=s.orden,
                    nombre=s.nombre,
                    rol_requerido=s.rol_requerido,
                    revisor_por_defecto_id=s.revisor_por_defecto_id,
                )
                for s in actual.pasos
            ],
        )


@enrutador.post(
    "/plantillas-flujo", response_model=PlantillaRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_plantilla(
    nueva: NuevaPlantilla, admin: Administrador, sesion: Sesion, solicitud_id: SolicitudId
) -> PlantillaRespuesta:
    """Reemplaza a la plantilla activa del mismo alcance, que queda desactivada."""
    return PlantillaRespuesta.desde(
        plantillas.crear(
            sesion,
            admin_id=admin.id,
            nombre=nueva.nombre,
            alcance=nueva.alcance,
            pasos=[plantillas.PasoNuevo(p.nombre, p.revisor_por_defecto_id) for p in nueva.pasos],
            solicitud_id=solicitud_id,
        )
    )


@enrutador.get("/plantillas-flujo", response_model=list[PlantillaRespuesta])
def listar_plantillas(_: Administrador, sesion: Sesion) -> list[PlantillaRespuesta]:
    return [PlantillaRespuesta.desde(p) for p in plantillas.listar(sesion)]


@enrutador.post("/plantillas-flujo/{plantilla_id}/desactivacion", response_model=PlantillaRespuesta)
def desactivar_plantilla(
    plantilla_id: int, admin: Administrador, sesion: Sesion, solicitud_id: SolicitudId
) -> PlantillaRespuesta:
    return PlantillaRespuesta.desde(
        plantillas.desactivar(sesion, plantilla_id, admin.id, solicitud_id)
    )


# --- Transiciones del responsable (Tabla 3.VI, P3, P9) ----------------------------------


@enrutador.post("/tramites/{tramite_id}/envio-a-validacion", response_model=TramiteRespuesta)
def enviar_a_validacion(
    tramite_id: int, usuario: Responsable, sesion: Sesion, solicitud_id: SolicitudId
) -> TramiteRespuesta:
    """Borrador → Pendiente de validación, con al menos un documento incorporado."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    return TramiteRespuesta.desde(
        tramites.enviar_a_validacion(sesion, tramite, usuario.id, solicitud_id)
    )


@enrutador.post("/tramites/{tramite_id}/subsanacion", response_model=TramiteRespuesta)
def subsanar(
    tramite_id: int, usuario: Responsable, sesion: Sesion, solicitud_id: SolicitudId
) -> TramiteRespuesta:
    """RN-13: Observado → Pendiente de validación sin crear versiones."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    return TramiteRespuesta.desde(tramites.subsanar(sesion, tramite, usuario.id, solicitud_id))


class NuevaCancelacion(BaseModel):
    motivo: Annotated[str, Field(min_length=1, max_length=1000, pattern=r"\S")]


@enrutador.post("/tramites/{tramite_id}/cancelacion", response_model=TramiteRespuesta)
def cancelar(
    tramite_id: int,
    nueva: NuevaCancelacion,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> TramiteRespuesta:
    """RF-26, RN-14: cancelación con motivo; el ciclo en curso y sus tareas abiertas dejan de
    admitir decisiones (DO-2026-10-23-CIERRE P1 y P2)."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    return TramiteRespuesta.desde(
        cancelacion.cancelar(
            sesion, tramite, usuario_id=usuario.id, motivo=nueva.motivo, solicitud_id=solicitud_id
        )
    )


# --- Flujo sugerido y ciclos (RF-17, RF-18, P2, P4) -------------------------------------


class PasoSugeridoRespuesta(BaseModel):
    orden: int
    nombre: str
    revisor_por_defecto_id: int
    asignada_a_id: int | None = Field(
        description="Null: el revisor por defecto es el responsable o no está habilitado; la "
        "tarea se creará sin asignar y señalada al administrador"
    )


class FlujoSugeridoRespuesta(BaseModel):
    alcance: AlcancePlantilla
    plantilla_id: int | None
    plantilla_nombre: str | None
    version_plantilla: int | None
    pasos: list[PasoSugeridoRespuesta]
    documentos_sin_validar: list[int] = Field(
        description="Documentos sin la clasificación o los campos de su esquema validados"
    )


@enrutador.get("/tramites/{tramite_id}/flujo-sugerido", response_model=FlujoSugeridoRespuesta)
def consultar_flujo_sugerido(
    tramite_id: int, usuario: Responsable, sesion: Sesion
) -> FlujoSugeridoRespuesta:
    """RF-17: la sugerencia no crea tareas; queda inactiva hasta que el responsable confirma."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id)
    sugerencia = ciclos.sugerir(sesion, tramite)
    plantilla = sugerencia.plantilla.plantilla if sugerencia.plantilla else None
    return FlujoSugeridoRespuesta(
        alcance=sugerencia.alcance,
        plantilla_id=plantilla.id if plantilla else None,
        plantilla_nombre=plantilla.nombre if plantilla else None,
        version_plantilla=plantilla.version if plantilla else None,
        pasos=[
            PasoSugeridoRespuesta(
                orden=p.orden,
                nombre=p.nombre,
                revisor_por_defecto_id=p.revisor_por_defecto_id,
                asignada_a_id=p.asignada_a_id,
            )
            for p in sugerencia.pasos
        ],
        documentos_sin_validar=ciclos.datos_faltantes(sesion, tramite.id),
    )


class ConfirmacionFlujo(BaseModel):
    model_config = {"extra": "forbid"}

    plantilla_id: int
    version_plantilla: int


class VersionCicloRespuesta(BaseModel):
    documento_id: int
    documento_nombre: str
    version_id: int
    version_numero: int


class TareaResumen(BaseModel):
    id: int
    ciclo_revision_id: int
    orden: int
    nombre: str
    rol_requerido: Rol
    estado: EstadoTarea
    asignada_a_id: int | None
    creada_en: datetime
    actualizada_en: datetime
    decision_id: int | None

    @classmethod
    def desde(cls, tarea: Tarea, decision: Decision | None) -> "TareaResumen":
        return cls(
            id=tarea.id,
            ciclo_revision_id=tarea.ciclo_revision_id,
            orden=tarea.orden,
            nombre=tarea.nombre,
            rol_requerido=tarea.rol_requerido,
            estado=tarea.estado,
            asignada_a_id=tarea.asignada_a_id,
            creada_en=tarea.creada_en,
            actualizada_en=tarea.actualizada_en,
            decision_id=None if decision is None else decision.id,
        )


class CicloRespuesta(BaseModel):
    id: int
    tramite_id: int
    numero: int
    estado: EstadoCiclo
    plantilla_flujo_id: int
    confirmado_por_id: int
    confirmado_en: datetime
    concluido_en: datetime | None
    versiones: list[VersionCicloRespuesta]
    tareas: list[TareaResumen]


def _versiones(sesion: Session, ciclo_id: int) -> list[VersionCicloRespuesta]:
    return [
        VersionCicloRespuesta(
            documento_id=v.documento.id,
            documento_nombre=v.documento.nombre,
            version_id=v.version.id,
            version_numero=v.version.numero,
        )
        for v in ciclos.versiones(sesion, ciclo_id)
    ]


def _tareas(sesion: Session, ciclo_id: int) -> list[TareaResumen]:
    return [
        TareaResumen.desde(t, tareas.decision(sesion, t.id))
        for t in ciclos.tareas(sesion, ciclo_id)
    ]


def _ciclo(sesion: Session, ciclo: CicloRevision) -> CicloRespuesta:
    return CicloRespuesta(
        id=ciclo.id,
        tramite_id=ciclo.tramite_id,
        numero=ciclo.numero,
        estado=ciclo.estado,
        plantilla_flujo_id=ciclo.plantilla_flujo_id,
        confirmado_por_id=ciclo.confirmado_por_id,
        confirmado_en=ciclo.confirmado_en,
        concluido_en=ciclo.concluido_en,
        versiones=_versiones(sesion, ciclo.id),
        tareas=_tareas(sesion, ciclo.id),
    )


@enrutador.post(
    "/tramites/{tramite_id}/ciclos",
    response_model=CicloRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def confirmar_flujo(
    tramite_id: int,
    confirmacion: ConfirmacionFlujo,
    usuario: Responsable,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> CicloRespuesta:
    """Tabla 3.VI: confirma los datos requeridos y el flujo, y crea el ciclo y sus tareas."""
    tramite = tramites.obtener_accesible(sesion, tramite_id, usuario.id, bloquear=True)
    ciclo = ciclos.confirmar_flujo(
        sesion,
        tramite=tramite,
        usuario_id=usuario.id,
        plantilla_id=confirmacion.plantilla_id,
        version_plantilla=confirmacion.version_plantilla,
        solicitud_id=solicitud_id,
    )
    return _ciclo(sesion, ciclo)


@enrutador.get("/tramites/{tramite_id}/ciclos", response_model=list[CicloRespuesta])
def listar_ciclos(tramite_id: int, usuario: Autenticado, sesion: Sesion) -> list[CicloRespuesta]:
    """RN-09: cada ciclo con sus versiones consideradas y sus tareas. El revisor ve los
    ciclos en los que tiene una tarea asignada."""
    acceso = acceso_de_consulta(sesion, tramite_id, usuario)
    return [
        _ciclo(sesion, c)
        for c in ciclos.listar(sesion, acceso.tramite.id)
        if acceso.es_responsable
        or usuario.id in {t.asignada_a_id for t in ciclos.tareas(sesion, c.id)}
    ]


# --- Tareas (RF-19, RF-20, P5 a P7) -----------------------------------------------------


class TramiteResumen(BaseModel):
    id: int
    titulo: str | None = Field(
        description="Nulo para el administrador operativo: solo ve el identificador "
        "(RF-24, DO-2026-10-23-DIF)"
    )
    estado: EstadoTramite


class CicloResumen(BaseModel):
    id: int
    numero: int
    estado: EstadoCiclo


class TareaListada(TareaResumen):
    tramite: TramiteResumen
    ciclo: CicloResumen

    @classmethod
    def con_contexto(
        cls, sesion: Session, contexto: tareas.TareaConContexto, *, con_titulo: bool = True
    ) -> "TareaListada":
        return cls(
            **TareaResumen.desde(
                contexto.tarea, tareas.decision(sesion, contexto.tarea.id)
            ).model_dump(),
            tramite=TramiteResumen(
                id=contexto.tramite.id,
                titulo=contexto.tramite.titulo if con_titulo else None,
                estado=contexto.tramite.estado,
            ),
            ciclo=CicloResumen(
                id=contexto.ciclo.id, numero=contexto.ciclo.numero, estado=contexto.ciclo.estado
            ),
        )


class DecisionRespuesta(BaseModel):
    id: int
    tarea_id: int
    actor_id: int
    tipo: TipoDecision
    motivo: str | None
    decidida_en: datetime
    controles_considerados: list[int] = Field(
        description="Ejecuciones de reglas registradas en DECISION_CONTROL (PD-02)"
    )

    @classmethod
    def desde(cls, sesion: Session, decision: Decision) -> "DecisionRespuesta":
        return cls(
            id=decision.id,
            tarea_id=decision.tarea_id,
            actor_id=decision.actor_id,
            tipo=decision.tipo,
            motivo=decision.motivo,
            decidida_en=decision.decidida_en,
            controles_considerados=[
                d.ejecucion.id for d in tareas.controles_de_la_decision(sesion, decision.id)
            ],
        )


class AsignacionRespuesta(BaseModel):
    anterior_id: int | None
    asignada_a_id: int
    asignada_por_id: int | None = Field(description="Null: asignación por defecto del flujo")
    asignada_en: datetime

    @classmethod
    def desde(cls, asignacion: AsignacionTarea) -> "AsignacionRespuesta":
        return cls(
            anterior_id=asignacion.anterior_id,
            asignada_a_id=asignacion.asignada_a_id,
            asignada_por_id=asignacion.asignada_por_id,
            asignada_en=asignacion.asignada_en,
        )


class TareaDetalle(TareaListada):
    versiones: list[VersionCicloRespuesta]
    controles: list[ControlRespuesta] = Field(
        description="Decidida: los registrados en DECISION_CONTROL; abierta: los vigentes del "
        "ciclo, que son los que se registrarán al decidir"
    )
    controles_pendientes: bool = Field(
        description="PD-02.3; las reglas se ejecutan de forma síncrona (DO-2026-10-22-REG P4)"
    )
    decision: DecisionRespuesta | None
    asignaciones: list[AsignacionRespuesta]


def _control(control: reglas.Control) -> ControlRespuesta:
    return ControlRespuesta(
        codigo_regla=control.regla.codigo,
        version_regla=control.regla.version,
        descripcion=control.regla.descripcion,
        vinculo_id=control.vinculo_id,
        resultado=control.resultado,
        explicacion=control.explicacion,
        ejecucion=None if control.detalle is None else EjecucionRespuesta.desde(control.detalle),
    )


def _control_registrado(detalle: reglas.DetalleEjecucion) -> ControlRespuesta:
    return ControlRespuesta(
        codigo_regla=detalle.regla.codigo,
        version_regla=detalle.regla.version,
        descripcion=detalle.regla.descripcion,
        vinculo_id=detalle.ejecucion.vinculo_id,
        resultado=detalle.ejecucion.resultado,
        explicacion=detalle.ejecucion.explicacion,
        ejecucion=EjecucionRespuesta.desde(detalle),
    )


@enrutador.get("/tareas", response_model=list[TareaListada])
def listar_mis_tareas(usuario: Autenticado, sesion: Sesion) -> list[TareaListada]:
    return [
        TareaListada.con_contexto(sesion, c) for c in tareas.listar_asignadas(sesion, usuario.id)
    ]


@enrutador.get("/tareas/sin-asignar", response_model=list[TareaListada])
def listar_tareas_sin_asignar(_: Administrador, sesion: Sesion) -> list[TareaListada]:
    """RC-P03.3.2: tareas abiertas señaladas al administrador; solo metadatos (RF-24)."""
    return [
        TareaListada.con_contexto(sesion, c, con_titulo=False)
        for c in tareas.listar_sin_asignar(sesion)
    ]


@enrutador.get("/tareas/{tarea_id}", response_model=TareaDetalle)
def abrir_tarea(tarea_id: int, usuario: Autenticado, sesion: Sesion) -> TareaDetalle:
    contexto = tareas.obtener_visible(sesion, tarea_id, usuario.id, revisor=es_revisor(usuario))
    resuelta = tareas.decision(sesion, tarea_id)
    controles = (
        [_control(c) for c in ciclos.controles(sesion, contexto.ciclo)]
        if resuelta is None
        else [_control_registrado(d) for d in tareas.controles_de_la_decision(sesion, resuelta.id)]
    )
    return TareaDetalle(
        **TareaListada.con_contexto(sesion, contexto).model_dump(),
        versiones=_versiones(sesion, contexto.ciclo.id),
        controles=controles,
        controles_pendientes=False,
        decision=None if resuelta is None else DecisionRespuesta.desde(sesion, resuelta),
        asignaciones=[AsignacionRespuesta.desde(a) for a in tareas.asignaciones(sesion, tarea_id)],
    )


class NuevaAsignacion(BaseModel):
    model_config = {"extra": "forbid"}

    usuario_id: int


@enrutador.put("/tareas/{tarea_id}/asignacion", response_model=TareaListada)
def asignar_tarea(
    tarea_id: int,
    asignacion: NuevaAsignacion,
    admin: Administrador,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> TareaListada:
    """RF-19: asigna o reasigna una tarea abierta; cada cambio queda registrado."""
    contexto = tareas.asignar(
        sesion,
        tarea_id=tarea_id,
        usuario_id=asignacion.usuario_id,
        admin_id=admin.id,
        solicitud_id=solicitud_id,
    )
    return TareaListada.con_contexto(sesion, contexto, con_titulo=False)


class NuevaDecision(BaseModel):
    model_config = {"extra": "forbid"}

    tipo: TipoDecision
    motivo: str | None = Field(default=None, max_length=5000)


@enrutador.post(
    "/tareas/{tarea_id}/decision",
    response_model=DecisionRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def decidir(
    tarea_id: int,
    nueva: NuevaDecision,
    usuario: Revisor,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> DecisionRespuesta:
    """RF-20, RN-08: aprobación u observación (con motivo) del revisor/aprobador asignado."""
    decision = tareas.decidir(
        sesion,
        tarea_id=tarea_id,
        usuario_id=usuario.id,
        tipo=nueva.tipo,
        motivo=nueva.motivo,
        solicitud_id=solicitud_id,
    )
    return DecisionRespuesta.desde(sesion, decision)


# --- Línea de tiempo (RF-22, P11) -------------------------------------------------------


class EventoRespuesta(BaseModel):
    """RF-21: actor, instante, acción, entidad afectada, resultado y versión relacionada."""

    id: int
    ocurrido_en: datetime
    actor_tipo: TipoActor
    actor_id: int | None
    accion: str
    entidad_tipo: str
    entidad_id: int
    resultado: ResultadoAuditoria
    version_id: int | None

    @classmethod
    def desde(cls, evento: EventoAuditoria) -> "EventoRespuesta":
        return cls(
            id=evento.id,
            ocurrido_en=evento.ocurrido_en,
            actor_tipo=evento.actor_tipo,
            actor_id=evento.actor_id,
            accion=evento.accion,
            entidad_tipo=evento.entidad_tipo,
            entidad_id=evento.entidad_id,
            resultado=evento.resultado,
            version_id=evento.version_id,
        )


class VersionEnlazada(BaseModel):
    documento_id: int
    version_id: int
    version_numero: int
    archivo_id: int


class HitoRespuesta(EventoRespuesta):
    version: VersionEnlazada | None = Field(
        description="Versión relacionada con el evento, si quien consulta puede abrirla"
    )


@enrutador.get("/tramites/{tramite_id}/linea-tiempo", response_model=list[HitoRespuesta])
def consultar_linea_de_tiempo(
    tramite_id: int, usuario: Autenticado, sesion: Sesion
) -> list[HitoRespuesta]:
    """RF-22: historial del trámite en orden, con acceso a la versión de cada evento. El
    revisor ve todos los eventos (solo metadatos) y abre las versiones de sus ciclos."""
    acceso = acceso_de_consulta(sesion, tramite_id, usuario)
    return [
        HitoRespuesta(
            **EventoRespuesta.desde(h.evento).model_dump(),
            version=(
                VersionEnlazada(
                    documento_id=h.version.documento_id,
                    version_id=h.version.id,
                    version_numero=h.version.numero,
                    archivo_id=h.version.archivo_id,
                )
                if h.version is not None and acceso.permite(h.version.id)
                else None
            ),
        )
        for h in evidencia.linea_de_tiempo(sesion, acceso.tramite.id)
    ]


# --- Firma digital simulada (RF-23, RN-11, RN-15, DO-2026-10-23-VER P5 y P6) -----------


class NuevaFirma(BaseModel):
    version_id: int = Field(description="Versión vigente comprendida en el ciclo aprobado")


class FirmaRespuesta(BaseModel):
    """V11: firmante, instante, versión, ciclo y referencia de integridad recalculable. Es
    una simulación sin validez jurídica."""

    id: int
    leyenda: str = Field(default=firma.LEYENDA, description="Rótulo obligatorio en la interfaz")
    simulada: bool = True
    tramite_id: int
    ciclo_revision_id: int
    ciclo_numero: int
    documento_id: int
    version_id: int
    version_numero: int
    firmante_id: int
    firmada_en: datetime
    huella_archivo: str = Field(description="SHA-256 del archivo de la versión firmada")
    algoritmo: str = "SHA-256"
    registro_canonico: str = Field(
        description="JSON cuyo SHA-256 es la referencia de integridad (claves ordenadas)"
    )
    referencia_integridad: str

    @classmethod
    def desde(cls, sesion: Session, aplicada: FirmaSimulada) -> "FirmaRespuesta":
        version = sesion.get_one(VersionDocumental, aplicada.version_id)
        huella = firma.huella(sesion, aplicada)
        return cls(
            id=aplicada.id,
            tramite_id=aplicada.tramite_id,
            ciclo_revision_id=aplicada.ciclo_revision_id,
            ciclo_numero=sesion.get_one(CicloRevision, aplicada.ciclo_revision_id).numero,
            documento_id=version.documento_id,
            version_id=version.id,
            version_numero=version.numero,
            firmante_id=aplicada.firmante_id,
            firmada_en=aplicada.firmada_en,
            huella_archivo=huella,
            registro_canonico=firma.registro_canonico(
                version_id=version.id,
                huella=huella,
                firmante_id=aplicada.firmante_id,
                firmada_en=aplicada.firmada_en,
            ),
            referencia_integridad=aplicada.referencia_integridad,
        )


# --- Evidencia de la decisión (PD-03, PD-06, P12) ---------------------------------------


class ValidacionEvidencia(BaseModel):
    validacion_id: int
    documento_id: int
    version_id: int
    clase: ClaseSugerencia
    campo: str
    valor_sugerido: str | None
    valor_sugerido_id: int | None
    localizador_sugerido: Localizador | None
    valor_validado: str | None
    tipo: TipoValidacion
    motivo_ausencia: MotivoAusencia | None
    validador_id: int
    validado_en: datetime
    reemplaza_a_id: int | None
    localizador_validado: Localizador | None


class EvidenciaRespuesta(BaseModel):
    """Cadena V1 a V4 desde una decisión. Mismo contrato para la vista, las pruebas EVD-01 y
    la demo (PD-03.4)."""

    decision: DecisionRespuesta
    tarea: TareaResumen
    ciclo: CicloResumen
    tramite: TramiteResumen
    tareas_del_ciclo: list[TareaResumen]
    versiones: list[VersionCicloRespuesta]
    validaciones: list[ValidacionEvidencia]
    controles: list[EjecucionRespuesta]
    eventos: list[EventoRespuesta]
    firma: FirmaRespuesta | None = Field(
        default=None, description="Firma simulada aplicada a una versión de este ciclo (V11)"
    )


@enrutador.get("/decisiones/{decision_id}/evidencia", response_model=EvidenciaRespuesta)
def consultar_evidencia(
    decision_id: int, usuario: Autenticado, sesion: Sesion
) -> EvidenciaRespuesta:
    actual = evidencia.obtener(sesion, decision_id, usuario.id, revisor=es_revisor(usuario))
    return EvidenciaRespuesta(
        decision=DecisionRespuesta.desde(sesion, actual.decision),
        tarea=TareaResumen.desde(actual.tarea, actual.decision),
        ciclo=CicloResumen(
            id=actual.ciclo.id, numero=actual.ciclo.numero, estado=actual.ciclo.estado
        ),
        tramite=TramiteResumen(
            id=actual.tramite.id, titulo=actual.tramite.titulo, estado=actual.tramite.estado
        ),
        tareas_del_ciclo=_tareas(sesion, actual.ciclo.id),
        versiones=_versiones(sesion, actual.ciclo.id),
        validaciones=[
            ValidacionEvidencia(
                validacion_id=v.validacion.id,
                documento_id=v.documento.id,
                version_id=v.validacion.version_id,
                clase=v.validacion.clase,
                campo=v.validacion.campo,
                valor_sugerido=None if v.sugerencia is None else v.sugerencia.valor,
                valor_sugerido_id=v.validacion.valor_sugerido_id,
                localizador_sugerido=localizador_de(v.fuente_sugerencia),
                valor_validado=v.validacion.valor_validado,
                tipo=v.validacion.tipo,
                motivo_ausencia=v.validacion.motivo_ausencia,
                validador_id=v.validacion.validador_id,
                validado_en=v.validacion.validado_en,
                reemplaza_a_id=v.validacion.reemplaza_a_id,
                localizador_validado=localizador_de(v.fuente_validacion),
            )
            for v in actual.validaciones
        ],
        controles=[EjecucionRespuesta.desde(c) for c in actual.controles],
        eventos=[EventoRespuesta.desde(e) for e in actual.eventos],
        firma=None if actual.firma is None else FirmaRespuesta.desde(sesion, actual.firma),
    )


@enrutador.post(
    "/tramites/{tramite_id}/firma",
    response_model=FirmaRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def firmar(
    tramite_id: int,
    nueva: NuevaFirma,
    usuario: Revisor,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> FirmaRespuesta:
    """RF-23: firma simulada de una versión del ciclo aprobado; el trámite queda Cerrado.
    Solo el revisor/aprobador con autorización de cierre y una tarea en ese ciclo."""
    acceso = tramites.obtener_para_consulta(sesion, tramite_id, usuario.id, revisor=True)
    # PD-05.2: bloquea el trámite; una incorporación simultánea espera o ya terminó.
    sesion.refresh(acceso.tramite, with_for_update=True)
    aplicada = firma.firmar(
        sesion,
        tramite=acceso.tramite,
        version_id=nueva.version_id,
        usuario_id=usuario.id,
        autorizacion_cierre=usuario.autorizacion_cierre,
        solicitud_id=solicitud_id,
    )
    return FirmaRespuesta.desde(sesion, aplicada)


@enrutador.get("/tramites/{tramite_id}/firma", response_model=FirmaRespuesta)
def consultar_firma(tramite_id: int, usuario: Autenticado, sesion: Sesion) -> FirmaRespuesta:
    """V11: la firma sigue consultable con el trámite Cerrado (RN-15)."""
    acceso = acceso_de_consulta(sesion, tramite_id, usuario)
    aplicada = firma.de_tramite(sesion, acceso.tramite.id)
    if aplicada is None or not acceso.permite(aplicada.version_id):
        raise NoEncontrado("El trámite no tiene una firma simulada")
    return FirmaRespuesta.desde(sesion, aplicada)
