"""Cuentas de usuario y roles (RF-25, RC-P03.2). Rutas y esquemas: RC-P01-003.

Todas las operaciones, salvo `GET /usuarios/yo`, requieren el rol de
administrador operativo (Tabla 3.II). La supresión (RF-25) requiere la Lambda de
operaciones de Cognito (§5.4.2) y todavía no está implementada.
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from atlas.api.dependencias import (
    UsuarioActual,
    exigir_rol,
    obtener_sesion,
    obtener_solicitud_id,
    obtener_usuario_actual,
)
from atlas.dominio.enumeraciones import EstadoUsuario, Rol
from atlas.servicios import cuentas

enrutador = APIRouter(prefix="/usuarios", tags=["cuentas"])

Sesion = Annotated[Session, Depends(obtener_sesion)]
Administrador = Annotated[UsuarioActual, Depends(exigir_rol(Rol.ADMINISTRADOR_OPERATIVO))]
SolicitudId = Annotated[uuid.UUID | None, Depends(obtener_solicitud_id)]


class CuentaRespuesta(BaseModel):
    id: int
    identificador_externo: str | None
    estado: EstadoUsuario
    roles: list[Rol]
    autorizacion_cierre: bool

    @classmethod
    def desde(cls, cuenta: cuentas.Cuenta) -> "CuentaRespuesta":
        return cls(
            id=cuenta.id,
            identificador_externo=cuenta.identificador_externo,
            estado=cuenta.estado,
            roles=sorted(cuenta.roles),
            autorizacion_cierre=cuenta.autorizacion_cierre,
        )


class YoRespuesta(BaseModel):
    id: int
    roles: list[Rol]
    autorizacion_cierre: bool


class AltaCuenta(BaseModel):
    identificador_externo: str = Field(min_length=1, max_length=128, pattern=r"^\S+$")


class CambioEstado(BaseModel):
    estado: Literal[EstadoUsuario.HABILITADA, EstadoUsuario.DESHABILITADA]


class CambioAutorizacionCierre(BaseModel):
    otorgada: bool


@enrutador.get("/yo", response_model=YoRespuesta)
def consultar_cuenta_propia(
    usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
) -> YoRespuesta:
    return YoRespuesta(
        id=usuario.id, roles=sorted(usuario.roles), autorizacion_cierre=usuario.autorizacion_cierre
    )


@enrutador.get("", response_model=list[CuentaRespuesta])
def listar_cuentas(_: Administrador, sesion: Sesion) -> list[CuentaRespuesta]:
    return [CuentaRespuesta.desde(c) for c in cuentas.listar(sesion)]


@enrutador.post("", response_model=CuentaRespuesta, status_code=status.HTTP_201_CREATED)
def dar_de_alta_cuenta(
    alta: AltaCuenta, admin: Administrador, sesion: Sesion, solicitud_id: SolicitudId
) -> CuentaRespuesta:
    cuenta = cuentas.dar_de_alta(
        sesion,
        actor_id=admin.id,
        identificador_externo=alta.identificador_externo,
        solicitud_id=solicitud_id,
    )
    return CuentaRespuesta.desde(cuenta)


@enrutador.get("/{usuario_id}", response_model=CuentaRespuesta)
def consultar_cuenta(usuario_id: int, _: Administrador, sesion: Sesion) -> CuentaRespuesta:
    return CuentaRespuesta.desde(cuentas.consultar(sesion, usuario_id))


@enrutador.put("/{usuario_id}/estado", response_model=CuentaRespuesta)
def cambiar_estado_cuenta(
    usuario_id: int,
    cambio: CambioEstado,
    admin: Administrador,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> CuentaRespuesta:
    cuenta = cuentas.cambiar_habilitacion(
        sesion,
        actor_id=admin.id,
        usuario_id=usuario_id,
        habilitada=cambio.estado == EstadoUsuario.HABILITADA,
        solicitud_id=solicitud_id,
    )
    return CuentaRespuesta.desde(cuenta)


@enrutador.put("/{usuario_id}/roles/{rol}", response_model=CuentaRespuesta)
def otorgar_rol(
    usuario_id: int, rol: Rol, admin: Administrador, sesion: Sesion, solicitud_id: SolicitudId
) -> CuentaRespuesta:
    cuenta = cuentas.cambiar_rol(
        sesion,
        actor_id=admin.id,
        usuario_id=usuario_id,
        rol=rol,
        otorgado=True,
        solicitud_id=solicitud_id,
    )
    return CuentaRespuesta.desde(cuenta)


@enrutador.delete("/{usuario_id}/roles/{rol}", response_model=CuentaRespuesta)
def retirar_rol(
    usuario_id: int, rol: Rol, admin: Administrador, sesion: Sesion, solicitud_id: SolicitudId
) -> CuentaRespuesta:
    cuenta = cuentas.cambiar_rol(
        sesion,
        actor_id=admin.id,
        usuario_id=usuario_id,
        rol=rol,
        otorgado=False,
        solicitud_id=solicitud_id,
    )
    return CuentaRespuesta.desde(cuenta)


@enrutador.put("/{usuario_id}/autorizacion-cierre", response_model=CuentaRespuesta)
def cambiar_autorizacion_cierre(
    usuario_id: int,
    cambio: CambioAutorizacionCierre,
    admin: Administrador,
    sesion: Sesion,
    solicitud_id: SolicitudId,
) -> CuentaRespuesta:
    cuenta = cuentas.cambiar_autorizacion_cierre(
        sesion,
        actor_id=admin.id,
        usuario_id=usuario_id,
        otorgada=cambio.otorgada,
        solicitud_id=solicitud_id,
    )
    return CuentaRespuesta.desde(cuenta)
