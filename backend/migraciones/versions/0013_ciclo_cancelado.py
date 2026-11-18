"""Ciclo de revisión cancelado junto con su trámite.

Revisión: 0013
Anterior: 0012
Trazabilidad: RF-26, RN-14.

- `ciclo_revision.estado` admite `cancelado`: el responsable canceló el trámite mientras el
  ciclo estaba en curso. Como los demás estados finales, solo se alcanza desde `en_curso` y
  fija `concluido_en`.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _transiciones(estados: str) -> str:
    # `estados` es una constante de esta migración, nunca un dato externo.
    return f"""
        CREATE OR REPLACE FUNCTION atlas.verificar_cambio_ciclo() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF (NEW.tramite_id, NEW.numero, NEW.plantilla_flujo_id, NEW.confirmado_por_id,
              NEW.confirmado_en)
             IS DISTINCT FROM
             (OLD.tramite_id, OLD.numero, OLD.plantilla_flujo_id, OLD.confirmado_por_id,
              OLD.confirmado_en)
             OR NOT (OLD.estado = 'en_curso' AND NEW.estado IN ({estados})) THEN
            RAISE EXCEPTION 'Transición del ciclo de revisión no admitida'
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          RETURN NEW;
        END $$;
    """


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE atlas.ciclo_revision DROP CONSTRAINT ck_ciclo_revision_estado;
        ALTER TABLE atlas.ciclo_revision ADD CONSTRAINT ck_ciclo_revision_estado
          CHECK (estado IN ('en_curso', 'aprobado', 'observado', 'desplazado', 'cancelado'));
        """
    )
    op.execute(_transiciones("'aprobado', 'observado', 'desplazado', 'cancelado'"))


def downgrade() -> None:
    """Solo para recrear bases locales y de pruebas (en E90A la demo se destruye)."""
    op.execute(_transiciones("'aprobado', 'observado', 'desplazado'"))
    op.execute(
        """
        -- Los ciclos son inmutables: los cancelados quedan y la restricción vuelve sin
        -- validar las filas existentes (como en 0010).
        ALTER TABLE atlas.ciclo_revision DROP CONSTRAINT ck_ciclo_revision_estado;
        ALTER TABLE atlas.ciclo_revision ADD CONSTRAINT ck_ciclo_revision_estado
          CHECK (estado IN ('en_curso', 'aprobado', 'observado', 'desplazado')) NOT VALID;
        """
    )
