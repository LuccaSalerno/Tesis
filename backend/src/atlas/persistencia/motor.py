"""Creación del motor y de las sesiones de base de datos.

Con `bd_autenticacion=iam` (RC-P10-04, DO-2026-10-22-OPS P4) cada conexión nueva usa un
token de autenticación de RDS firmado con la identidad del proceso: no hay claves de base
en la configuración. El token dura 15 minutos y solo sirve para abrir la conexión.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from atlas.configuracion import Configuracion


def generador_token_iam(configuracion: Configuracion) -> Callable[[str, str, int], str]:
    """Firma tokens de RDS localmente (no contacta AWS)."""
    import boto3

    cliente = boto3.client("rds", region_name=configuracion.aws_region)

    def generar(host: str, usuario: str, puerto: int) -> str:
        token: str = cliente.generate_db_auth_token(
            DBHostname=host, Port=puerto, DBUsername=usuario, Region=configuracion.aws_region
        )
        return token

    return generar


def crear_motor(
    configuracion: Configuracion,
    *,
    migracion: bool = False,
    generador: Callable[[str, str, int], str] | None = None,
    **opciones: Any,
) -> Engine:
    configuracion.validar_despliegue()
    url = configuracion.url_migracion() if migracion else configuracion.url_aplicacion()
    opciones.setdefault("pool_pre_ping", True)
    motor = create_engine(url, connect_args=configuracion.argumentos_conexion(), **opciones)
    if configuracion.bd_autenticacion == "iam":
        firmar = generador or generador_token_iam(configuracion)

        @event.listens_for(motor, "do_connect")
        def _con_token(
            _dialecto: Any, _registro: Any, _argumentos: Any, parametros: dict[str, Any]
        ) -> None:
            parametros["password"] = firmar(
                parametros["host"], parametros["user"], int(parametros.get("port") or 5432)
            )

    return motor


def crear_fabrica_sesiones(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=motor, expire_on_commit=False)
