"""Lambda privada de operaciones (V-DB, V-MT).

Sin AWS: Secrets Manager y Step Functions simulados con moto, PostgreSQL real. La
inicialización privilegiada se prueba contra un superusuario solo si la CI lo ofrece
(`ATLAS_PRUEBAS_PG_SUPERUSUARIO`); en RDS se verifica en la sesión autorizada (V-DB).
"""

import json
import os
import uuid
from typing import Any

import psycopg
import pytest
from alembic.script import ScriptDirectory
from psycopg import sql

from atlas.configuracion import Configuracion, ErrorConfiguracion
from atlas.integraciones.aws import crear_cliente
from atlas.operacion import lambda_operaciones as ops
from tests.conftest import configuracion_sin_base, lineas_registro

SUPERUSUARIO = os.environ.get("ATLAS_PRUEBAS_PG_SUPERUSUARIO")


def test_v_db_sentencias_sin_delete_y_con_rds_iam() -> None:
    n = ops.Nombres(base="pfi_demo", app="atlas_demo_app", migracion="atlas_demo_migracion")
    servidor = [s.as_string() for s in ops.sentencias_servidor(n)]
    base = [s.as_string() for s in ops.sentencias_base(n)]
    assert 'REVOKE ALL ON DATABASE "pfi_demo" FROM PUBLIC' in servidor
    # Rds_iam al final, cuando ya no se abre otra conexión maestra.
    assert not any("rds_iam" in s for s in servidor)
    assert base[-2:] == [
        'REVOKE "atlas_demo_migracion" FROM CURRENT_USER',
        'GRANT rds_iam TO "atlas_demo_migracion", "atlas_demo_app"',
    ]
    assert any("GRANT SELECT, INSERT, UPDATE ON TABLES" in s for s in base)
    assert not any("DELETE" in s or "TRUNCATE" in s for s in servidor + base)


class ConexionFalsa:
    def __init__(self, existe: bool, ejecutadas: list[tuple[str, Any]]) -> None:
        self.existe = existe
        self.ejecutadas = ejecutadas

    def __enter__(self) -> "ConexionFalsa":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sentencia: Any, parametros: Any = None) -> Any:
        self.ejecutadas.append((str(sentencia), parametros))
        existe = self.existe

        class Resultado:
            def fetchone(self) -> tuple[int] | None:
                return (1,) if existe else None

        return Resultado()


def _configuracion_ops(**campos: Any) -> Configuracion:
    return configuracion_sin_base(bd_usuario_migracion="atlas_demo_migracion", **campos)


def test_v_db_inicializar_se_niega_si_la_base_existe() -> None:
    ejecutadas: list[tuple[str, Any]] = []
    with pytest.raises(ops.ErrorOperacion, match="base_ya_inicializada"):
        ops.inicializar_base(_configuracion_ops(), lambda _: ConexionFalsa(True, ejecutadas))
    assert len(ejecutadas) == 1  # solo la comprobación


def test_v_db_inicializar_ejecuta_servidor_y_base_en_orden() -> None:
    ejecutadas: list[tuple[str, Any]] = []
    bases: list[str] = []

    def conectar(base: str) -> ConexionFalsa:
        bases.append(base)
        return ConexionFalsa(False, ejecutadas)

    resultado = ops.inicializar_base(_configuracion_ops(), conectar)
    assert bases == ["postgres", "sin_base"]
    # Después de rds_iam no hay más sentencias ni conexiones con el maestro.
    assert "rds_iam" in ejecutadas[-1][0]
    assert sum("rds_iam" in sentencia for sentencia, _ in ejecutadas) == 1
    assert resultado == {"base": "sin_base", "usuarios": ["atlas_demo_migracion", "nadie"]}
    n = ops.nombres(_configuracion_ops())
    assert len(ejecutadas) == 1 + len(ops.sentencias_servidor(n)) + len(ops.sentencias_base(n))


def test_v_db_nombres_exigen_usuario_de_migracion() -> None:
    with pytest.raises(ErrorConfiguracion):
        ops.nombres(configuracion_sin_base())


def test_credencial_maestra_desde_secrets_manager(
    moto_local: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    configuracion = _configuracion_ops(
        aws_endpoint_url=moto_local, bd_host_migracion="instancia.ejemplo.local"
    )
    with pytest.raises(ErrorConfiguracion, match="SECRETO_MAESTRO"):
        ops.conector_maestro(configuracion)
    secreto = crear_cliente(configuracion, "secretsmanager").create_secret(
        Name=f"rds-maestro-{uuid.uuid4()}",
        SecretString=json.dumps({"username": "maestro", "password": "ficticia"}),
    )
    capturadas: list[str] = []
    monkeypatch.setattr(ops.psycopg, "connect", lambda info, **_: capturadas.append(info))
    conectar = ops.conector_maestro(
        configuracion.model_copy(update={"ops_secreto_maestro_arn": secreto["ARN"]})
    )
    conectar("postgres")
    assert "host=instancia.ejemplo.local" in capturadas[0]
    assert "user=maestro" in capturadas[0] and "dbname=postgres" in capturadas[0]


@pytest.mark.integracion
@pytest.mark.skipif(SUPERUSUARIO is None, reason="Requiere un superusuario de PostgreSQL (CI)")
def test_v_db_inicializacion_real_en_postgresql_16() -> None:
    nombre = f"ops_{uuid.uuid4().hex[:8]}"
    n = ops.Nombres(base=nombre, app=f"{nombre}_app", migracion=f"{nombre}_migracion")
    configuracion = configuracion_sin_base(
        bd_nombre=n.base, bd_usuario=n.app, bd_usuario_migracion=n.migracion
    )

    def conectar(base: str) -> Any:
        return psycopg.connect(f"{SUPERUSUARIO} dbname={base}", autocommit=True)

    with conectar("postgres") as conexion:
        conexion.execute(
            "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rds_iam')"
            " THEN CREATE ROLE rds_iam; END IF; END $$"
        )
    try:
        ops.inicializar_base(configuracion, conectar)
        with conectar(n.base) as conexion:
            dueno = conexion.execute(
                "SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname = 'atlas'"
            ).fetchone()
            vector = conexion.execute(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
            publico = conexion.execute(
                "SELECT has_database_privilege('public', %s, 'CONNECT')", (n.base,)
            ).fetchone()
            # El maestro no conserva la pertenencia explícita al usuario de migración.
            pertenece = conexion.execute(
                "SELECT count(*) FROM pg_auth_members WHERE roleid = %s::regrole"
                " AND member = current_user::regrole",
                (n.migracion,),
            ).fetchone()
            iam = conexion.execute(
                "SELECT count(*) FROM pg_auth_members WHERE roleid = 'rds_iam'::regrole"
                " AND member IN (%s::regrole, %s::regrole)",
                (n.migracion, n.app),
            ).fetchone()
        assert dueno == (n.migracion,) and vector == (1,) and publico == (False,)
        assert pertenece == (0,) and iam == (2,)
        with pytest.raises(ops.ErrorOperacion, match="base_ya_inicializada"):
            ops.inicializar_base(configuracion, conectar)
    finally:
        with conectar("postgres") as conexion:
            conexion.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(n.base)))
            for rol in (n.app, n.migracion):
                conexion.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(rol)))


# --- Migraciones, administrador y drenaje contra la base de pruebas ---------------------


@pytest.mark.integracion
def test_estado_y_migracion_idempotente(base_migrada: Configuracion) -> None:
    cabeza = ScriptDirectory.from_config(ops.configuracion_alembic(base_migrada)).get_current_head()
    estado = ops.estado_migraciones(base_migrada)
    assert estado["al_dia"] is True and estado["revision_actual"] == cabeza
    resultado = ops.migrar(base_migrada)
    assert resultado["revision_anterior"] == resultado["revision_actual"] == cabeza


@pytest.mark.integracion
def test_crear_administrador_una_sola_vez(base_reiniciada: Configuracion) -> None:
    sub = f"sub-{uuid.uuid4()}"
    primero = ops.ejecutar(
        {"accion": "crear_administrador", "identificador_externo": sub}, base_reiniciada
    )
    assert isinstance(primero["usuario_id"], int)
    with pytest.raises(ops.ErrorOperacion, match="administrador_ya_existe"):
        ops.ejecutar(
            {"accion": "crear_administrador", "identificador_externo": "otro"}, base_reiniciada
        )
    with pytest.raises(ops.ErrorOperacion, match="falta_identificador"):
        ops.ejecutar({"accion": "crear_administrador"}, base_reiniciada)


@pytest.mark.integracion
def test_v_mt_verificar_drenaje_cuenta_lo_pendiente(base_migrada: Configuracion) -> None:
    resultado = ops.ejecutar({"accion": "verificar_drenaje"}, base_migrada)
    claves = ("urls_vigentes", "cargas_pendientes", "trabajos_abiertos", "ejecuciones_activas")
    assert all(isinstance(resultado[c], int) for c in claves)
    assert resultado["drenado"] is (not any(resultado[c] for c in claves))


@pytest.mark.integracion
def test_ejecutar_despacha_las_acciones(base_migrada: Configuracion) -> None:
    assert ops.ejecutar({"accion": "estado_migraciones"}, base_migrada)["al_dia"] is True
    assert ops.ejecutar({"accion": "migrar"}, base_migrada)["al_dia"] is True
    with pytest.raises(ops.ErrorOperacion, match="base_ya_inicializada"):
        ops.ejecutar(
            {"accion": "inicializar_base"},
            base_migrada,
            conectar_maestro=lambda _: lambda __: ConexionFalsa(True, []),
        )


def test_rnf_09_manejar_no_filtra_mensajes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(ops, "obtener_configuracion", configuracion_sin_base)
    assert ops.manejar({"accion": "borrar_todo"}, None) == {
        "accion": "borrar_todo",
        "resultado": "rechazada",
        "codigo": "accion_desconocida",
    }

    def explotar(*_: Any, **__: Any) -> Any:
        raise RuntimeError("password=secreta host=instancia")

    monkeypatch.setattr(ops, "ejecutar", explotar)
    respuesta = ops.manejar({"accion": "migrar"}, None)
    assert respuesta == {"accion": "migrar", "resultado": "fallida", "codigo": "RuntimeError"}
    monkeypatch.setattr(ops, "ejecutar", lambda *_: {"al_dia": True})
    assert ops.manejar({"accion": "estado_migraciones"}, None)["resultado"] == "completada"
    salida = capsys.readouterr().out
    assert "secreta" not in salida
    eventos = {r["evento"] for r in lineas_registro(salida)}
    assert {"operacion_rechazada", "operacion_fallida", "operacion_completada"} <= eventos
