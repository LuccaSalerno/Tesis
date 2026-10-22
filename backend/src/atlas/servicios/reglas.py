"""Ejecución y consulta de las reglas de consistencia (RF-16, RN-02, RN-06, §5.3.5, PD-01).

DO-2026-10-22-REG: las reglas se ejecutan en la misma transacción que la acción que las
dispara (P4), sobre cada vínculo confirmado cuyos documentos tienen tipos validados que
corresponden a la regla (P5), con los valores validados vigentes de la versión vigente de
cada documento (P6). Solo se registra una ejecución nueva si cambiaron las versiones o las
validaciones de entrada; las anteriores nunca se modifican. Las reglas no cambian el
estado del trámite ni deciden nada (RN-06).
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from atlas.dominio import reglas
from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    ClaseSugerencia,
    DisparadorRegla,
    EstadoVinculo,
    ResultadoRegla,
    TipoDocumental,
    TipoValidacion,
)
from atlas.persistencia.modelos import (
    Documento,
    EjecucionRegla,
    EjecucionReglaVersion,
    EntradaRegla,
    ValidacionHumana,
    VersionDocumental,
    VinculoDocumental,
)
from atlas.procesamiento import esquemas
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import NoEncontrado

SIN_VINCULO = "No hay documentos vinculados con los tipos que compara la regla."


@dataclass(frozen=True)
class EstadoValidado:
    """Lo validado de la versión vigente de un documento: tipo y campos de su esquema, con
    valor (`campos`) o declarados ausentes por una persona (`ausentes`, DO-2026-10-22-WEB)."""

    documento: Documento
    version: VersionDocumental
    tipo: TipoDocumental | None
    campos: dict[str, ValidacionHumana]
    ausentes: dict[str, ValidacionHumana]


def estado_validado(sesion: Session, documento: Documento) -> EstadoValidado:
    version = sesion.get_one(VersionDocumental, documento.version_vigente_id)
    validaciones = list(
        sesion.scalars(select(ValidacionHumana).where(ValidacionHumana.version_id == version.id))
    )
    reemplazadas = {v.reemplaza_a_id for v in validaciones}
    vigentes = [v for v in validaciones if v.id not in reemplazadas]
    clasificacion = next((v for v in vigentes if v.clase == ClaseSugerencia.CLASIFICACION), None)
    tipo = (
        None
        if clasificacion is None
        else TipoDocumental(clasificacion.valor_validado or "")  # la clasificación nunca es ausente
    )
    esquema = set() if tipo is None else {c.nombre for c in esquemas.CAMPOS[tipo]}
    del_esquema = [v for v in vigentes if v.clase == ClaseSugerencia.CAMPO and v.campo in esquema]
    return EstadoValidado(
        documento=documento,
        version=version,
        tipo=tipo,
        campos={v.campo: v for v in del_esquema if v.tipo != TipoValidacion.AUSENTE},
        ausentes={v.campo: v for v in del_esquema if v.tipo == TipoValidacion.AUSENTE},
    )


def _estados(sesion: Session, vinculo: VinculoDocumental) -> tuple[EstadoValidado, EstadoValidado]:
    origen = sesion.get_one(Documento, vinculo.documento_origen_id)
    destino = sesion.get_one(Documento, vinculo.documento_destino_id)
    return estado_validado(sesion, origen), estado_validado(sesion, destino)


def _ultima(sesion: Session, vinculo_id: int, regla: reglas.Regla) -> EjecucionRegla | None:
    return sesion.scalars(
        select(EjecucionRegla)
        .where(
            EjecucionRegla.vinculo_id == vinculo_id,
            EjecucionRegla.codigo_regla == regla.codigo,
            EjecucionRegla.version_regla == regla.version,
        )
        .order_by(EjecucionRegla.id.desc())
        .limit(1)
    ).first()


def _insumos(sesion: Session, ejecucion_id: int) -> tuple[set[int], set[int]]:
    versiones = set(
        sesion.scalars(
            select(EjecucionReglaVersion.version_id).where(
                EjecucionReglaVersion.ejecucion_regla_id == ejecucion_id
            )
        )
    )
    entradas = set(
        sesion.scalars(
            select(EntradaRegla.validacion_id).where(
                EntradaRegla.ejecucion_regla_id == ejecucion_id
            )
        )
    )
    return versiones, entradas


def ejecutar(
    sesion: Session,
    *,
    tramite_id: int,
    disparador: DisparadorRegla,
    documento_id: int | None = None,
    vinculo_id: int | None = None,
    solicitud_id: uuid.UUID | None = None,
) -> list[EjecucionRegla]:
    """Ejecuta las reglas pertinentes de los vínculos confirmados afectados (P4, P5)."""
    consulta = select(VinculoDocumental).where(
        VinculoDocumental.tramite_id == tramite_id,
        VinculoDocumental.estado == EstadoVinculo.CONFIRMADO,
    )
    if documento_id is not None:
        consulta = consulta.where(
            or_(
                VinculoDocumental.documento_origen_id == documento_id,
                VinculoDocumental.documento_destino_id == documento_id,
            )
        )
    if vinculo_id is not None:
        consulta = consulta.where(VinculoDocumental.id == vinculo_id)
    nuevas: list[EjecucionRegla] = []
    for vinculo in sesion.scalars(consulta.order_by(VinculoDocumental.id)).all():
        estados = _estados(sesion, vinculo)
        por_tipo = {e.tipo: e for e in estados if e.tipo is not None}
        for regla in reglas.pertinentes(estados[0].tipo, estados[1].tipo):
            usadas = {
                tipo: {c: por_tipo[tipo].campos[c] for c in campos if c in por_tipo[tipo].campos}
                for tipo, campos in regla.campos.items()
            }
            # Una ausencia declarada también es una entrada: la explicación la cita (V3).
            declaradas = {
                tipo: {
                    c: por_tipo[tipo].ausentes[c] for c in campos if c in por_tipo[tipo].ausentes
                }
                for tipo, campos in regla.campos.items()
            }
            versiones = {por_tipo[tipo].version.id for tipo in regla.tipos}
            entradas = {
                v.id for grupo in (usadas, declaradas) for c in grupo.values() for v in c.values()
            }
            ultima = _ultima(sesion, vinculo.id, regla)
            if ultima is not None and _insumos(sesion, ultima.id) == (versiones, entradas):
                continue  # mismas entradas: la ejecución vigente ya refleja este estado
            evaluacion = regla.evaluar(
                {
                    tipo: {c: v.valor_validado or "" for c, v in campos.items()}
                    for tipo, campos in usadas.items()
                },
                {tipo: frozenset(campos) for tipo, campos in declaradas.items()},
            )
            ejecucion = EjecucionRegla(
                tramite_id=tramite_id,
                vinculo_id=vinculo.id,
                codigo_regla=regla.codigo,
                version_regla=regla.version,
                resultado=evaluacion.resultado,
                explicacion=evaluacion.explicacion,
                disparador=disparador,
            )
            sesion.add(ejecucion)
            sesion.flush()
            sesion.add_all(
                [
                    EjecucionReglaVersion(
                        ejecucion_regla_id=ejecucion.id,
                        version_id=por_tipo[tipo].version.id,
                        papel=tipo,
                    )
                    for tipo in regla.tipos
                ]
                + [
                    EntradaRegla(ejecucion_regla_id=ejecucion.id, validacion_id=i)
                    for i in sorted(entradas)
                ]
            )
            sesion.flush()
            registrar_evento_auditoria(
                sesion,
                accion=AccionAuditoria.REGLA_EJECUTADA,
                entidad_tipo="ejecucion_regla",
                entidad_id=ejecucion.id,
                actor_id=None,  # la ejecuta el sistema; la acción que la disparó ya está auditada
                tramite_id=tramite_id,
                solicitud_id=solicitud_id,
            )
            nuevas.append(ejecucion)
    return nuevas


# --- Consulta (RF-16, V3) --------------------------------------------------------------


@dataclass(frozen=True)
class VersionConsiderada:
    papel: TipoDocumental
    version: VersionDocumental
    documento: Documento


@dataclass(frozen=True)
class ValorComparado:
    papel: TipoDocumental
    validacion: ValidacionHumana


@dataclass(frozen=True)
class DetalleEjecucion:
    ejecucion: EjecucionRegla
    regla: reglas.Regla
    versiones: list[VersionConsiderada]
    valores: list[ValorComparado]


@dataclass(frozen=True)
class Control:
    """Situación actual de una regla en un vínculo, o sin vínculo pertinente (P5)."""

    regla: reglas.Regla
    vinculo_id: int | None
    detalle: DetalleEjecucion | None

    @property
    def resultado(self) -> ResultadoRegla:
        return (
            ResultadoRegla.NO_APLICABLE
            if self.detalle is None
            else self.detalle.ejecucion.resultado
        )

    @property
    def explicacion(self) -> str:
        return SIN_VINCULO if self.detalle is None else self.detalle.ejecucion.explicacion


def _regla(ejecucion: EjecucionRegla) -> reglas.Regla:
    return next(
        r
        for r in reglas.CATALOGO
        if (r.codigo, r.version) == (ejecucion.codigo_regla, ejecucion.version_regla)
    )


def detalles(sesion: Session, ejecuciones: Iterable[EjecucionRegla]) -> list[DetalleEjecucion]:
    resultado: list[DetalleEjecucion] = []
    for ejecucion in ejecuciones:
        filas = sesion.execute(
            select(EjecucionReglaVersion, VersionDocumental, Documento)
            .join(VersionDocumental, VersionDocumental.id == EjecucionReglaVersion.version_id)
            .join(Documento, Documento.id == VersionDocumental.documento_id)
            .where(EjecucionReglaVersion.ejecucion_regla_id == ejecucion.id)
            .order_by(EjecucionReglaVersion.papel)
        ).all()
        versiones = [
            VersionConsiderada(papel=TipoDocumental(f.papel), version=v, documento=d)
            for f, v, d in filas
        ]
        papel_de_version = {c.version.id: c.papel for c in versiones}
        validaciones = sesion.scalars(
            select(ValidacionHumana)
            .join(EntradaRegla, EntradaRegla.validacion_id == ValidacionHumana.id)
            .where(EntradaRegla.ejecucion_regla_id == ejecucion.id)
            .order_by(ValidacionHumana.id)
        ).all()
        resultado.append(
            DetalleEjecucion(
                ejecucion=ejecucion,
                regla=_regla(ejecucion),
                versiones=versiones,
                valores=[
                    ValorComparado(papel=papel_de_version[v.version_id], validacion=v)
                    for v in validaciones
                ],
            )
        )
    return resultado


def obtener(sesion: Session, tramite_id: int, ejecucion_id: int) -> DetalleEjecucion:
    ejecucion = sesion.get(EjecucionRegla, ejecucion_id)
    if ejecucion is None or ejecucion.tramite_id != tramite_id:
        raise NoEncontrado("La ejecución no existe en este trámite")
    return detalles(sesion, [ejecucion])[0]


def historial(sesion: Session, tramite_id: int) -> list[DetalleEjecucion]:
    return detalles(
        sesion,
        sesion.scalars(
            select(EjecucionRegla)
            .where(EjecucionRegla.tramite_id == tramite_id)
            .order_by(EjecucionRegla.id)
        ).all(),
    )


def vigentes(sesion: Session, tramite_id: int) -> list[Control]:
    """Última ejecución de cada regla pertinente por vínculo confirmado, más las reglas sin
    vínculo pertinente como no aplicables (P5: calculado, no se guarda)."""
    controles: list[Control] = []
    con_vinculo: set[str] = set()
    vinculos = sesion.scalars(
        select(VinculoDocumental)
        .where(
            VinculoDocumental.tramite_id == tramite_id,
            VinculoDocumental.estado == EstadoVinculo.CONFIRMADO,
        )
        .order_by(VinculoDocumental.id)
    ).all()
    for vinculo in vinculos:
        origen, destino = _estados(sesion, vinculo)
        for regla in reglas.pertinentes(origen.tipo, destino.tipo):
            ultima = _ultima(sesion, vinculo.id, regla)
            if ultima is None:  # pragma: no cover - toda vinculación pertinente ya se ejecutó
                continue
            con_vinculo.add(regla.codigo)
            controles.append(Control(regla, vinculo.id, detalles(sesion, [ultima])[0]))
    controles.extend(
        Control(regla, None, None) for regla in reglas.CATALOGO if regla.codigo not in con_vinculo
    )
    return sorted(controles, key=lambda c: (c.regla.codigo, c.vinculo_id or 0))
