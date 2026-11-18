"""Carga de archivos e incorporación como documento nuevo (RF-04, RF-05, RF-07, §5.3.1).

Recorrido: la API autoriza la carga y emite una URL prefirmada; el navegador
transfiere el archivo a S3; al confirmar, la API verifica el objeto y registra el
archivo pendiente y su trabajo en una transacción, y recién después inicia la
ejecución de Step Functions. Si el inicio falla, el trabajo queda pendiente para
el reconciliador. La carga no modifica versiones ni el estado del trámite.

Vencimiento: la carga vive en el prefijo de cargas
temporales y tiene 24 h para confirmarse; al incorporarse, el original se
traslada al prefijo definitivo. La limpieza retira los objetos temporales que ya
no se necesitan, de forma idempotente y sin tocar los documentos confirmados.
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import exists, func, select, text, update
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    EstadoIncorporacion,
    EstadoSugerenciaVersion,
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
from atlas.integraciones.ciclo_vida_s3 import (
    PREFIJO_CARGAS_TEMPORALES,
    PREFIJO_DOCUMENTOS,
    PREFIJO_RESULTADOS,
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
    SugerenciaVersion,
    TrabajoProcesamiento,
    Tramite,
    VersionDocumental,
)
from atlas.registro import registrar_evento
from atlas.servicios import admision, ciclos, tramites
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, NoEncontrado

_registrador = logging.getLogger("atlas.cargas")

TIPOS_CONTENIDO = {
    FormatoArchivo.PDF: "application/pdf",
    FormatoArchivo.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def vencimiento(creacion: datetime, vigencia_s: int) -> datetime:
    return creacion + timedelta(seconds=vigencia_s)


def _vencida(creacion: datetime, vigencia_s: int, ahora: datetime | None = None) -> bool:
    return vencimiento(creacion, vigencia_s) <= (ahora or datetime.now(UTC))


def clave_definitiva(clave_temporal: str) -> str:
    """`cargas-temporales/tramites/{t}/{uuid}` → `documentos/tramites/{t}/{uuid}`."""
    if not clave_temporal.startswith(PREFIJO_CARGAS_TEMPORALES):
        raise ValueError("La clave no pertenece al prefijo de cargas temporales")
    return PREFIJO_DOCUMENTOS + clave_temporal.removeprefix(PREFIJO_CARGAS_TEMPORALES)


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
    """Comprobaciones preliminares y URL prefirmada de un solo uso."""
    tramites.exigir_no_terminal(tramite)
    if tamano_bytes > limites.tamano_maximo_bytes:
        validar_tamano(tamano_bytes, tamano_bytes, limites)
    clave = f"{PREFIJO_CARGAS_TEMPORALES}tramites/{tramite.id}/{uuid.uuid4()}"
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
    vigencia_pendiente_s: int,
    limite_concurrencia: int,
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
            iniciar_procesamiento(sesion, orquestador, trabajo)
        return CargaConfirmada(archivo=archivo, trabajo=trabajo, nueva=False)

    tramites.exigir_no_terminal(tramite)
    if _vencida(autorizacion.creada_en, vigencia_pendiente_s):
        raise Conflicto("La carga venció sin confirmarse. Volvé a iniciar la carga.")
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
    # Sin cupo queda «en espera»; el reconciliador lo admite después.
    admision.admitir(sesion, trabajo, limite_concurrencia)
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
    if trabajo.estado == EstadoTrabajo.PENDIENTE:
        iniciar_procesamiento(sesion, orquestador, trabajo)
    sesion.refresh(archivo)
    return CargaConfirmada(archivo=archivo, trabajo=trabajo, nueva=True)


def _trabajo_de(sesion: Session, archivo_id: int) -> TrabajoProcesamiento:
    trabajo = sesion.scalar(
        select(TrabajoProcesamiento).where(TrabajoProcesamiento.archivo_id == archivo_id)
    )
    if trabajo is None:
        raise NoEncontrado("El archivo no tiene trabajo de procesamiento")
    return trabajo


def iniciar_procesamiento(
    sesion: Session, orquestador: OrquestadorProcesamiento, trabajo: TrabajoProcesamiento
) -> None:
    try:
        orquestador.iniciar(trabajo.id, trabajo.intento)
    except ErrorIntegracion as error:
        # El trabajo sigue pendiente y registrado: lo recupera el reconciliador.
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


def reintentar(
    sesion: Session,
    orquestador: OrquestadorProcesamiento,
    *,
    tramite: Tramite,
    archivo_id: int,
    usuario_id: int,
    limite_concurrencia: int,
    solicitud_id: uuid.UUID | None = None,
) -> tuple[Archivo, TrabajoProcesamiento]:
    """Intento nuevo tras un fallo definitivo, por decisión explícita del responsable
    (RNF-06). Pasa por la admisión: puede quedar en espera de cupo."""
    tramites.exigir_no_terminal(tramite)
    archivo = sesion.get(Archivo, archivo_id)
    if archivo is None or archivo.tramite_id != tramite.id:
        raise NoEncontrado("El archivo no existe")
    trabajo = sesion.scalar(
        select(TrabajoProcesamiento)
        .where(TrabajoProcesamiento.archivo_id == archivo.id)
        .with_for_update()
    )
    if trabajo is None or trabajo.estado != EstadoTrabajo.FALLIDO:
        raise Conflicto("Solo se reintenta un procesamiento fallido")
    anterior = trabajo.intento
    trabajo.intento = anterior + 1  # el intento anterior queda descartado
    trabajo.codigo_error = None
    trabajo.ejecucion_iniciada_en = None
    admitido = admision.admitir(sesion, trabajo, limite_concurrencia)
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.PROCESAMIENTO_REINTENTADO,
        entidad_tipo="archivo",
        entidad_id=archivo.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    registrar_evento(
        _registrador, "procesamiento_reintentado", trabajo_id=trabajo.id, intento=anterior + 1
    )
    sesion.commit()
    if admitido == EstadoTrabajo.PENDIENTE:
        iniciar_procesamiento(sesion, orquestador, trabajo)
    sesion.refresh(archivo)
    return archivo, trabajo


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


def sugerencias_version(
    sesion: Session, tramite_id: int
) -> list[tuple[SugerenciaVersion, Documento]]:
    """RF-06: relaciones de versión sugeridas para los archivos del trámite."""
    filas = sesion.execute(
        select(SugerenciaVersion, Documento)
        .join(Documento, Documento.id == SugerenciaVersion.documento_id)
        .where(Documento.tramite_id == tramite_id)
    ).all()
    return [(sugerencia, documento) for sugerencia, documento in filas]


def _archivo_incorporable(
    sesion: Session,
    almacen: AlmacenDocumental,
    tramite: Tramite,
    archivo_id: int,
    vigencia_pendiente_s: int,
) -> Archivo:
    """Archivo pendiente, vigente y movido al prefijo definitivo con su huella verificada."""
    tramites.exigir_no_terminal(tramite)
    archivo = sesion.get(Archivo, archivo_id, with_for_update=True)
    if archivo is None or archivo.tramite_id != tramite.id:
        raise NoEncontrado("El archivo no existe en este trámite")
    if archivo.estado_incorporacion != EstadoIncorporacion.PENDIENTE:
        raise Conflicto("El archivo ya fue incorporado, descartado o venció")
    if _vencida(archivo.cargado_en, vigencia_pendiente_s):
        raise Conflicto("La carga venció: pasaron más de 24 horas sin incorporarla.")
    # El original pasa al prefijo definitivo, fuera de la limpieza de temporales, y se
    # comprueba que la copia conserve la huella registrada (§5.4.3).
    destino = clave_definitiva(archivo.clave_objeto)
    almacen.copiar(archivo.clave_objeto, destino)
    if hashlib.sha256(almacen.leer(destino)).hexdigest() != archivo.huella:
        raise ErrorIntegracion("s3_copia_inconsistente")
    archivo.estado_incorporacion = EstadoIncorporacion.INCORPORADO
    archivo.clave_objeto = destino
    return archivo


def _nuevo_id_version(sesion: Session) -> int:
    return int(
        sesion.scalar(
            text("SELECT nextval(pg_get_serial_sequence('atlas.version_documental', 'id'))")
        )
    )


def _cambio_documental(
    sesion: Session,
    tramite: Tramite,
    *,
    usuario_id: int,
    version_id: int,
    solicitud_id: uuid.UUID | None,
) -> None:
    """RN-12: el ciclo en curso queda desplazado, sus tareas abiertas anuladas y el
    trámite vuelve a Borrador, en la misma transacción que la incorporación."""
    ciclos.desplazar_en_curso(
        sesion,
        tramite_id=tramite.id,
        usuario_id=usuario_id,
        version_id=version_id,
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
            version_id=version_id,
            solicitud_id=solicitud_id,
        )
    tramite.actualizado_en = func.now()
    sesion.flush()


def _resolver_sugerencia(
    sesion: Session, archivo_id: int, estado: EstadoSugerenciaVersion, usuario_id: int
) -> SugerenciaVersion | None:
    sugerencia = sesion.scalar(
        select(SugerenciaVersion)
        .where(
            SugerenciaVersion.archivo_id == archivo_id,
            SugerenciaVersion.estado == EstadoSugerenciaVersion.PENDIENTE,
        )
        .with_for_update()
    )
    if sugerencia is not None:
        sugerencia.estado = estado
        sugerencia.resuelta_por_id = usuario_id
        sugerencia.resuelta_en = datetime.now(UTC)
        sesion.flush()
    return sugerencia


def incorporar_como_documento_nuevo(
    sesion: Session,
    almacen: AlmacenDocumental,
    *,
    tramite: Tramite,
    archivo_id: int,
    usuario_id: int,
    nombre: str | None,
    vigencia_pendiente_s: int,
    solicitud_id: uuid.UUID | None = None,
) -> tuple[Documento, VersionDocumental]:
    """RF-07: el archivo pendiente pasa a ser un documento nuevo con su versión inicial
    vigente. Si había una relación de versión sugerida, queda rechazada: el archivo es un
    documento independiente del candidato (RF-07). El trámite (bloqueado por el llamador)
    vuelve a Borrador (Tabla 3.VI, RN-12)."""
    archivo = _archivo_incorporable(sesion, almacen, tramite, archivo_id, vigencia_pendiente_s)
    version_id = _nuevo_id_version(sesion)
    documento = Documento(
        tramite_id=tramite.id, nombre=nombre or archivo.nombre, version_vigente_id=version_id
    )
    sesion.add(documento)
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
    rechazada = _resolver_sugerencia(
        sesion, archivo.id, EstadoSugerenciaVersion.RECHAZADA, usuario_id
    )
    if rechazada is not None:
        registrar_evento_auditoria(
            sesion,
            accion=AccionAuditoria.SUGERENCIA_VERSION_RECHAZADA,
            entidad_tipo="sugerencia_version",
            entidad_id=rechazada.id,
            actor_id=usuario_id,
            tramite_id=tramite.id,
            version_id=version.id,
            solicitud_id=solicitud_id,
        )
    _cambio_documental(
        sesion, tramite, usuario_id=usuario_id, version_id=version.id, solicitud_id=solicitud_id
    )
    return documento, version


def incorporar_como_version(
    sesion: Session,
    almacen: AlmacenDocumental,
    *,
    tramite: Tramite,
    archivo_id: int,
    usuario_id: int,
    vigencia_pendiente_s: int,
    solicitud_id: uuid.UUID | None = None,
) -> tuple[Documento, VersionDocumental]:
    """RF-07: confirma la relación de versión sugerida (RF-06). El archivo se incorpora al
    historial del documento candidato como su nueva versión vigente; la anterior queda
    inmutable con sus validaciones. RN-12: ciclo desplazado, tareas anuladas y trámite a
    Borrador. La versión nueva empieza sin valores validados: sus
    controles dejan de usar la anterior y se ejecutan al validarla (RN-02, RN-06)."""
    tramites.exigir_no_terminal(tramite)
    existente = sesion.get(Archivo, archivo_id)
    if existente is None or existente.tramite_id != tramite.id:
        raise NoEncontrado("El archivo no existe en este trámite")
    sugerencia = sesion.scalar(
        select(SugerenciaVersion).where(
            SugerenciaVersion.archivo_id == archivo_id,
            SugerenciaVersion.estado == EstadoSugerenciaVersion.PENDIENTE,
        )
    )
    if sugerencia is None:
        raise Conflicto("El archivo no tiene una relación de versión sugerida pendiente")
    documento = sesion.get(Documento, sugerencia.documento_id, with_for_update=True)
    if documento is None or documento.tramite_id != tramite.id:
        raise Conflicto("El documento candidato ya no pertenece al trámite")
    archivo = _archivo_incorporable(sesion, almacen, tramite, archivo_id, vigencia_pendiente_s)
    anterior = sesion.get_one(VersionDocumental, documento.version_vigente_id)
    version = VersionDocumental(
        id=_nuevo_id_version(sesion),
        documento_id=documento.id,
        archivo_id=archivo.id,
        numero=anterior.numero + 1,
        version_previa_id=anterior.id,
        creado_por_id=usuario_id,
    )
    sesion.add(version)
    sesion.flush()
    documento.version_vigente_id = version.id
    # `tipo` refleja la clasificación validada de la versión vigente (del modelo): la
    # nueva todavía no la tiene y no hereda la de la anterior (RN-02).
    documento.tipo = None
    sesion.flush()
    _resolver_sugerencia(sesion, archivo.id, EstadoSugerenciaVersion.CONFIRMADA, usuario_id)
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.VERSION_INCORPORADA,
        entidad_tipo="documento",
        entidad_id=documento.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        version_id=version.id,
        solicitud_id=solicitud_id,
    )
    _cambio_documental(
        sesion, tramite, usuario_id=usuario_id, version_id=version.id, solicitud_id=solicitud_id
    )
    return documento, version


def descartar(
    sesion: Session,
    *,
    tramite: Tramite,
    archivo_id: int,
    usuario_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> Archivo:
    """RF-07: el archivo pendiente se descarta sin crear documento ni versión; no cambia el
    conjunto documental ni el estado del trámite."""
    tramites.exigir_no_terminal(tramite)
    archivo = sesion.get(Archivo, archivo_id, with_for_update=True)
    if archivo is None or archivo.tramite_id != tramite.id:
        raise NoEncontrado("El archivo no existe en este trámite")
    if archivo.estado_incorporacion != EstadoIncorporacion.PENDIENTE:
        raise Conflicto("El archivo ya fue incorporado, descartado o venció")
    archivo.estado_incorporacion = EstadoIncorporacion.DESCARTADO
    _resolver_sugerencia(sesion, archivo.id, EstadoSugerenciaVersion.DESCARTADA, usuario_id)
    registrar_evento_auditoria(
        sesion,
        accion=AccionAuditoria.ARCHIVO_DESCARTADO,
        entidad_tipo="archivo",
        entidad_id=archivo.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        solicitud_id=solicitud_id,
    )
    sesion.flush()
    return archivo


@dataclass
class ResumenLimpieza:
    """Solo conteos: nada de claves, nombres ni contenido (regla 5 de AGENTS.md)."""

    revisadas: int = 0
    vencidas: int = 0
    objetos_limpiados: int = 0
    versiones_eliminadas: int = 0
    multipartes_abortadas: int = 0
    diferidas: int = 0
    errores: list[str] = field(default_factory=list)


def limpiar_cargas_vencidas(
    sesion: Session,
    almacen: AlmacenDocumental,
    *,
    vigencia_pendiente_s: int,
    ahora: datetime | None = None,
    lote: int = 100,
) -> ResumenLimpieza:
    """Limpieza segura e idempotente de cargas temporales.

    Revisa las autorizaciones con más de 24 h y sin limpiar:
    - sin archivo registrado: la carga nunca se confirmó;
    - con archivo pendiente vencido: pasa a `vencido` (auditado) antes de limpiar;
    - con archivo incorporado: su original ya está en el prefijo definitivo.
    Antes de eliminar comprueba que la clave sea temporal y que ningún archivo
    incorporado la use. Primero confirma los cambios de estado, después elimina
    todas las versiones del objeto y recién entonces marca la autorización como
    limpiada: si algo falla, la próxima ejecución lo retoma.
    """
    instante = ahora or datetime.now(UTC)
    limite = instante - timedelta(seconds=vigencia_pendiente_s)
    resumen = ResumenLimpieza()
    autorizaciones = list(
        sesion.scalars(
            select(AutorizacionCarga)
            .where(AutorizacionCarga.limpiada_en.is_(None), AutorizacionCarga.creada_en <= limite)
            .order_by(AutorizacionCarga.id)
            .limit(lote)
            .with_for_update(skip_locked=True)
        )
    )
    for autorizacion in autorizaciones:
        resumen.revisadas += 1
        if autorizacion.archivo_id is not None:
            archivo = sesion.get_one(Archivo, autorizacion.archivo_id, with_for_update=True)
            if archivo.estado_incorporacion == EstadoIncorporacion.PENDIENTE:
                if not _vencida(archivo.cargado_en, vigencia_pendiente_s, instante):
                    resumen.diferidas += 1  # se confirmó tarde: todavía está vigente
                    continue
                marcado = sesion.execute(
                    update(Archivo)
                    .where(
                        Archivo.id == archivo.id,
                        Archivo.estado_incorporacion == EstadoIncorporacion.PENDIENTE,
                    )
                    .values(estado_incorporacion=EstadoIncorporacion.VENCIDO)
                )
                if marcado.rowcount == 1:  # type: ignore[attr-defined]
                    resumen.vencidas += 1
                    registrar_evento_auditoria(
                        sesion,
                        accion=AccionAuditoria.CARGA_VENCIDA,
                        entidad_tipo="archivo",
                        entidad_id=archivo.id,
                        actor_id=None,
                        tramite_id=archivo.tramite_id,
                    )
        if not _clave_temporal_liberada(sesion, autorizacion.clave_objeto):
            resumen.errores.append("clave_en_uso")
            continue
        prefijos = _resultados_a_eliminar(sesion, autorizacion.archivo_id)
        sesion.commit()
        try:
            resumen.versiones_eliminadas += almacen.eliminar_definitivamente(
                autorizacion.clave_objeto
            )
            # Los resultados intermedios de una carga vencida
            # se eliminan con ella; los de archivos incorporados se conservan.
            for prefijo in prefijos:
                resumen.versiones_eliminadas += almacen.eliminar_prefijo(prefijo)
        except ErrorIntegracion as error:
            resumen.errores.append(error.codigo)
            continue
        sesion.execute(
            update(AutorizacionCarga)
            .where(AutorizacionCarga.id == autorizacion.id)
            .values(limpiada_en=func.now())
        )
        sesion.commit()
        resumen.objetos_limpiados += 1
    sesion.commit()
    try:
        resumen.multipartes_abortadas = almacen.abortar_multipartes(
            PREFIJO_CARGAS_TEMPORALES, limite
        )
    except ErrorIntegracion as error:
        resumen.errores.append(error.codigo)
    registrar_evento(
        _registrador,
        "limpieza_cargas_temporales",
        logging.WARNING if resumen.errores else logging.INFO,
        codigo_error=",".join(sorted(set(resumen.errores))) or None,
        revisadas=resumen.revisadas,
        vencidas=resumen.vencidas,
        objetos_limpiados=resumen.objetos_limpiados,
        versiones_eliminadas=resumen.versiones_eliminadas,
        multipartes_abortadas=resumen.multipartes_abortadas,
        diferidas=resumen.diferidas,
    )
    return resumen


def _resultados_a_eliminar(sesion: Session, archivo_id: int | None) -> list[str]:
    if archivo_id is None:
        return []
    archivo = sesion.get_one(Archivo, archivo_id)
    if archivo.estado_incorporacion not in (
        EstadoIncorporacion.VENCIDO,
        EstadoIncorporacion.DESCARTADO,
    ):
        return []
    trabajo_id = sesion.scalar(
        select(TrabajoProcesamiento.id).where(TrabajoProcesamiento.archivo_id == archivo_id)
    )
    return [] if trabajo_id is None else [f"{PREFIJO_RESULTADOS}{trabajo_id}/"]


def _clave_temporal_liberada(sesion: Session, clave: str) -> bool:
    """Solo se elimina una clave temporal que ningún archivo incorporado use."""
    if not clave.startswith(PREFIJO_CARGAS_TEMPORALES):
        return False
    en_uso = sesion.scalar(
        select(
            exists().where(
                Archivo.clave_objeto == clave,
                Archivo.estado_incorporacion == EstadoIncorporacion.INCORPORADO,
            )
        )
    )
    return not en_uso
