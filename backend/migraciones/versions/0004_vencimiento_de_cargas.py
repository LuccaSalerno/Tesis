"""Vencimiento de cargas pendientes y traslado de originales confirmados.

Revisión: 0004
Anterior: 0003
Trazabilidad: RF-04, RF-05, RF-07.

- `archivo.estado_incorporacion` admite `vencido`: una carga pendiente que no se
  incorporó dentro de su vigencia. Los estados distintos de `pendiente` son finales.
- Al incorporarse, el original se traslada del prefijo de cargas temporales al
  definitivo: `clave_objeto` cambia una sola vez y solo en esa transición. La
  huella y los metadatos de carga no cambian nunca, ni siquiera para el propietario.
- `autorizacion_carga.limpiada_en` registra que la limpieza de su objeto temporal
  terminó, para que el proceso sea idempotente y no vuelva a revisarla.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _por_cada_rol_con_acceso(tabla: str, sentencia: str) -> None:
    """Igual que en 0002: aplica `sentencia` a cada rol (salvo el propietario) con acceso."""
    # `tabla` y `sentencia` son constantes de esta migración, nunca datos externos.
    op.execute(
        f"""
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN SELECT DISTINCT grantee FROM information_schema.role_table_grants
                   WHERE table_schema = 'atlas' AND table_name = '{tabla}'
                     AND grantee <> current_user
          LOOP
            EXECUTE format('{sentencia}', r.grantee);
          END LOOP;
        END $$;
        """  # noqa: S608
    )


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE atlas.archivo DROP CONSTRAINT ck_archivo_estado_incorporacion;
        ALTER TABLE atlas.archivo ADD CONSTRAINT ck_archivo_estado_incorporacion
          CHECK (estado_incorporacion IN ('pendiente', 'incorporado', 'descartado', 'vencido'));

        CREATE FUNCTION atlas.verificar_cambio_archivo() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF (NEW.huella, NEW.tramite_id, NEW.nombre, NEW.formato, NEW.tamano_bytes,
              NEW.cargado_por_id, NEW.cargado_en)
             IS DISTINCT FROM
             (OLD.huella, OLD.tramite_id, OLD.nombre, OLD.formato, OLD.tamano_bytes,
              OLD.cargado_por_id, OLD.cargado_en) THEN
            RAISE EXCEPTION 'La huella y los metadatos de carga de un archivo no cambian'
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          IF OLD.estado_incorporacion <> 'pendiente'
             AND NEW.estado_incorporacion IS DISTINCT FROM OLD.estado_incorporacion THEN
            RAISE EXCEPTION 'El archivo ya no está pendiente: su estado es final'
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          IF NEW.clave_objeto IS DISTINCT FROM OLD.clave_objeto AND NOT (
               OLD.estado_incorporacion = 'pendiente'
               AND NEW.estado_incorporacion = 'incorporado'
               AND OLD.clave_objeto LIKE 'cargas-temporales/%'
               AND NEW.clave_objeto LIKE 'documentos/%') THEN
            RAISE EXCEPTION 'La clave del objeto solo cambia al trasladar un archivo incorporado'
              USING ERRCODE = 'integrity_constraint_violation';
          END IF;
          RETURN NEW;
        END $$;

        CREATE TRIGGER tg_archivo_verificacion_cambio BEFORE UPDATE ON atlas.archivo
          FOR EACH ROW EXECUTE FUNCTION atlas.verificar_cambio_archivo();

        ALTER TABLE atlas.autorizacion_carga ADD COLUMN limpiada_en timestamptz;
        """
    )
    _por_cada_rol_con_acceso(
        "archivo", "GRANT UPDATE (estado_incorporacion, clave_objeto) ON atlas.archivo TO %I"
    )
    _por_cada_rol_con_acceso(
        "autorizacion_carga",
        "GRANT UPDATE (archivo_id, limpiada_en) ON atlas.autorizacion_carga TO %I",
    )


def downgrade() -> None:
    """Solo para recrear bases locales y de pruebas: en AWS la demo no baja migraciones,
    se destruye. El estado `vencido` no existe en 0003 y pasa a `descartado`."""
    op.execute(
        """
        ALTER TABLE atlas.autorizacion_carga DROP COLUMN limpiada_en;
        DROP TRIGGER tg_archivo_verificacion_cambio ON atlas.archivo;
        DROP FUNCTION atlas.verificar_cambio_archivo();
        UPDATE atlas.archivo SET estado_incorporacion = 'descartado'
          WHERE estado_incorporacion = 'vencido';
        ALTER TABLE atlas.archivo DROP CONSTRAINT ck_archivo_estado_incorporacion;
        ALTER TABLE atlas.archivo ADD CONSTRAINT ck_archivo_estado_incorporacion
          CHECK (estado_incorporacion IN ('pendiente', 'incorporado', 'descartado'));
        """
    )
