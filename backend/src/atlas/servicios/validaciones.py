"""Validación humana de la clasificación y de los campos (RF-09, RF-12, RN-02, RN-03).

Reglas: solo la versión vigente; trámite en Borrador o
Pendiente de validación; los campos, después de validar la clasificación y según el
esquema del tipo validado; valores en formato canónico.

Cada validación es una fila nueva: una corrección posterior referencia la que
reemplaza, y quien valida debe indicar cuál es la vigente (si otra persona validó antes,
la operación se rechaza sin efectos). Solo los valores validados alimentan reglas y
decisiones (RN-02); la IA no interviene aquí. Cada validación vuelve a ejecutar las
reglas de consistencia pertinentes y puede sugerir vínculos (hito 1.7).
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from atlas.dominio import formatos
from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    ClaseSugerencia,
    DisparadorRegla,
    EstadoTramite,
    MotivoAusencia,
    TipoDocumental,
    TipoValidacion,
)
from atlas.dominio.fuentes import FuenteIndicada
from atlas.persistencia.modelos import (
    Documento,
    ReferenciaFuente,
    Tramite,
    ValidacionHumana,
    ValorSugerido,
    VersionDocumental,
)
from atlas.procesamiento import esquemas
from atlas.servicios import reglas, resultados, vinculos
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, ErrorDominio
from atlas.servicios.tramites import documento_del_tramite

ESTADOS_QUE_ADMITEN = frozenset({EstadoTramite.BORRADOR, EstadoTramite.PENDIENTE_VALIDACION})
CAMPO_CLASIFICACION = esquemas.CAMPO_CLASIFICACION


@dataclass
class EstadoDato:
    """Lo que la persona ve de un dato: la sugerencia, la validación vigente y el historial."""

    clase: ClaseSugerencia
    campo: str
    sugerencia: tuple[ValorSugerido, ReferenciaFuente | None] | None
    vigente: ValidacionHumana | None
    historial: list[ValidacionHumana] = field(default_factory=list)


@dataclass
class ValidacionesDeVersion:
    documento: Documento
    version: VersionDocumental
    tipo_validado: TipoDocumental | None
    clasificacion: EstadoDato
    campos: list[EstadoDato]
    fuera_de_esquema: list[ValidacionHumana]
    fuentes: dict[int, ReferenciaFuente]


def _vigentes(validaciones: list[ValidacionHumana]) -> dict[tuple[str, str], ValidacionHumana]:
    reemplazadas = {v.reemplaza_a_id for v in validaciones if v.reemplaza_a_id is not None}
    return {(v.clase, v.campo): v for v in validaciones if v.id not in reemplazadas}


def consultar(sesion: Session, tramite: Tramite, documento_id: int) -> ValidacionesDeVersion:
    documento = documento_del_tramite(sesion, tramite, documento_id)
    version = sesion.get_one(VersionDocumental, documento.version_vigente_id)
    validaciones = list(
        sesion.scalars(
            select(ValidacionHumana)
            .where(ValidacionHumana.version_id == version.id)
            .order_by(ValidacionHumana.id)
        )
    )
    vigentes = _vigentes(validaciones)
    _, sugeridas = resultados.sugerencias_vigentes(sesion, version.archivo_id)
    sugerencias = {(v.clase, v.campo): (v, f) for v, f in sugeridas}

    def estado(
        clase: ClaseSugerencia,
        campo: str,
        sugerencia: tuple[ValorSugerido, ReferenciaFuente | None] | None,
    ) -> EstadoDato:
        return EstadoDato(
            clase=clase,
            campo=campo,
            sugerencia=sugerencia,
            vigente=vigentes.get((clase, campo)),
            historial=[v for v in validaciones if (v.clase, v.campo) == (clase, campo)],
        )

    clasificacion = estado(
        ClaseSugerencia.CLASIFICACION,
        CAMPO_CLASIFICACION,
        sugerencias.get((ClaseSugerencia.CLASIFICACION, CAMPO_CLASIFICACION)),
    )
    tipo = (
        TipoDocumental(clasificacion.vigente.valor_validado or "")
        if clasificacion.vigente
        else None
    )
    campos: list[EstadoDato] = []
    nombres: set[str] = set()
    if tipo is not None:
        esquema = esquemas.version_esquema_extraccion(tipo)
        for campo in esquemas.CAMPOS[tipo]:
            nombres.add(campo.nombre)
            sugerida = sugerencias.get((ClaseSugerencia.CAMPO, campo.nombre))
            # RF-10: solo se presenta la sugerencia extraída con el esquema del tipo validado.
            if sugerida is not None and sugerida[0].version_esquema != esquema:
                sugerida = None
            campos.append(estado(ClaseSugerencia.CAMPO, campo.nombre, sugerida))
    fuera = [v for v in validaciones if v.clase == ClaseSugerencia.CAMPO and v.campo not in nombres]
    ids_fuente = {v.fuente_id for v in validaciones if v.fuente_id is not None}
    fuentes = {
        f.id: f
        for f in sesion.scalars(select(ReferenciaFuente).where(ReferenciaFuente.id.in_(ids_fuente)))
    }
    return ValidacionesDeVersion(
        documento=documento,
        version=version,
        tipo_validado=tipo,
        clasificacion=clasificacion,
        campos=campos,
        fuera_de_esquema=fuera,
        fuentes=fuentes,
    )


@dataclass(frozen=True)
class ValidacionRegistrada:
    validacion: ValidacionHumana
    fuente: ReferenciaFuente | None
    advertencias: list[str]


def registrar(
    sesion: Session,
    *,
    tramite: Tramite,
    documento_id: int,
    usuario_id: int,
    campo: str,
    valor_validado: str | None,
    valor_sugerido_id: int | None,
    reemplaza_a_id: int | None,
    fuente: FuenteIndicada | None,
    ausente: MotivoAusencia | None = None,
    solicitud_id: uuid.UUID | None = None,
) -> ValidacionRegistrada:
    """Registra una confirmación, una corrección, un valor sin sugerencia o una ausencia.

    Una ausencia declara que el campo no consta en la versión o no
    aplica: no lleva valor ni fuente y puede descartar la sugerencia. Nunca se inventa un
    valor. El trámite llega bloqueado por el llamador.
    """
    if tramite.estado not in ESTADOS_QUE_ADMITEN:
        raise Conflicto("El estado del trámite no admite validar datos")
    if (ausente is None) == (valor_validado is None):
        raise ErrorDominio("Indicá un valor validado o declaralo ausente, no ambas cosas")
    actual = consultar(sesion, tramite, documento_id)
    clase = ClaseSugerencia.CLASIFICACION if campo == CAMPO_CLASIFICACION else ClaseSugerencia.CAMPO

    advertencias: list[str] = []
    valor: str | None = None
    if clase is ClaseSugerencia.CLASIFICACION:
        if valor_validado is None:
            raise ErrorDominio("La clasificación no admite ausencia: validá un tipo documental")
        try:
            valor = TipoDocumental(valor_validado.strip()).value
        except ValueError as error:
            raise ErrorDominio("El tipo documental no pertenece al catálogo") from error
        dato = actual.clasificacion
    else:
        if actual.tipo_validado is None:
            raise Conflicto("Validá primero la clasificación del documento")
        definicion = next(
            (c for c in esquemas.CAMPOS[actual.tipo_validado] if c.nombre == campo), None
        )
        if definicion is None:
            raise ErrorDominio("El campo no pertenece al esquema del tipo validado")
        if valor_validado is not None:
            valor, advertencias = formatos.canonico(valor_validado, definicion.clase)
        dato = next(d for d in actual.campos if d.campo == campo)

    vigente_id = dato.vigente.id if dato.vigente else None
    if reemplaza_a_id != vigente_id:
        raise Conflicto("La validación de este dato cambió. Consultala de nuevo antes de validar.")

    sugerencia, fuente_sugerida = dato.sugerencia if dato.sugerencia else (None, None)
    if valor_sugerido_id is not None and (sugerencia is None or sugerencia.id != valor_sugerido_id):
        raise ErrorDominio("La sugerencia indicada no corresponde a este dato")
    if ausente is not None:
        tipo = TipoValidacion.AUSENTE
        if fuente is not None:
            raise ErrorDominio("Una ausencia no lleva fuente")
    elif valor_sugerido_id is None:
        tipo = TipoValidacion.SIN_SUGERENCIA
    elif sugerencia is not None and valor == sugerencia.valor:
        tipo = TipoValidacion.CONFIRMACION
    else:
        tipo = TipoValidacion.CORRECCION

    referencia: ReferenciaFuente | None = None
    if fuente is not None and tipo is not TipoValidacion.CONFIRMACION:
        # §5.3.3: si la corrección usa otra fuente, también se registra esa referencia.
        if fuente.vacia:
            raise ErrorDominio("La fuente debe indicar página, sección o fragmento")
        referencia = ReferenciaFuente(
            archivo_id=actual.version.archivo_id,
            pagina=fuente.pagina,
            seccion=fuente.seccion,
            fragmento=fuente.fragmento,
        )
        sesion.add(referencia)
        sesion.flush()
    elif tipo not in (TipoValidacion.SIN_SUGERENCIA, TipoValidacion.AUSENTE):
        referencia = fuente_sugerida

    validacion = ValidacionHumana(
        version_id=actual.version.id,
        clase=clase,
        campo=campo,
        valor_sugerido_id=valor_sugerido_id,
        reemplaza_a_id=reemplaza_a_id,
        validador_id=usuario_id,
        fuente_id=referencia.id if referencia is not None else None,
        valor_validado=valor,
        tipo=tipo,
        motivo_ausencia=ausente,
    )
    try:
        with sesion.begin_nested():
            sesion.add(validacion)
            sesion.flush()
    except IntegrityError as error:
        # Respaldo de la base ante una carrera: solo un reemplazo se completa (§5.3.3).
        raise Conflicto(
            "La validación de este dato cambió. Consultala de nuevo antes de validar."
        ) from error

    if clase is ClaseSugerencia.CLASIFICACION:
        actual.documento.tipo = TipoDocumental(valor or "")  # P3 del modelo (RN-02)
        sesion.flush()

    registrar_evento_auditoria(
        sesion,
        accion=_accion(clase, tipo),
        entidad_tipo="validacion_humana",
        entidad_id=validacion.id,
        actor_id=usuario_id,
        tramite_id=tramite.id,
        version_id=actual.version.id,
        solicitud_id=solicitud_id,
    )
    # §5.3.5: con el dato validado, sugerir vínculos y volver a
    # ejecutar las reglas de los vínculos confirmados del documento, en esta transacción.
    vinculos.sugerir(
        sesion, tramite_id=tramite.id, documento_id=actual.documento.id, solicitud_id=solicitud_id
    )
    reglas.ejecutar(
        sesion,
        tramite_id=tramite.id,
        disparador=DisparadorRegla.VALIDACION,
        documento_id=actual.documento.id,
        solicitud_id=solicitud_id,
    )
    sesion.refresh(validacion)
    return ValidacionRegistrada(validacion=validacion, fuente=referencia, advertencias=advertencias)


def _accion(clase: ClaseSugerencia, tipo: TipoValidacion) -> AccionAuditoria:
    if clase is ClaseSugerencia.CLASIFICACION:
        return (
            AccionAuditoria.CLASIFICACION_CONFIRMADA
            if tipo is TipoValidacion.CONFIRMACION
            else AccionAuditoria.CLASIFICACION_CORREGIDA
        )
    return {
        TipoValidacion.CONFIRMACION: AccionAuditoria.CAMPO_CONFIRMADO,
        TipoValidacion.CORRECCION: AccionAuditoria.CAMPO_CORREGIDO,
        TipoValidacion.SIN_SUGERENCIA: AccionAuditoria.CAMPO_REGISTRADO,
        TipoValidacion.AUSENTE: AccionAuditoria.CAMPO_DECLARADO_AUSENTE,
    }[tipo]
