"""Cuentas de usuario, roles y autorización de cierre (RF-25, RC-P03.2, RF-21).

Las cuentas se dan de alta por su identificador externo (sub de Cognito); el alta
no concede acceso a trámites. Solo los cambios efectivos generan eventos.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import exists, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import AccionAuditoria, EstadoUsuario, Rol
from atlas.persistencia.modelos import Usuario, UsuarioRol
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, NoEncontrado

ENTIDAD = "usuario"
BLOQUEO_INICIALIZACION = 7_410_002


@dataclass(frozen=True)
class Cuenta:
    id: int
    identificador_externo: str | None
    estado: EstadoUsuario
    roles: frozenset[Rol]
    autorizacion_cierre: bool
    nombre_visible: str | None = None


def _roles(sesion: Session, usuario_id: int) -> frozenset[Rol]:
    filas = sesion.scalars(select(UsuarioRol.rol).where(UsuarioRol.usuario_id == usuario_id))
    return frozenset(Rol(r) for r in filas)


def _cuenta(sesion: Session, usuario: Usuario) -> Cuenta:
    return Cuenta(
        id=usuario.id,
        identificador_externo=usuario.identificador_externo,
        estado=EstadoUsuario(usuario.estado),
        roles=_roles(sesion, usuario.id),
        autorizacion_cierre=usuario.autorizacion_cierre,
        nombre_visible=usuario.nombre_visible,
    )


def _obtener_modificable(sesion: Session, usuario_id: int) -> Usuario:
    usuario = sesion.get(Usuario, usuario_id, with_for_update=True)
    if usuario is None:
        raise NoEncontrado("La cuenta no existe")
    if usuario.estado == EstadoUsuario.SUPRIMIDA:
        raise Conflicto("La cuenta fue suprimida y no admite cambios")
    return usuario


def buscar_por_identificador_externo(sesion: Session, identificador_externo: str) -> Cuenta | None:
    usuario = sesion.scalar(
        select(Usuario).where(Usuario.identificador_externo == identificador_externo)
    )
    return None if usuario is None else _cuenta(sesion, usuario)


def consultar(sesion: Session, usuario_id: int) -> Cuenta:
    usuario = sesion.get(Usuario, usuario_id)
    if usuario is None:
        raise NoEncontrado("La cuenta no existe")
    return _cuenta(sesion, usuario)


def listar(sesion: Session) -> list[Cuenta]:
    return [_cuenta(sesion, u) for u in sesion.scalars(select(Usuario).order_by(Usuario.id))]


def dar_de_alta(
    sesion: Session,
    *,
    actor_id: int | None,
    identificador_externo: str,
    nombre_visible: str | None = None,
    solicitud_id: uuid.UUID | None = None,
) -> Cuenta:
    usuario = Usuario(
        identificador_externo=identificador_externo,
        estado=EstadoUsuario.HABILITADA,
        nombre_visible=nombre_visible,
    )
    try:
        with sesion.begin_nested():
            sesion.add(usuario)
            sesion.flush()
    except IntegrityError as error:
        raise Conflicto("Ya existe una cuenta con ese identificador externo") from error
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.CUENTA_ALTA,
        entidad_tipo=ENTIDAD,
        entidad_id=usuario.id,
        actor_id=actor_id,
        solicitud_id=solicitud_id,
    )
    return _cuenta(sesion, usuario)


def cambiar_habilitacion(
    sesion: Session,
    *,
    actor_id: int | None,
    usuario_id: int,
    habilitada: bool,
    solicitud_id: uuid.UUID | None = None,
) -> Cuenta:
    usuario = _obtener_modificable(sesion, usuario_id)
    nuevo = EstadoUsuario.HABILITADA if habilitada else EstadoUsuario.DESHABILITADA
    if usuario.estado != nuevo:
        usuario.estado = nuevo
        sesion.flush()
        registrar_evento_auditoria(
            sesion,
            accion=(
                AccionAuditoria.CUENTA_HABILITADA
                if habilitada
                else AccionAuditoria.CUENTA_DESHABILITADA
            ),
            entidad_tipo=ENTIDAD,
            entidad_id=usuario.id,
            actor_id=actor_id,
            solicitud_id=solicitud_id,
        )
    return _cuenta(sesion, usuario)


def cambiar_rol(
    sesion: Session,
    *,
    actor_id: int | None,
    usuario_id: int,
    rol: Rol,
    otorgado: bool,
    solicitud_id: uuid.UUID | None = None,
) -> Cuenta:
    usuario = _obtener_modificable(sesion, usuario_id)
    actual = sesion.get(UsuarioRol, (usuario_id, rol))
    if otorgado and actual is None:
        sesion.add(UsuarioRol(usuario_id=usuario_id, rol=rol))
    elif not otorgado and actual is not None:
        sesion.delete(actual)
    else:
        return _cuenta(sesion, usuario)
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.ROL_OTORGADO if otorgado else AccionAuditoria.ROL_RETIRADO,
        entidad_tipo=ENTIDAD,
        entidad_id=usuario.id,
        actor_id=actor_id,
        solicitud_id=solicitud_id,
    )
    return _cuenta(sesion, usuario)


def cambiar_autorizacion_cierre(
    sesion: Session,
    *,
    actor_id: int | None,
    usuario_id: int,
    otorgada: bool,
    solicitud_id: uuid.UUID | None = None,
) -> Cuenta:
    """RC-P03.2: permiso adicional de la cuenta; no da acceso a ningún trámite."""
    usuario = _obtener_modificable(sesion, usuario_id)
    if usuario.autorizacion_cierre != otorgada:
        usuario.autorizacion_cierre = otorgada
        sesion.flush()
        registrar_evento_auditoria(
            sesion,
            accion=(
                AccionAuditoria.AUTORIZACION_CIERRE_OTORGADA
                if otorgada
                else AccionAuditoria.AUTORIZACION_CIERRE_RETIRADA
            ),
            entidad_tipo=ENTIDAD,
            entidad_id=usuario.id,
            actor_id=actor_id,
            solicitud_id=solicitud_id,
        )
    return _cuenta(sesion, usuario)


def existe_administrador(sesion: Session) -> bool:
    return bool(
        sesion.scalar(select(exists().where(UsuarioRol.rol == Rol.ADMINISTRADOR_OPERATIVO)))
    )


def crear_administrador_inicial(sesion: Session, identificador_externo: str) -> Cuenta:
    """Operación manual del operador (DT-AUT-02): solo si todavía no hay administradores.

    Se atribuye al sistema; nunca se expone por HTTP.
    """
    # Serializa inicializaciones concurrentes hasta el fin de la transacción.
    sesion.execute(text("SELECT pg_advisory_xact_lock(:clave)"), {"clave": BLOQUEO_INICIALIZACION})
    if existe_administrador(sesion):
        raise Conflicto("Ya existe un administrador operativo")
    cuenta = dar_de_alta(sesion, actor_id=None, identificador_externo=identificador_externo)
    return cambiar_rol(
        sesion, actor_id=None, usuario_id=cuenta.id, rol=Rol.ADMINISTRADOR_OPERATIVO, otorgado=True
    )


def cambiar_nombre(
    sesion: Session,
    *,
    actor_id: int,
    usuario_id: int,
    nombre_visible: str | None,
    solicitud_id: uuid.UUID | None = None,
) -> Cuenta:
    """DO-2026-10-22-WEB F5: el administrador carga el nombre que muestra la interfaz."""
    usuario = _obtener_modificable(sesion, usuario_id)
    if usuario.nombre_visible != nombre_visible:
        usuario.nombre_visible = nombre_visible
        sesion.flush()
        registrar_evento_auditoria(
            sesion,
            accion=AccionAuditoria.CUENTA_NOMBRE_CAMBIADO,
            entidad_tipo=ENTIDAD,
            entidad_id=usuario.id,
            actor_id=actor_id,
            solicitud_id=solicitud_id,
        )
    return _cuenta(sesion, usuario)


def directorio(sesion: Session, ids: list[int]) -> dict[int, str | None]:
    """Solo id y nombre visible: lo necesario para mostrar quién actuó (F5)."""
    filas = sesion.execute(
        select(Usuario.id, Usuario.nombre_visible).where(Usuario.id.in_(ids))
    ).all()
    return {i: n for i, n in filas}
