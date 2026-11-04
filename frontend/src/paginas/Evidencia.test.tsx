import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { evidencia } from "@/pruebas/datos";
import { renderizarEn, simularApi } from "@/pruebas/entorno";

import { Evidencia } from "./Evidencia";

describe("Evidencia de la decisión (PD-03, V1 a V4)", () => {
  it("responde quién, cuándo, qué y por qué, y resalta las entradas de un control", async () => {
    simularApi({
      "/decisiones/7/evidencia": evidencia,
      "/usuarios/directorio": [{ id: 5, nombre_visible: "Sofía Herrera" }, { id: 4, nombre_visible: "Laura Méndez" }],
    });
    const usuario = userEvent.setup();
    renderizarEn("/decisiones/7/evidencia", "/decisiones/:decisionId/evidencia", <Evidencia />);
    expect(await screen.findByText("Corregir la fecha de la orden")).toBeInTheDocument();
    expect(screen.getAllByText("Observación").length).toBeGreaterThan(0);
    expect(await screen.findAllByText("Sofía Herrera")).not.toHaveLength(0);

    const filaFecha = screen.getByText("15 mar 2027").closest("tr")!;
    const filaMoneda = screen.getByText("ARS").closest("tr")!;
    expect(filaFecha.className).not.toMatch(/bg-advertencia-suave/);
    const control = screen.getByRole("button", { name: /Fecha de la orden dentro de la vigencia/ });
    await usuario.click(control);
    expect(control).toHaveAttribute("aria-pressed", "true");
    expect(filaFecha.className).toMatch(/bg-advertencia-suave/);
    expect(filaMoneda.className).not.toMatch(/bg-advertencia-suave/);
  });
});
