"""Tareas: listado, vista, asignación y decisión del revisor/aprobador.

RF-19, RF-20, RN-07, RN-08, RN-09, PD-02, PD-05, RC-P03.3, RF-24,
DO-2026-10-22-TAR (P5, P6 y P7).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    EstadoCiclo,
    EstadoTarea,
    EstadoTramite,
    TipoDecision,
)
from atlas.persistencia.modelos import (
    AsignacionTarea,
    CicloRevision,
    Decision,
    DecisionControl,
    EjecucionRegla,
    Tarea,
    Tramite,
)
from atlas.servicios import ciclos, plantillas, reglas
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, ErrorDominio, NoEncontrado, NoPermitido

# PD-05.3: mensaje fijo para la decisión sobre una tarea de un ciclo desplazado.
TAREA_DESACTUALIZADA = "La documentación del trámite cambió; esta tarea ya no admite decisiones"


@dataclass(frozen=True)
class TareaConContexto:
    tarea: Tarea
    ciclo: CicloRevision
    tramite: Tramite


def _contexto(sesion: Session, tarea: Tarea, *, bloquear: bool = False) -> TareaConContexto:
    ciclo = sesion.get_one(CicloRevision, tarea.ciclo_revision_id)
    tramite = sesion.get_one(Tramite, ciclo.tramite_id, with_for_update=bloquear)
    return TareaConContexto(tarea=tarea, ciclo=ciclo, tramite=tramite)


def _no_encontrada() -> NoEncontrado:
    return NoEncontrado("La tarea no existe o no tenés acceso")


def obtener_visible(
    sesion: Session, tarea_id: int, usuario_id: int, *, revisor: bool
) -> TareaConContexto:
    """El responsable del trámite y el revisor/aprobador con una tarea asignada en el mismo
    ciclo (P8)."""
    tarea = sesion.get(Tarea, tarea_id)
    if tarea is None:
        raise _no_encontrada()
    contexto = _contexto(sesion, tarea)
    if contexto.tramite.responsable_id != usuario_id and not (
        revisor
        and usuario_id in {t.asignada_a_id for t in ciclos.tareas(sesion, contexto.ciclo.id)}
    ):
        raise _no_encontrada()
    return contexto


def listar_asignadas(sesion: Session, usuario_id: int) -> list[TareaConContexto]:
    return [
        _contexto(sesion, t)
        for t in sesion.scalars(
            select(Tarea).where(Tarea.asignada_a_id == usuario_id).order_by(Tarea.id)
        )
    ]


def listar_sin_asignar(sesion: Session) -> list[TareaConContexto]:
    """Para el administrador (RC-P03.3.2): solo metadatos, sin contenido documental (RF-24)."""
    return [
        _contexto(sesion, t)
        for t in sesion.scalars(
            select(Tarea)
            .where(Tarea.asignada_a_id.is_(None), Tarea.estado.in_(ciclos.ABIERTAS))
            .order_by(Tarea.id)
        )
    ]


def decision(sesion: Session, tarea_id: int) -> Decision | None:
    return sesion.scalar(select(Decision).where(Decision.tarea_id == tarea_id))


def controles_de_la_decision(sesion: Session, decision_id: int) -> list[reglas.DetalleEjecucion]:
    """V4: las ejecuciones registradas al decidir, nunca «la última disponible»."""
    return reglas.detalles(
        sesion,
        sesion.scalars(
            select(EjecucionRegla)
            .join(DecisionControl, DecisionControl.ejecucion_regla_id == EjecucionRegla.id)
            .where(DecisionControl.decision_id == decision_id)
            .order_by(EjecucionRegla.id)
        ).all(),
    )


# --- Asignación (RF-19, P7) -------------------------------------------------------------


def asignar(
    sesion: Session,
    *,
    tarea_id: int,
    usuario_id: int,
    admin_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> TareaConContexto:
    """Asigna o reasigna una tarea abierta a un revisor/aprobador habilitado que no sea el
    responsable del trámite (RC-P03.3)."""
    tarea = sesion.get(Tarea, tarea_id)
    if tarea is None:
        raise _no_encontrada()
    contexto = _contexto(sesion, tarea, bloquear=True)  # PD-05.2
    sesion.refresh(tarea)
    if tarea.estado not in ciclos.ABIERTAS:
        raise Conflicto("Solo se asigna una tarea abierta")
    if usuario_id == contexto.tramite.responsable_id:
        raise ErrorDominio("Una tarea no se asigna al responsable de su trámite")
    if not plantillas.es_revisor_habilitado(sesion, usuario_id):
        raise ErrorDominio("La cuenta no está habilitada para el rol requerido")
    if tarea.asignada_a_id == usuario_id:
        return contexto  # sin cambios: no se registra nada
    anterior = tarea.asignada_a_id
    tarea.asignada_a_id = usuario_id
    sesion.add(
        AsignacionTarea(
            tarea_id=tarea.id,
            anterior_id=anterior,
            asignada_a_id=usuario_id,
            asignada_por_id=admin_id,
        )
    )
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=(
            AccionAuditoria.TAREA_ASIGNADA if anterior is None else AccionAuditoria.TAREA_REASIGNADA
        ),
        entidad_tipo="tarea",
        entidad_id=tarea.id,
        actor_id=admin_id,
        tramite_id=contexto.tramite.id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(tarea)
    return contexto


def asignaciones(sesion: Session, tarea_id: int) -> list[AsignacionTarea]:
    return list(
        sesion.scalars(
            select(AsignacionTarea)
            .where(AsignacionTarea.tarea_id == tarea_id)
            .order_by(AsignacionTarea.id)
        )
    )


# --- Decisión (RF-20, RN-08, P5, P6) ----------------------------------------------------


def _auditar(
    sesion: Session,
    accion: AccionAuditoria,
    entidad_tipo: str,
    entidad_id: int,
    actor_id: int,
    tramite_id: int,
    solicitud_id: uuid.UUID | None,
) -> None:
    registrar_evento_auditoria(
        sesion,
        accion=accion,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        actor_id=actor_id,
        tramite_id=tramite_id,
        solicitud_id=solicitud_id,
    )


def decidir(
    sesion: Session,
    *,
    tarea_id: int,
    usuario_id: int,
    tipo: TipoDecision,
    motivo: str | None,
    solicitud_id: uuid.UUID | None = None,
) -> Decision:
    tarea = sesion.get(Tarea, tarea_id)
    if tarea is None:
        raise _no_encontrada()
    # PD-05.2: bloquea el trámite; una incorporación simultánea espera o ya terminó.
    contexto = _contexto(sesion, tarea, bloquear=True)
    sesion.refresh(tarea)
    sesion.refresh(contexto.ciclo)
    # Sin acceso: 404, como si no existiera. El rol lo exige la ruta (RN-08).
    obtener_visible(sesion, tarea_id, usuario_id, revisor=True)
    if tarea.asignada_a_id != usuario_id:
        raise NoPermitido("Solo el revisor/aprobador asignado resuelve la tarea")
    if tarea.estado == EstadoTarea.ANULADA or contexto.ciclo.estado == EstadoCiclo.DESPLAZADO:
        raise Conflicto(TAREA_DESACTUALIZADA)
    if (
        tarea.estado != EstadoTarea.PENDIENTE
        or contexto.ciclo.estado != EstadoCiclo.EN_CURSO
        or contexto.tramite.estado != EstadoTramite.PENDIENTE_APROBACION
    ):
        raise Conflicto("La tarea no admite decisiones en su estado actual")
    motivo = motivo.strip() if motivo else None
    if tipo == TipoDecision.OBSERVACION and not motivo:
        raise ErrorDominio("La observación exige un motivo")
    # P6: los controles que se mostraban en la tarea, por identificador de ejecución.
    considerados = [
        c.detalle.ejecucion.id
        for c in ciclos.controles(sesion, contexto.ciclo)
        if c.detalle is not None
    ]
    nueva = Decision(tarea_id=tarea.id, actor_id=usuario_id, tipo=tipo, motivo=motivo)
    sesion.add(nueva)
    sesion.flush()
    sesion.add_all(
        DecisionControl(decision_id=nueva.id, ejecucion_regla_id=e) for e in sorted(considerados)
    )
    tramite = contexto.tramite
    ciclo = contexto.ciclo
    siguientes = [t for t in ciclos.tareas(sesion, ciclo.id) if t.orden > tarea.orden]
    if tipo == TipoDecision.APROBACION:
        tarea.estado = EstadoTarea.APROBADA
        sesion.flush()
        _auditar(
            sesion,
            AccionAuditoria.TAREA_APROBADA,
            "decision",
            nueva.id,
            usuario_id,
            tramite.id,
            solicitud_id,
        )
        if siguientes:
            siguiente = siguientes[0]
            siguiente.estado = EstadoTarea.PENDIENTE
            sesion.flush()
            registrar_evento_auditoria(
                sesion,
                accion=AccionAuditoria.TAREA_HABILITADA,
                entidad_tipo="tarea",
                entidad_id=siguiente.id,
                actor_id=None,
                tramite_id=tramite.id,
                solicitud_id=solicitud_id,
            )
        else:
            ciclo.estado = EstadoCiclo.APROBADO
            ciclo.concluido_en = func.clock_timestamp()
            tramite.estado = EstadoTramite.APROBADO
            sesion.flush()
            _auditar(
                sesion,
                AccionAuditoria.TRAMITE_APROBADO,
                "tramite",
                tramite.id,
                usuario_id,
                tramite.id,
                solicitud_id,
            )
    else:
        tarea.estado = EstadoTarea.OBSERVADA
        ciclo.estado = EstadoCiclo.OBSERVADO
        ciclo.concluido_en = func.clock_timestamp()
        tramite.estado = EstadoTramite.OBSERVADO
        sesion.flush()
        _auditar(
            sesion,
            AccionAuditoria.TAREA_OBSERVADA,
            "decision",
            nueva.id,
            usuario_id,
            tramite.id,
            solicitud_id,
        )
        for siguiente in siguientes:
            siguiente.estado = EstadoTarea.DESCARTADA
            sesion.flush()
            registrar_evento_auditoria(
                sesion,
                accion=AccionAuditoria.TAREA_DESCARTADA,
                entidad_tipo="tarea",
                entidad_id=siguiente.id,
                actor_id=None,
                tramite_id=tramite.id,
                solicitud_id=solicitud_id,
            )
        _auditar(
            sesion,
            AccionAuditoria.TRAMITE_OBSERVADO,
            "tramite",
            tramite.id,
            usuario_id,
            tramite.id,
            solicitud_id,
        )
    sesion.refresh(nueva)
    return nueva
