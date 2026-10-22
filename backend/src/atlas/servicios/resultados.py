"""Persistencia de los resultados del procesamiento (§5.3.1, §5.3.3, RC-P08.6).

Solo el intento vigente de un trabajo en curso registra resultados: los de un intento
anterior se descartan y se registra el descarte. Repetir la persistencia del mismo
intento no duplica efectos. Los resultados se asocian con el archivo; no modifican
versiones ni el estado del trámite.
"""

import logging
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import ClaseSugerencia, EstadoTrabajo, MotivoSinFuente
from atlas.persistencia.modelos import (
    Archivo,
    Fragmento,
    ReferenciaFuente,
    TrabajoProcesamiento,
    ValorSugerido,
)
from atlas.procesamiento.analisis import Clasificacion, Extraccion
from atlas.procesamiento.errores import ErrorPermanente
from atlas.procesamiento.esquemas import CAMPO_CLASIFICACION
from atlas.registro import registrar_evento

_registrador = logging.getLogger("atlas.procesamiento")

Resultado = Literal["persistido", "ya_persistido", "descartado"]
_EN_CURSO = (EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_EJECUCION)


def _trabajo_vigente(sesion: Session, trabajo_id: int, intento: int) -> TrabajoProcesamiento | None:
    trabajo = sesion.get(TrabajoProcesamiento, trabajo_id, with_for_update=True)
    if trabajo is None:
        raise ErrorPermanente("trabajo_inexistente")
    if trabajo.intento != intento or trabajo.estado not in _EN_CURSO:
        return None
    return trabajo


def preparar(sesion: Session, trabajo_id: int, intento: int) -> tuple[str, str]:
    """Devuelve (formato, clave del objeto): referencias técnicas para las etapas."""
    trabajo = _trabajo_vigente(sesion, trabajo_id, intento)
    if trabajo is None:
        raise ErrorPermanente("intento_obsoleto")
    archivo = sesion.get_one(Archivo, trabajo.archivo_id)
    return str(archivo.formato), archivo.clave_objeto


def persistir(
    sesion: Session,
    *,
    trabajo_id: int,
    intento: int,
    clasificacion: Clasificacion,
    extraccion: Extraccion,
    indexacion: dict[str, Any],
) -> Resultado:
    trabajo = sesion.get(TrabajoProcesamiento, trabajo_id, with_for_update=True)
    if trabajo is None:
        raise ErrorPermanente("trabajo_inexistente")
    if trabajo.intento == intento and trabajo.estado == EstadoTrabajo.COMPLETADO:
        return "ya_persistido"
    if trabajo.intento != intento or trabajo.estado not in _EN_CURSO:
        registrar_evento(
            _registrador,
            "resultado_descartado",
            trabajo_id=trabajo_id,
            codigo_error="intento_obsoleto",
        )
        return "descartado"

    comunes = {
        "archivo_id": trabajo.archivo_id,
        "trabajo_id": trabajo_id,
        "intento": intento,
    }
    sesion.add(
        ValorSugerido(
            **comunes,
            clase=ClaseSugerencia.CLASIFICACION,
            campo=CAMPO_CLASIFICACION,
            valor=clasificacion.tipo.value,
            valor_original=clasificacion.tipo.value,
            motivo_sin_fuente=MotivoSinFuente.NO_APLICA,
            modelo=clasificacion.uso.modelo,
            version_instrucciones=clasificacion.version_instrucciones,
            version_esquema=clasificacion.version_esquema,
        )
    )
    for campo in extraccion.campos:
        fuente_id = None
        if campo.motivo_sin_fuente is None:
            fuente = ReferenciaFuente(
                **comunes, pagina=campo.pagina, seccion=campo.seccion, fragmento=campo.fragmento
            )
            sesion.add(fuente)
            sesion.flush()
            fuente_id = fuente.id
        sesion.add(
            ValorSugerido(
                **comunes,
                fuente_id=fuente_id,
                clase=ClaseSugerencia.CAMPO,
                campo=campo.campo,
                valor=campo.valor,
                valor_original=campo.valor_original,
                motivo_sin_fuente=campo.motivo_sin_fuente,
                modelo=extraccion.uso.modelo,
                version_instrucciones=extraccion.version_instrucciones,
                version_esquema=extraccion.version_esquema,
            )
        )
    for fragmento in indexacion["fragmentos"]:
        # El fragmento conserva su localizador (§5.3.4); se asocia con el documento y la
        # versión a través del archivo una vez incorporado.
        fuente = ReferenciaFuente(
            **comunes,
            pagina=fragmento["pagina"],
            seccion=(fragmento["seccion"] or fragmento["localizador"])[:255],
        )
        sesion.add(fuente)
        sesion.flush()
        sesion.add(
            Fragmento(
                **comunes,
                fuente_id=fuente.id,
                contenido=fragmento["texto"],
                embedding=fragmento["embedding"],
                orden=fragmento["orden"],
                modelo_embeddings=indexacion["modelo_embeddings"],
                version_segmentacion=indexacion["version_segmentacion"],
            )
        )
    trabajo.estado = EstadoTrabajo.COMPLETADO
    trabajo.codigo_error = None
    sesion.flush()
    registrar_evento(_registrador, "resultado_persistido", trabajo_id=trabajo_id)
    return "persistido"


def registrar_fallo(sesion: Session, *, trabajo_id: int, intento: int, codigo: str) -> bool:
    """Fallo técnico del intento vigente (§5.3.1). No modifica el trámite."""
    trabajo = _trabajo_vigente(sesion, trabajo_id, intento)
    if trabajo is None:
        return False
    trabajo.estado = EstadoTrabajo.FALLIDO
    trabajo.codigo_error = codigo[:60]
    sesion.flush()
    registrar_evento(
        _registrador, "trabajo_fallido", logging.WARNING, trabajo_id=trabajo_id, codigo_error=codigo
    )
    return True


def sugerencias_vigentes(
    sesion: Session, archivo_id: int
) -> tuple[TrabajoProcesamiento | None, list[tuple[ValorSugerido, ReferenciaFuente | None]]]:
    """Sugerencias del intento vigente del trabajo del archivo (las anteriores quedan en
    el historial)."""
    trabajo = sesion.scalar(
        select(TrabajoProcesamiento).where(TrabajoProcesamiento.archivo_id == archivo_id)
    )
    if trabajo is None:
        return None, []
    filas = sesion.execute(
        select(ValorSugerido, ReferenciaFuente)
        .outerjoin(ReferenciaFuente, ReferenciaFuente.id == ValorSugerido.fuente_id)
        .where(ValorSugerido.trabajo_id == trabajo.id, ValorSugerido.intento == trabajo.intento)
        .order_by(ValorSugerido.id)
    ).all()
    return trabajo, [(v, f) for v, f in filas]
