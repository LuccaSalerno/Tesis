"""Firma digital simulada y cierre del trámite (RF-23, RN-11, RN-15, V11).

Solo la aplica un revisor/aprobador con autorización de cierre
 que tuvo una tarea asignada en el ciclo aprobado, sobre una versión vigente de
ese ciclo. La referencia de integridad es el SHA-256 de un registro canónico (versión,
huella del archivo, firmante e instante), visible y recalculable. Es una simulación: no
tiene validez jurídica y así se rotula en la interfaz y en la API.
"""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, EstadoCiclo, EstadoTramite
from atlas.persistencia.modelos import (
    Archivo,
    CicloRevision,
    CicloRevisionVersion,
    Documento,
    FirmaSimulada,
    Tramite,
    VersionDocumental,
)
from atlas.servicios import ciclos
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, NoPermitido
from atlas.servicios.tramites import ESTADOS_TERMINALES

LEYENDA: Final = "Firma digital simulada — sin validez jurídica"


def registro_canonico(
    *, version_id: int, huella: str, firmante_id: int, firmada_en: datetime
) -> str:
    """JSON con claves ordenadas y sin espacios: quien tenga estos datos recalcula la
    referencia."""
    return json.dumps(
        {
            "firmada_en": firmada_en.astimezone(UTC).isoformat(),
            "firmante_id": firmante_id,
            "huella_archivo": huella,
            "version_id": version_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def referencia_integridad(
    *, version_id: int, huella: str, firmante_id: int, firmada_en: datetime
) -> str:
    registro = registro_canonico(
        version_id=version_id, huella=huella, firmante_id=firmante_id, firmada_en=firmada_en
    )
    return hashlib.sha256(registro.encode()).hexdigest()


def ciclo_aprobado(sesion: Session, tramite_id: int) -> CicloRevision | None:
    """El último ciclo aprobado del trámite."""
    return sesion.scalar(
        select(CicloRevision)
        .where(CicloRevision.tramite_id == tramite_id, CicloRevision.estado == EstadoCiclo.APROBADO)
        .order_by(CicloRevision.numero.desc())
        .limit(1)
    )


def de_tramite(sesion: Session, tramite_id: int) -> FirmaSimulada | None:
    return sesion.scalar(select(FirmaSimulada).where(FirmaSimulada.tramite_id == tramite_id))


def huella(sesion: Session, firma: FirmaSimulada) -> str:
    version = sesion.get_one(VersionDocumental, firma.version_id)
    return sesion.get_one(Archivo, version.archivo_id).huella


def firmar(
    sesion: Session,
    *,
    tramite: Tramite,
    version_id: int,
    usuario_id: int,
    autorizacion_cierre: bool,
    solicitud_id: uuid.UUID | None = None,
) -> FirmaSimulada:
    """Aplica la firma simulada y cierra el trámite (bloqueado por el llamador)."""
    if tramite.estado in ESTADOS_TERMINALES:
        raise Conflicto("El trámite está cerrado o cancelado y no admite una firma")
    if not autorizacion_cierre:
        raise NoPermitido("Firmar exige la autorización de cierre")
    ciclo = ciclo_aprobado(sesion, tramite.id)
    if tramite.estado != EstadoTramite.APROBADO or ciclo is None:
        raise Conflicto("Solo se firma un trámite Aprobado")
    if usuario_id not in {t.asignada_a_id for t in ciclos.tareas(sesion, ciclo.id)}:
        raise NoPermitido("Firma quien tuvo una tarea asignada en el ciclo aprobado")
    del_ciclo = sesion.get(CicloRevisionVersion, (ciclo.id, version_id))
    version = sesion.get(VersionDocumental, version_id)
    if del_ciclo is None or version is None:
        raise Conflicto("La versión no pertenece al ciclo aprobado")
    if sesion.get_one(Documento, version.documento_id).version_vigente_id != version.id:
        raise Conflicto("La versión ya no es la vigente de su documento")
    firmada_en = datetime.now(UTC)
    firma = FirmaSimulada(
        tramite_id=tramite.id,
        ciclo_revision_id=ciclo.id,
        version_id=version.id,
        firmante_id=usuario_id,
        referencia_integridad=referencia_integridad(
            version_id=version.id,
            huella=sesion.get_one(Archivo, version.archivo_id).huella,
            firmante_id=usuario_id,
            firmada_en=firmada_en,
        ),
        firmada_en=firmada_en,
    )
    sesion.add(firma)
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.FIRMA_SIMULADA_APLICADA,
        entidad_tipo="firma_simulada",
        entidad_id=firma.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        version_id=version.id,
        solicitud_id=solicitud_id,
    )
    tramite.estado = EstadoTramite.CERRADO
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.TRAMITE_CERRADO,
        entidad_tipo="tramite",
        entidad_id=tramite.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        version_id=version.id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(firma)
    return firma
