"""Detección de una posible versión nueva al procesar un archivo (RF-06, DO-2026-10-23-VER P1).

Reglas explicables, sin IA adicional: un documento del trámite es candidato si el tipo
validado de su versión vigente es igual al tipo sugerido del archivo y coincide el número
documental o, si no, el CUIT de la contraparte, el proveedor o el emisor. Gana el número
sobre el CUIT y, ante un empate, el documento cuya versión vigente es más reciente. Se
compara lo sugerido para el archivo con lo **validado** del documento; la relación es solo
una sugerencia hasta que el responsable la confirma (RF-07).
"""

from datetime import datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    ClaseSugerencia,
    CriterioVersion,
    EstadoIncorporacion,
    TipoDocumental,
)
from atlas.persistencia.modelos import (
    Archivo,
    Documento,
    SugerenciaVersion,
    Tramite,
    ValorSugerido,
    VersionDocumental,
)
from atlas.procesamiento.contenido import comparable
from atlas.servicios.reglas import estado_validado
from atlas.servicios.tramites import ESTADOS_TERMINALES

CAMPO_NUMERO: Final = "numero"
CAMPO_CUIT: Final = {
    TipoDocumental.CONTRATO: "cuit_contraparte",
    TipoDocumental.PRESUPUESTO: "cuit_proveedor",
    TipoDocumental.ORDEN_COMPRA: "cuit_proveedor",
    TipoDocumental.FACTURA: "cuit_emisor",
    TipoDocumental.COMPROBANTE: "cuit_contraparte",
}


def _sugeridos(sesion: Session, archivo_id: int, intento: int) -> dict[str, str]:
    filas = sesion.scalars(
        select(ValorSugerido).where(
            ValorSugerido.archivo_id == archivo_id, ValorSugerido.intento == intento
        )
    ).all()
    return {
        ("tipo" if f.clase == ClaseSugerencia.CLASIFICACION else f.campo): f.valor for f in filas
    }


def detectar(sesion: Session, archivo_id: int, intento: int) -> SugerenciaVersion | None:
    """Registra la relación sugerida, si hay candidata, para un archivo todavía pendiente."""
    archivo = sesion.get_one(Archivo, archivo_id)
    tramite = sesion.get_one(Tramite, archivo.tramite_id)
    # RN-14, RN-15: un resultado tardío no sugiere nada en un trámite cerrado o cancelado.
    if (
        archivo.estado_incorporacion != EstadoIncorporacion.PENDIENTE
        or tramite.estado in ESTADOS_TERMINALES
    ):
        return None
    existente = sesion.scalar(
        select(SugerenciaVersion).where(SugerenciaVersion.archivo_id == archivo_id)
    )
    if existente is not None:
        return existente
    sugeridos = _sugeridos(sesion, archivo_id, intento)
    try:
        tipo = TipoDocumental(sugeridos.get("tipo", ""))
    except ValueError:
        return None
    candidatos: list[tuple[int, datetime, Documento, str]] = []
    documentos = sesion.scalars(
        select(Documento).where(Documento.tramite_id == archivo.tramite_id)
    ).all()
    for documento in documentos:
        estado = estado_validado(sesion, documento)
        if estado.tipo != tipo:
            continue
        for prioridad, campo in ((0, CAMPO_NUMERO), (1, CAMPO_CUIT[tipo])):
            sugerido, validado = sugeridos.get(campo), estado.campos.get(campo)
            if (
                sugerido
                and validado
                and validado.valor_validado
                and (comparable(sugerido) == comparable(validado.valor_validado))
            ):
                vigente = sesion.get_one(VersionDocumental, documento.version_vigente_id)
                candidatos.append((prioridad, vigente.creado_en, documento, campo))
                break
    if not candidatos:
        return None
    # Número antes que CUIT; dentro de cada criterio, la versión vigente más reciente.
    candidatos.sort(key=lambda c: (c[0], -c[1].timestamp()))
    prioridad, _, documento, campo = candidatos[0]
    sugerencia = SugerenciaVersion(
        archivo_id=archivo_id,
        documento_id=documento.id,
        criterio=CriterioVersion.NUMERO if prioridad == 0 else CriterioVersion.CUIT,
        campo=campo,
    )
    sesion.add(sugerencia)
    sesion.flush()
    return sugerencia
