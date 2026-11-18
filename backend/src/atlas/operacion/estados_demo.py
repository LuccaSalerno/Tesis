"""Fotos de la base para repetir la demo. Temporal: se retira
después de la exposición.

`guardar` copia los datos de cada tabla del esquema `atlas` a un esquema aparte
(`atlas_estado_<nombre>`, sin acceso del usuario de aplicación); `restablecer` vuelve a esos
datos en una sola transacción. Lo invoca el operador desde la Lambda de operaciones, nunca
la API: es una operación administrativa sobre una sesión descartable, como destruir RDS, y no
una operación funcional de borrado (RNF-04, RN-10).

Para restablecer, el usuario de migración (dueño de las tablas) desactiva los *triggers* de
usuario que impiden borrar o truncar, y los reactiva antes de confirmar; si algo falla, la
transacción revierte todo, también los *triggers*. Las identidades no retroceden, así los
identificadores nuevos (y los tokens de Textract que los usan) no repiten los anteriores.
"""

import re
from collections.abc import Sequence
from typing import Any, Final

from sqlalchemy import Connection, Engine, text

from atlas.persistencia.base import ESQUEMA

NOMBRE_VALIDO: Final = re.compile(r"[a-z][a-z0-9_]{0,30}")
PREFIJO: Final = "atlas_estado_"
EXCLUIDAS: Final = frozenset({"alembic_version"})


class EstadoInvalido(Exception):
    """El código es el único mensaje."""


def esquema_de(nombre: str) -> str:
    if not NOMBRE_VALIDO.fullmatch(nombre):
        raise EstadoInvalido("nombre_de_estado_invalido")
    return PREFIJO + nombre


def _q(conexion: Connection, identificador: str) -> str:
    return conexion.dialect.identifier_preparer.quote(identificador)


def _tablas(conexion: Connection, esquema: str) -> list[str]:
    filas = conexion.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = :e ORDER BY tablename"),
        {"e": esquema},
    ).scalars()
    return [t for t in filas if t not in EXCLUIDAS]


def _columnas(conexion: Connection, esquema: str, tabla: str) -> list[str]:
    return list(
        conexion.execute(
            text(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_schema = :e AND table_name = :t ORDER BY ordinal_position"
            ),
            {"e": esquema, "t": tabla},
        ).scalars()
    )


def _orden_de_carga(conexion: Connection, tablas: Sequence[str]) -> list[str]:
    """Padres antes que hijos según las claves foráneas no diferibles. Las diferibles
    (documento ↔ versión vigente) se verifican al confirmar y no imponen orden."""
    dependencias: dict[str, set[str]] = {t: set() for t in tablas}
    for hija, padre in conexion.execute(
        text(
            "SELECT c.conrelid::regclass::text, c.confrelid::regclass::text"
            " FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace"
            " WHERE c.contype = 'f' AND NOT c.condeferrable AND n.nspname = :e"
        ),
        {"e": ESQUEMA},
    ):
        hija, padre = hija.split(".")[-1], padre.split(".")[-1]
        if hija != padre and hija in dependencias and padre in dependencias:
            dependencias[hija].add(padre)
    orden: list[str] = []
    pendientes = dict(dependencias)
    while pendientes:
        listas = sorted(t for t, padres in pendientes.items() if padres <= set(orden))
        if not listas:
            raise EstadoInvalido("dependencias_circulares")
        orden.extend(listas)
        for t in listas:
            del pendientes[t]
    return orden


def guardar(motor: Engine, nombre: str) -> dict[str, Any]:
    """Reemplaza la foto `nombre` por el contenido actual de cada tabla."""
    esquema = esquema_de(nombre)
    with motor.begin() as conexion:
        destino = _q(conexion, esquema)
        conexion.execute(text(f"DROP SCHEMA IF EXISTS {destino} CASCADE"))
        conexion.execute(text(f"CREATE SCHEMA {destino}"))
        filas = 0
        tablas = _tablas(conexion, ESQUEMA)
        for tabla in tablas:
            t = _q(conexion, tabla)
            filas += conexion.execute(
                text(f"CREATE TABLE {destino}.{t} AS TABLE {_q(conexion, ESQUEMA)}.{t}")
            ).rowcount
    return {"estado": nombre, "tablas": len(tablas), "filas": filas}


def restablecer(motor: Engine, nombre: str) -> dict[str, Any]:
    """Vuelve cada tabla al contenido de la foto `nombre`, en una sola transacción."""
    esquema = esquema_de(nombre)
    with motor.begin() as conexion:
        tablas = _tablas(conexion, ESQUEMA)
        if not _tablas(conexion, esquema):
            raise EstadoInvalido("estado_inexistente")
        if _tablas(conexion, esquema) != tablas or any(
            _columnas(conexion, esquema, t) != _columnas(conexion, ESQUEMA, t) for t in tablas
        ):
            # Una migración posterior a la foto: los datos ya no corresponden al esquema.
            raise EstadoInvalido("estado_incompatible_con_el_esquema")
        origen, atlas = _q(conexion, esquema), _q(conexion, ESQUEMA)
        calificadas = [f"{atlas}.{_q(conexion, t)}" for t in tablas]
        for tabla in calificadas:
            conexion.execute(text(f"ALTER TABLE {tabla} DISABLE TRIGGER USER"))
        conexion.execute(text(f"TRUNCATE {', '.join(calificadas)} CONTINUE IDENTITY"))
        filas = 0
        for tabla in _orden_de_carga(conexion, tablas):
            t = _q(conexion, tabla)
            columnas = ", ".join(_q(conexion, c) for c in _columnas(conexion, ESQUEMA, tabla))
            filas += conexion.execute(
                text(
                    # Identificadores del catálogo, citados: no hay datos externos.
                    f"INSERT INTO {atlas}.{t} ({columnas}) OVERRIDING SYSTEM VALUE"  # noqa: S608
                    f" SELECT {columnas} FROM {origen}.{t}"
                )
            ).rowcount
        # Las identidades nunca retroceden: siguen por encima de lo restablecido.
        for tabla, columna in conexion.execute(
            text(
                "SELECT table_name, column_name FROM information_schema.columns"
                " WHERE table_schema = :e AND is_identity = 'YES'"
            ),
            {"e": ESQUEMA},
        ).all():
            if tabla in tablas:
                conexion.execute(
                    text(
                        # nextval avanza la secuencia: nunca devuelve un valor ya usado.
                        "SELECT setval(pg_get_serial_sequence(:t, :c), GREATEST("  # noqa: S608
                        "nextval(pg_get_serial_sequence(:t, :c)),"
                        f" (SELECT COALESCE(max({_q(conexion, columna)}), 0)"
                        f" FROM {atlas}.{_q(conexion, tabla)})))"
                    ),
                    {"t": f"{ESQUEMA}.{tabla}", "c": columna},
                )
        # Verifica ahora las claves diferidas: con eventos pendientes no se puede reactivar.
        conexion.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        for tabla in calificadas:
            conexion.execute(text(f"ALTER TABLE {tabla} ENABLE TRIGGER USER"))
    return {"estado": nombre, "tablas": len(tablas), "filas": filas}
