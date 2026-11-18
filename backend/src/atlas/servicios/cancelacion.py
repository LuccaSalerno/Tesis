"""Cancelación del trámite por su responsable (RF-26, RN-14).

Desde Borrador, Pendiente de validación, Pendiente de aprobación u Observado (Tabla 3.VI),
con un motivo. El ciclo en curso queda cancelado y sus tareas abiertas anuladas, en la misma
transacción, con el trámite bloqueado por el llamador. Documentos, versiones,
decisiones y eventos se conservan; no genera aprobación ni firma. Cancelado es terminal (RN-15).
"""

import uuid
from typing import Final

from sqlalchemy import func
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, EstadoCiclo, EstadoTramite
from atlas.persistencia.modelos import Tramite
from atlas.servicios import ciclos
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, ErrorDominio

CANCELABLES: Final = frozenset(
    {
        EstadoTramite.BORRADOR,
        EstadoTramite.PENDIENTE_VALIDACION,
        EstadoTramite.PENDIENTE_APROBACION,
        EstadoTramite.OBSERVADO,
    }
)


def cancelar(
    sesion: Session,
    tramite: Tramite,
    *,
    usuario_id: int,
    motivo: str,
    solicitud_id: uuid.UUID | None = None,
) -> Tramite:
    if tramite.estado not in CANCELABLES:
        raise Conflicto(
            "Solo se cancela un trámite en Borrador, Pendiente de validación, "
            "Pendiente de aprobación u Observado"
        )
    motivo = motivo.strip()
    if not motivo:
        raise ErrorDominio("La cancelación exige un motivo")
    ciclo = ciclos.en_curso(sesion, tramite.id)
    if ciclo is not None:
        ciclo.estado = EstadoCiclo.CANCELADO
        ciclo.concluido_en = func.clock_timestamp()
        sesion.flush()
        registrar_evento_auditoria(
            sesion,
            accion=AccionAuditoria.CICLO_CANCELADO,
            entidad_tipo="ciclo_revision",
            entidad_id=ciclo.id,
            actor_id=usuario_id,
            tramite_id=tramite.id,
            solicitud_id=solicitud_id,
        )
        ciclos.anular_tareas_abiertas(
            sesion,
            ciclo.id,
            usuario_id=usuario_id,
            tramite_id=tramite.id,
            solicitud_id=solicitud_id,
        )
    tramite.estado = EstadoTramite.CANCELADO
    tramite.motivo_cancelacion = motivo
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.TRAMITE_CANCELADO,
        entidad_tipo="tramite",
        entidad_id=tramite.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(tramite)
    return tramite
