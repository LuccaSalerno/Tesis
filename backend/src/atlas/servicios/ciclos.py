"""Sugerencia y confirmación del flujo, ciclos de revisión y su desplazamiento.

RF-17, RF-18, RN-09, RN-12, Tabla 3.VI.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    AlcancePlantilla,
    EstadoCiclo,
    EstadoTarea,
    EstadoTramite,
    TipoDocumental,
)
from atlas.persistencia.modelos import (
    AsignacionTarea,
    CicloRevision,
    CicloRevisionVersion,
    Documento,
    Tarea,
    Tramite,
    VersionDocumental,
)
from atlas.procesamiento import esquemas
from atlas.servicios import plantillas, reglas
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, NoEncontrado

ABIERTAS = frozenset({EstadoTarea.EN_ESPERA, EstadoTarea.PENDIENTE})


# --- Sugerencia (RF-17) -------------------------------------------------------------


@dataclass(frozen=True)
class PasoSugerido:
    orden: int
    nombre: str
    revisor_por_defecto_id: int
    asignada_a_id: int | None  # None: el revisor por defecto es el responsable


@dataclass(frozen=True)
class Sugerencia:
    alcance: AlcancePlantilla
    plantilla: plantillas.Plantilla | None
    pasos: list[PasoSugerido]


def _alcance(sesion: Session, tramite_id: int) -> AlcancePlantilla:
    """Con un documento vigente clasificado como contrato, la plantilla de contratos."""
    con_contrato = sesion.scalar(
        select(Documento.id)
        .where(Documento.tramite_id == tramite_id, Documento.tipo == TipoDocumental.CONTRATO)
        .limit(1)
    )
    return AlcancePlantilla.GENERAL if con_contrato is None else AlcancePlantilla.CONTRATO


def _asignable(sesion: Session, tramite: Tramite, usuario_id: int) -> bool:
    return usuario_id != tramite.responsable_id and plantillas.es_revisor_habilitado(
        sesion, usuario_id
    )


def sugerir(sesion: Session, tramite: Tramite) -> Sugerencia:
    """Se calcula al consultarla y no se guarda: no existe ninguna tarea hasta confirmarla."""
    alcance = _alcance(sesion, tramite.id)
    plantilla = plantillas.activa(sesion, alcance)
    pasos = (
        []
        if plantilla is None
        else [
            PasoSugerido(
                orden=p.orden,
                nombre=p.nombre,
                revisor_por_defecto_id=p.revisor_por_defecto_id,
                asignada_a_id=(
                    p.revisor_por_defecto_id
                    if _asignable(sesion, tramite, p.revisor_por_defecto_id)
                    else None
                ),
            )
            for p in plantilla.pasos
        ]
    )
    return Sugerencia(alcance=alcance, plantilla=plantilla, pasos=pasos)


# --- Confirmación (Tabla 3.VI, RF-18) -----------------------------------------------


def datos_faltantes(sesion: Session, tramite_id: int) -> list[int]:
    """Documentos cuya versión vigente no tiene validada la clasificación o algún campo del
    esquema de su tipo sin resolver."""
    faltantes: list[int] = []
    for documento in sesion.scalars(
        select(Documento).where(Documento.tramite_id == tramite_id).order_by(Documento.id)
    ):
        validado = reglas.estado_validado(sesion, documento)
        # Cada campo resuelto por una persona, con valor o ausente.
        if validado.tipo is None or set(validado.campos) | set(validado.ausentes) != {
            c.nombre for c in esquemas.CAMPOS[validado.tipo]
        }:
            faltantes.append(documento.id)
    return faltantes


def confirmar_flujo(
    sesion: Session,
    *,
    tramite: Tramite,
    usuario_id: int,
    plantilla_id: int,
    version_plantilla: int,
    solicitud_id: uuid.UUID | None = None,
) -> CicloRevision:
    """Pendiente de validación → Pendiente de aprobación: crea el ciclo con las versiones
    vigentes y todas sus tareas en una transacción. El trámite llega bloqueado."""
    if tramite.estado != EstadoTramite.PENDIENTE_VALIDACION:
        raise Conflicto("El flujo se confirma con el trámite en Pendiente de validación")
    sugerencia = sugerir(sesion, tramite)
    if sugerencia.plantilla is None or (
        sugerencia.plantilla.plantilla.id,
        sugerencia.plantilla.plantilla.version,
    ) != (plantilla_id, version_plantilla):
        raise Conflicto("La plantilla indicada ya no es la sugerida para este trámite")
    faltantes = datos_faltantes(sesion, tramite.id)
    if faltantes:
        raise Conflicto(
            "Faltan validar la clasificación o campos de los documentos "
            + ", ".join(str(d) for d in faltantes)
        )
    numero = (
        sesion.scalar(
            select(func.max(CicloRevision.numero)).where(CicloRevision.tramite_id == tramite.id)
        )
        or 0
    ) + 1
    ciclo = CicloRevision(
        tramite_id=tramite.id,
        numero=numero,
        plantilla_flujo_id=plantilla_id,
        confirmado_por_id=usuario_id,
    )
    sesion.add(ciclo)
    sesion.flush()
    sesion.add_all(
        CicloRevisionVersion(ciclo_revision_id=ciclo.id, version_id=v)
        for v in sesion.scalars(
            select(Documento.version_vigente_id).where(Documento.tramite_id == tramite.id)
        )
    )
    tareas: list[tuple[Tarea, PasoSugerido]] = []
    for paso in sugerencia.pasos:
        tarea = Tarea(
            ciclo_revision_id=ciclo.id,
            orden=paso.orden,
            nombre=paso.nombre,
            rol_requerido=sugerencia.plantilla.pasos[paso.orden - 1].rol_requerido,
            estado=EstadoTarea.PENDIENTE if paso.orden == 1 else EstadoTarea.EN_ESPERA,
            asignada_a_id=paso.asignada_a_id,
        )
        sesion.add(tarea)
        tareas.append((tarea, paso))
    sesion.flush()
    tramite.estado = EstadoTramite.PENDIENTE_APROBACION
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.FLUJO_CONFIRMADO,
        entidad_tipo="ciclo_revision",
        entidad_id=ciclo.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    for tarea, paso in tareas:
        if paso.asignada_a_id is not None:
            sesion.add(AsignacionTarea(tarea_id=tarea.id, asignada_a_id=paso.asignada_a_id))
            sesion.flush()
        # La asignación por defecto proviene de la configuración del administrador
        #: se atribuye al sistema. Sin asignar queda señalada.
        registrar_evento_auditoria(
            sesion,
            accion=(
                AccionAuditoria.TAREA_SIN_ASIGNAR
                if paso.asignada_a_id is None
                else AccionAuditoria.TAREA_ASIGNADA
            ),
            entidad_tipo="tarea",
            entidad_id=tarea.id,
            actor_id=None,
            tramite_id=tramite.id,
            solicitud_id=solicitud_id,
        )
    sesion.refresh(ciclo)
    return ciclo


# --- Consulta ---------------------------------------------------------------------------


def obtener(sesion: Session, ciclo_id: int) -> CicloRevision:
    ciclo = sesion.get(CicloRevision, ciclo_id)
    if ciclo is None:
        raise NoEncontrado("El ciclo de revisión no existe o no tenés acceso")
    return ciclo


def listar(sesion: Session, tramite_id: int) -> list[CicloRevision]:
    return list(
        sesion.scalars(
            select(CicloRevision)
            .where(CicloRevision.tramite_id == tramite_id)
            .order_by(CicloRevision.numero)
        )
    )


def en_curso(sesion: Session, tramite_id: int) -> CicloRevision | None:
    return sesion.scalar(
        select(CicloRevision).where(
            CicloRevision.tramite_id == tramite_id,
            CicloRevision.estado == EstadoCiclo.EN_CURSO,
        )
    )


@dataclass(frozen=True)
class VersionDelCiclo:
    documento: Documento
    version: VersionDocumental


def versiones(sesion: Session, ciclo_id: int) -> list[VersionDelCiclo]:
    """RN-09, V1: el conjunto exacto de versiones consideradas en el ciclo."""
    filas = sesion.execute(
        select(Documento, VersionDocumental)
        .join(VersionDocumental, VersionDocumental.documento_id == Documento.id)
        .join(CicloRevisionVersion, CicloRevisionVersion.version_id == VersionDocumental.id)
        .where(CicloRevisionVersion.ciclo_revision_id == ciclo_id)
        .order_by(Documento.id)
    ).all()
    return [VersionDelCiclo(documento=d, version=v) for d, v in filas]


def tareas(sesion: Session, ciclo_id: int) -> list[Tarea]:
    return list(
        sesion.scalars(
            select(Tarea).where(Tarea.ciclo_revision_id == ciclo_id).order_by(Tarea.orden)
        )
    )


def controles(sesion: Session, ciclo: CicloRevision) -> list[reglas.Control]:
    """Las ejecuciones vigentes cuyas versiones pertenecen todas al ciclo, más las
    reglas no aplicables. Es lo que muestra la tarea y lo que registra DECISION_CONTROL."""
    del_ciclo = {v.version.id for v in versiones(sesion, ciclo.id)}
    return [
        c
        for c in reglas.vigentes(sesion, ciclo.tramite_id)
        if c.detalle is None or {v.version.id for v in c.detalle.versiones} <= del_ciclo
    ]


# --- Desplazamiento (RN-12) -----------------------------------------------


def desplazar_en_curso(
    sesion: Session,
    *,
    tramite_id: int,
    usuario_id: int,
    version_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> CicloRevision | None:
    """Un cambio confirmado del conjunto documental desplaza el ciclo en curso: sus tareas
    abiertas dejan de admitir decisiones. Las decisiones ya tomadas quedan en el historial.
    Corre en la misma transacción que la incorporación."""
    ciclo = en_curso(sesion, tramite_id)
    if ciclo is None:
        return None
    ciclo.estado = EstadoCiclo.DESPLAZADO
    ciclo.concluido_en = func.clock_timestamp()
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.CICLO_DESPLAZADO,
        entidad_tipo="ciclo_revision",
        entidad_id=ciclo.id,
        actor_id=usuario_id,
        tramite_id=tramite_id,
        version_id=version_id,
        solicitud_id=solicitud_id,
    )
    anular_tareas_abiertas(
        sesion,
        ciclo.id,
        usuario_id=usuario_id,
        tramite_id=tramite_id,
        version_id=version_id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(ciclo)
    return ciclo


def anular_tareas_abiertas(
    sesion: Session,
    ciclo_id: int,
    *,
    usuario_id: int,
    tramite_id: int,
    version_id: int | None = None,
    solicitud_id: uuid.UUID | None = None,
) -> None:
    for tarea in tareas(sesion, ciclo_id):
        if tarea.estado in ABIERTAS:
            tarea.estado = EstadoTarea.ANULADA
            sesion.flush()
            registrar_evento_auditoria(
                sesion,
                accion=AccionAuditoria.TAREA_ANULADA,
                entidad_tipo="tarea",
                entidad_id=tarea.id,
                actor_id=usuario_id,
                tramite_id=tramite_id,
                version_id=version_id,
                solicitud_id=solicitud_id,
            )
