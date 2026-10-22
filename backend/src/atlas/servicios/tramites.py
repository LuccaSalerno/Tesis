"""Trámites: creación, listado y apertura con acceso derivado (RF-03, RF-02, §5.2).

El acceso a un trámite no se registra por separado: se deriva de ser su
responsable o de tener una tarea asignada en él. Las tareas llegan con el hito
1.8; hasta entonces el acceso es solo del responsable.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, EstadoTramite, TipoDocumental
from atlas.persistencia.modelos import Documento, Tramite, VersionDocumental
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


def listar_accesibles(sesion: Session, usuario_id: int) -> list[Tramite]:
    consulta = select(Tramite).where(Tramite.responsable_id == usuario_id).order_by(Tramite.id)
    return list(sesion.scalars(consulta))


def obtener_accesible(
    sesion: Session, tramite_id: int, usuario_id: int, *, bloquear: bool = False
) -> Tramite:
    """Inexistente y sin acceso responden igual, para no revelar qué trámites existen."""
    tramite = sesion.get(Tramite, tramite_id, with_for_update=bloquear)
    if tramite is None or tramite.responsable_id != usuario_id:
        raise NoEncontrado("El trámite no existe o no tenés acceso")
    return tramite


def exigir_no_terminal(tramite: Tramite) -> None:
    """RN-15: Cerrado y Cancelado no admiten nuevas cargas ni incorporaciones."""
    if tramite.estado in ESTADOS_TERMINALES:
        raise Conflicto("El trámite está cerrado o cancelado y no admite nueva documentación")


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
