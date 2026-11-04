/**
 * Rótulos y tonos del dominio. Cada familia de estados tiene su propio vocabulario visual
 * para no confundir el estado del trámite, el técnico del procesamiento, el de una tarea,
 * una sugerencia de la IA con un valor validado o una advertencia con una decisión.
 */
import type {
  CriterioVersion,
  EstadoCiclo,
  EstadoTarea,
  EstadoTrabajo,
  EstadoTramite,
  MotivoAusencia,
  ResultadoRegla,
  Rol,
  TipoDecision,
  TipoDocumental,
  TipoValidacion,
} from "@/api/tipos";

export type Tono = "neutro" | "info" | "exito" | "advertencia" | "peligro" | "primario";

type Catalogo<K extends string> = Record<K, { rotulo: string; tono: Tono }>;

export const ESTADO_TRAMITE: Catalogo<EstadoTramite> = {
  borrador: { rotulo: "Borrador", tono: "neutro" },
  pendiente_validacion: { rotulo: "Pendiente de validación", tono: "info" },
  pendiente_aprobacion: { rotulo: "Pendiente de aprobación", tono: "primario" },
  observado: { rotulo: "Observado", tono: "advertencia" },
  aprobado: { rotulo: "Aprobado", tono: "exito" },
  cerrado: { rotulo: "Cerrado", tono: "exito" },
  cancelado: { rotulo: "Cancelado", tono: "neutro" },
};

export const ESTADO_TAREA: Catalogo<EstadoTarea> = {
  en_espera: { rotulo: "En espera", tono: "neutro" },
  pendiente: { rotulo: "Pendiente", tono: "primario" },
  aprobada: { rotulo: "Aprobada", tono: "exito" },
  observada: { rotulo: "Observada", tono: "advertencia" },
  anulada: { rotulo: "Anulada", tono: "neutro" },
  descartada: { rotulo: "Descartada", tono: "neutro" },
};

export const ESTADO_CICLO: Catalogo<EstadoCiclo> = {
  en_curso: { rotulo: "En curso", tono: "primario" },
  aprobado: { rotulo: "Aprobado", tono: "exito" },
  observado: { rotulo: "Observado", tono: "advertencia" },
  desplazado: { rotulo: "Desplazado por cambio documental", tono: "neutro" },
  cancelado: { rotulo: "Cancelado con el trámite", tono: "neutro" },
};

export const ESTADO_TRABAJO: Catalogo<EstadoTrabajo> = {
  pendiente: { rotulo: "En cola", tono: "neutro" },
  // RC-P08.13: la espera por capacidad no es un error.
  en_espera: { rotulo: "En espera de capacidad", tono: "neutro" },
  en_ejecucion: { rotulo: "Procesando", tono: "info" },
  completado: { rotulo: "Procesado", tono: "exito" },
  fallido: { rotulo: "Falla técnica", tono: "peligro" },
};

export const RESULTADO_REGLA: Catalogo<ResultadoRegla> = {
  cumplimiento: { rotulo: "Cumple", tono: "exito" },
  advertencia: { rotulo: "Advertencia", tono: "advertencia" },
  falta_de_datos: { rotulo: "Falta de datos", tono: "neutro" },
  no_aplicable: { rotulo: "No aplicable", tono: "neutro" },
};

export const TIPO_VALIDACION: Catalogo<TipoValidacion> = {
  confirmacion: { rotulo: "Confirmado", tono: "exito" },
  correccion: { rotulo: "Corregido", tono: "info" },
  sin_sugerencia: { rotulo: "Registrado manualmente", tono: "info" },
  ausente: { rotulo: "Declarado ausente", tono: "neutro" },
};

export const DECISION: Catalogo<TipoDecision> = {
  aprobacion: { rotulo: "Aprobación", tono: "exito" },
  observacion: { rotulo: "Observación", tono: "advertencia" },
};

export const MOTIVO_AUSENCIA: Record<MotivoAusencia, string> = {
  no_consta: "No consta en el documento",
  no_aplica: "No aplica a este caso",
};

export const TIPO_DOCUMENTAL: Record<TipoDocumental, string> = {
  contrato: "Contrato",
  presupuesto: "Presupuesto",
  orden_compra: "Orden de compra",
  factura: "Factura",
  comprobante: "Comprobante",
};

export const ROL: Record<Rol, string> = {
  responsable_tramite: "Responsable del trámite",
  revisor_aprobador: "Revisor/Aprobador",
  administrador_operativo: "Administrador operativo",
};

export const CAMPO: Record<string, string> = {
  tipo_documental: "Tipo documental",
  contraparte: "Contraparte",
  cuit_contraparte: "CUIT de la contraparte",
  fecha_celebracion: "Fecha de celebración",
  vigencia_desde: "Vigencia desde",
  vigencia_hasta: "Vigencia hasta",
  monto_total: "Monto total",
  moneda: "Moneda",
  numero: "Número",
  fecha: "Fecha",
  fecha_emision: "Fecha de emisión",
  proveedor: "Proveedor",
  cuit_proveedor: "CUIT del proveedor",
  emisor: "Emisor",
  cuit_emisor: "CUIT del emisor",
  importe_total: "Importe total",
  importe: "Importe",
};

export function rotuloCampo(campo: string): string {
  return CAMPO[campo] ?? campo;
}

/** Acciones de auditoría (RF-21) en lenguaje del usuario, para el historial. */
export const ACCION: Record<string, string> = {
  tramite_creado: "Trámite creado",
  carga_confirmada: "Archivo cargado",
  carga_vencida: "Carga vencida",
  documento_incorporado: "Documento incorporado",
  tramite_vuelve_a_borrador: "El trámite vuelve a Borrador",
  clasificacion_confirmada: "Clasificación confirmada",
  clasificacion_corregida: "Clasificación corregida",
  campo_confirmado: "Dato confirmado",
  campo_corregido: "Dato corregido",
  campo_registrado: "Dato registrado manualmente",
  campo_declarado_ausente: "Dato declarado ausente",
  vinculo_creado: "Vínculo creado",
  vinculo_sugerido: "Vínculo sugerido por el sistema",
  vinculo_confirmado: "Vínculo confirmado",
  vinculo_rechazado: "Vínculo rechazado",
  vinculo_eliminado: "Vínculo eliminado",
  regla_ejecutada: "Control de consistencia ejecutado",
  tramite_enviado_a_validacion: "Enviado a validación",
  flujo_confirmado: "Flujo de revisión confirmado",
  tarea_asignada: "Tarea asignada",
  tarea_reasignada: "Tarea reasignada",
  tarea_sin_asignar: "Tarea sin asignar (señalada al administrador)",
  tarea_habilitada: "Tarea habilitada",
  tarea_aprobada: "Tarea aprobada",
  tarea_observada: "Tarea observada",
  tarea_descartada: "Tarea descartada",
  tramite_aprobado: "Trámite aprobado",
  tramite_observado: "Trámite observado",
  tramite_subsanado: "Observación subsanada",
  ciclo_desplazado: "Ciclo desplazado por cambio documental",
  procesamiento_reintentado: "Procesamiento reintentado",
  version_incorporada: "Versión nueva incorporada",
  sugerencia_version_rechazada: "Relación de versión rechazada",
  archivo_descartado: "Archivo descartado",
  firma_simulada_aplicada: "Firma digital simulada aplicada",
  tramite_cerrado: "Trámite cerrado",
  tramite_cancelado: "Trámite cancelado",
  ciclo_cancelado: "Ciclo cancelado con el trámite",
  tarea_anulada: "Tarea anulada",
  cuenta_suprimida: "Cuenta suprimida",
};

/** Criterio explicable de la versión nueva sugerida (RF-06, DO-2026-10-23-VER P1). */
export const CRITERIO_VERSION: Record<CriterioVersion, string> = {
  numero: "coincide el número documental",
  cuit: "coincide el CUIT",
};

/** Rótulo obligatorio de la firma (RF-23, P6): nunca se presenta como firma jurídica. */
export const LEYENDA_FIRMA = "Firma digital simulada — sin validez jurídica";

export function rotuloAccion(accion: string): string {
  return ACCION[accion] ?? accion.replaceAll("_", " ");
}

/** Prefijo con que el procesamiento simulado (WEB F9) rotula sus sugerencias. */
const PREFIJO_SIMULACION = "simulacion-local";

export function esSimulado(modelo: string | null | undefined): boolean {
  return !!modelo && modelo.startsWith(PREFIJO_SIMULACION);
}
