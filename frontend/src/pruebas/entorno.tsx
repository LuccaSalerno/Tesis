/**
 * Utilidades de prueba: la API se simula con un `fetch` que responde por ruta. Estos datos son
 * de prueba de componentes; nunca se presentan como evidencia de funcionamiento (§4).
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

export type Respuestas = Record<string, unknown | ((cuerpo: unknown) => [number, unknown])>;

export function simularApi(respuestas: Respuestas) {
  const llamadas: { metodo: string; ruta: string; cuerpo: unknown }[] = [];
  const fetchSimulado = vi.fn(async (entrada: Request | string, init?: RequestInit) => {
    const pedido = entrada instanceof Request ? entrada : new Request(entrada, init);
    const url = new URL(pedido.url);
    const ruta = url.pathname.replace(/^\/api/, "");
    const texto = pedido.method === "GET" ? "" : await pedido.text();
    const cuerpo = texto ? JSON.parse(texto) : null;
    llamadas.push({ metodo: pedido.method, ruta, cuerpo });
    const clave = `${pedido.method} ${ruta}`;
    const respuesta = respuestas[clave] ?? respuestas[ruta];
    if (respuesta === undefined) return new Response(JSON.stringify({ detalle: "No existe" }), { status: 404 });
    const [estado, datos] = typeof respuesta === "function" ? (respuesta as (c: unknown) => [number, unknown])(cuerpo) : [200, respuesta];
    return new Response(JSON.stringify(datos), { status: estado, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchSimulado);
  return llamadas;
}

export function renderizarEn(ruta: string, patron: string, elemento: ReactElement) {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const enrutador = createMemoryRouter([{ path: patron, element: elemento }], { initialEntries: [ruta] });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={enrutador} />
    </QueryClientProvider>,
  );
}
