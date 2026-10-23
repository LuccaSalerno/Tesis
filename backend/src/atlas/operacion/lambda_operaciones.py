"""Lambda privada de operaciones, dentro de la VPC (RC-P10-15, DO-2026-10-22-OPS P3).

Solo la invoca el operador autorizado, de forma manual y con el plan aprobado. Cada
acción devuelve únicamente identificadores, revisiones y conteos: nunca contenido
documental ni credenciales (AGENTS.md §2.5).

- `inicializar_base`: con la credencial maestra (Secrets Manager), crea la base del
  entorno, sus usuarios con `rds_iam`, el esquema `atlas`, pgvector y los privilegios.
  Se niega si la base ya existe. Es de un solo uso: después la credencial maestra puede
  quedar sin acceso por contraseña (DIF-95), y no se vuelve a usar en la sesión.
- `migrar` y `estado_migraciones`: Alembic con el usuario de migración, directo a RDS.
- `crear_administrador`: primer administrador operativo (DT-AUT-02).
- `verificar_drenaje`: conteos de lo que impide pasar a `offline` (RC-P10-09).
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

import psycopg
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from psycopg import sql
from psycopg.conninfo import make_conninfo
from sqlalchemy import Engine, func, select
from sqlalchemy.pool import NullPool

from atlas.configuracion import Configuracion, ErrorConfiguracion, obtener_configuracion
from atlas.dominio.enumeraciones import EstadoIncorporacion, EstadoTrabajo
from atlas.integraciones.aws import crear_cliente
from atlas.persistencia.base import ESQUEMA
from atlas.persistencia.modelos import Archivo, AutorizacionCarga, TrabajoProcesamiento
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from atlas.registro import configurar_registro, registrar_evento
from atlas.servicios.cuentas import crear_administrador_inicial
from atlas.servicios.errores import Conflicto

_registrador = logging.getLogger("atlas.operacion")

ACCIONES: Final = frozenset(
    {"inicializar_base", "migrar", "estado_migraciones", "crear_administrador", "verificar_drenaje"}
)


class ErrorOperacion(Exception):
    """Falla controlada: el código es el único mensaje."""


# --- Inicialización privilegiada ---------------------------------------------------------


@dataclass(frozen=True)
class Nombres:
    base: str
    app: str
    migracion: str


def nombres(configuracion: Configuracion) -> Nombres:
    if not configuracion.bd_usuario_migracion:
        raise ErrorConfiguracion("Falta ATLAS_BD_USUARIO_MIGRACION")
    return Nombres(
        base=configuracion.bd_nombre,
        app=configuracion.bd_usuario,
        migracion=configuracion.bd_usuario_migracion,
    )


def sentencias_servidor(n: Nombres) -> list[sql.Composable]:
    """En la base `postgres`: usuarios (todavía sin IAM) y base propia sin acceso de PUBLIC."""
    app, migracion, base = (
        sql.Identifier(n.app),
        sql.Identifier(n.migracion),
        sql.Identifier(n.base),
    )
    return [
        sql.SQL("CREATE ROLE {} LOGIN").format(migracion),
        sql.SQL("CREATE ROLE {} LOGIN").format(app),
        # PostgreSQL 16: quien crea el rol necesita pertenecer a él para asignarle objetos.
        # La pertenencia es temporal: se revoca al final de `sentencias_base`.
        sql.SQL("GRANT {} TO CURRENT_USER").format(migracion),
        sql.SQL("CREATE DATABASE {} OWNER {}").format(base, migracion),
        sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(base),
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}, {}, CURRENT_USER").format(
            base, migracion, app
        ),
        sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path = atlas, public").format(app, base),
        sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path = atlas, public").format(
            migracion, base
        ),
    ]


def sentencias_base(n: Nombres) -> list[sql.Composable]:
    """En la base nueva: pgvector, esquema del usuario de migración y privilegios mínimos
    del usuario de aplicación (sin DELETE ni TRUNCATE, RNF-04, PD-04-002).

    `rds_iam` va al final y después no se abre otra conexión maestra: RDS exige IAM (PAM) a
    todo miembro directo o indirecto de `rds_iam` (`pg_hba.conf`: `+rds_iam ... pam`), y el
    maestro es miembro del usuario de migración mientras dura la inicialización. Verificado
    en la sesión e90-ensayo-1 (DIF-95)."""
    app, migracion = sql.Identifier(n.app), sql.Identifier(n.migracion)
    return [
        sql.SQL("CREATE EXTENSION IF NOT EXISTS vector"),
        sql.SQL("REVOKE CREATE ON SCHEMA public FROM PUBLIC"),
        sql.SQL("CREATE SCHEMA atlas AUTHORIZATION {}").format(migracion),
        sql.SQL("GRANT USAGE ON SCHEMA atlas TO {}").format(app),
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA atlas "
            "GRANT SELECT, INSERT, UPDATE ON TABLES TO {}"
        ).format(migracion, app),
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA atlas "
            "GRANT USAGE, SELECT ON SEQUENCES TO {}"
        ).format(migracion, app),
        sql.SQL("REVOKE {} FROM CURRENT_USER").format(migracion),
        sql.SQL("GRANT rds_iam TO {}, {}").format(migracion, app),
    ]


Conectar = Callable[[str], Any]


def conector_maestro(configuracion: Configuracion) -> Conectar:
    """Conexión directa a la instancia con la credencial maestra y TLS verificado."""
    if not configuracion.ops_secreto_maestro_arn or not configuracion.bd_host_migracion:
        raise ErrorConfiguracion("Faltan ATLAS_OPS_SECRETO_MAESTRO_ARN y ATLAS_BD_HOST_MIGRACION")
    secreto = json.loads(
        crear_cliente(configuracion, "secretsmanager").get_secret_value(
            SecretId=configuracion.ops_secreto_maestro_arn
        )["SecretString"]
    )

    def conectar(base: str) -> Any:
        conninfo = make_conninfo(
            host=configuracion.bd_host_migracion,
            port=configuracion.bd_puerto,
            dbname=base,
            user=secreto["username"],
            password=secreto["password"],
            **configuracion.argumentos_conexion(),
        )
        return psycopg.connect(conninfo, autocommit=True)

    return conectar


def inicializar_base(configuracion: Configuracion, conectar: Conectar) -> dict[str, Any]:
    n = nombres(configuracion)
    with conectar("postgres") as conexion:
        existe = conexion.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (n.base,)
        ).fetchone()
        if existe:
            raise ErrorOperacion("base_ya_inicializada")
        for sentencia in sentencias_servidor(n):
            conexion.execute(sentencia)
    with conectar(n.base) as conexion:
        for sentencia in sentencias_base(n):
            conexion.execute(sentencia)
    return {"base": n.base, "usuarios": [n.migracion, n.app]}


# --- Migraciones -------------------------------------------------------------------------


def configuracion_alembic(configuracion: Configuracion) -> Config:
    config = Config()
    config.set_main_option("script_location", str(configuracion.ops_directorio_migraciones))
    config.attributes["configuracion"] = configuracion
    return config


def _revision_actual(motor: Engine) -> str | None:
    with motor.connect() as conexion:
        contexto = MigrationContext.configure(conexion, opts={"version_table_schema": ESQUEMA})
        return contexto.get_current_revision()


def estado_migraciones(configuracion: Configuracion) -> dict[str, Any]:
    motor = crear_motor(configuracion, migracion=True, poolclass=NullPool, pool_pre_ping=False)
    try:
        actual = _revision_actual(motor)
    finally:
        motor.dispose()
    cabeza = ScriptDirectory.from_config(configuracion_alembic(configuracion)).get_current_head()
    return {"revision_actual": actual, "revision_esperada": cabeza, "al_dia": actual == cabeza}


def migrar(configuracion: Configuracion) -> dict[str, Any]:
    antes = estado_migraciones(configuracion)["revision_actual"]
    command.upgrade(configuracion_alembic(configuracion), "head")
    despues = estado_migraciones(configuracion)
    return {"revision_anterior": antes, **despues}


# --- Administrador inicial y drenaje -----------------------------------------------------


def crear_administrador(configuracion: Configuracion, identificador_externo: str) -> dict[str, Any]:
    motor = crear_motor(configuracion, migracion=True, poolclass=NullPool)
    try:
        with crear_fabrica_sesiones(motor)() as sesion, sesion.begin():
            cuenta = crear_administrador_inicial(sesion, identificador_externo)
    except Conflicto as error:
        raise ErrorOperacion("administrador_ya_existe") from error
    finally:
        motor.dispose()
    return {"usuario_id": cuenta.id}


def verificar_drenaje(configuracion: Configuracion) -> dict[str, Any]:
    """Solo lectura: URLs prefirmadas vigentes, cargas sin incorporar, trabajos abiertos y
    ejecuciones de Step Functions en curso. `drenado` exige los cuatro en cero."""
    ahora = datetime.now(UTC)
    motor = crear_motor(configuracion, migracion=True, poolclass=NullPool)
    try:
        with crear_fabrica_sesiones(motor)() as sesion:
            urls = sesion.scalar(
                select(func.count())
                .select_from(AutorizacionCarga)
                .where(AutorizacionCarga.archivo_id.is_(None), AutorizacionCarga.expira_en > ahora)
            )
            cargas = sesion.scalar(
                select(func.count())
                .select_from(Archivo)
                .where(Archivo.estado_incorporacion == EstadoIncorporacion.PENDIENTE)
            )
            trabajos = sesion.scalar(
                select(func.count())
                .select_from(TrabajoProcesamiento)
                .where(
                    TrabajoProcesamiento.estado.in_(
                        [EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_EJECUCION]
                    )
                )
            )
    finally:
        motor.dispose()
    paginas = (
        crear_cliente(configuracion, "stepfunctions")
        .get_paginator("list_executions")
        .paginate(
            stateMachineArn=configuracion.sfn_maquina_procesamiento_arn or "",
            statusFilter="RUNNING",
        )
    )
    ejecuciones = sum(len(p["executions"]) for p in paginas)
    conteos = {
        "urls_vigentes": int(urls or 0),
        "cargas_pendientes": int(cargas or 0),
        "trabajos_abiertos": int(trabajos or 0),
        "ejecuciones_activas": ejecuciones,
    }
    return {**conteos, "drenado": not any(conteos.values())}


# --- Punto de entrada --------------------------------------------------------------------


def ejecutar(
    evento: dict[str, Any],
    configuracion: Configuracion,
    conectar_maestro: Callable[[Configuracion], Conectar] = conector_maestro,
) -> dict[str, Any]:
    accion = evento.get("accion")
    if accion not in ACCIONES:
        raise ErrorOperacion("accion_desconocida")
    if accion == "inicializar_base":
        return inicializar_base(configuracion, conectar_maestro(configuracion))
    if accion == "migrar":
        return migrar(configuracion)
    if accion == "estado_migraciones":
        return estado_migraciones(configuracion)
    if accion == "crear_administrador":
        identificador = evento.get("identificador_externo")
        if not isinstance(identificador, str) or not identificador:
            raise ErrorOperacion("falta_identificador_externo")
        return crear_administrador(configuracion, identificador)
    return verificar_drenaje(configuracion)


def manejar(evento: dict[str, Any], _contexto: Any) -> dict[str, Any]:
    configuracion = obtener_configuracion()
    configurar_registro(configuracion.nivel_registro)
    accion = str(evento.get("accion"))
    try:
        resultado = ejecutar(evento, configuracion)
    except ErrorOperacion as error:
        registrar_evento(
            _registrador,
            "operacion_rechazada",
            logging.WARNING,
            accion=accion,
            codigo_error=str(error),
        )
        return {"accion": accion, "resultado": "rechazada", "codigo": str(error)}
    except Exception as error:
        # Sin el mensaje: puede incluir parámetros de conexión o SQL.
        registrar_evento(
            _registrador,
            "operacion_fallida",
            logging.ERROR,
            accion=accion,
            codigo_error=type(error).__name__,
        )
        return {"accion": accion, "resultado": "fallida", "codigo": type(error).__name__}
    registrar_evento(
        _registrador, "operacion_completada", accion=accion, entorno=configuracion.entorno
    )
    return {"accion": accion, "resultado": "completada", **resultado}
