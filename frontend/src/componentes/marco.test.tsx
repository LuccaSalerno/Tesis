import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { simularApi } from "@/pruebas/entorno";

import { Marco } from "./marco";

const sesion = vi.hoisted(() => ({ roles: [] as string[] }));
vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({
    yo: { id: 1, roles: sesion.roles, autorizacion_cierre: false, nombre_visible: "Persona" },
    tiene: (rol: string) => sesion.roles.includes(rol),
    salir: () => undefined,
  }),
}));

function renderizar() {
  const enrutador = createMemoryRouter([{ path: "/", element: <Marco /> }]);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <RouterProvider router={enrutador} />
    </QueryClientProvider>,
  );
}

describe("navegación por rol (Tabla 3.II, §3.4.1)", () => {
  it("el administrador no ve trámites ni tareas, y el mantenimiento se avisa", async () => {
    sesion.roles = ["administrador_operativo"];
    simularApi({ "/salud": { estado: "mantenimiento", entorno: "demo", operacion: "draining" } });
    renderizar();
    expect(screen.getByRole("link", { name: "Administración" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Trámites" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Mis tareas" })).not.toBeInTheDocument();
    expect(await screen.findByText(/cerrando la sesión/)).toBeInTheDocument();
  });

  it("el revisor ve trámites y su bandeja, sin administración", () => {
    sesion.roles = ["revisor_aprobador"];
    simularApi({ "/salud": { estado: "ok", entorno: "demo", operacion: "active" } });
    renderizar();
    expect(screen.getByRole("link", { name: "Mis tareas" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Administración" })).not.toBeInTheDocument();
  });
});
