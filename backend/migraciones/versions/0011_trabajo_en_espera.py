"""Estado técnico «En espera» del trabajo de procesamiento.

Revisión: 0011
Anterior: 0010
Trazabilidad: RNF-06, §5.3.1.

- `trabajo_procesamiento.estado` admite `en_espera`: el trabajo quedó registrado, pero no
  hay cupo de procesamiento. Es técnico y no cambia el estado funcional del trámite.
- Índice por estado y fecha de creación: la admisión cuenta los trabajos en curso y el
  reconciliador recorre pendientes y en espera por antigüedad.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE atlas.trabajo_procesamiento DROP CONSTRAINT ck_trabajo_procesamiento_estado;
        ALTER TABLE atlas.trabajo_procesamiento ADD CONSTRAINT ck_trabajo_procesamiento_estado
          CHECK (estado IN ('pendiente', 'en_espera', 'en_ejecucion', 'completado', 'fallido'));
        CREATE INDEX ix_trabajo_procesamiento_estado_creado_en
          ON atlas.trabajo_procesamiento (estado, creado_en);
        """
    )


def downgrade() -> None:
    # Solo para bases locales o de pruebas: un trabajo en espera vuelve a pendiente.
    op.execute(
        """
        DROP INDEX atlas.ix_trabajo_procesamiento_estado_creado_en;
        UPDATE atlas.trabajo_procesamiento SET estado = 'pendiente' WHERE estado = 'en_espera';
        ALTER TABLE atlas.trabajo_procesamiento DROP CONSTRAINT ck_trabajo_procesamiento_estado;
        ALTER TABLE atlas.trabajo_procesamiento ADD CONSTRAINT ck_trabajo_procesamiento_estado
          CHECK (estado IN ('pendiente', 'en_ejecucion', 'completado', 'fallido'));
        """
    )
