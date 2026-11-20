"""Valores cerrados del dominio (tesis §5.2: se representan mediante enumeraciones).

En la base se guardan como `varchar` con `CHECK`; estos valores son la
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
    VENCIDO = "vencido"  # no se incorporó dentro de su vigencia


class FormatoArchivo(StrEnum):
    """Formatos admitidos."""

    PDF = "pdf"
    DOCX = "docx"


class TipoDocumental(StrEnum):
    """Tipos documentales admitidos (§3.3.3)."""

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
    """Estado técnico del procesamiento de un archivo (§5.3.1).

    Es independiente del estado funcional del trámite. «En espera»: registrado
    sin cupo de procesamiento; lo admite el reconciliador.
    """

    PENDIENTE = "pendiente"  # registrado; inicio de la ejecución no confirmado
    EN_ESPERA = "en_espera"  # registrado; sin cupo de procesamiento todavía
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
    AUSENTE = "ausente"  # una persona declara que no consta o no aplica


class MotivoAusencia(StrEnum):
    """Por qué un campo del esquema no tiene valor en la versión."""

    NO_CONSTA = "no_consta"  # el dato no figura en el documento
    NO_APLICA = "no_aplica"  # el dato no corresponde a este caso documental


class MotivoAbstencion(StrEnum):
    """Por qué una consulta asistida no responde (RF-13)."""

    EVIDENCIA_INSUFICIENTE = "evidencia_insuficiente"  # lo indicó el modelo
    SIN_CITAS_VALIDAS = "sin_citas_validas"  # ninguna afirmación citó fragmentos recuperados
    SIN_FRAGMENTOS = "sin_fragmentos"  # no hay documentación autorizada indexada


class TipoVinculo(StrEnum):
    """Qué justifica un vínculo entre documentos (RF-14)."""

    REFERENCIA = "referencia"  # un documento cita al otro
    CAMPOS = "campos"  # los documentos comparten datos validados


class OrigenVinculo(StrEnum):
    """RN-05: el vínculo manual rige de inmediato; el automático espera confirmación."""

    MANUAL = "manual"
    AUTOMATICO = "automatico"


class EstadoVinculo(StrEnum):
    """Ciclo del vínculo (RF-14, RF-15). La eliminación es lógica."""

    PENDIENTE = "pendiente"  # sugerido, sin efecto hasta confirmarse
    CONFIRMADO = "confirmado"
    RECHAZADO = "rechazado"
    ELIMINADO = "eliminado"


class ResultadoRegla(StrEnum):
    """Los cuatro resultados de una regla de consistencia (§5.3.5)."""

    CUMPLIMIENTO = "cumplimiento"
    ADVERTENCIA = "advertencia"
    FALTA_DE_DATOS = "falta_de_datos"
    NO_APLICABLE = "no_aplicable"


class DisparadorRegla(StrEnum):
    """Qué provocó una ejecución de reglas (§5.3.5)."""

    VINCULO = "vinculo"  # vínculo creado o confirmado
    VALIDACION = "validacion"  # validación de la clasificación o de un campo


class AlcancePlantilla(StrEnum):
    """A qué trámites se sugiere una plantilla de flujo."""

    CONTRATO = "contrato"  # algún documento vigente clasificado como contrato
    GENERAL = "general"


class EstadoCiclo(StrEnum):
    """Situación de un ciclo de revisión (RN-09, RN-12)."""

    EN_CURSO = "en_curso"
    APROBADO = "aprobado"
    OBSERVADO = "observado"
    DESPLAZADO = "desplazado"  # cambió el conjunto documental (RN-12)
    CANCELADO = "cancelado"  # el responsable canceló el trámite (RN-14)


class EstadoTarea(StrEnum):
    """Estado de una tarea; no es un estado del trámite."""

    EN_ESPERA = "en_espera"  # espera la aprobación de la tarea anterior
    PENDIENTE = "pendiente"  # habilitada para decidir
    APROBADA = "aprobada"
    OBSERVADA = "observada"
    ANULADA = "anulada"  # por cambio documental (RN-12)
    DESCARTADA = "descartada"  # el ciclo concluyó por una observación anterior


class TipoDecision(StrEnum):
    """Resolución de una tarea (RF-20)."""

    APROBACION = "aprobacion"
    OBSERVACION = "observacion"


class AccionAuditoria(StrEnum):
    """Catálogo de acciones auditadas (RF-21)."""

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
    PROCESAMIENTO_REINTENTADO = "procesamiento_reintentado"  # RNF-06
    VERSION_INCORPORADA = "version_incorporada"  # RF-07: relación de versión confirmada
    SUGERENCIA_VERSION_RECHAZADA = "sugerencia_version_rechazada"  # RF-07
    ARCHIVO_DESCARTADO = "archivo_descartado"  # RF-07
    FIRMA_SIMULADA_APLICADA = "firma_simulada_aplicada"  # RF-23, RN-11
    TRAMITE_CERRADO = "tramite_cerrado"  # RF-23
    DOCUMENTO_INCORPORADO = "documento_incorporado"
    TRAMITE_VUELVE_A_BORRADOR = "tramite_vuelve_a_borrador"
    CLASIFICACION_CONFIRMADA = "clasificacion_confirmada"
    CLASIFICACION_CORREGIDA = "clasificacion_corregida"
    CAMPO_CONFIRMADO = "campo_confirmado"
    CAMPO_CORREGIDO = "campo_corregido"
    CAMPO_REGISTRADO = "campo_registrado"
    CAMPO_DECLARADO_AUSENTE = "campo_declarado_ausente"
    VINCULO_CREADO = "vinculo_creado"
    VINCULO_SUGERIDO = "vinculo_sugerido"
    VINCULO_CONFIRMADO = "vinculo_confirmado"
    VINCULO_RECHAZADO = "vinculo_rechazado"
    VINCULO_ELIMINADO = "vinculo_eliminado"
    REGLA_EJECUTADA = "regla_ejecutada"
    PLANTILLA_CREADA = "plantilla_creada"
    PLANTILLA_DESACTIVADA = "plantilla_desactivada"
    TRAMITE_ENVIADO_A_VALIDACION = "tramite_enviado_a_validacion"
    FLUJO_CONFIRMADO = "flujo_confirmado"
    TAREA_ASIGNADA = "tarea_asignada"
    TAREA_REASIGNADA = "tarea_reasignada"
    TAREA_SIN_ASIGNAR = "tarea_sin_asignar"
    TAREA_HABILITADA = "tarea_habilitada"
    TAREA_APROBADA = "tarea_aprobada"
    TAREA_OBSERVADA = "tarea_observada"
    TAREA_DESCARTADA = "tarea_descartada"
    TAREA_ANULADA = "tarea_anulada"
    TRAMITE_APROBADO = "tramite_aprobado"
    TRAMITE_OBSERVADO = "tramite_observado"
    TRAMITE_SUBSANADO = "tramite_subsanado"
    CICLO_DESPLAZADO = "ciclo_desplazado"
    TRAMITE_CANCELADO = "tramite_cancelado"  # RF-26, RN-14
    CICLO_CANCELADO = "ciclo_cancelado"  # RN-14
    CUENTA_SUPRIMIDA = "cuenta_suprimida"  # RF-25
    CUENTA_NOMBRE_CAMBIADO = "cuenta_nombre_cambiado"


class CriterioVersion(StrEnum):
    """Por qué un archivo podría ser versión nueva de un documento (RF-06)."""

    NUMERO = "numero"  # mismo tipo y mismo número documental
    CUIT = "cuit"  # mismo tipo y mismo CUIT de la contraparte, proveedor o emisor


class EstadoSugerenciaVersion(StrEnum):
    """Resolución de la relación de versión sugerida por el responsable (RF-07)."""

    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"  # incorporado como documento independiente
    DESCARTADA = "descartada"  # el archivo se descartó
