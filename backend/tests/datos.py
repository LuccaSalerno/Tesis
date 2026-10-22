"""Constructores de datos sintéticos para las pruebas del modelo (sin contenido real)."""

import hashlib
import uuid

from sqlalchemy import Connection, Engine, text

from tests.conftest import CLAVES_PRUEBA


def crear_usuario(conexion: Connection, estado: str = "habilitada") -> int:
    externo = None if estado == "suprimida" else f"sub-{uuid.uuid4()}"
    return int(
        conexion.execute(
            text(
                "INSERT INTO atlas.usuario (identificador_externo, estado) "
                "VALUES (:externo, :estado) RETURNING id"
            ),
            {"externo": externo, "estado": estado},
        ).scalar_one()
    )


def crear_tramite(
    conexion: Connection, responsable_id: int, titulo: str = "Trámite de prueba"
) -> int:
    return int(
        conexion.execute(
            text(
                "INSERT INTO atlas.tramite (responsable_id, titulo) "
                "VALUES (:responsable, :titulo) RETURNING id"
            ),
            {"responsable": responsable_id, "titulo": titulo},
        ).scalar_one()
    )


def crear_archivo(
    conexion: Connection,
    tramite_id: int,
    usuario_id: int,
    estado: str = "incorporado",
    formato: str = "pdf",
) -> int:
    clave = f"tramites/{tramite_id}/{uuid.uuid4()}"
    return int(
        conexion.execute(
            text(
                "INSERT INTO atlas.archivo (tramite_id, clave_objeto, huella, estado_incorporacion,"
                " nombre, formato, tamano_bytes, cargado_por_id)"
                " VALUES (:tramite, :clave, :huella, :estado, 'C-v1.pdf', :formato, 1024, :usuario)"
                " RETURNING id"
            ),
            {
                "tramite": tramite_id,
                "clave": clave,
                "huella": hashlib.sha256(clave.encode()).hexdigest(),
                "estado": estado,
                "formato": formato,
                "usuario": usuario_id,
            },
        ).scalar_one()
    )


def proximo_id_version(conexion: Connection) -> int:
    return int(
        conexion.execute(
            text("SELECT nextval(pg_get_serial_sequence('atlas.version_documental', 'id'))")
        ).scalar_one()
    )


def crear_documento(
    conexion: Connection, tramite_id: int, archivo_id: int, usuario_id: int
) -> tuple[int, int]:
    """Crea un documento con su versión inicial vigente en la misma transacción (§5.2)."""
    version_id = proximo_id_version(conexion)
    documento_id = int(
        conexion.execute(
            text(
                "INSERT INTO atlas.documento (tramite_id, nombre, version_vigente_id) "
                "VALUES (:tramite, 'Contrato de mantenimiento', :version) RETURNING id"
            ),
            {"tramite": tramite_id, "version": version_id},
        ).scalar_one()
    )
    insertar_version(conexion, version_id, documento_id, archivo_id, usuario_id, 1, None)
    return documento_id, version_id


def insertar_version(
    conexion: Connection,
    version_id: int | None,
    documento_id: int,
    archivo_id: int,
    usuario_id: int,
    numero: int,
    version_previa_id: int | None,
) -> int:
    columnas = "documento_id, archivo_id, creado_por_id, numero, version_previa_id"
    valores = ":documento, :archivo, :usuario, :numero, :previa"
    if version_id is not None:
        columnas, valores = f"id, {columnas}", f":id, {valores}"
    return int(
        conexion.execute(
            text(
                # Columnas fijas de esta función; los valores van como parámetros.
                f"INSERT INTO atlas.version_documental ({columnas}) "  # noqa: S608
                f"VALUES ({valores}) RETURNING id"
            ),
            {
                "id": version_id,
                "documento": documento_id,
                "archivo": archivo_id,
                "usuario": usuario_id,
                "numero": numero,
                "previa": version_previa_id,
            },
        ).scalar_one()
    )


def registrar_evento(conexion: Connection, tramite_id: int, actor_id: int) -> int:
    return int(
        conexion.execute(
            text(
                "INSERT INTO atlas.evento_auditoria (tramite_id, actor_id, actor_tipo,"
                " entidad_tipo, entidad_id, accion, resultado) VALUES (:tramite, :actor,"
                " 'usuario', 'tramite', :tramite, 'tramite_creado', 'exito') RETURNING id"
            ),
            {"tramite": tramite_id, "actor": actor_id},
        ).scalar_one()
    )


def escenario_documento(conexion: Connection) -> dict[str, int]:
    """Usuario responsable, trámite, archivo incorporado y documento con versión 1."""
    usuario = crear_usuario(conexion)
    tramite = crear_tramite(conexion, usuario)
    archivo = crear_archivo(conexion, tramite, usuario)
    documento, version = crear_documento(conexion, tramite, archivo, usuario)
    return {
        "usuario": usuario,
        "tramite": tramite,
        "archivo": archivo,
        "documento": documento,
        "version": version,
    }


def crear_cuenta(
    motor: Engine, *roles: str, estado: str = "habilitada", autorizacion_cierre: bool = False
) -> tuple[int, str]:
    """Cuenta confirmada en la base (la aplicación no puede borrarla: datos únicos por prueba)."""
    sub = f"sub-{uuid.uuid4()}"
    with motor.begin() as conexion:
        usuario_id = conexion.execute(
            text(
                "INSERT INTO atlas.usuario (identificador_externo, estado, autorizacion_cierre)"
                " VALUES (:s, 'habilitada', :a) RETURNING id"
            ),
            {"s": sub, "a": autorizacion_cierre},
        ).scalar_one()
        for rol in roles:
            conexion.execute(
                text("INSERT INTO atlas.usuario_rol (usuario_id, rol) VALUES (:u, :r)"),
                {"u": usuario_id, "r": rol},
            )
        if estado != "habilitada":
            conexion.execute(
                text(
                    "UPDATE atlas.usuario SET estado = :e, identificador_externo ="
                    " CASE WHEN CAST(:e AS varchar) = 'suprimida' THEN NULL"
                    " ELSE identificador_externo END"
                    " WHERE id = :u"
                ),
                {"e": estado, "u": usuario_id},
            )
    return int(usuario_id), sub


def portador(sub: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {CLAVES_PRUEBA.emitir(sub)}"}
