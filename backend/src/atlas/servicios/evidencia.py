"""Evidencia de la decisión y línea de tiempo del trámite (RF-21, RF-22, PD-03, PD-06).

DO-2026-10-22-TAR, P11 y P12. La evidencia se reconstruye desde las relaciones de la
Figura 5.4 sin duplicar información: las validaciones son las vigentes en el instante de
la decisión (cadena de reemplazos y fecha), y los controles, los registrados en
DECISION_CONTROL. Acceso: el responsable y quien tiene una tarea asignada en el ciclo.
"""

from dataclasses import dataclass

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from atlas.persistencia.modelos import (
    CicloRevision,
    Decision,
    Documento,
    EventoAuditoria,
    FirmaSimulada,
    ReferenciaFuente,
    Tarea,
    Tramite,
    ValidacionHumana,
    ValorSugerido,
    VersionDocumental,
)
from atlas.servicios import ciclos, firma, reglas, tareas
from atlas.servicios.errores import NoEncontrado


@dataclass(frozen=True)
class ValidacionConsiderada:
    """PD-03: valor sugerido, valor validado, actor, fecha, versión y fuente."""

    validacion: ValidacionHumana
    documento: Documento
    sugerencia: ValorSugerido | None
    fuente_sugerencia: ReferenciaFuente | None
    fuente_validacion: ReferenciaFuente | None


@dataclass(frozen=True)
class Evidencia:
    decision: Decision
    tarea: Tarea
    ciclo: CicloRevision
    tramite: Tramite
    tareas_del_ciclo: list[Tarea]
    versiones: list[ciclos.VersionDelCiclo]
    validaciones: list[ValidacionConsiderada]
    controles: list[reglas.DetalleEjecucion]
    eventos: list[EventoAuditoria]
    firma: FirmaSimulada | None


def _validaciones(
    sesion: Session, versiones: list[ciclos.VersionDelCiclo], decision: Decision
) -> list[ValidacionConsiderada]:
    documentos = {v.version.id: v.documento for v in versiones}
    registradas = list(
        sesion.scalars(
            select(ValidacionHumana)
            .where(
                ValidacionHumana.version_id.in_(documentos),
                ValidacionHumana.validado_en <= decision.decidida_en,
            )
            .order_by(ValidacionHumana.version_id, ValidacionHumana.id)
        )
    )
    reemplazadas = {v.reemplaza_a_id for v in registradas if v.reemplaza_a_id is not None}
    vigentes = [v for v in registradas if v.id not in reemplazadas]
    sugerencias = {
        s.id: s
        for s in sesion.scalars(
            select(ValorSugerido).where(
                ValorSugerido.id.in_({v.valor_sugerido_id for v in vigentes} - {None})
            )
        )
    }
    ids_fuente = {v.fuente_id for v in vigentes} | {s.fuente_id for s in sugerencias.values()}
    fuentes = {
        f.id: f
        for f in sesion.scalars(
            select(ReferenciaFuente).where(ReferenciaFuente.id.in_(ids_fuente - {None}))
        )
    }
    resultado: list[ValidacionConsiderada] = []
    for validacion in vigentes:
        sugerencia = (
            sugerencias[validacion.valor_sugerido_id] if validacion.valor_sugerido_id else None
        )
        resultado.append(
            ValidacionConsiderada(
                validacion=validacion,
                documento=documentos[validacion.version_id],
                sugerencia=sugerencia,
                fuente_sugerencia=(
                    fuentes.get(sugerencia.fuente_id)
                    if sugerencia is not None and sugerencia.fuente_id
                    else None
                ),
                fuente_validacion=(
                    fuentes.get(validacion.fuente_id) if validacion.fuente_id else None
                ),
            )
        )
    return resultado


def obtener(sesion: Session, decision_id: int, usuario_id: int, *, revisor: bool) -> Evidencia:
    decision = sesion.get(Decision, decision_id)
    if decision is None:
        raise NoEncontrado("La decisión no existe o no tenés acceso")
    tarea = sesion.get_one(Tarea, decision.tarea_id)
    ciclo = sesion.get_one(CicloRevision, tarea.ciclo_revision_id)
    tramite = sesion.get_one(Tramite, ciclo.tramite_id)
    del_ciclo = ciclos.tareas(sesion, ciclo.id)
    if tramite.responsable_id != usuario_id and not (
        revisor and usuario_id in {t.asignada_a_id for t in del_ciclo}
    ):
        raise NoEncontrado("La decisión no existe o no tenés acceso")
    versiones = ciclos.versiones(sesion, ciclo.id)
    validaciones = _validaciones(sesion, versiones, decision)
    controles = tareas.controles_de_la_decision(sesion, decision.id)
    aplicada = firma.de_tramite(sesion, tramite.id)
    if aplicada is not None and aplicada.ciclo_revision_id != ciclo.id:
        aplicada = None
    decisiones = sesion.scalars(
        select(Decision.id).where(Decision.tarea_id.in_([t.id for t in del_ciclo]))
    ).all()
    entidades = (
        [("ciclo_revision", ciclo.id)]
        + [("tarea", t.id) for t in del_ciclo]
        + [("decision", d) for d in decisiones]
        + [("validacion_humana", v.validacion.id) for v in validaciones]
        + [("ejecucion_regla", c.ejecucion.id) for c in controles]
        + ([] if aplicada is None else [("firma_simulada", aplicada.id)])
    )
    eventos = list(
        sesion.scalars(
            select(EventoAuditoria)
            .where(
                EventoAuditoria.tramite_id == tramite.id,
                tuple_(EventoAuditoria.entidad_tipo, EventoAuditoria.entidad_id).in_(entidades),
            )
            .order_by(EventoAuditoria.ocurrido_en, EventoAuditoria.id)
        )
    )
    return Evidencia(
        decision=decision,
        tarea=tarea,
        ciclo=ciclo,
        tramite=tramite,
        tareas_del_ciclo=del_ciclo,
        versiones=versiones,
        validaciones=validaciones,
        controles=controles,
        eventos=eventos,
        firma=aplicada,
    )


# --- Línea de tiempo (RF-22, P11) --------------------------------------------------------


@dataclass(frozen=True)
class Hito:
    evento: EventoAuditoria
    version: VersionDocumental | None


def linea_de_tiempo(sesion: Session, tramite_id: int) -> list[Hito]:
    """Eventos del trámite en orden, con la versión relacionada cuando corresponde."""
    filas = sesion.execute(
        select(EventoAuditoria, VersionDocumental)
        .outerjoin(VersionDocumental, VersionDocumental.id == EventoAuditoria.version_id)
        .where(EventoAuditoria.tramite_id == tramite_id)
        .order_by(EventoAuditoria.ocurrido_en, EventoAuditoria.id)
    ).all()
    return [Hito(evento=e, version=v) for e, v in filas]
