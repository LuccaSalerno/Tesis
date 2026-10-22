"""Migraciones e inicialización de PostgreSQL con pgvector real (RC-P10-15, PD-04)."""

import pytest
from alembic import command
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from atlas.configuracion import Configuracion
from atlas.persistencia.motor import crear_fabrica_sesiones, crear_motor
from tests.conftest import configuracion_alembic

pytestmark = pytest.mark.integracion


def _revision_actual(motor: Engine) -> str | None:
    with motor.connect() as conexion:
        return conexion.execute(text("SELECT version_num FROM atlas.alembic_version")).scalar()


def test_rc_p10_15_migraciones_reproducibles_desde_cero(
    configuracion_tests: Configuracion, motor_migracion: Engine
) -> None:
    config = configuracion_alembic(configuracion_tests)
    for _ in range(2):
        command.downgrade(config, "base")
        assert _revision_actual(motor_migracion) is None
        command.upgrade(config, "head")
        assert _revision_actual(motor_migracion) == "0001"


def test_rc_p10_15_pgvector_disponible_para_usuario_de_aplicacion(
    motor_aplicacion: Engine,
) -> None:
    with motor_aplicacion.connect() as conexion:
        distancia = conexion.execute(
            text("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")
        ).scalar()
    assert distancia == 1.0


def test_rnf_04_rn_10_usuario_de_aplicacion_no_borra_ni_altera_esquema(
    configuracion_tests: Configuracion, motor_migracion: Engine
) -> None:
    app = configuracion_tests.bd_usuario
    consulta = text("SELECT has_table_privilege(:app, 'atlas.prueba_privilegios', :privilegio)")
    with motor_migracion.begin() as conexion:
        conexion.execute(text("CREATE TABLE atlas.prueba_privilegios (id integer PRIMARY KEY)"))
        try:
            privilegios = {
                p: conexion.execute(consulta, {"app": app, "privilegio": p}).scalar()
                for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
            }
            crea_en_esquema = conexion.execute(
                text("SELECT has_schema_privilege(:app, 'atlas', 'CREATE')"), {"app": app}
            ).scalar()
        finally:
            conexion.execute(text("DROP TABLE atlas.prueba_privilegios"))
    assert privilegios == {
        "SELECT": True,
        "INSERT": True,
        "UPDATE": True,
        "DELETE": False,
        "TRUNCATE": False,
    }
    assert crea_en_esquema is False


def test_rc_p10_usuario_de_aplicacion_no_accede_a_otra_base(
    configuracion_tests: Configuracion,
) -> None:
    otra = configuracion_tests.url_aplicacion().set(database="atlas_dev")
    motor = create_engine(otra, poolclass=NullPool)
    with pytest.raises(OperationalError, match="permission denied"), motor.connect():
        pass
    motor.dispose()


def test_rc_p10_motor_de_aplicacion_conecta_con_su_usuario(
    configuracion_tests: Configuracion,
) -> None:
    motor = crear_motor(configuracion_tests)
    with crear_fabrica_sesiones(motor)() as sesion:
        usuario, ruta_busqueda = sesion.execute(
            text("SELECT current_user, current_setting('search_path')")
        ).one()
    motor.dispose()
    assert usuario == configuracion_tests.bd_usuario
    assert ruta_busqueda.startswith("atlas")
