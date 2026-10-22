"""Registro de eventos de auditoría (RF-21, RN-10). Solo inserta: los eventos son inmutables."""

import uuid

from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, ResultadoAuditoria, TipoActor
from atlas.persistencia.modelos import EventoAuditoria


def registrar_evento_auditoria(
    sesion: Session,
    *,
    accion: AccionAuditoria,
    entidad_tipo: str,
    entidad_id: int,
    actor_id: int | None,
    tramite_id: int | None = None,
    version_id: int | None = None,
    solicitud_id: uuid.UUID | None = None,
    resultado: ResultadoAuditoria = ResultadoAuditoria.EXITO,
) -> EventoAuditoria:
    """`actor_id=None` atribuye la acción al sistema (por ejemplo, la inicialización manual)."""
    evento = EventoAuditoria(
        tramite_id=tramite_id,
        actor_id=actor_id,
        actor_tipo=TipoActor.SISTEMA if actor_id is None else TipoActor.USUARIO,
        version_id=version_id,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        accion=accion,
        resultado=resultado,
        solicitud_id=solicitud_id,
    )
    sesion.add(evento)
    sesion.flush()
    return evento
