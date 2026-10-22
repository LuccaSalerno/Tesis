"""Dependencias comunes de la API: sesión de base, identidad y autorización (RF-01, RF-02, RN-01).

La autorización se deniega por defecto (§5.4.3). Las respuestas 401/403 no
explican el motivo; los registros guardan solo códigos técnicos e identificadores.
"""

import logging
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from atlas.autenticacion.verificador import ErrorAutenticacion, VerificadorJwt
from atlas.dominio.enumeraciones import EstadoUsuario, Rol
from atlas.registro import registrar_evento
from atlas.servicios import cuentas

_registrador = logging.getLogger("atlas.api")
_portador = HTTPBearer(auto_error=False)

NO_AUTENTICADO = "No autenticado"
NO_PERMITIDO = "Operación no permitida"


def obtener_sesion(request: Request) -> Iterator[Session]:
    """Sesión por solicitud: se confirma al terminar o se revierte ante un error.

    Una operación puede confirmar antes por sí misma cuando la tesis lo exige
    (la carga se confirma antes de iniciar Step Functions, §5.3.1).
    """
    with request.app.state.fabrica_sesiones() as sesion:
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise


def obtener_solicitud_id(request: Request) -> uuid.UUID | None:
    valor = getattr(request.state, "solicitud_id", None)
    return uuid.UUID(valor) if valor else None


@dataclass(frozen=True)
class UsuarioActual:
    id: int
    roles: frozenset[Rol]
    autorizacion_cierre: bool


def _rechazar_autenticacion(request: Request, codigo: str) -> HTTPException:
    registrar_evento(
        _registrador,
        "autenticacion_rechazada",
        logging.WARNING,
        solicitud_id=getattr(request.state, "solicitud_id", None),
        codigo_error=codigo,
    )
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, NO_AUTENTICADO, headers={"WWW-Authenticate": "Bearer"}
    )


def _denegar(request: Request, codigo: str, usuario_id: int | None = None) -> HTTPException:
    registrar_evento(
        _registrador,
        "autorizacion_denegada",
        logging.WARNING,
        solicitud_id=getattr(request.state, "solicitud_id", None),
        usuario_id=usuario_id,
        codigo_error=codigo,
    )
    return HTTPException(status.HTTP_403_FORBIDDEN, NO_PERMITIDO)


def obtener_usuario_actual(
    request: Request,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_portador)],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> UsuarioActual:
    """RF-01 y RN-01: token válido y cuenta registrada y habilitada en cada solicitud,
    aunque el token todavía no haya vencido (§5.4.3)."""
    if credenciales is None:
        raise _rechazar_autenticacion(request, "token_ausente")
    verificador: VerificadorJwt = request.app.state.verificador_jwt
    try:
        identidad = verificador.verificar(credenciales.credentials)
    except ErrorAutenticacion as error:
        raise _rechazar_autenticacion(request, error.codigo) from error
    cuenta = cuentas.buscar_por_identificador_externo(sesion, identidad.identificador_externo)
    if cuenta is None:
        raise _denegar(request, "cuenta_no_registrada")
    if cuenta.estado != EstadoUsuario.HABILITADA:
        raise _denegar(request, "cuenta_no_habilitada", cuenta.id)
    return UsuarioActual(
        id=cuenta.id, roles=cuenta.roles, autorizacion_cierre=cuenta.autorizacion_cierre
    )


def exigir_rol(rol: Rol) -> Callable[..., UsuarioActual]:
    """RF-02: la operación requiere el rol indicado (Tabla 3.II)."""

    def dependencia(
        request: Request,
        usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
    ) -> UsuarioActual:
        if rol not in usuario.roles:
            raise _denegar(request, "rol_requerido_ausente", usuario.id)
        return usuario

    return dependencia


def es_revisor(usuario: UsuarioActual) -> bool:
    """El acceso derivado de una tarea exige el rol de revisor/aprobador (RF-19, P8)."""
    return Rol.REVISOR_APROBADOR in usuario.roles
