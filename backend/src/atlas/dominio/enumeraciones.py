"""Valores cerrados del dominio (tesis §5.2: se representan mediante enumeraciones).

En la base se guardan como `varchar` con `CHECK` (PD-04); estos valores son la
única fuente de los catálogos y la migración `0002` los replica literalmente.
"""

from enum import StrEnum


class EstadoUsuario(StrEnum):
    """Habilitación de la cuenta (RF-25, RN-01)."""

    HABILITADA = "habilitada"
    DESHABILITADA = "deshabilitada"
    SUPRIMIDA = "suprimida"


class Rol(StrEnum):
    """Los tres roles de la tesis (§3.3.2, Tabla 3.II)."""

    RESPONSABLE_TRAMITE = "responsable_tramite"
    REVISOR_APROBADOR = "revisor_aprobador"
    ADMINISTRADOR_OPERATIVO = "administrador_operativo"


class EstadoTramite(StrEnum):
    """Los siete estados funcionales del trámite (§3.2.1, Figura 3.5)."""

    BORRADOR = "borrador"
    PENDIENTE_VALIDACION = "pendiente_validacion"
    PENDIENTE_APROBACION = "pendiente_aprobacion"
    OBSERVADO = "observado"
    APROBADO = "aprobado"
    CERRADO = "cerrado"
    CANCELADO = "cancelado"


class EstadoIncorporacion(StrEnum):
    """Situación de un archivo cargado frente al conjunto documental (RF-04, RF-07)."""

    PENDIENTE = "pendiente"
    INCORPORADO = "incorporado"
    DESCARTADO = "descartado"
    VENCIDO = "vencido"  # no se incorporó dentro de su vigencia (DO-2026-10-22-CARGAS)


class FormatoArchivo(StrEnum):
    """Formatos admitidos (RC-P04)."""

    PDF = "pdf"
    DOCX = "docx"


class TipoDocumental(StrEnum):
    """Tipos documentales admitidos (§3.3.3, RC-P04)."""

    CONTRATO = "contrato"
    PRESUPUESTO = "presupuesto"
    ORDEN_COMPRA = "orden_compra"
    FACTURA = "factura"
    COMPROBANTE = "comprobante"


class TipoActor(StrEnum):
    """Quién realiza una acción auditada (RF-21)."""

    USUARIO = "usuario"
    SISTEMA = "sistema"


class ResultadoAuditoria(StrEnum):
    """Resultado de una acción auditada (RF-21)."""

    EXITO = "exito"
    RECHAZO = "rechazo"


class EstadoTrabajo(StrEnum):
    """Estado técnico del procesamiento de un archivo (§5.3.1, RC-P08).

    Es independiente del estado funcional del trámite. «En espera» (RC-P08.8)
    llega con el control de admisión y el reconciliador (Etapa 3).
    """

    PENDIENTE = "pendiente"  # registrado; inicio de la ejecución no confirmado
    EN_EJECUCION = "en_ejecucion"
    COMPLETADO = "completado"
    FALLIDO = "fallido"


class ClaseSugerencia(StrEnum):
    """Qué produjo el procesamiento (§5.3.2): la categoría o un campo extraído."""

    CLASIFICACION = "clasificacion"
    CAMPO = "campo"


class MotivoSinFuente(StrEnum):
    """Por qué una sugerencia no tiene localizador verificable (RF-11)."""

    NO_INFORMADA = "no_informada"  # el modelo no indicó página ni fragmento
    NO_VERIFICADA = "no_verificada"  # el fragmento citado no está en la página indicada
    NO_APLICA = "no_aplica"  # la clasificación se refiere al documento completo


class TipoValidacion(StrEnum):
    """Cómo resolvió la persona el dato (RF-09, RF-12, §5.3.3)."""

    CONFIRMACION = "confirmacion"  # aceptó la sugerencia tal cual
    CORRECCION = "correccion"  # registró un valor distinto del sugerido
    SIN_SUGERENCIA = "sin_sugerencia"  # el dato no tenía sugerencia


class MotivoAbstencion(StrEnum):
    """Por qué una consulta asistida no responde (RF-13, DO-2026-10-22-RAG, P3)."""

    EVIDENCIA_INSUFICIENTE = "evidencia_insuficiente"  # lo indicó el modelo
    SIN_CITAS_VALIDAS = "sin_citas_validas"  # ninguna afirmación citó fragmentos recuperados
    SIN_FRAGMENTOS = "sin_fragmentos"  # no hay documentación autorizada indexada


class AccionAuditoria(StrEnum):
    """Catálogo de acciones auditadas (RF-21). Se amplía con cada hito."""

    CUENTA_ALTA = "cuenta_alta"
    CUENTA_HABILITADA = "cuenta_habilitada"
    CUENTA_DESHABILITADA = "cuenta_deshabilitada"
    ROL_OTORGADO = "rol_otorgado"
    ROL_RETIRADO = "rol_retirado"
    AUTORIZACION_CIERRE_OTORGADA = "autorizacion_cierre_otorgada"
    AUTORIZACION_CIERRE_RETIRADA = "autorizacion_cierre_retirada"
    TRAMITE_CREADO = "tramite_creado"
    CARGA_CONFIRMADA = "carga_confirmada"
    CARGA_VENCIDA = "carga_vencida"
    DOCUMENTO_INCORPORADO = "documento_incorporado"
    TRAMITE_VUELVE_A_BORRADOR = "tramite_vuelve_a_borrador"
    CLASIFICACION_CONFIRMADA = "clasificacion_confirmada"
    CLASIFICACION_CORREGIDA = "clasificacion_corregida"
    CAMPO_CONFIRMADO = "campo_confirmado"
    CAMPO_CORREGIDO = "campo_corregido"
    CAMPO_REGISTRADO = "campo_registrado"
