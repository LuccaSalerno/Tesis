import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";

import { crearClienteConsultas, rutas } from "@/App";
import { simularApi } from "@/pruebas/entorno";

import { ProveedorSesion } from "./sesion";

const ahora = "2026-11-10T19:00:00Z";
const token = (sub: string) =>
  `e30.${btoa(JSON.stringify({ sub, exp: Math.floor(Date.now() / 1000) + 3600 })).replace(/=+$/, "")}.firma`;
const persona = (id: number, nombre: string) => ({ id, nombre_visible: nombre, roles: ["revisor_aprobador"], autorizacion_cierre: false });
const tarea = (id: number, nombre: string) => ({
  id,
  nombre,
  estado: "pendiente",
  actualizada_en: ahora,
  ciclo: { id: 1, numero: 1 },
  tramite: { id: 2, titulo: "Mantenimiento integral de planta", estado: "pendiente_aprobacion" },
});

describe("sesión", () => {
  it("al cerrar sesión no muestra datos de la persona anterior y el ingreso empieza por Inicio", async () => {
    let actual = "martin";
    simularApi({
      "/salud": { estado: "ok", entorno: "local", operacion: "active" },
      "/usuarios/yo": () => [200, actual === "martin" ? persona(2, "Martín Ríos") : persona(3, "Sofía Herrera")],
      "/tareas": () => [200, actual === "martin" ? [tarea(10, "Revisión legal")] : [tarea(11, "Aprobación final")]],
    });
    const enrutador = createMemoryRouter(rutas, { initialEntries: ["/tareas"] });
    render(
      <QueryClientProvider client={crearClienteConsultas()}>
        <ProveedorSesion>
          <RouterProvider router={enrutador} />
        </ProveedorSesion>
      </QueryClientProvider>,
    );
    const usuario = userEvent.setup();
    const ingresar = async (sub: string) => {
      await usuario.type(await screen.findByLabelText(/Token de acceso/), token(sub));
      await usuario.click(screen.getByRole("button", { name: "Ingresar" }));
    };

    // Sin sesión, el ingreso vuelve a la pantalla pedida.
    await ingresar("martin");
    expect(await screen.findByRole("link", { name: "Revisión legal" })).toBeInTheDocument();

    await usuario.click(screen.getByRole("button", { name: /Cerrar sesión/ }));
    actual = "sofia";
    await ingresar("sofia");
    expect(await screen.findByRole("heading", { name: /Hola/ })).toBeInTheDocument();
    expect(enrutador.state.location.pathname).toBe("/");

    await usuario.click(screen.getByRole("link", { name: "Mis tareas" }));
    expect(await screen.findByRole("link", { name: "Aprobación final" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Revisión legal" })).not.toBeInTheDocument();
  });
});
