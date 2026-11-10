import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { simularApi } from "@/pruebas/entorno";

import { Documentos } from "./Documentos";
import { MarcoTramite } from "./MarcoTramite";

vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({ yo: { id: 4, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" }, tiene: () => true }),
}));

const ahora = "2026-11-10T19:00:00Z";

describe("carga de archivos (RF-03, §5.3.1)", () => {
  it("carga varios archivos elegidos a la vez, de a uno, y un fallo no detiene a los demás", async () => {
    let siguiente = 0;
    const llamadas = simularApi({
      "/tramites/3": { id: 3, titulo: "En vivo", descripcion: null, estado: "borrador", responsable_id: 4, creado_en: ahora, actualizado_en: ahora, documentos: [] },
      "/tramites/3/archivos": [],
      "/usuarios/directorio": [],
      "POST /tramites/3/cargas": (cuerpo: unknown) => {
        const { nombre } = cuerpo as { nombre: string };
        if (nombre.startsWith("roto")) return [422, { detalle: "El archivo supera los 20 MB." }];
        siguiente += 1;
        return [201, { id: siguiente, url: `https://s3.local/carga-${siguiente}`, metodo: "PUT", encabezados: {} }];
      },
      "POST /tramites/3/cargas/1/confirmacion": () => [200, { id: 11 }],
      "POST /tramites/3/cargas/2/confirmacion": () => [200, { id: 12 }],
    });
    // La transferencia va directo al almacenamiento con la URL prefirmada, no a la API.
    const transferencias: string[] = [];
    const api = globalThis.fetch;
    vi.stubGlobal("fetch", (entrada: Request | string, init?: RequestInit) => {
      if (typeof entrada === "string" && entrada.startsWith("https://s3.local/")) {
        transferencias.push(entrada);
        return Promise.resolve(new Response(null, { status: 200 }));
      }
      return api(entrada, init);
    });
    const enrutador = createMemoryRouter(
      [{ path: "/tramites/:tramiteId", element: <MarcoTramite />, children: [{ path: "documentos", element: <Documentos /> }] }],
      { initialEntries: ["/tramites/3/documentos"] },
    );
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}>
        <RouterProvider router={enrutador} />
      </QueryClientProvider>,
    );
    const pdf = (nombre: string) => new File(["%PDF-1.7"], nombre, { type: "application/pdf" });
    await userEvent.setup().upload(await screen.findByLabelText("Archivos a cargar"), [pdf("contrato.pdf"), pdf("roto.pdf"), pdf("factura.pdf")]);

    expect(await screen.findByText("2 archivos recibidos")).toBeInTheDocument();
    expect(screen.getByText(/roto\.pdf: El archivo supera los 20 MB\./)).toBeInTheDocument();
    const cargas = llamadas.filter((l) => l.metodo === "POST" && l.ruta === "/tramites/3/cargas");
    expect(cargas.map((l) => (l.cuerpo as { nombre: string }).nombre)).toEqual(["contrato.pdf", "roto.pdf", "factura.pdf"]);
    expect(transferencias).toEqual(["https://s3.local/carga-1", "https://s3.local/carga-2"]);
    expect(llamadas.filter((l) => l.ruta.endsWith("/confirmacion")).map((l) => l.ruta)).toEqual([
      "/tramites/3/cargas/1/confirmacion",
      "/tramites/3/cargas/2/confirmacion",
    ]);
  });
});
