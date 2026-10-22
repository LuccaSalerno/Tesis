"""Entorno de migraciones de Alembic (RC-P10-15).

Se conecta con el usuario de migración de la base indicada por la
configuración del proceso, toma un bloqueo consultivo para impedir migraciones
concurrentes y guarda la tabla de versiones en el esquema `atlas`. No instala
extensiones: pgvector pertenece a la inicialización privilegiada.
"""

from alembic import context
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from atlas.configuracion import Configuracion, obtener_configuracion
from atlas.persistencia.base import ESQUEMA, Base

# Identificador fijo del bloqueo consultivo de migraciones.
BLOQUEO_MIGRACION = 7_410_001

configuracion: Configuracion = (
    context.config.attributes.get("configuracion") or obtener_configuracion()
)


def ejecutar_migraciones() -> None:
    motor = create_engine(configuracion.url_migracion(), poolclass=NullPool)
    with motor.connect() as conexion:
        # Bloqueo de sesión: sobrevive a las transacciones que abre Alembic.
        conexion.execute(text("SELECT pg_advisory_lock(:clave)"), {"clave": BLOQUEO_MIGRACION})
        conexion.commit()
        try:
            context.configure(
                connection=conexion,
                target_metadata=Base.metadata,
                version_table_schema=ESQUEMA,
                include_schemas=True,
                transaction_per_migration=True,
            )
            with context.begin_transaction():
                context.run_migrations()
        finally:
            conexion.execute(
                text("SELECT pg_advisory_unlock(:clave)"), {"clave": BLOQUEO_MIGRACION}
            )
            conexion.commit()
    motor.dispose()


if context.is_offline_mode():
    raise SystemExit("Modo offline no soportado: las migraciones se aplican con conexión real.")
ejecutar_migraciones()
