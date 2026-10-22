/** Datos de prueba de componentes con la forma del contrato (no son evidencia). */
import type { Evidencia, TareaDetalle } from "@/api/tipos";

const ahora = "2026-10-22T19:00:00Z";

export const tareaPendiente: TareaDetalle = {
  id: 11,
  ciclo_revision_id: 3,
  orden: 2,
  nombre: "Aprobación final",
  rol_requerido: "revisor_aprobador",
  estado: "pendiente",
  asignada_a_id: 5,
  creada_en: ahora,
  actualizada_en: ahora,
  decision_id: null,
  tramite: { id: 2, titulo: "Servicio de mantenimiento", estado: "pendiente_aprobacion" },
  ciclo: { id: 3, numero: 1, estado: "en_curso" },
  versiones: [
    { documento_id: 1, documento_nombre: "Contrato", version_id: 21, version_numero: 1 },
    { documento_id: 2, documento_nombre: "Orden de compra", version_id: 22, version_numero: 1 },
  ],
  controles: [
    {
      codigo_regla: "R3-VIGENCIA-OC-CONTRATO",
      version_regla: "1",
      descripcion: "Fecha de la orden dentro de la vigencia",
      vinculo_id: 9,
      resultado: "advertencia",
      explicacion: "La fecha de la orden (2027-03-15) está fuera de la vigencia.",
      ejecucion: null,
    },
  ],
  controles_pendientes: false,
  decision: null,
  asignaciones: [],
};

export const evidencia: Evidencia = {
  decision: { id: 7, tarea_id: 11, actor_id: 5, tipo: "observacion", motivo: "Corregir la fecha de la orden", decidida_en: ahora, controles_considerados: [31, 32] },
  tarea: { ...tareaPendiente, estado: "observada", decision_id: 7 },
  ciclo: { id: 3, numero: 1, estado: "observado" },
  tramite: { id: 2, titulo: "Servicio de mantenimiento", estado: "observado" },
  tareas_del_ciclo: [{ ...tareaPendiente, estado: "observada", decision_id: 7 }],
  versiones: tareaPendiente.versiones,
  validaciones: [
    { validacion_id: 101, documento_id: 1, version_id: 21, clase: "campo", campo: "vigencia_hasta", valor_sugerido: "2027-02-28", valor_sugerido_id: 50, localizador_sugerido: { pagina: 6, seccion: null, fragmento: "Fin de vigencia" }, valor_validado: "2027-02-28", tipo: "confirmacion", motivo_ausencia: null, validador_id: 4, validado_en: ahora, reemplaza_a_id: null, localizador_validado: null },
    { validacion_id: 102, documento_id: 2, version_id: 22, clase: "campo", campo: "fecha", valor_sugerido: null, valor_sugerido_id: null, localizador_sugerido: null, valor_validado: "2027-03-15", tipo: "sin_sugerencia", motivo_ausencia: null, validador_id: 4, validado_en: ahora, reemplaza_a_id: null, localizador_validado: null },
    { validacion_id: 103, documento_id: 2, version_id: 22, clase: "campo", campo: "moneda", valor_sugerido: null, valor_sugerido_id: null, localizador_sugerido: null, valor_validado: "ARS", tipo: "sin_sugerencia", motivo_ausencia: null, validador_id: 4, validado_en: ahora, reemplaza_a_id: null, localizador_validado: null },
  ],
  controles: [
    {
      id: 31, vinculo_id: 9, codigo_regla: "R3-VIGENCIA-OC-CONTRATO", version_regla: "1", descripcion: "Fecha de la orden dentro de la vigencia", resultado: "advertencia",
      explicacion: "Fuera de la vigencia.", disparador: "vinculo", ejecutada_en: ahora,
      versiones: [{ papel: "contrato", documento_id: 1, documento_nombre: "Contrato", version_id: 21, version_numero: 1 }, { papel: "orden_compra", documento_id: 2, documento_nombre: "Orden de compra", version_id: 22, version_numero: 1 }],
      valores: [{ papel: "contrato", campo: "vigencia_hasta", valor_validado: "2027-02-28", tipo: "confirmacion", validacion_id: 101, version_id: 21 }, { papel: "orden_compra", campo: "fecha", valor_validado: "2027-03-15", tipo: "sin_sugerencia", validacion_id: 102, version_id: 22 }],
    },
  ],
  eventos: [{ id: 900, ocurrido_en: ahora, actor_tipo: "usuario", actor_id: 5, accion: "tarea_observada", entidad_tipo: "decision", entidad_id: 7, resultado: "exito", version_id: null }],
};
