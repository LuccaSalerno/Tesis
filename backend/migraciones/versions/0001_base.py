"""Revisión base: verifica los prerrequisitos de la inicialización privilegiada.

Revisión: 0001
Anterior: ninguna
pgvector y el esquema se crean fuera de las migraciones.
No crea entidades del dominio; la Figura 5.4 se incorpora en revisiones siguientes.
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conexion = op.get_bind()
    if (
        conexion.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
        is None
    ):
        raise RuntimeError("Falta la extensión pgvector: ejecutar la inicialización privilegiada")
    if conexion.execute(text("SELECT 1 FROM pg_namespace WHERE nspname = 'atlas'")).first() is None:
        raise RuntimeError("Falta el esquema atlas: ejecutar la inicialización privilegiada")


def downgrade() -> None:
    pass
