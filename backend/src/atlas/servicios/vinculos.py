"""Vínculos entre documentos del mismo trámite (RF-14, RF-15, RN-05, §5.3.5).

DO-2026-10-22-REG:
- P1: el tipo indica qué justifica el vínculo: una referencia (con fuente opcional en el
  documento de origen) o campos compartidos.
- P2: eliminar es una baja lógica; la fila y sus ejecuciones quedan en el historial.
- P3: el sistema sugiere vínculos solo con valores validados y coincidentes (los CUIT que
  comparan R1 y R2); quedan pendientes y sin efecto hasta que el responsable los confirma.
  Un par que ya tuvo un vínculo, en cualquier estado, no se vuelve a sugerir.
- P7: se crean, confirman, rechazan y eliminan con el trámite en Borrador o Pendiente de
  validación. Un vínculo no cambia la vigencia de las versiones ni transfiere validaciones.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import (
    AccionAuditoria,
    DisparadorRegla,
    EstadoTramite,
    EstadoVinculo,
    OrigenVinculo,
    TipoDocumental,
    TipoVinculo,
)
from atlas.dominio.fuentes import FuenteIndicada
from atlas.persistencia.modelos import (
    Documento,
    ReferenciaFuente,
    Tramite,
    VersionDocumental,
    VinculoDocumental,
)
from atlas.servicios import reglas
from atlas.servicios.auditoria import registrar_evento_auditoria
from atlas.servicios.errores import Conflicto, ErrorDominio, NoEncontrado
from atlas.servicios.tramites import documento_del_tramite

ESTADOS_QUE_ADMITEN = frozenset({EstadoTramite.BORRADOR, EstadoTramite.PENDIENTE_VALIDACION})
YA_VINCULADOS = "Los documentos ya tienen un vínculo pendiente o confirmado"


@dataclass(frozen=True)
class CriterioSugerencia:
    """Par de campos validados cuya coincidencia sugiere un vínculo de origen a destino."""

    tipo_origen: TipoDocumental
    campo_origen: str
    tipo_destino: TipoDocumental
    campo_destino: str
    texto: str


CRITERIOS = (
    CriterioSugerencia(
        TipoDocumental.FACTURA,
        "cuit_emisor",
        TipoDocumental.ORDEN_COMPRA,
        "cuit_proveedor",
        "El CUIT del emisor de la factura coincide con el CUIT del proveedor de la orden de compra",
    ),
    CriterioSugerencia(
        TipoDocumental.ORDEN_COMPRA,
        "cuit_proveedor",
        TipoDocumental.CONTRATO,
        "cuit_contraparte",
        "El CUIT del proveedor de la orden de compra coincide con el CUIT de la contraparte"
        " del contrato",
    ),
)


def _exigir_estado(tramite: Tramite) -> None:
    if tramite.estado not in ESTADOS_QUE_ADMITEN:
        raise Conflicto("El estado del trámite no admite cambiar vínculos")


def _vinculo(sesion: Session, tramite: Tramite, vinculo_id: int) -> VinculoDocumental:
    vinculo = sesion.get(VinculoDocumental, vinculo_id)
    if vinculo is None or vinculo.tramite_id != tramite.id:
        raise NoEncontrado("El vínculo no existe en este trámite")
    return vinculo


def _insertar(sesion: Session, vinculo: VinculoDocumental) -> None:
    try:
        with sesion.begin_nested():
            sesion.add(vinculo)
            sesion.flush()
    except IntegrityError as error:
        # Respaldo de la base: un solo vínculo activo por par (índice único parcial).
        raise Conflicto(YA_VINCULADOS) from error
    sesion.refresh(vinculo)


def _auditar(
    sesion: Session,
    accion: AccionAuditoria,
    vinculo: VinculoDocumental,
    actor_id: int | None,
    solicitud_id: uuid.UUID | None,
) -> None:
    registrar_evento_auditoria(
        sesion,
        accion=accion,
        entidad_tipo="vinculo_documental",
        entidad_id=vinculo.id,
        actor_id=actor_id,
        tramite_id=vinculo.tramite_id,
        solicitud_id=solicitud_id,
    )


def crear(
    sesion: Session,
    *,
    tramite: Tramite,
    usuario_id: int,
    documento_origen_id: int,
    documento_destino_id: int,
    tipo: TipoVinculo,
    justificacion: str,
    fuente: FuenteIndicada | None = None,
    solicitud_id: uuid.UUID | None = None,
) -> VinculoDocumental:
    """RF-14 y RN-05: el vínculo manual rige de inmediato y dispara las reglas.

    El trámite llega bloqueado por el llamador (PD-05.2).
    """
    _exigir_estado(tramite)
    origen = documento_del_tramite(sesion, tramite, documento_origen_id)
    destino = documento_del_tramite(sesion, tramite, documento_destino_id)
    if origen.id == destino.id:
        raise ErrorDominio("Un documento no puede vincularse consigo mismo")
    if not justificacion.strip():
        raise ErrorDominio("La justificación del vínculo no puede estar vacía")
    if _activo(sesion, origen.id, destino.id) is not None:
        raise Conflicto(YA_VINCULADOS)
    referencia: ReferenciaFuente | None = None
    if fuente is not None:
        if tipo is not TipoVinculo.REFERENCIA:
            raise ErrorDominio("Solo un vínculo por referencia indica una fuente")
        if fuente.vacia:
            raise ErrorDominio("La fuente debe indicar página, sección o fragmento")
        version = sesion.get_one(VersionDocumental, origen.version_vigente_id)
        referencia = ReferenciaFuente(
            archivo_id=version.archivo_id,
            pagina=fuente.pagina,
            seccion=fuente.seccion,
            fragmento=fuente.fragmento,
        )
        sesion.add(referencia)
        sesion.flush()
    vinculo = VinculoDocumental(
        tramite_id=tramite.id,
        documento_origen_id=origen.id,
        documento_destino_id=destino.id,
        tipo=tipo,
        origen=OrigenVinculo.MANUAL,
        estado=EstadoVinculo.CONFIRMADO,
        justificacion=justificacion.strip(),
        fuente_id=None if referencia is None else referencia.id,
        creado_por_id=usuario_id,
    )
    _insertar(sesion, vinculo)
    _auditar(sesion, AccionAuditoria.VINCULO_CREADO, vinculo, usuario_id, solicitud_id)
    reglas.ejecutar(
        sesion,
        tramite_id=tramite.id,
        disparador=DisparadorRegla.VINCULO,
        vinculo_id=vinculo.id,
        solicitud_id=solicitud_id,
    )
    return vinculo


def _resolver(
    sesion: Session,
    *,
    tramite: Tramite,
    vinculo_id: int,
    usuario_id: int,
    desde: EstadoVinculo,
    hacia: EstadoVinculo,
    error: str,
) -> VinculoDocumental:
    _exigir_estado(tramite)
    vinculo = _vinculo(sesion, tramite, vinculo_id)
    if vinculo.estado != desde:
        raise Conflicto(error)
    vinculo.estado = hacia
    vinculo.resuelto_por_id = usuario_id
    vinculo.resuelto_en = func.clock_timestamp()
    sesion.flush()
    sesion.refresh(vinculo)
    return vinculo


def confirmar(
    sesion: Session,
    *,
    tramite: Tramite,
    vinculo_id: int,
    usuario_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> VinculoDocumental:
    """RF-15: la sugerencia confirmada pasa a regir y dispara las reglas."""
    vinculo = _resolver(
        sesion,
        tramite=tramite,
        vinculo_id=vinculo_id,
        usuario_id=usuario_id,
        desde=EstadoVinculo.PENDIENTE,
        hacia=EstadoVinculo.CONFIRMADO,
        error="Solo se confirma un vínculo sugerido pendiente",
    )
    _auditar(sesion, AccionAuditoria.VINCULO_CONFIRMADO, vinculo, usuario_id, solicitud_id)
    reglas.ejecutar(
        sesion,
        tramite_id=tramite.id,
        disparador=DisparadorRegla.VINCULO,
        vinculo_id=vinculo.id,
        solicitud_id=solicitud_id,
    )
    return vinculo


def rechazar(
    sesion: Session,
    *,
    tramite: Tramite,
    vinculo_id: int,
    usuario_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> VinculoDocumental:
    """RF-15: la sugerencia rechazada queda en el historial sin efecto."""
    vinculo = _resolver(
        sesion,
        tramite=tramite,
        vinculo_id=vinculo_id,
        usuario_id=usuario_id,
        desde=EstadoVinculo.PENDIENTE,
        hacia=EstadoVinculo.RECHAZADO,
        error="Solo se rechaza un vínculo sugerido pendiente",
    )
    _auditar(sesion, AccionAuditoria.VINCULO_RECHAZADO, vinculo, usuario_id, solicitud_id)
    return vinculo


def eliminar(
    sesion: Session,
    *,
    tramite: Tramite,
    vinculo_id: int,
    usuario_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> VinculoDocumental:
    """RF-14 y P2: baja lógica de un vínculo confirmado; sus ejecuciones quedan en el
    historial y dejan de mostrarse como vigentes."""
    vinculo = _resolver(
        sesion,
        tramite=tramite,
        vinculo_id=vinculo_id,
        usuario_id=usuario_id,
        desde=EstadoVinculo.CONFIRMADO,
        hacia=EstadoVinculo.ELIMINADO,
        error="Solo se elimina un vínculo confirmado; una sugerencia se rechaza",
    )
    _auditar(sesion, AccionAuditoria.VINCULO_ELIMINADO, vinculo, usuario_id, solicitud_id)
    return vinculo


def _activo(sesion: Session, a: int, b: int) -> VinculoDocumental | None:
    return sesion.scalars(
        select(VinculoDocumental).where(
            func.least(
                VinculoDocumental.documento_origen_id, VinculoDocumental.documento_destino_id
            )
            == min(a, b),
            func.greatest(
                VinculoDocumental.documento_origen_id, VinculoDocumental.documento_destino_id
            )
            == max(a, b),
            VinculoDocumental.estado.in_([EstadoVinculo.PENDIENTE, EstadoVinculo.CONFIRMADO]),
        )
    ).first()


def sugerir(
    sesion: Session,
    *,
    tramite_id: int,
    documento_id: int,
    solicitud_id: uuid.UUID | None = None,
) -> list[VinculoDocumental]:
    """RF-15 y P3: sugerencias por CUIT validado coincidente, atribuidas al sistema."""
    documentos = sesion.scalars(
        select(Documento).where(Documento.tramite_id == tramite_id).order_by(Documento.id)
    ).all()
    estados = {d.id: reglas.estado_validado(sesion, d) for d in documentos}
    este = estados[documento_id]
    if este.tipo is None:
        return []
    ya_vinculados = {
        frozenset((v.documento_origen_id, v.documento_destino_id))
        for v in sesion.scalars(
            select(VinculoDocumental).where(VinculoDocumental.tramite_id == tramite_id)
        )
    }
    sugeridos: list[VinculoDocumental] = []
    for otro in estados.values():
        if otro.documento.id == documento_id or otro.tipo is None:
            continue
        if frozenset((documento_id, otro.documento.id)) in ya_vinculados:
            continue
        for criterio in CRITERIOS:
            if (este.tipo, otro.tipo) == (criterio.tipo_origen, criterio.tipo_destino):
                origen, destino = este, otro
            elif (otro.tipo, este.tipo) == (criterio.tipo_origen, criterio.tipo_destino):
                origen, destino = otro, este
            else:
                continue
            valor_origen = origen.campos.get(criterio.campo_origen)
            valor_destino = destino.campos.get(criterio.campo_destino)
            if valor_origen is None or valor_destino is None:
                continue
            if valor_origen.valor_validado != valor_destino.valor_validado:
                continue
            vinculo = VinculoDocumental(
                tramite_id=tramite_id,
                documento_origen_id=origen.documento.id,
                documento_destino_id=destino.documento.id,
                tipo=TipoVinculo.CAMPOS,
                origen=OrigenVinculo.AUTOMATICO,
                estado=EstadoVinculo.PENDIENTE,
                justificacion=f"{criterio.texto} ({valor_origen.valor_validado}).",
            )
            _insertar(sesion, vinculo)
            _auditar(sesion, AccionAuditoria.VINCULO_SUGERIDO, vinculo, None, solicitud_id)
            sugeridos.append(vinculo)
    return sugeridos


def listar(sesion: Session, tramite_id: int, *, historial: bool = False) -> list[VinculoDocumental]:
    consulta = select(VinculoDocumental).where(VinculoDocumental.tramite_id == tramite_id)
    if not historial:
        consulta = consulta.where(
            VinculoDocumental.estado.in_([EstadoVinculo.PENDIENTE, EstadoVinculo.CONFIRMADO])
        )
    return list(sesion.scalars(consulta.order_by(VinculoDocumental.id)))


def fuentes(sesion: Session, vinculos: list[VinculoDocumental]) -> dict[int, ReferenciaFuente]:
    ids = {v.fuente_id for v in vinculos if v.fuente_id is not None}
    return {
        f.id: f
        for f in sesion.scalars(select(ReferenciaFuente).where(ReferenciaFuente.id.in_(ids)))
    }
