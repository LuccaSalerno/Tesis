"""Plantillas de flujo configuradas por el administrador operativo (RF-17).

Inmutables y versionadas por alcance, de uno a tres pasos con un
revisor/aprobador por defecto; a lo sumo una activa por alcance. Una plantilla nueva
reemplaza a la activa de su alcance. Se desactivan, nunca se borran. El revisor del
último paso necesita autorización de cierre.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, AlcancePlantilla, EstadoUsuario, Rol
from atlas.persistencia.modelos import PlantillaFlujo, PlantillaFlujoPaso, Usuario, UsuarioRol
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, ErrorDominio, NoEncontrado

MAX_PASOS = 3  # flujos secuenciales de una a tres tareas


@dataclass(frozen=True)
class PasoNuevo:
    nombre: str
    revisor_por_defecto_id: int


@dataclass(frozen=True)
class Plantilla:
    plantilla: PlantillaFlujo
    pasos: list[PlantillaFlujoPaso]


def es_revisor_habilitado(sesion: Session, usuario_id: int) -> bool:
    """RF-19: cuenta habilitada con el rol de revisor/aprobador."""
    usuario = sesion.get(Usuario, usuario_id)
    if usuario is None or usuario.estado != EstadoUsuario.HABILITADA:
        return False
    return (
        sesion.scalar(
            select(UsuarioRol.usuario_id).where(
                UsuarioRol.usuario_id == usuario_id, UsuarioRol.rol == Rol.REVISOR_APROBADOR
            )
        )
        is not None
    )


def _exigir_revisor(sesion: Session, usuario_id: int, *, cierre: bool) -> None:
    if not es_revisor_habilitado(sesion, usuario_id):
        raise ErrorDominio(f"La cuenta {usuario_id} no es un revisor/aprobador habilitado")
    if cierre and not sesion.get_one(Usuario, usuario_id).autorizacion_cierre:
        raise ErrorDominio("El revisor del último paso necesita autorización de cierre")


def _pasos(sesion: Session, plantilla_id: int) -> list[PlantillaFlujoPaso]:
    return list(
        sesion.scalars(
            select(PlantillaFlujoPaso)
            .where(PlantillaFlujoPaso.plantilla_flujo_id == plantilla_id)
            .order_by(PlantillaFlujoPaso.orden)
        )
    )


def obtener(sesion: Session, plantilla_id: int) -> Plantilla:
    plantilla = sesion.get(PlantillaFlujo, plantilla_id)
    if plantilla is None:
        raise NoEncontrado("La plantilla no existe")
    return Plantilla(plantilla, _pasos(sesion, plantilla.id))


def activa(sesion: Session, alcance: AlcancePlantilla) -> Plantilla | None:
    plantilla = sesion.scalar(
        select(PlantillaFlujo).where(PlantillaFlujo.alcance == alcance, PlantillaFlujo.activa)
    )
    return None if plantilla is None else Plantilla(plantilla, _pasos(sesion, plantilla.id))


def listar(sesion: Session) -> list[Plantilla]:
    return [
        Plantilla(p, _pasos(sesion, p.id))
        for p in sesion.scalars(
            select(PlantillaFlujo).order_by(PlantillaFlujo.alcance, PlantillaFlujo.version)
        )
    ]


def _desactivar(
    sesion: Session, plantilla: PlantillaFlujo, admin_id: int, solicitud_id: uuid.UUID | None
) -> None:
    plantilla.activa = False
    plantilla.desactivada_por_id = admin_id
    plantilla.desactivada_en = func.clock_timestamp()
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.PLANTILLA_DESACTIVADA,
        entidad_tipo="plantilla_flujo",
        entidad_id=plantilla.id,
        actor_id=admin_id,
        solicitud_id=solicitud_id,
    )


def crear(
    sesion: Session,
    *,
    admin_id: int,
    nombre: str,
    alcance: AlcancePlantilla,
    pasos: list[PasoNuevo],
    solicitud_id: uuid.UUID | None = None,
) -> Plantilla:
    if not 1 <= len(pasos) <= MAX_PASOS:
        raise ErrorDominio(f"Una plantilla tiene de uno a {MAX_PASOS} pasos")
    for orden, paso in enumerate(pasos, start=1):
        _exigir_revisor(sesion, paso.revisor_por_defecto_id, cierre=orden == len(pasos))
    # Serializa las altas del mismo alcance: versión correlativa y una sola activa.
    sesion.execute(
        text("SELECT pg_advisory_xact_lock(hashtext('atlas.plantilla_flujo:' || :alcance))"),
        {"alcance": alcance.value},
    )
    anterior = activa(sesion, alcance)
    if anterior is not None:
        _desactivar(sesion, anterior.plantilla, admin_id, solicitud_id)
    version = (
        sesion.scalar(
            select(func.max(PlantillaFlujo.version)).where(PlantillaFlujo.alcance == alcance)
        )
        or 0
    ) + 1
    plantilla = PlantillaFlujo(
        nombre=nombre, alcance=alcance, version=version, creada_por_id=admin_id
    )
    sesion.add(plantilla)
    sesion.flush()
    sesion.add_all(
        PlantillaFlujoPaso(
            plantilla_flujo_id=plantilla.id,
            orden=orden,
            nombre=paso.nombre,
            rol_requerido=Rol.REVISOR_APROBADOR,
            revisor_por_defecto_id=paso.revisor_por_defecto_id,
        )
        for orden, paso in enumerate(pasos, start=1)
    )
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.PLANTILLA_CREADA,
        entidad_tipo="plantilla_flujo",
        entidad_id=plantilla.id,
        actor_id=admin_id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(plantilla)
    return Plantilla(plantilla, _pasos(sesion, plantilla.id))


def desactivar(
    sesion: Session, plantilla_id: int, admin_id: int, solicitud_id: uuid.UUID | None = None
) -> Plantilla:
    actual = obtener(sesion, plantilla_id)
    if not actual.plantilla.activa:
        raise Conflicto("La plantilla ya está desactivada")
    _desactivar(sesion, actual.plantilla, admin_id, solicitud_id)
    sesion.refresh(actual.plantilla)
    return actual
