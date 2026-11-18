"""Nombre visible de las cuentas y validación de campos ausentes.

Revisión: 0010
Anterior: 0009
Trazabilidad: RF-12, RF-25, Tabla 3.VI, §6.3.1 («campos intencionalmente ausentes»).

- `usuario.nombre_visible`: nombre para mostrar en la interfaz y en la evidencia, cargado
  por el administrador. Opcional; no es un identificador.
- `validacion_humana`: tipo `ausente` (una persona declara que el dato no consta en la
  versión o no aplica), sin valor validado y con `motivo_ausencia`. Puede referenciar la
  sugerencia que descarta. Los demás tipos siguen exigiendo valor.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE atlas.usuario ADD COLUMN nombre_visible varchar(120);
        ALTER TABLE atlas.usuario ADD CONSTRAINT ck_usuario_nombre_visible_no_vacio
          CHECK (nombre_visible IS NULL OR btrim(nombre_visible) <> '');

        ALTER TABLE atlas.validacion_humana ALTER COLUMN valor_validado DROP NOT NULL;
        -- Deja la de una bajada anterior a 0009 (solo en bases locales o de pruebas).
        ALTER TABLE atlas.validacion_humana
          DROP CONSTRAINT IF EXISTS ck_validacion_humana_valor_presente;
        ALTER TABLE atlas.validacion_humana ADD COLUMN motivo_ausencia varchar(20);
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_tipo;
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_tipo
          CHECK (tipo IN ('confirmacion', 'correccion', 'sin_sugerencia', 'ausente'));
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_sin_sugerencia;
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_sin_sugerencia
          CHECK (tipo = 'ausente'
                 OR (tipo = 'sin_sugerencia') = (valor_sugerido_id IS NULL));
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_motivo_ausencia
          CHECK (motivo_ausencia IS NULL OR motivo_ausencia IN ('no_consta', 'no_aplica'));
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_ausente
          CHECK ((tipo = 'ausente') = (valor_validado IS NULL)
                 AND (tipo = 'ausente') = (motivo_ausencia IS NOT NULL));
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_ausente_es_campo
          CHECK (tipo <> 'ausente' OR clase = 'campo');
        """
    )


def downgrade() -> None:
    """Solo para recrear bases locales y de pruebas (en E90A la demo se destruye).

    Las validaciones `ausente` ya registradas son inmutables: las restricciones anteriores se
    restauran `NOT VALID` (rigen para filas nuevas) y las bajadas siguientes eliminan la tabla.
    """
    op.execute(
        """
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_ausente_es_campo;
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_ausente;
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_motivo_ausencia;
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_sin_sugerencia;
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_sin_sugerencia
          CHECK ((tipo = 'sin_sugerencia') = (valor_sugerido_id IS NULL)) NOT VALID;
        ALTER TABLE atlas.validacion_humana DROP CONSTRAINT ck_validacion_humana_tipo;
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_tipo
          CHECK (tipo IN ('confirmacion', 'correccion', 'sin_sugerencia')) NOT VALID;
        ALTER TABLE atlas.validacion_humana ADD CONSTRAINT ck_validacion_humana_valor_presente
          CHECK (valor_validado IS NOT NULL) NOT VALID;
        ALTER TABLE atlas.validacion_humana DROP COLUMN motivo_ausencia;
        ALTER TABLE atlas.usuario DROP CONSTRAINT ck_usuario_nombre_visible_no_vacio;
        ALTER TABLE atlas.usuario DROP COLUMN nombre_visible;
        """
    )
