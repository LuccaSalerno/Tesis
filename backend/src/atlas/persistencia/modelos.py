"""Modelo físico del núcleo de la Figura 5.4 (PD-04, incremento 1).

Refleja la migración `0002`. Las restricciones que el ORM no expresa
(triggers de inmutabilidad, privilegios por columna) viven solo en la migración.
Detalle y justificación: docs/diseno/PD-04_Modelo_Fisico_Propuesta.md.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from atlas.dominio.enumeraciones import (
    EstadoIncorporacion,
    EstadoTramite,
    EstadoUsuario,
    FormatoArchivo,
    ResultadoAuditoria,
    Rol,
    TipoActor,
    TipoDocumental,
)
from atlas.persistencia.base import Base


def catalogo(enumeracion: type[StrEnum], longitud: int) -> Enum:
    """Columna `varchar(longitud)` con los valores de la enumeración.

    El CHECK con el catálogo está en la migración (PD-04).
    """
    return Enum(
        enumeracion,
        native_enum=False,
        create_constraint=False,
        length=longitud,
        values_callable=lambda e: [m.value for m in e],
    )


def _id() -> Mapped[int]:
    return mapped_column(BigInteger, Identity(always=False), primary_key=True)


def _instante() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint(
            "(estado = 'suprimida') = (identificador_externo IS NULL)",
            name="suprimida_sin_identificador",
        ),
    )

    id: Mapped[int] = _id()
    identificador_externo: Mapped[str | None] = mapped_column(String(128), unique=True)
    estado: Mapped[EstadoUsuario] = mapped_column(
        catalogo(EstadoUsuario, 20), nullable=False, server_default=EstadoUsuario.HABILITADA.value
    )
    autorizacion_cierre: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    creado_en: Mapped[datetime] = _instante()
    actualizado_en: Mapped[datetime] = _instante()


class UsuarioRol(Base):
    __tablename__ = "usuario_rol"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    rol: Mapped[Rol] = mapped_column(catalogo(Rol, 30), primary_key=True)


class Tramite(Base):
    __tablename__ = "tramite"
    __table_args__ = (
        CheckConstraint("btrim(titulo) <> ''", name="titulo_no_vacio"),
        CheckConstraint(
            "(estado = 'cancelado') = (motivo_cancelacion IS NOT NULL)", name="motivo_si_cancelado"
        ),
    )

    id: Mapped[int] = _id()
    responsable_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[EstadoTramite] = mapped_column(
        catalogo(EstadoTramite, 30), nullable=False, server_default=EstadoTramite.BORRADOR.value
    )
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = _instante()
    actualizado_en: Mapped[datetime] = _instante()


class Archivo(Base):
    __tablename__ = "archivo"
    __table_args__ = (
        CheckConstraint("huella ~ '^[0-9a-f]{64}$'", name="huella_sha256"),
        CheckConstraint("tamano_bytes > 0", name="tamano_positivo"),
    )

    id: Mapped[int] = _id()
    tramite_id: Mapped[int] = mapped_column(ForeignKey("tramite.id"), nullable=False, index=True)
    clave_objeto: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    huella: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    estado_incorporacion: Mapped[EstadoIncorporacion] = mapped_column(
        catalogo(EstadoIncorporacion, 20),
        nullable=False,
        server_default=EstadoIncorporacion.PENDIENTE.value,
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    formato: Mapped[FormatoArchivo] = mapped_column(catalogo(FormatoArchivo, 10), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cargado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    cargado_en: Mapped[datetime] = _instante()


class Documento(Base):
    __tablename__ = "documento"
    __table_args__ = (
        # Exactamente una versión vigente y del propio documento (§5.2). Diferida:
        # documento y versión inicial se insertan en la misma transacción.
        ForeignKeyConstraint(
            ["id", "version_vigente_id"],
            ["version_documental.documento_id", "version_documental.id"],
            name="fk_documento_version_vigente",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
    )

    id: Mapped[int] = _id()
    tramite_id: Mapped[int] = mapped_column(ForeignKey("tramite.id"), nullable=False, index=True)
    tipo: Mapped[TipoDocumental | None] = mapped_column(catalogo(TipoDocumental, 20))
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    version_vigente_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)


class VersionDocumental(Base):
    __tablename__ = "version_documental"
    __table_args__ = (
        UniqueConstraint("documento_id", "id"),
        UniqueConstraint("documento_id", "numero"),
        ForeignKeyConstraint(
            ["documento_id", "version_previa_id"],
            ["version_documental.documento_id", "version_documental.id"],
            name="fk_version_documental_version_previa",
        ),
        CheckConstraint("numero > 0", name="numero_positivo"),
        CheckConstraint(
            "(numero = 1) = (version_previa_id IS NULL)", name="primera_sin_predecesora"
        ),
    )

    id: Mapped[int] = _id()
    documento_id: Mapped[int] = mapped_column(ForeignKey("documento.id"), nullable=False)
    archivo_id: Mapped[int] = mapped_column(ForeignKey("archivo.id"), nullable=False, unique=True)
    version_previa_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = _instante()
    creado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)


class EventoAuditoria(Base):
    __tablename__ = "evento_auditoria"
    __table_args__ = (
        CheckConstraint(
            "(actor_tipo = 'usuario') = (actor_id IS NOT NULL)", name="actor_coherente"
        ),
        Index("ix_evento_auditoria_tramite_id_ocurrido_en", "tramite_id", "ocurrido_en"),
        Index("ix_evento_auditoria_entidad_tipo_entidad_id", "entidad_tipo", "entidad_id"),
    )

    id: Mapped[int] = _id()
    tramite_id: Mapped[int | None] = mapped_column(ForeignKey("tramite.id"))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    actor_tipo: Mapped[TipoActor] = mapped_column(catalogo(TipoActor, 10), nullable=False)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("version_documental.id"))
    entidad_tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    entidad_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    resultado: Mapped[ResultadoAuditoria] = mapped_column(
        catalogo(ResultadoAuditoria, 20), nullable=False
    )
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("clock_timestamp()")
    )
    solicitud_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
