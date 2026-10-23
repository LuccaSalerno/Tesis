"""Reconciliador de trabajos de procesamiento (RC-P08.3, 8 a 12; DO-2026-10-23-REC P3, P10).

Se ejecuta cada cinco minutos y hace tres cosas, en este orden:

1. **Inicios inciertos:** un trabajo `pendiente` con más de dos minutos se contrasta con su
   ejecución real, buscada por el nombre determinista del intento. Si no existe, se inicia;
   si existe, se reconoce. Nunca se crea una segunda ejecución del mismo intento.
2. **Trabajos interrumpidos:** un trabajo `en_ejecucion` cuya ejecución terminó sin registrar
   resultado, o que supera el límite de 30 minutos, pasa a fallido y libera su cupo. Un
   resultado tardío de ese intento se descarta (RC-P08.6).
3. **Admisión:** los trabajos `en_espera` se admiten por antigüedad mientras haya cupo, bajo
   el mismo lock que la confirmación de cargas. No es un intento nuevo (RC-P08.11).

Ningún paso modifica el estado funcional del trámite. Los registros llevan solo identificadores.
"""

import logging
from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import EstadoTrabajo
from atlas.integraciones.puertos import ErrorIntegracion
from atlas.persistencia.modelos import TrabajoProcesamiento
from atlas.registro import registrar_evento
from atlas.servicios import admision
from atlas.servicios.cargas import iniciar_procesamiento

_registrador = logging.getLogger("atlas.reconciliacion")

GRACIA_INICIO: Final = timedelta(minutes=2)
LIMITE_TRABAJO: Final = timedelta(minutes=30)
TERMINADAS: Final = frozenset({"FAILED", "TIMED_OUT", "ABORTED"})


class Orquestador(Protocol):
    def iniciar(self, trabajo_id: int, intento: int) -> None: ...

    def estado(self, trabajo_id: int, intento: int) -> str: ...


@dataclass
class Resumen:
    iniciados: list[int] = field(default_factory=list)
    reconocidos: list[int] = field(default_factory=list)
    interrumpidos: list[int] = field(default_factory=list)
    vencidos: list[int] = field(default_factory=list)
    admitidos: list[int] = field(default_factory=list)
    sin_resolver: list[int] = field(default_factory=list)

    def conteos(self) -> dict[str, int]:
        return {nombre: len(ids) for nombre, ids in self.__dict__.items()}


def _en_alcance(consulta: Any, alcance: Collection[int] | None) -> Any:
    """Sin alcance, todos los trabajos (producción); con alcance, solo esos (pruebas, nivel B)."""
    return consulta if alcance is None else consulta.where(TrabajoProcesamiento.id.in_(alcance))


def _fallar(sesion: Session, trabajo: TrabajoProcesamiento, codigo: str) -> None:
    trabajo.estado = EstadoTrabajo.FALLIDO
    trabajo.codigo_error = codigo
    sesion.commit()


def _evento(accion: str, trabajo: TrabajoProcesamiento, **extra: str) -> None:
    registrar_evento(
        _registrador,
        "reconciliacion",
        logging.INFO,
        accion=accion,
        trabajo_id=trabajo.id,
        intento=trabajo.intento,
        **extra,
    )


def _inicios_inciertos(
    sesion: Session,
    orquestador: Orquestador,
    ahora: datetime,
    resumen: Resumen,
    alcance: Collection[int] | None,
) -> None:
    consulta = (
        select(TrabajoProcesamiento)
        .where(
            TrabajoProcesamiento.estado == EstadoTrabajo.PENDIENTE,
            TrabajoProcesamiento.actualizado_en < ahora - GRACIA_INICIO,
        )
        .order_by(TrabajoProcesamiento.creado_en)
    )
    trabajos = sesion.scalars(_en_alcance(consulta, alcance)).all()
    for trabajo in trabajos:
        try:
            real = orquestador.estado(trabajo.id, trabajo.intento)
        except ErrorIntegracion as error:
            resumen.sin_resolver.append(trabajo.id)
            _evento("consulta_fallida", trabajo, codigo_error=error.codigo)
            continue
        if real == "inexistente":
            iniciar_procesamiento(sesion, orquestador, trabajo)
            destino = (
                resumen.iniciados
                if trabajo.estado == EstadoTrabajo.EN_EJECUCION
                else resumen.sin_resolver
            )
            destino.append(trabajo.id)
            _evento("inicio_recuperado", trabajo, estado=trabajo.estado.value)
        elif real in TERMINADAS:
            _fallar(sesion, trabajo, "ejecucion_interrumpida")
            resumen.interrumpidos.append(trabajo.id)
            _evento("ejecucion_terminada_sin_resultado", trabajo, estado_ejecucion=real)
        else:
            # La solicitud anterior fue aceptada: se reconoce, sin una segunda ejecución.
            trabajo.estado = EstadoTrabajo.EN_EJECUCION
            trabajo.ejecucion_iniciada_en = trabajo.ejecucion_iniciada_en or ahora
            sesion.commit()
            resumen.reconocidos.append(trabajo.id)
            _evento("inicio_reconocido", trabajo, estado_ejecucion=real)


def _interrumpidos(
    sesion: Session,
    orquestador: Orquestador,
    ahora: datetime,
    resumen: Resumen,
    alcance: Collection[int] | None,
) -> None:
    consulta = select(TrabajoProcesamiento).where(
        TrabajoProcesamiento.estado == EstadoTrabajo.EN_EJECUCION
    )
    trabajos = sesion.scalars(_en_alcance(consulta, alcance)).all()
    for trabajo in trabajos:
        inicio = trabajo.ejecucion_iniciada_en or trabajo.creado_en
        if ahora - inicio > LIMITE_TRABAJO:
            _fallar(sesion, trabajo, "tiempo_agotado")
            resumen.vencidos.append(trabajo.id)
            _evento("tiempo_agotado", trabajo)
            continue
        try:
            real = orquestador.estado(trabajo.id, trabajo.intento)
        except ErrorIntegracion as error:
            resumen.sin_resolver.append(trabajo.id)
            _evento("consulta_fallida", trabajo, codigo_error=error.codigo)
            continue
        if real in TERMINADAS:
            _fallar(sesion, trabajo, "ejecucion_interrumpida")
            resumen.interrumpidos.append(trabajo.id)
            _evento("ejecucion_terminada_sin_resultado", trabajo, estado_ejecucion=real)


def _admitir_en_espera(
    sesion: Session,
    orquestador: Orquestador,
    limite: int,
    resumen: Resumen,
    alcance: Collection[int] | None,
) -> None:
    admision.bloquear(sesion)
    cupo = limite - admision.en_curso(sesion)
    if cupo <= 0:
        sesion.commit()
        return
    consulta = (
        select(TrabajoProcesamiento)
        .where(TrabajoProcesamiento.estado == EstadoTrabajo.EN_ESPERA)
        .order_by(TrabajoProcesamiento.creado_en, TrabajoProcesamiento.id)
        .limit(cupo)
        .with_for_update()
    )
    admitidos = list(sesion.scalars(_en_alcance(consulta, alcance)).all())
    for trabajo in admitidos:
        trabajo.estado = EstadoTrabajo.PENDIENTE
    sesion.commit()  # el cupo queda tomado antes de iniciar, aunque el inicio falle
    for trabajo in admitidos:
        iniciar_procesamiento(sesion, orquestador, trabajo)
        resumen.admitidos.append(trabajo.id)
        _evento("admitido", trabajo, estado=trabajo.estado.value)


def reconciliar(
    sesion: Session,
    orquestador: Orquestador,
    *,
    limite: int,
    ahora: datetime | None = None,
    alcance: Collection[int] | None = None,
) -> Resumen:
    """`alcance` limita los trabajos examinados (pruebas); el cupo se cuenta sobre todos."""
    momento = ahora or datetime.now(UTC)
    resumen = Resumen()
    _inicios_inciertos(sesion, orquestador, momento, resumen, alcance)
    _interrumpidos(sesion, orquestador, momento, resumen, alcance)
    _admitir_en_espera(sesion, orquestador, limite, resumen, alcance)
    registrar_evento(_registrador, "reconciliacion_completada", **resumen.conteos())
    return resumen
