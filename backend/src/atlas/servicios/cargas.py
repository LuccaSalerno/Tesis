"""Carga de archivos e incorporación como documento nuevo (RF-04, RF-05, RF-07, §5.3.1).

Recorrido: la API autoriza la carga y emite una URL prefirmada; el navegador
transfiere el archivo a S3; al confirmar, la API verifica el objeto y registra el
archivo pendiente y su trabajo en una transacción, y recién después inicia la
ejecución de Step Functions. Si el inicio falla, el trabajo queda pendiente para
el reconciliador. La carga no modifica versiones ni el estado del trámite.
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    EstadoIncorporacion,
    EstadoTrabajo,
    EstadoTramite,
    FormatoArchivo,
)
from atlas.dominio.validacion_archivo import (
    ArchivoRechazado,
    LimitesCarga,
    validar_contenido,
    validar_tamano,
)
from atlas.integraciones.puertos import (
    AlmacenDocumental,
    ErrorIntegracion,
    OrquestadorProcesamiento,
)
from atlas.persistencia.modelos import (
    Archivo,
    AutorizacionCarga,
    Documento,
    TrabajoProcesamiento,
    Tramite,
    VersionDocumental,
)
from atlas.registro import registrar_evento
from atlas.servicios import tramites
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, NoEncontrado

_registrador = logging.getLogger("atlas.cargas")

TIPOS_CONTENIDO = {
    FormatoArchivo.PDF: "application/pdf",
    FormatoArchivo.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass(frozen=True)
class CargaAutorizada:
    autorizacion: AutorizacionCarga
    url: str
    tipo_contenido: str


@dataclass(frozen=True)
class CargaConfirmada:
    archivo: Archivo
    trabajo: TrabajoProcesamiento
    nueva: bool


def autorizar(
    sesion: Session,
    almacen: AlmacenDocumental,
    limites: LimitesCarga,
    *,
    tramite: Tramite,
    usuario_id: int,
    nombre: str,
    formato: FormatoArchivo,
    tamano_bytes: int,
    vigencia_s: int,
) -> CargaAutorizada:
    """Comprobaciones preliminares (RC-P04) y URL prefirmada de un solo uso."""
    tramites.exigir_no_terminal(tramite)
    if tamano_bytes > limites.tamano_maximo_bytes:
        validar_tamano(tamano_bytes, tamano_bytes, limites)
    clave = f"tramites/{tramite.id}/cargas/{uuid.uuid4()}"
    tipo_contenido = TIPOS_CONTENIDO[formato]
    url = almacen.url_carga(clave, tipo_contenido, vigencia_s)
    autorizacion = AutorizacionCarga(
        tramite_id=tramite.id,
        usuario_id=usuario_id,
        clave_objeto=clave,
        nombre=nombre,
        formato=formato,
        tamano_bytes=tamano_bytes,
        expira_en=datetime.now(UTC) + timedelta(seconds=vigencia_s),
    )
    sesion.add(autorizacion)
    sesion.flush()
    return CargaAutorizada(autorizacion=autorizacion, url=url, tipo_contenido=tipo_contenido)


def confirmar(
    sesion: Session,
    almacen: AlmacenDocumental,
    orquestador: OrquestadorProcesamiento,
    limites: LimitesCarga,
    *,
    tramite: Tramite,
    autorizacion_id: int,
    usuario_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> CargaConfirmada:
    """Verifica el objeto, registra archivo y trabajo, confirma la transacción e inicia
    el procesamiento. Una confirmación repetida devuelve el mismo archivo (§5.3.1)."""
    autorizacion = sesion.scalar(
        select(AutorizacionCarga)
        .where(
            AutorizacionCarga.id == autorizacion_id,
            AutorizacionCarga.tramite_id == tramite.id,
            AutorizacionCarga.usuario_id == usuario_id,
        )
        .with_for_update()
    )
    if autorizacion is None:
        raise NoEncontrado("La carga no existe")

    if autorizacion.archivo_id is not None:
        archivo = sesion.get_one(Archivo, autorizacion.archivo_id)
        trabajo = _trabajo_de(sesion, archivo.id)
        sesion.commit()
        if trabajo.estado == EstadoTrabajo.PENDIENTE:
            _iniciar_procesamiento(sesion, orquestador, trabajo)
        return CargaConfirmada(archivo=archivo, trabajo=trabajo, nueva=False)

    tramites.exigir_no_terminal(tramite)
    if autorizacion.expira_en < datetime.now(UTC):
        raise Conflicto("La autorización de carga venció. Volvé a iniciar la carga.")
    metadatos = almacen.metadatos(autorizacion.clave_objeto)
    if metadatos is None:
        raise ArchivoRechazado(
            "archivo_no_recibido",
            "No se recibió el archivo. Transferilo con la URL autorizada y volvé a confirmar.",
        )
    validar_tamano(metadatos.tamano_bytes, autorizacion.tamano_bytes, limites)
    datos = almacen.leer(autorizacion.clave_objeto)
    formato = FormatoArchivo(autorizacion.formato)
    validar_contenido(datos, formato, limites)

    archivo = Archivo(
        tramite_id=tramite.id,
        clave_objeto=autorizacion.clave_objeto,
        huella=hashlib.sha256(datos).hexdigest(),
        estado_incorporacion=EstadoIncorporacion.PENDIENTE,
        nombre=autorizacion.nombre,
        formato=formato,
        tamano_bytes=metadatos.tamano_bytes,
        cargado_por_id=usuario_id,
    )
    sesion.add(archivo)
    sesion.flush()
    trabajo = TrabajoProcesamiento(archivo_id=archivo.id, intento=1)
    sesion.add(trabajo)
    autorizacion.archivo_id = archivo.id
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.CARGA_CONFIRMADA,
        entidad_tipo="archivo",
        entidad_id=archivo.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    sesion.commit()  # §5.3.1: archivo y trabajo quedan registrados antes de iniciar
    _iniciar_procesamiento(sesion, orquestador, trabajo)
    sesion.refresh(archivo)
    return CargaConfirmada(archivo=archivo, trabajo=trabajo, nueva=True)


def _trabajo_de(sesion: Session, archivo_id: int) -> TrabajoProcesamiento:
    trabajo = sesion.scalar(
        select(TrabajoProcesamiento).where(TrabajoProcesamiento.archivo_id == archivo_id)
    )
    if trabajo is None:
        raise NoEncontrado("El archivo no tiene trabajo de procesamiento")
    return trabajo


def _iniciar_procesamiento(
    sesion: Session, orquestador: OrquestadorProcesamiento, trabajo: TrabajoProcesamiento
) -> None:
    try:
        orquestador.iniciar(trabajo.id, trabajo.intento)
    except ErrorIntegracion as error:
        # El trabajo sigue pendiente y registrado: lo recupera el reconciliador (RC-P08.3).
        registrar_evento(
            _registrador,
            "inicio_procesamiento_pendiente",
            logging.WARNING,
            trabajo_id=trabajo.id,
            codigo_error=error.codigo,
        )
        return
    trabajo.estado = EstadoTrabajo.EN_EJECUCION
    trabajo.ejecucion_iniciada_en = datetime.now(UTC)
    sesion.commit()
    sesion.refresh(trabajo)


def listar_archivos(
    sesion: Session, tramite_id: int
) -> list[tuple[Archivo, TrabajoProcesamiento | None]]:
    filas = sesion.execute(
        select(Archivo, TrabajoProcesamiento)
        .outerjoin(TrabajoProcesamiento, TrabajoProcesamiento.archivo_id == Archivo.id)
        .where(Archivo.tramite_id == tramite_id)
        .order_by(Archivo.id)
    ).all()
    return [(archivo, trabajo) for archivo, trabajo in filas]


def incorporar_como_documento_nuevo(
    sesion: Session,
    *,
    tramite: Tramite,
    archivo_id: int,
    usuario_id: int,
    nombre: str | None,
    solicitud_id: uuid.UUID | None = None,
) -> tuple[Documento, VersionDocumental]:
    """RF-07: el archivo pendiente pasa a ser un documento nuevo con su versión inicial
    vigente. El trámite (bloqueado por el llamador) vuelve a Borrador (Tabla 3.VI).

    PD-05.1: cuando existan ciclos de revisión, en esta misma transacción se cerrará
    el ciclo y se anularán sus tareas abiertas (hito 1.8 / Etapa 2).
    """
    tramites.exigir_no_terminal(tramite)
    archivo = sesion.get(Archivo, archivo_id, with_for_update=True)
    if archivo is None or archivo.tramite_id != tramite.id:
        raise NoEncontrado("El archivo no existe en este trámite")
    if archivo.estado_incorporacion != EstadoIncorporacion.PENDIENTE:
        raise Conflicto("El archivo ya fue incorporado o descartado")

    version_id = int(
        sesion.scalar(
            text("SELECT nextval(pg_get_serial_sequence('atlas.version_documental', 'id'))")
        )
    )
    documento = Documento(
        tramite_id=tramite.id, nombre=nombre or archivo.nombre, version_vigente_id=version_id
    )
    sesion.add(documento)
    sesion.flush()
    archivo.estado_incorporacion = EstadoIncorporacion.INCORPORADO
    sesion.flush()
    version = VersionDocumental(
        id=version_id,
        documento_id=documento.id,
        archivo_id=archivo.id,
        numero=1,
        creado_por_id=usuario_id,
    )
    sesion.add(version)
    sesion.flush()
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.DOCUMENTO_INCORPORADO,
        entidad_tipo="documento",
        entidad_id=documento.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        version_id=version.id,
        solicitud_id=solicitud_id,
    )
    if tramite.estado != EstadoTramite.BORRADOR:
        tramite.estado = EstadoTramite.BORRADOR
        registrar_evento_auditoria(
            sesion,
            accion=AccionAuditoria.TRAMITE_VUELVE_A_BORRADOR,
            entidad_tipo="tramite",
            entidad_id=tramite.id,
            actor_id=usuario_id,
            tramite_id=tramite.id,
            version_id=version.id,
            solicitud_id=solicitud_id,
        )
    tramite.actualizado_en = func.now()
    sesion.flush()
    return documento, version
