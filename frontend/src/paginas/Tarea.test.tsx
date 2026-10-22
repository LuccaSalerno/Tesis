import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { tareaPendiente } from "@/pruebas/datos";
import { renderizarEn, simularApi } from "@/pruebas/entorno";

import { Tarea } from "./Tarea";

vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({ yo: { id: 5, roles: ["revisor_aprobador"], autorizacion_cierre: true, nombre_visible: "Sofía" }, tiene: () => true }),
}));

describe("decisión del revisor (RF-20, RN-08, Fig. 3.8)", () => {
  it("presenta la advertencia como apoyo y exige motivo para observar", async () => {
    const llamadas = simularApi({
      "/tareas/11": tareaPendiente,
      "/usuarios/directorio": [{ id: 5, nombre_visible: "Sofía Herrera" }],
      "POST /tareas/11/decision": (cuerpo: unknown) => [201, { id: 7, tarea_id: 11, actor_id: 5, ...(cuerpo as object), decidida_en: "2026-10-22T19:00:00Z", controles_considerados: [] }],
    });
    const usuario = userEvent.setup();
    renderizarEn("/tareas/11", "/tareas/:tareaId", <Tarea />);
    expect(await screen.findByText("1 advertencia de consistencia")).toBeInTheDocument();
    expect(screen.getByText(/no aprueba ni observa por sí sola/)).toBeInTheDocument();

    await usuario.click(screen.getByRole("button", { name: /Observar/ }));
    const dialogo = await screen.findByRole("dialog");
    const registrar = within(dialogo).getByRole("button", { name: "Registrar observación" });
    expect(registrar).toBeDisabled();
    await usuario.type(within(dialogo).getByLabelText("Motivo de la observación"), "Corregir la fecha");
    expect(registrar).toBeEnabled();
    await usuario.click(registrar);
    const decision = llamadas.find((l) => l.metodo === "POST");
    expect(decision?.cuerpo).toEqual({ tipo: "observacion", motivo: "Corregir la fecha" });
  });

  it("no ofrece decidir una tarea que no está pendiente", async () => {
    simularApi({ "/tareas/11": { ...tareaPendiente, estado: "anulada" } });
    renderizarEn("/tareas/11", "/tareas/:tareaId", <Tarea />);
    expect(await screen.findByText(/esta tarea ya no admite decisiones/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Aprobar/ })).not.toBeInTheDocument();
  });
});
