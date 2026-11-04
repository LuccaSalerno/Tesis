"""Trámites: creación, listado, apertura con acceso derivado y transiciones del
responsable (RF-03, RF-02, §5.2, Tabla 3.VI).

El acceso a un trámite no se registra por separado: se deriva de ser su responsable o
de tener una tarea asignada en él. En este último caso es de solo lectura y se limita a
las versiones de los ciclos de esas tareas (DO-2026-10-22-TAR, P8).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, EstadoTramite, TipoDocumental
from atlas.persistencia.modelos import (
    CicloRevision,
    CicloRevisionVersion,
    Documento,
    Tarea,
    Tramite,
    VersionDocumental,
)
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, NoEncontrado

ESTADOS_TERMINALES = frozenset({EstadoTramite.CERRADO, EstadoTramite.CANCELADO})


@dataclass(frozen=True)
class DocumentoVigente:
    id: int
    nombre: str
    tipo: TipoDocumental | None
    version_vigente_id: int
    numero_version: int
    archivo_id: int


def crear(
    sesion: Session,
    *,
    responsable_id: int,
    titulo: str,
    descripcion: str | None,
    solicitud_id: uuid.UUID | None = None,
) -> Tramite:
    tramite = Tramite(responsable_id=responsable_id, titulo=titulo, descripcion=descripcion)
    sesion.add(tramite)
    sesion.flush()
    sesion.refresh(tramite)
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.TRAMITE_CREADO,
        entidad_tipo="tramite",
        entidad_id=tramite.id,
        actor_id=responsable_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    return tramite


@dataclass(frozen=True)
class Acceso:
    """Acceso de consulta: `versiones` es None para el responsable (todo el trámite) o el
    conjunto de versiones de los ciclos en los que la persona tiene una tarea asignada."""

    tramite: Tramite
    versiones: frozenset[int] | None

    @property
    def es_responsable(self) -> bool:
        return self.versiones is None

    def permite(self, version_id: int) -> bool:
        return self.versiones is None or version_id in self.versiones


def listar_accesibles(sesion: Session, usuario_id: int, *, revisor: bool = False) -> list[Tramite]:
    condicion = Tramite.responsable_id == usuario_id
    if revisor:
        con_tarea = (
            select(CicloRevision.tramite_id)
            .join(Tarea, Tarea.ciclo_revision_id == CicloRevision.id)
            .where(Tarea.asignada_a_id == usuario_id)
        )
        condicion = condicion | Tramite.id.in_(con_tarea)
    return list(sesion.scalars(select(Tramite).where(condicion).order_by(Tramite.id)))


def _no_encontrado() -> NoEncontrado:
    return NoEncontrado("El trámite no existe o no tenés acceso")


def obtener_accesible(
    sesion: Session, tramite_id: int, usuario_id: int, *, bloquear: bool = False
) -> Tramite:
    """Operaciones del responsable. Inexistente y sin acceso responden igual, para no
    revelar qué trámites existen."""
    tramite = sesion.get(Tramite, tramite_id, with_for_update=bloquear)
    if tramite is None or tramite.responsable_id != usuario_id:
        raise _no_encontrado()
    return tramite


def versiones_asignadas(sesion: Session, tramite_id: int, usuario_id: int) -> frozenset[int]:
    """Versiones de los ciclos del trámite en los que la persona tiene una tarea asignada."""
    return frozenset(
        sesion.scalars(
            select(CicloRevisionVersion.version_id)
            .join(CicloRevision, CicloRevision.id == CicloRevisionVersion.ciclo_revision_id)
            .join(Tarea, Tarea.ciclo_revision_id == CicloRevision.id)
            .where(CicloRevision.tramite_id == tramite_id, Tarea.asignada_a_id == usuario_id)
        )
    )


def obtener_para_consulta(
    sesion: Session, tramite_id: int, usuario_id: int, *, revisor: bool
) -> Acceso:
    """Consultas: el responsable ve todo; el revisor/aprobador, las versiones de sus ciclos."""
    tramite = sesion.get(Tramite, tramite_id)
    if tramite is None:
        raise _no_encontrado()
    if tramite.responsable_id == usuario_id:
        return Acceso(tramite, None)
    versiones = versiones_asignadas(sesion, tramite.id, usuario_id) if revisor else frozenset()
    if not versiones:
        raise _no_encontrado()
    return Acceso(tramite, versiones)


def exigir_no_terminal(tramite: Tramite) -> None:
    """RN-15: Cerrado y Cancelado no admiten nuevas cargas ni incorporaciones."""
    if tramite.estado in ESTADOS_TERMINALES:
        raise Conflicto("El trámite está cerrado o cancelado y no admite nueva documentación")


def _cambiar_estado(
    sesion: Session,
    tramite: Tramite,
    estado: EstadoTramite,
    accion: AccionAuditoria,
    usuario_id: int,
    solicitud_id: uuid.UUID | None,
) -> Tramite:
    tramite.estado = estado
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=accion,
        entidad_tipo="tramite",
        entidad_id=tramite.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(tramite)
    return tramite


def enviar_a_validacion(
    sesion: Session, tramite: Tramite, usuario_id: int, solicitud_id: uuid.UUID | None = None
) -> Tramite:
    """Tabla 3.VI: Borrador → Pendiente de validación, con al menos un documento incorporado."""
    if tramite.estado != EstadoTramite.BORRADOR:
        raise Conflicto("Solo un trámite en Borrador se envía a validación")
    primero = select(Documento.id).where(Documento.tramite_id == tramite.id).limit(1)
    if sesion.scalar(primero) is None:
        raise Conflicto("El trámite necesita al menos un documento incorporado")
    return _cambiar_estado(
        sesion,
        tramite,
        EstadoTramite.PENDIENTE_VALIDACION,
        AccionAuditoria.TRAMITE_ENVIADO_A_VALIDACION,
        usuario_id,
        solicitud_id,
    )


def subsanar(
    sesion: Session, tramite: Tramite, usuario_id: int, solicitud_id: uuid.UUID | None = None
) -> Tramite:
    """RN-13: Observado → Pendiente de validación sin crear versiones. Las decisiones del
    ciclo observado quedan en el historial y no habilitan la continuidad (P9)."""
    if tramite.estado != EstadoTramite.OBSERVADO:
        raise Conflicto("Solo un trámite Observado admite la subsanación")
    return _cambiar_estado(
        sesion,
        tramite,
        EstadoTramite.PENDIENTE_VALIDACION,
        AccionAuditoria.TRAMITE_SUBSANADO,
        usuario_id,
        solicitud_id,
    )


def documentos_vigentes(sesion: Session, tramite_id: int) -> list[DocumentoVigente]:
    filas = sesion.execute(
        select(Documento, VersionDocumental)
        .join(VersionDocumental, VersionDocumental.id == Documento.version_vigente_id)
        .where(Documento.tramite_id == tramite_id)
        .order_by(Documento.id)
    ).all()
    return [
        DocumentoVigente(
            id=documento.id,
            nombre=documento.nombre,
            tipo=None if documento.tipo is None else TipoDocumental(documento.tipo),
            version_vigente_id=version.id,
            numero_version=version.numero,
            archivo_id=version.archivo_id,
        )
        for documento, version in filas
    ]


def documentos_de_versiones(sesion: Session, versiones: frozenset[int]) -> set[int]:
    return set(
        sesion.scalars(
            select(VersionDocumental.documento_id).where(VersionDocumental.id.in_(versiones))
        )
    )


def documento_del_tramite(sesion: Session, tramite: Tramite, documento_id: int) -> Documento:
    documento = sesion.get(Documento, documento_id)
    if documento is None or documento.tramite_id != tramite.id:
        raise NoEncontrado("El documento no existe en este trámite")
    return documento
