import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { simularApi } from "@/pruebas/entorno";

import { EspacioValidacion } from "./EspacioValidacion";
import { MarcoTramite } from "./MarcoTramite";

vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({ yo: { id: 4, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" }, tiene: () => true }),
}));
vi.mock("@/componentes/visor", () => ({ VisorDocumento: () => <div>visor</div>, DialogoFuente: () => null }));

const ahora = "2026-10-22T19:00:00Z";
const validaciones = {
  documento_id: 5,
  version: { id: 21, numero: 1, archivo_id: 8 },
  tipo_validado: "contrato",
  clasificacion: {
    campo: "tipo_documental",
    sugerencia: null,
    vigente: { id: 1, version_id: 21, campo: "tipo_documental", valor_validado: "contrato", tipo: "sin_sugerencia", motivo_ausencia: null, valor_sugerido_id: null, reemplaza_a_id: null, validador_id: 4, validado_en: ahora, localizador: null },
    historial: [],
  },
  campos: [{ campo: "fecha_celebracion", sugerencia: null, vigente: null, historial: [] }],
  fuera_de_esquema: [],
};

describe("espacio de validación (RF-12)", () => {
  it("declara un campo ausente sin inventar un valor", async () => {
    const llamadas = simularApi({
      "/tramites/3": { id: 3, titulo: "En vivo", descripcion: null, estado: "borrador", responsable_id: 4, creado_en: ahora, actualizado_en: ahora, documentos: [{ id: 5, nombre: "Contrato", tipo: "contrato", version_vigente: { id: 21, numero: 1, archivo_id: 8 } }] },
      "/tramites/3/documentos/5/validaciones": validaciones,
      "/tramites/3/archivos": [],
      "/usuarios/directorio": [],
      "POST /tramites/3/documentos/5/validaciones": () => [201, {}],
    });
    const enrutador = createMemoryRouter(
      [{ path: "/tramites/:tramiteId", element: <MarcoTramite />, children: [{ path: "documentos/:documentoId", element: <EspacioValidacion /> }] }],
      { initialEntries: ["/tramites/3/documentos/5"] },
    );
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <RouterProvider router={enrutador} />
      </QueryClientProvider>,
    );
    const usuario = userEvent.setup();
    const dato = (await screen.findByRole("heading", { name: "Fecha de celebración" })).closest("li")!;
    await usuario.click(within(dato).getByRole("button", { name: "No consta / no aplica" }));
    await usuario.click(within(dato).getByRole("button", { name: "Guardar" }));
    const envio = llamadas.find((l) => l.metodo === "POST");
    expect(envio?.cuerpo).toEqual({ campo: "fecha_celebracion", valor_sugerido_id: null, reemplaza_a_id: null, ausente: "no_consta" });
  });
});
