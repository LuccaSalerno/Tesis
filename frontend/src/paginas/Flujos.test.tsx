import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { Ciclo, Cuenta, Plantilla, TramiteDetalle } from "@/api/tipos";
import { simularApi } from "@/pruebas/entorno";

import { Administracion } from "./Administracion";
import { MarcoTramite } from "./tramite/MarcoTramite";
import { Revision } from "./tramite/Revision";

const sesion = vi.hoisted(() => ({
  yo: { id: 1, roles: ["administrador_operativo"], autorizacion_cierre: false, nombre_visible: "Administración" },
}));
vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({ yo: sesion.yo, tiene: (rol: string) => sesion.yo.roles.includes(rol) }),
}));

const ahora = "2026-11-09T12:00:00Z";
const directorio = [
  { id: 3, nombre_visible: "Martín Ríos", suprimida: false },
  { id: 4, nombre_visible: "Sofía Herrera", suprimida: false },
];

function mostrar(ruta: string, rutas: Parameters<typeof createMemoryRouter>[0]) {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={createMemoryRouter(rutas, { initialEntries: [ruta] })} />
    </QueryClientProvider>,
  );
}

// --- Administración: plantillas y autorización de cierre (RF-17, RF-25, DO-2026-10-22-TAR P1) ---

const cuentas: Cuenta[] = [
  { id: 1, identificador_externo: "sub-admin", estado: "habilitada", roles: ["administrador_operativo"], autorizacion_cierre: false, nombre_visible: "Administración" },
  { id: 3, identificador_externo: "sub-martin", estado: "habilitada", roles: ["revisor_aprobador"], autorizacion_cierre: false, nombre_visible: "Martín Ríos" },
  { id: 4, identificador_externo: "sub-sofia", estado: "habilitada", roles: ["revisor_aprobador"], autorizacion_cierre: true, nombre_visible: "Sofía Herrera" },
];

const plantilla: Plantilla = {
  id: 1,
  nombre: "Revisión de contratos",
  alcance: "contrato",
  version: 1,
  activa: true,
  creada_en: ahora,
  creada_por_id: 1,
  desactivada_en: null,
  pasos: [
    { orden: 1, nombre: "Revisión legal", revisor_por_defecto_id: 3, rol_requerido: "revisor_aprobador" },
    { orden: 2, nombre: "Aprobación final", revisor_por_defecto_id: 4, rol_requerido: "revisor_aprobador" },
  ],
};

function administracion(extra: Record<string, unknown> = {}) {
  const llamadas = simularApi({
    "/administracion/estado-general": { tramites_por_estado: {}, tareas_por_estado: {}, tareas_sin_asignar: 0, tareas_bloqueadas: [], trabajos_por_estado: {}, tramites: [] },
    "/plantillas-flujo": [plantilla],
    "/tareas/sin-asignar": [],
    "/usuarios": cuentas,
    "/usuarios/directorio": directorio,
    ...extra,
  });
  mostrar("/administracion", [{ path: "/administracion", element: <Administracion /> }]);
  return llamadas;
}

const anterior: Plantilla = {
  ...plantilla,
  id: 0,
  version: 1,
  activa: false,
  pasos: [{ orden: 1, nombre: "Aprobación", revisor_por_defecto_id: 4, rol_requerido: "revisor_aprobador" }],
};
const vigente: Plantilla = { ...plantilla, version: 2 };

describe("flujos de revisión en administración", () => {
  it("muestra el flujo de cada tipo de trámite con quién resuelve cada paso", async () => {
    administracion({ "/plantillas-flujo": [vigente, anterior] });
    const contratos = (await screen.findByRole("heading", { name: /Trámites con contrato/ })).closest("section")!;
    expect(within(contratos).getByText("Revisión de contratos · v2")).toBeInTheDocument();
    expect(await within(contratos).findByText("Martín Ríos")).toBeInTheDocument();
    expect(within(contratos).getByText("Versiones anteriores (1)")).toBeInTheDocument();
    const demas = screen.getByRole("heading", { name: "Demás trámites" }).closest("section")!;
    expect(within(demas).getByText("Sin flujo configurado.")).toBeInTheDocument();
  });

  it("edita el flujo vigente como versión nueva, con los pasos reordenados", async () => {
    const llamadas = administracion({
      "/plantillas-flujo": [vigente],
      "POST /plantillas-flujo": () => [201, { ...vigente, id: 3, version: 3 }],
    });
    const usuario = userEvent.setup();
    const contratos = (await screen.findByRole("heading", { name: /Trámites con contrato/ })).closest("section")!;
    await usuario.click(within(contratos).getByRole("button", { name: "Editar" }));
    expect(within(contratos).getByLabelText("Nombre del flujo")).toHaveValue("Revisión de contratos");
    // Solo quien tiene autorización de cierre puede resolver el último paso.
    expect(within(within(contratos).getByLabelText("Quién resuelve el paso 2")).queryByRole("option", { name: "Martín Ríos" })).toBeNull();
    await usuario.click(within(contratos).getByRole("button", { name: "Bajar el paso 1" }));
    // Martín pasó a ser el último paso: deja de ser elegible y hay que elegir de nuevo.
    expect(within(contratos).getByLabelText("Quién resuelve el paso 2")).toHaveValue("");
    await usuario.selectOptions(within(contratos).getByLabelText("Quién resuelve el paso 1"), "3");
    await usuario.selectOptions(within(contratos).getByLabelText("Quién resuelve el paso 2"), "4");
    await usuario.click(within(contratos).getByRole("button", { name: "Guardar como versión 3" }));
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({
      nombre: "Revisión de contratos",
      alcance: "contrato",
      pasos: [
        { nombre: "Aprobación final", revisor_por_defecto_id: 3 },
        { nombre: "Revisión legal", revisor_por_defecto_id: 4 },
      ],
    });
  });

  it("vuelve a usar una versión anterior como versión nueva", async () => {
    const llamadas = administracion({
      "/plantillas-flujo": [vigente, anterior],
      "POST /plantillas-flujo": () => [201, { ...anterior, id: 3, version: 3, activa: true }],
    });
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByText("Versiones anteriores (1)"));
    await usuario.click(screen.getByRole("button", { name: "Volver a usar como v3" }));
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({
      nombre: "Revisión de contratos",
      alcance: "contrato",
      pasos: [{ nombre: "Aprobación", revisor_por_defecto_id: 4 }],
    });
  });

  it("otorga la autorización de cierre desde la lista de cuentas", async () => {
    const llamadas = administracion({
      "PUT /usuarios/3/autorizacion-cierre": () => [200, { ...cuentas[1], autorizacion_cierre: true }],
    });
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: "Otorgar la autorización de cierre a Martín Ríos" }));
    expect(llamadas.find((l) => l.metodo === "PUT")).toMatchObject({ ruta: "/usuarios/3/autorizacion-cierre", cuerpo: { otorgada: true } });
    expect(screen.getByRole("button", { name: "Retirar la autorización de cierre a Sofía Herrera" })).toBeInTheDocument();
  });
});

// --- Trámite: por qué se sugiere el flujo y recorrido del ciclo (RF-17, RF-18) ---

function tramite(estado: TramiteDetalle["estado"], tipo: TramiteDetalle["documentos"][number]["tipo"]): TramiteDetalle {
  return {
    id: 3,
    titulo: "Mantenimiento integral de planta",
    descripcion: null,
    estado,
    responsable_id: 2,
    creado_en: ahora,
    actualizado_en: ahora,
    documentos: [{ id: 5, nombre: "Contrato de mantenimiento", tipo, version_vigente: { id: 21, numero: 1, archivo_id: 8 } }],
  };
}

function revision(estado: TramiteDetalle["estado"], tipo: TramiteDetalle["documentos"][number]["tipo"], extra: Record<string, unknown>) {
  sesion.yo = { id: 2, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" };
  simularApi({
    "/tramites/3": tramite(estado, tipo),
    "/tramites/3/controles": { vigentes: [], historial: [] },
    "/tramites/3/ciclos": [],
    "/usuarios/directorio": directorio,
    ...extra,
  });
  mostrar("/tramites/3/revision", [
    { path: "/tramites/:tramiteId", element: <MarcoTramite />, children: [{ path: "revision", element: <Revision /> }] },
  ]);
}

describe("flujo sugerido", () => {
  it("muestra los pasos y quién los resuelve, listo para confirmar", async () => {
    revision("pendiente_validacion", "contrato", {
      "/tramites/3/flujo-sugerido": {
        alcance: "contrato",
        plantilla_id: 1,
        plantilla_nombre: "Revisión de contratos",
        version_plantilla: 1,
        documentos_sin_validar: [],
        pasos: [
          { orden: 1, nombre: "Revisión legal", revisor_por_defecto_id: 3, asignada_a_id: 3 },
          { orden: 2, nombre: "Aprobación final", revisor_por_defecto_id: 4, asignada_a_id: 4 },
        ],
      },
    });
    expect(await screen.findByText("Revisión de contratos · v1")).toBeInTheDocument();
    expect(await screen.findByText("Sofía Herrera")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Confirmar el flujo/ })).toBeEnabled();
  });

  it("no sugiere un flujo hasta que los documentos estén validados", async () => {
    revision("pendiente_validacion", null, {
      "/tramites/3/flujo-sugerido": {
        alcance: "general",
        plantilla_id: null,
        plantilla_nombre: null,
        version_plantilla: null,
        documentos_sin_validar: [5],
        pasos: [],
      },
    });
    expect(await screen.findByText("Validá los documentos para ver el flujo")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Contrato de mantenimiento" })).toBeInTheDocument();
    expect(screen.queryByText(/No hay un flujo configurado/)).toBeNull();
    expect(screen.queryByRole("button", { name: /Confirmar el flujo/ })).toBeNull();
  });
});

describe("recorrido del ciclo", () => {
  it("muestra los pasos en orden, con su estado y la evidencia", async () => {
    const tarea = (id: number, orden: number, nombre: string, estado: Ciclo["tareas"][number]["estado"], asignada: number) => ({
      id, ciclo_revision_id: 2, orden, nombre, rol_requerido: "revisor_aprobador" as const, estado, asignada_a_id: asignada, creada_en: ahora, actualizada_en: ahora, decision_id: estado === "observada" ? 7 : null,
    });
    const ciclo: Ciclo = {
      id: 2, numero: 1, estado: "observado", tramite_id: 3, plantilla_flujo_id: 1, confirmado_por_id: 2, confirmado_en: ahora, concluido_en: ahora,
      versiones: [{ documento_id: 5, documento_nombre: "Contrato de mantenimiento", version_id: 21, version_numero: 1 }],
      tareas: [tarea(12, 2, "Aprobación final", "descartada", 4), tarea(11, 1, "Revisión legal", "observada", 3)],
    };
    revision("observado", "contrato", { "/tramites/3/ciclos": [ciclo] });
    const pasos = await screen.findAllByText(/^Paso \d$/);
    expect(pasos.map((p) => p.nextSibling?.textContent)).toEqual(["Revisión legal", "Aprobación final"]);
    expect(screen.getByRole("link", { name: /Evidencia de la decisión/ })).toHaveAttribute("href", "/decisiones/7/evidencia");
  });
});
