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


class AccionAuditoria(StrEnum):
    """Catálogo de acciones auditadas (RF-21). Se amplía con cada hito."""

    CUENTA_ALTA = "cuenta_alta"
    CUENTA_HABILITADA = "cuenta_habilitada"
    CUENTA_DESHABILITADA = "cuenta_deshabilitada"
    ROL_OTORGADO = "rol_otorgado"
    ROL_RETIRADO = "rol_retirado"
    AUTORIZACION_CIERRE_OTORGADA = "autorizacion_cierre_otorgada"
    AUTORIZACION_CIERRE_RETIRADA = "autorizacion_cierre_retirada"
