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
    Float,
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from atlas.dominio.enumeraciones import (
    ClaseSugerencia,
    EstadoIncorporacion,
    EstadoTrabajo,
    EstadoTramite,
    EstadoUsuario,
    FormatoArchivo,
    MotivoAbstencion,
    MotivoSinFuente,
    ResultadoAuditoria,
    Rol,
    TipoActor,
    TipoDocumental,
    TipoValidacion,
)
from atlas.persistencia.base import Base
from atlas.persistencia.vector import Vector


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


class AutorizacionCarga(Base):
    """Técnica (+): URL prefirmada emitida para una carga (§5.3.1, RC-P04). Se usa una sola vez."""

    __tablename__ = "autorizacion_carga"
    __table_args__ = (CheckConstraint("tamano_bytes > 0", name="tamano_positivo"),)

    id: Mapped[int] = _id()
    tramite_id: Mapped[int] = mapped_column(ForeignKey("tramite.id"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    clave_objeto: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    formato: Mapped[FormatoArchivo] = mapped_column(catalogo(FormatoArchivo, 10), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    creada_en: Mapped[datetime] = _instante()
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    archivo_id: Mapped[int | None] = mapped_column(ForeignKey("archivo.id"), unique=True)
    limpiada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TrabajoProcesamiento(Base):
    """Técnica (+): trabajo de procesamiento de un archivo (§5.3.1, RC-P08)."""

    __tablename__ = "trabajo_procesamiento"
    __table_args__ = (CheckConstraint("intento > 0", name="intento_positivo"),)

    id: Mapped[int] = _id()
    archivo_id: Mapped[int] = mapped_column(ForeignKey("archivo.id"), nullable=False, unique=True)
    intento: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    estado: Mapped[EstadoTrabajo] = mapped_column(
        catalogo(EstadoTrabajo, 20), nullable=False, server_default=EstadoTrabajo.PENDIENTE.value
    )
    ejecucion_iniciada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    codigo_error: Mapped[str | None] = mapped_column(String(60))
    creado_en: Mapped[datetime] = _instante()
    actualizado_en: Mapped[datetime] = _instante()


class ReferenciaFuente(Base):
    """Figura 5.4: localizador del origen de un resultado automático (§5.3.3, RF-11)."""

    __tablename__ = "referencia_fuente"
    __table_args__ = (
        CheckConstraint("pagina IS NULL OR pagina > 0", name="pagina_positiva"),
        CheckConstraint("(trabajo_id IS NULL) = (intento IS NULL)", name="trabajo_e_intento"),
        CheckConstraint(
            "pagina IS NOT NULL OR seccion IS NOT NULL OR fragmento IS NOT NULL",
            name="algun_localizador",
        ),
    )

    id: Mapped[int] = _id()
    archivo_id: Mapped[int] = mapped_column(ForeignKey("archivo.id"), nullable=False, index=True)
    pagina: Mapped[int | None] = mapped_column(Integer)
    seccion: Mapped[str | None] = mapped_column(String(255))
    fragmento: Mapped[str | None] = mapped_column(Text)
    # Sin trabajo ni intento: fuente indicada por una persona al corregir (§5.3.3).
    trabajo_id: Mapped[int | None] = mapped_column(ForeignKey("trabajo_procesamiento.id"))
    intento: Mapped[int | None] = mapped_column(Integer)
    creado_en: Mapped[datetime] = _instante()


class ValorSugerido(Base):
    """Figura 5.4: sugerencia automática; solo su validación humana la vuelve utilizable."""

    __tablename__ = "valor_sugerido"
    __table_args__ = (
        UniqueConstraint("trabajo_id", "intento", "clase", "campo"),
        CheckConstraint(
            "(fuente_id IS NULL) = (motivo_sin_fuente IS NOT NULL)", name="fuente_o_motivo"
        ),
    )

    id: Mapped[int] = _id()
    archivo_id: Mapped[int] = mapped_column(ForeignKey("archivo.id"), nullable=False, index=True)
    fuente_id: Mapped[int | None] = mapped_column(ForeignKey("referencia_fuente.id"))
    clase: Mapped[ClaseSugerencia] = mapped_column(catalogo(ClaseSugerencia, 20), nullable=False)
    campo: Mapped[str] = mapped_column(String(60), nullable=False)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    valor_original: Mapped[str] = mapped_column(Text, nullable=False)
    motivo_sin_fuente: Mapped[MotivoSinFuente | None] = mapped_column(catalogo(MotivoSinFuente, 20))
    trabajo_id: Mapped[int] = mapped_column(ForeignKey("trabajo_procesamiento.id"), nullable=False)
    intento: Mapped[int] = mapped_column(Integer, nullable=False)
    modelo: Mapped[str] = mapped_column(String(120), nullable=False)
    version_instrucciones: Mapped[str] = mapped_column(String(40), nullable=False)
    version_esquema: Mapped[str] = mapped_column(String(40), nullable=False)
    creado_en: Mapped[datetime] = _instante()


class ValidacionHumana(Base):
    """Figura 5.4: confirmación o corrección de un dato de una versión (RF-09, RF-12, RN-03).

    Inmutable: una corrección posterior es una fila nueva que referencia la que reemplaza.
    """

    __tablename__ = "validacion_humana"
    __table_args__ = (
        CheckConstraint(
            "(tipo = 'sin_sugerencia') = (valor_sugerido_id IS NULL)", name="sin_sugerencia"
        ),
        CheckConstraint("btrim(valor_validado) <> ''", name="valor_no_vacio"),
        Index(
            "uq_validacion_humana_primera",
            "version_id",
            "clase",
            "campo",
            unique=True,
            postgresql_where=text("reemplaza_a_id IS NULL"),
        ),
    )

    id: Mapped[int] = _id()
    version_id: Mapped[int] = mapped_column(
        ForeignKey("version_documental.id"), nullable=False, index=True
    )
    clase: Mapped[ClaseSugerencia] = mapped_column(catalogo(ClaseSugerencia, 20), nullable=False)
    campo: Mapped[str] = mapped_column(String(60), nullable=False)
    valor_sugerido_id: Mapped[int | None] = mapped_column(ForeignKey("valor_sugerido.id"))
    reemplaza_a_id: Mapped[int | None] = mapped_column(
        ForeignKey("validacion_humana.id"), unique=True
    )
    validador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    fuente_id: Mapped[int | None] = mapped_column(ForeignKey("referencia_fuente.id"))
    valor_validado: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[TipoValidacion] = mapped_column(catalogo(TipoValidacion, 20), nullable=False)
    validado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("clock_timestamp()")
    )


DIMENSIONES_EMBEDDING = 1024  # Cohere Embed Multilingual v3 (tesis §5.4.1, RC-P07.3)


class Fragmento(Base):
    """Figura 5.4: fragmento indexado de un archivo, con su localizador y su vector."""

    __tablename__ = "fragmento"
    __table_args__ = (
        UniqueConstraint("trabajo_id", "intento", "orden"),
        CheckConstraint("btrim(contenido) <> ''", name="contenido_no_vacio"),
        CheckConstraint("orden > 0", name="orden_positivo"),
    )

    id: Mapped[int] = _id()
    archivo_id: Mapped[int] = mapped_column(ForeignKey("archivo.id"), nullable=False, index=True)
    fuente_id: Mapped[int | None] = mapped_column(ForeignKey("referencia_fuente.id"))
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSIONES_EMBEDDING), nullable=False)
    trabajo_id: Mapped[int] = mapped_column(ForeignKey("trabajo_procesamiento.id"), nullable=False)
    intento: Mapped[int] = mapped_column(Integer, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    modelo_embeddings: Mapped[str] = mapped_column(String(120), nullable=False)
    version_segmentacion: Mapped[str] = mapped_column(String(40), nullable=False)
    creado_en: Mapped[datetime] = _instante()


class ConsultaAsistida(Base):
    """Técnica (+): registro de cada consulta asistida (§5.2, §5.3.4, DO-2026-10-22-RAG P2)."""

    __tablename__ = "consulta_asistida"
    __table_args__ = (
        CheckConstraint(
            "suficiente = (respuesta IS NOT NULL) AND suficiente = (motivo_abstencion IS NULL)",
            name="respuesta_o_abstencion",
        ),
        CheckConstraint("btrim(pregunta) <> ''", name="pregunta_no_vacia"),
    )

    id: Mapped[int] = _id()
    tramite_id: Mapped[int] = mapped_column(ForeignKey("tramite.id"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    suficiente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    respuesta: Mapped[str | None] = mapped_column(Text)
    afirmaciones: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    motivo_abstencion: Mapped[MotivoAbstencion | None] = mapped_column(
        catalogo(MotivoAbstencion, 30)
    )
    modelo_generacion: Mapped[str | None] = mapped_column(String(120))
    version_instrucciones: Mapped[str | None] = mapped_column(String(40))
    modelo_embeddings: Mapped[str] = mapped_column(String(120), nullable=False)
    tokens_entrada: Mapped[int | None] = mapped_column(Integer)
    tokens_salida: Mapped[int | None] = mapped_column(Integer)
    duracion_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("clock_timestamp()")
    )


class ConsultaFragmento(Base):
    """Técnica (+): fragmentos recuperados para una consulta y si fueron citados."""

    __tablename__ = "consulta_fragmento"
    __table_args__ = (
        UniqueConstraint("consulta_id", "fragmento_id"),
        CheckConstraint("posicion > 0", name="posicion_positiva"),
    )

    consulta_id: Mapped[int] = mapped_column(ForeignKey("consulta_asistida.id"), primary_key=True)
    posicion: Mapped[int] = mapped_column(Integer, primary_key=True)
    fragmento_id: Mapped[int] = mapped_column(ForeignKey("fragmento.id"), nullable=False)
    distancia: Mapped[float] = mapped_column(Float, nullable=False)
    citado: Mapped[bool] = mapped_column(Boolean, nullable=False)
