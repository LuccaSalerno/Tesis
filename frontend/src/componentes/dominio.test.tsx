import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import type { Control } from "@/api/tipos";
import { evidencia, tareaPendiente } from "@/pruebas/datos";
import { simularApi } from "@/pruebas/entorno";

import { TarjetaControl, ValorSugerido, ValorValidado } from "./dominio";

const conConsultas = (nodo: ReactNode) =>
  render(<QueryClientProvider client={new QueryClient()}>{nodo}</QueryClientProvider>);

describe("sugerencia de la IA frente a valor validado (RF-12, WEB)", () => {
  it("rotula la sugerencia y marca la simulación local solo cuando corresponde", () => {
    const { rerender } = render(<ValorSugerido campo="vigencia_hasta" valor="2027-02-28" modelo="us.anthropic.claude-haiku" />);
    expect(screen.getByText("Sugerido")).toBeInTheDocument();
    expect(screen.queryByText("Simulación local")).not.toBeInTheDocument();
    expect(screen.getByText("28 feb 2027")).toBeInTheDocument();
    rerender(<ValorSugerido campo="vigencia_hasta" valor="2027-02-28" modelo="simulacion-local-oraculo-PD07" />);
    expect(screen.getByText("Simulación local")).toBeInTheDocument();
  });

  it("muestra el tipo documental con su rótulo", () => {
    render(<ValorSugerido campo="tipo_documental" valor="contrato" />);
    expect(screen.getByText("Contrato")).toBeInTheDocument();
  });

  it("muestra quién validó y declara la ausencia sin inventar un valor", async () => {
    simularApi({ "/usuarios/directorio": [{ id: 7, nombre_visible: "Laura Méndez" }] });
    conConsultas(
      <ValorValidado
        campo="fecha_celebracion"
        validacion={{ valor_validado: null, tipo: "ausente", motivo_ausencia: "no_consta", validador_id: 7, validado_en: "2026-10-22T19:00:00Z" }}
      />,
    );
    expect(screen.getByText("Declarado ausente")).toBeInTheDocument();
    expect(screen.getByText("No consta en el documento")).toBeInTheDocument();
    expect(await screen.findByText("Laura Méndez")).toBeInTheDocument();
  });
});

describe("tarjeta de control (RF-16)", () => {
  it("muestra la versión de la regla tal como la registró la ejecución y abre el documento", async () => {
    const alVerFuente = vi.fn();
    const ejecucion = { ...evidencia.controles[0], version_regla: "v1" } as NonNullable<Control["ejecucion"]>;
    const control = { ...tareaPendiente.controles[0], ejecucion } as Control;
    render(<ul><TarjetaControl control={control} alVerFuente={alVerFuente} /></ul>);
    expect(screen.getByText(/^Regla v1 · ejecutada/)).toBeInTheDocument();
    await userEvent.click(screen.getAllByRole("button", { name: "Ver documento" })[0]!);
    const version = ejecucion.versiones[0]!;
    expect(alVerFuente).toHaveBeenCalledWith({ versionId: version.version_id, titulo: `${version.documento_nombre} · v${version.version_numero}` });
  });
});
