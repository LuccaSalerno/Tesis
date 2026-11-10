/**
 * Consultas y mutaciones de la API con TanStack Query. Cada clave identifica un recurso del
 * backend; las mutaciones invalidan lo que cambian para que la pantalla refleje el estado
 * real (nunca se asume el resultado de una operación).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, exigir } from "./cliente";
import type { components } from "./esquema";

type S = components["schemas"];

export const claves = {
  salud: ["salud"] as const,
  tramites: ["tramites"] as const,
  tramite: (t: number) => ["tramite", t] as const,
  archivos: (t: number) => ["tramite", t, "archivos"] as const,
  sugerencias: (t: number, a: number) => ["tramite", t, "sugerencias", a] as const,
  validaciones: (t: number, d: number) => ["tramite", t, "validaciones", d] as const,
  vinculos: (t: number) => ["tramite", t, "vinculos"] as const,
  controles: (t: number) => ["tramite", t, "controles"] as const,
  ciclos: (t: number) => ["tramite", t, "ciclos"] as const,
  flujo: (t: number) => ["tramite", t, "flujo"] as const,
  lineaTiempo: (t: number) => ["tramite", t, "linea-tiempo"] as const,
  firma: (t: number) => ["tramite", t, "firma"] as const,
  estadoGeneral: ["estado-general"] as const,
  consultas: (t: number) => ["tramite", t, "consultas"] as const,
  tareas: ["tareas"] as const,
  tarea: (id: number) => ["tarea", id] as const,
  evidencia: (id: number) => ["evidencia", id] as const,
  sinAsignar: ["tareas", "sin-asignar"] as const,
  plantillas: ["plantillas"] as const,
  cuentas: ["cuentas"] as const,
};

// --- Lectura -----------------------------------------------------------------------------

export function useSalud() {
  return useQuery({
    queryKey: claves.salud,
    queryFn: () => exigir(api.GET("/salud")),
    refetchInterval: 60_000,
  });
}

export function useTramites() {
  return useQuery({ queryKey: claves.tramites, queryFn: () => exigir(api.GET("/tramites")) });
}

const ruta = (t: number) => ({ params: { path: { tramite_id: t } } });

export function useTramite(t: number) {
  return useQuery({
    queryKey: claves.tramite(t),
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}", ruta(t))),
  });
}

/** Estado técnico de las cargas: se consulta periódicamente mientras haya trabajos abiertos. */
export function useArchivos(t: number) {
  return useQuery({
    queryKey: claves.archivos(t),
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}/archivos", ruta(t))),
    refetchInterval: (consulta) =>
      consulta.state.data?.some(
        (a) => a.trabajo && ["pendiente", "en_espera", "en_ejecucion"].includes(a.trabajo.estado),
      )
        ? 4000
        : false,
  });
}

export function useSugerencias(t: number, archivo: number | undefined) {
  return useQuery({
    queryKey: claves.sugerencias(t, archivo ?? 0),
    enabled: archivo !== undefined,
    queryFn: () =>
      exigir(
        api.GET("/tramites/{tramite_id}/archivos/{archivo_id}/sugerencias", {
          params: { path: { tramite_id: t, archivo_id: archivo ?? 0 } },
        }),
      ),
  });
}

export function useValidaciones(t: number, documento: number) {
  return useQuery({
    queryKey: claves.validaciones(t, documento),
    queryFn: () =>
      exigir(
        api.GET("/tramites/{tramite_id}/documentos/{documento_id}/validaciones", {
          params: { path: { tramite_id: t, documento_id: documento } },
        }),
      ),
  });
}

export function useVinculos(t: number) {
  return useQuery({
    queryKey: claves.vinculos(t),
    queryFn: () =>
      exigir(
        api.GET("/tramites/{tramite_id}/vinculos", {
          params: { path: { tramite_id: t }, query: { historial: true } },
        }),
      ),
  });
}

export function useControles(t: number) {
  return useQuery({
    queryKey: claves.controles(t),
    queryFn: () =>
      exigir(
        api.GET("/tramites/{tramite_id}/controles", {
          params: { path: { tramite_id: t }, query: { historial: true } },
        }),
      ),
  });
}

export function useCiclos(t: number) {
  return useQuery({
    queryKey: claves.ciclos(t),
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}/ciclos", ruta(t))),
  });
}

export function useFlujoSugerido(t: number) {
  return useQuery({
    queryKey: claves.flujo(t),
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}/flujo-sugerido", ruta(t))),
  });
}

export function useLineaTiempo(t: number) {
  return useQuery({
    queryKey: claves.lineaTiempo(t),
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}/linea-tiempo", ruta(t))),
  });
}

export function useConsultas(t: number) {
  return useQuery({
    queryKey: claves.consultas(t),
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}/consultas", ruta(t))),
  });
}

export function useTareas() {
  // Las tareas llegan por acciones de otras personas: la bandeja se vuelve a pedir al abrirla.
  return useQuery({ queryKey: claves.tareas, staleTime: 0, queryFn: () => exigir(api.GET("/tareas")) });
}

export function useTarea(id: number) {
  return useQuery({
    queryKey: claves.tarea(id),
    queryFn: () => exigir(api.GET("/tareas/{tarea_id}", { params: { path: { tarea_id: id } } })),
  });
}

export function useEvidencia(id: number) {
  return useQuery({
    queryKey: claves.evidencia(id),
    queryFn: () =>
      exigir(
        api.GET("/decisiones/{decision_id}/evidencia", { params: { path: { decision_id: id } } }),
      ),
  });
}

export function useTareasSinAsignar(habilitado: boolean) {
  return useQuery({
    queryKey: claves.sinAsignar,
    enabled: habilitado,
    queryFn: () => exigir(api.GET("/tareas/sin-asignar")),
  });
}

export function usePlantillas() {
  return useQuery({
    queryKey: claves.plantillas,
    queryFn: () => exigir(api.GET("/plantillas-flujo")),
  });
}

export function useCuentas() {
  return useQuery({
    queryKey: claves.cuentas,
    queryFn: () => exigir(api.GET("/usuarios")),
  });
}

/** Firma simulada del trámite cerrado (RF-23, V11); sin firma, la API responde 404. */
export function useFirma(t: number, habilitado: boolean) {
  return useQuery({
    queryKey: claves.firma(t),
    enabled: habilitado,
    queryFn: () => exigir(api.GET("/tramites/{tramite_id}/firma", ruta(t))),
  });
}

/** RF-24: estado general para el administrador, solo metadatos y conteos. */
export function useEstadoGeneral() {
  return useQuery({
    queryKey: claves.estadoGeneral,
    queryFn: () => exigir(api.GET("/administracion/estado-general")),
  });
}

/** URL de lectura breve del original de una versión (WEB F4): se pide al abrir el visor. */
export function useArchivoVersion(t: number, version: number | undefined) {
  return useQuery({
    queryKey: ["tramite", t, "archivo-version", version],
    enabled: version !== undefined,
    staleTime: 60_000, // la URL vence a los 5 minutos
    queryFn: () =>
      exigir(
        api.GET("/tramites/{tramite_id}/versiones/{version_id}/archivo", {
          params: { path: { tramite_id: t, version_id: version ?? 0 } },
        }),
      ),
  });
}

// --- Mutaciones --------------------------------------------------------------------------

function useInvalidar() {
  const cliente = useQueryClient();
  return (...prefijos: (readonly unknown[])[]) =>
    Promise.all(prefijos.map((queryKey) => cliente.invalidateQueries({ queryKey })));
}

export function useCrearTramite() {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (cuerpo: S["NuevoTramite"]) => exigir(api.POST("/tramites", { body: cuerpo })),
    onSuccess: () => invalidar(claves.tramites),
  });
}

export function useRegistrarValidacion(t: number, documento: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (cuerpo: S["NuevaValidacion"]) =>
      exigir(
        api.POST("/tramites/{tramite_id}/documentos/{documento_id}/validaciones", {
          params: { path: { tramite_id: t, documento_id: documento } },
          body: cuerpo,
        }),
      ),
    onSuccess: () => invalidar(claves.tramite(t)),
  });
}

export function useIncorporar(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: ({ archivo, nombre }: { archivo: number; nombre: string }) =>
      exigir(
        api.POST("/tramites/{tramite_id}/archivos/{archivo_id}/incorporacion", {
          params: { path: { tramite_id: t, archivo_id: archivo } },
          body: { nombre },
        }),
      ),
    onSuccess: () => invalidar(claves.tramite(t), claves.tramites),
  });
}

/** RF-07: confirma la relación de versión sugerida (RF-06); RN-12 lo aplica la API. */
export function useIncorporarVersion(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (archivo: number) =>
      exigir(
        api.POST("/tramites/{tramite_id}/archivos/{archivo_id}/version", {
          params: { path: { tramite_id: t, archivo_id: archivo } },
        }),
      ),
    onSuccess: () => invalidar(claves.tramite(t), claves.tramites, claves.tareas),
  });
}

/** RF-07: descarta el archivo pendiente sin crear documento ni versión. */
export function useDescartar(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (archivo: number) =>
      exigir(
        api.POST("/tramites/{tramite_id}/archivos/{archivo_id}/descarte", {
          params: { path: { tramite_id: t, archivo_id: archivo } },
        }),
      ),
    onSuccess: () => invalidar(claves.archivos(t), claves.lineaTiempo(t)),
  });
}

/** RF-26, RN-14: cancelación con motivo por el responsable. */
export function useCancelar(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (motivo: string) =>
      exigir(api.POST("/tramites/{tramite_id}/cancelacion", { ...ruta(t), body: { motivo } })),
    onSuccess: () => invalidar(claves.tramite(t), claves.tramites, claves.tareas),
  });
}

/** RF-25: supresión irreversible de una cuenta por el administrador. */
export function useSuprimir() {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (usuario: number) =>
      exigir(api.POST("/usuarios/{usuario_id}/supresion", { params: { path: { usuario_id: usuario } } })),
    onSuccess: () => invalidar(claves.cuentas, claves.estadoGeneral, ["directorio"]),
  });
}

/** RF-23: firma simulada de una versión del ciclo aprobado; el trámite queda Cerrado. */
export function useFirmar(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (version: number) =>
      exigir(api.POST("/tramites/{tramite_id}/firma", { ...ruta(t), body: { version_id: version } })),
    onSuccess: () => invalidar(claves.tramite(t), claves.tramites, ["evidencia"]),
  });
}

/** Intento nuevo tras una falla técnica, por decisión del responsable (RNF-06, RC-P08.4). */
export function useReintentar(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (archivo: number) =>
      exigir(
        api.POST("/tramites/{tramite_id}/archivos/{archivo_id}/reintento", {
          params: { path: { tramite_id: t, archivo_id: archivo } },
        }),
      ),
    onSuccess: () => invalidar(claves.archivos(t)),
  });
}

export function useTransicion(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (accion: "envio-a-validacion" | "subsanacion") =>
      accion === "envio-a-validacion"
        ? exigir(api.POST("/tramites/{tramite_id}/envio-a-validacion", ruta(t)))
        : exigir(api.POST("/tramites/{tramite_id}/subsanacion", ruta(t))),
    onSuccess: () => invalidar(claves.tramite(t), claves.tramites),
  });
}

export function useConfirmarFlujo(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (cuerpo: S["ConfirmacionFlujo"]) =>
      exigir(api.POST("/tramites/{tramite_id}/ciclos", { ...ruta(t), body: cuerpo })),
    onSuccess: () => invalidar(claves.tramite(t), claves.tramites, claves.tareas),
  });
}

export function useDecidir(tarea: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (cuerpo: S["NuevaDecision"]) =>
      exigir(
        api.POST("/tareas/{tarea_id}/decision", {
          params: { path: { tarea_id: tarea } },
          body: cuerpo,
        }),
      ),
    onSuccess: () => invalidar(["tarea"], claves.tareas, ["tramite"]),
  });
}

export function useResolverVinculo(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: ({ vinculo, accion }: { vinculo: number; accion: "confirmacion" | "rechazo" | "eliminacion" }) => {
      const opciones = { params: { path: { tramite_id: t, vinculo_id: vinculo } } };
      if (accion === "eliminacion")
        return exigir(api.DELETE("/tramites/{tramite_id}/vinculos/{vinculo_id}", opciones));
      if (accion === "confirmacion")
        return exigir(api.POST("/tramites/{tramite_id}/vinculos/{vinculo_id}/confirmacion", opciones));
      return exigir(api.POST("/tramites/{tramite_id}/vinculos/{vinculo_id}/rechazo", opciones));
    },
    onSuccess: () => invalidar(claves.tramite(t)),
  });
}

export function useCrearVinculo(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (cuerpo: S["NuevoVinculo"]) =>
      exigir(api.POST("/tramites/{tramite_id}/vinculos", { ...ruta(t), body: cuerpo })),
    onSuccess: () => invalidar(claves.tramite(t)),
  });
}

export function useConsultar(t: number) {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (pregunta: string) =>
      exigir(api.POST("/tramites/{tramite_id}/consultas", { ...ruta(t), body: { pregunta } })),
    onSuccess: () => invalidar(claves.consultas(t)),
  });
}

export function useAsignar() {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: ({ tarea, usuario }: { tarea: number; usuario: number }) =>
      exigir(
        api.PUT("/tareas/{tarea_id}/asignacion", {
          params: { path: { tarea_id: tarea } },
          body: { usuario_id: usuario },
        }),
      ),
    onSuccess: () => invalidar(claves.sinAsignar, claves.tareas, ["tarea"]),
  });
}

export function useCrearPlantilla() {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (cuerpo: S["NuevaPlantilla"]) => exigir(api.POST("/plantillas-flujo", { body: cuerpo })),
    onSuccess: () => invalidar(claves.plantillas),
  });
}

/** RF-25: la autorización de cierre es un permiso adicional que otorga o retira el administrador. */
export function useCambiarCierre() {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: ({ usuario, otorgada }: { usuario: number; otorgada: boolean }) =>
      exigir(
        api.PUT("/usuarios/{usuario_id}/autorizacion-cierre", {
          params: { path: { usuario_id: usuario } },
          body: { otorgada },
        }),
      ),
    onSuccess: () => invalidar(claves.cuentas),
  });
}

export function useCambiarNombre() {
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: ({ usuario, nombre }: { usuario: number; nombre: string | null }) =>
      exigir(
        api.PUT("/usuarios/{usuario_id}/nombre", {
          params: { path: { usuario_id: usuario } },
          body: { nombre_visible: nombre },
        }),
      ),
    onSuccess: () => invalidar(claves.cuentas, ["directorio"]),
  });
}
