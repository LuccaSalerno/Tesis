import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { EstadoGeneral, TramiteDetalle } from "@/api/tipos";
import { simularApi } from "@/pruebas/entorno";

import { Administracion } from "./Administracion";
import { MarcoTramite } from "./tramite/MarcoTramite";
import { Resumen } from "./tramite/Resumen";

const sesion = vi.hoisted(() => ({
  yo: { id: 4, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" },
}));
vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({ yo: sesion.yo, tiene: (rol: string) => sesion.yo.roles.includes(rol) }),
}));

const ahora = "2026-10-23T12:00:00Z";
const MOTIVO = "El proveedor desistió de la contratación";

function tramite(estado: TramiteDetalle["estado"], motivo: string | null = null): TramiteDetalle {
  return {
    id: 3,
    titulo: "Servicio de mantenimiento",
    descripcion: null,
    estado,
    motivo_cancelacion: motivo,
    responsable_id: 4,
    creado_en: ahora,
    actualizado_en: ahora,
    documentos: [],
  };
}

function mostrar(elemento: "resumen" | "administracion") {
  const rutas =
    elemento === "resumen"
      ? [{ path: "/tramites/:tramiteId", element: <MarcoTramite />, children: [{ path: "resumen", element: <Resumen /> }] }]
      : [{ path: "/administracion", element: <Administracion /> }];
  const enrutador = createMemoryRouter(rutas, {
    initialEntries: [elemento === "resumen" ? "/tramites/3/resumen" : "/administracion"],
  });
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={enrutador} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  sesion.yo = { id: 4, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" };
});

describe("cancelación del trámite (RF-26, RN-14)", () => {
  it("exige el motivo y lo envía", async () => {
    const llamadas = simularApi({
      "/tramites/3": tramite("borrador"),
      "/tramites/3/ciclos": [],
      "/tramites/3/controles": { vigentes: [], historial: [] },
      "/usuarios/directorio": [],
      "POST /tramites/3/cancelacion": () => [200, tramite("cancelado", MOTIVO)],
    });
    mostrar("resumen");
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: "Cancelar trámite" }));
    const dialogo = await screen.findByRole("dialog");
    const confirmar = within(dialogo).getByRole("button", { name: "Cancelar definitivamente" });
    expect(confirmar).toBeDisabled();
    await usuario.type(within(dialogo).getByLabelText("Motivo"), MOTIVO);
    await usuario.click(confirmar);
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({ motivo: MOTIVO });
  });

  it("muestra el motivo y no ofrece cancelar un trámite cancelado o aprobado", async () => {
    simularApi({
      "/tramites/3": tramite("cancelado", MOTIVO),
      "/tramites/3/ciclos": [],
      "/tramites/3/controles": { vigentes: [], historial: [] },
      "/usuarios/directorio": [],
    });
    mostrar("resumen");
    expect(await screen.findByText(MOTIVO)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancelar trámite" })).not.toBeInTheDocument();
  });
});

const estadoGeneral: EstadoGeneral = {
  tramites_por_estado: { borrador: 2, cerrado: 1 },
  tareas_por_estado: { pendiente: 1 },
  tareas_sin_asignar: 0,
  tareas_bloqueadas: [{ tarea_id: 11, tramite_id: 3, asignada_a_id: 6 }],
  trabajos_por_estado: { fallido: 1 },
  tramites: [
    { id: 3, estado: "pendiente_aprobacion", responsable_id: 4, creado_en: ahora, actualizado_en: ahora, documentos: 3, tareas_abiertas: 1, tareas_sin_asignar: 0 },
  ],
};

const cuentas = [
  { id: 1, identificador_externo: "sub-admin", estado: "habilitada", roles: ["administrador_operativo"], autorizacion_cierre: false, nombre_visible: "Administración" },
  { id: 6, identificador_externo: "sub-revisor", estado: "deshabilitada", roles: ["revisor_aprobador"], autorizacion_cierre: false, nombre_visible: "Martín Ríos" },
  { id: 7, identificador_externo: null, estado: "suprimida", roles: [], autorizacion_cierre: false, nombre_visible: null },
];

describe("administración (RF-24, RF-25)", () => {
  it("muestra el estado general sin títulos y suprime con confirmación", async () => {
    sesion.yo = { id: 1, roles: ["administrador_operativo"], autorizacion_cierre: false, nombre_visible: "Administración" };
    const llamadas = simularApi({
      "/administracion/estado-general": estadoGeneral,
      "/plantillas-flujo": [],
      "/tareas/sin-asignar": [],
      "/usuarios": cuentas,
      "/usuarios/directorio": [],
      "POST /usuarios/6/supresion": () => [200, { ...cuentas[1], estado: "suprimida", identificador_externo: null, nombre_visible: null, roles: [] }],
    });
    mostrar("administracion");
    expect(await screen.findByText("TR-3")).toBeInTheDocument();
    expect(screen.getByText(/1 tarea\(s\) asignadas a cuentas no habilitadas/)).toBeInTheDocument();
    expect(screen.queryByText("Servicio de mantenimiento")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Suprimir la cuenta 1" })).not.toBeInTheDocument(); // la propia
    expect(screen.queryByRole("button", { name: "Suprimir la cuenta 7" })).not.toBeInTheDocument(); // ya suprimida
    expect(screen.getByText("Cuenta suprimida")).toBeInTheDocument();
    const usuario = userEvent.setup();
    await usuario.click(screen.getByRole("button", { name: "Suprimir la cuenta 6" }));
    await usuario.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Suprimir definitivamente" }));
    expect(llamadas.filter((l) => l.metodo === "POST").map((l) => l.ruta)).toEqual(["/usuarios/6/supresion"]);
  });
});
