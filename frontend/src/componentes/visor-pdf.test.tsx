import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { useEffect, type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { simularApi } from "@/pruebas/entorno";

import VisorDocumento from "./visor-pdf";

const montajes: string[] = [];
const archivos: string[] = [];

vi.mock("react-pdf", () => ({
  pdfjs: { GlobalWorkerOptions: {} },
  Document: ({ file, children, onLoadSuccess }: { file: string; children: ReactNode; onLoadSuccess: (p: { numPages: number }) => void }) => {
    archivos.push(file);
    useEffect(() => {
      montajes.push(file);
      onLoadSuccess({ numPages: 10 });
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [file]);
    return <div>{children}</div>;
  },
  Page: ({ pageNumber }: { pageNumber: number }) => <p>Página mostrada {pageNumber}</p>,
}));

describe("visor del original (RF-11, WEB F4)", () => {
  it("no vuelve a descargar el PDF cuando la consulta se refresca y salta de página sin recargarlo", async () => {
    let firmas = 0;
    const llamadas = simularApi({
      "/tramites/3/versiones/21/archivo": () => [200, { nombre: "Contrato", formato: "pdf", url: `https://s3.local/contrato.pdf?firma=${++firmas}` }],
    });
    const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const visor = (pagina: number) => (
      <QueryClientProvider client={cliente}>
        <VisorDocumento tramiteId={3} fuente={{ versionId: 21, pagina, fragmento: `dato de la página ${pagina}` }} />
      </QueryClientProvider>
    );
    const { rerender } = render(visor(4));
    expect(await screen.findByText("Página mostrada 4")).toBeInTheDocument();

    // Validar un dato invalida todo el trámite: llega una URL firmada nueva para el mismo archivo.
    await cliente.invalidateQueries({ queryKey: ["tramite", 3] });
    await waitFor(() => expect(llamadas.filter((l) => l.ruta.endsWith("/archivo"))).toHaveLength(2));
    expect(screen.getByRole("link", { name: /Abrir el original/ })).toHaveAttribute("href", "https://s3.local/contrato.pdf?firma=2");

    rerender(visor(6));
    expect(await screen.findByText("Página mostrada 6")).toBeInTheDocument();
    expect(new Set(archivos)).toEqual(new Set(["https://s3.local/contrato.pdf?firma=1"]));
    expect(montajes).toEqual(["https://s3.local/contrato.pdf?firma=1"]);
  });
});
