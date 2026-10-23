import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Ciclo, Firma, TramiteDetalle } from "@/api/tipos";
import { simularApi } from "@/pruebas/entorno";

import { Documentos } from "./Documentos";
import { MarcoTramite } from "./MarcoTramite";
import { Resumen } from "./Resumen";

const sesion = vi.hoisted(() => ({
  yo: { id: 4, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" },
}));
vi.mock("@/lib/sesion", () => ({
  useSesion: () => ({ yo: sesion.yo, tiene: (rol: string) => sesion.yo.roles.includes(rol) }),
}));

const ahora = "2026-10-23T12:00:00Z";
const LEYENDA = "Firma digital simulada — sin validez jurídica";

function tramite(estado: TramiteDetalle["estado"]): TramiteDetalle {
  return {
    id: 3,
    titulo: "Servicio de mantenimiento",
    descripcion: null,
    estado,
    responsable_id: 4,
    creado_en: ahora,
    actualizado_en: ahora,
    documentos: [{ id: 5, nombre: "Orden de compra", tipo: "orden_compra", version_vigente: { id: 21, numero: 1, archivo_id: 8 } }],
  };
}

const ciclo: Ciclo = {
  id: 2,
  numero: 1,
  estado: "aprobado",
  tramite_id: 3,
  plantilla_flujo_id: 1,
  confirmado_por_id: 4,
  confirmado_en: ahora,
  concluido_en: ahora,
  versiones: [{ documento_id: 5, documento_nombre: "Orden de compra", version_id: 21, version_numero: 1 }],
  tareas: [{ id: 11, ciclo_revision_id: 2, orden: 1, nombre: "Aprobación final", rol_requerido: "revisor_aprobador", estado: "aprobada", asignada_a_id: 6, creada_en: ahora, actualizada_en: ahora, decision_id: 7 }],
};

const firma: Firma = {
  id: 1,
  leyenda: LEYENDA,
  simulada: true,
  tramite_id: 3,
  ciclo_revision_id: 2,
  ciclo_numero: 1,
  documento_id: 5,
  version_id: 21,
  version_numero: 1,
  firmante_id: 6,
  firmada_en: ahora,
  huella_archivo: "a".repeat(64),
  algoritmo: "SHA-256",
  registro_canonico: '{"firmada_en":"2026-10-23T12:00:00+00:00","firmante_id":6,"huella_archivo":"aaa","version_id":21}',
  referencia_integridad: "b".repeat(64),
};

const pendiente = {
  id: 9,
  nombre: "O-v2_Orden_Compra.pdf",
  formato: "pdf",
  tamano_bytes: 1000,
  huella: "c".repeat(64),
  estado_incorporacion: "pendiente",
  cargado_en: ahora,
  vence_en: ahora,
  trabajo: { id: 3, estado: "completado", intento: 1, creado_en: ahora, ejecucion_iniciada_en: ahora, actualizado_en: ahora },
  sugerencia_version: { documento_id: 5, documento_nombre: "Orden de compra", criterio: "cuit", campo: "cuit_proveedor", estado: "pendiente" },
};

function mostrar(pantalla: "documentos" | "resumen") {
  const enrutador = createMemoryRouter(
    [{ path: "/tramites/:tramiteId", element: <MarcoTramite />, children: [{ path: "documentos", element: <Documentos /> }, { path: "resumen", element: <Resumen /> }] }],
    { initialEntries: [`/tramites/3/${pantalla}`] },
  );
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={enrutador} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  sesion.yo = { id: 4, roles: ["responsable_tramite"], autorizacion_cierre: false, nombre_visible: "Laura" };
});

describe("versión nueva sugerida (RF-06, RF-07)", () => {
  it("muestra el criterio y confirma la versión", async () => {
    const llamadas = simularApi({
      "/tramites/3": tramite("aprobado"),
      "/tramites/3/archivos": [pendiente],
      "/usuarios/directorio": [],
      "POST /tramites/3/archivos/9/version": () => [201, {}],
    });
    mostrar("documentos");
    expect(await screen.findByText("Posible versión nueva de «Orden de compra»")).toBeInTheDocument();
    expect(screen.getByText(/coincide el CUIT \(CUIT del proveedor\)/)).toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: "Incorporar como versión nueva" }));
    expect(llamadas.some((l) => l.metodo === "POST" && l.ruta === "/tramites/3/archivos/9/version")).toBe(true);
  });

  it("descarta sin crear documento ni versión", async () => {
    const llamadas = simularApi({
      "/tramites/3": tramite("borrador"),
      "/tramites/3/archivos": [{ ...pendiente, sugerencia_version: null }],
      "/usuarios/directorio": [],
      "POST /tramites/3/archivos/9/descarte": () => [200, {}],
    });
    mostrar("documentos");
    await userEvent.setup().click(await screen.findByRole("button", { name: "Descartar" }));
    expect(screen.queryByText(/Posible versión nueva/)).not.toBeInTheDocument();
    expect(llamadas.filter((l) => l.metodo === "POST").map((l) => l.ruta)).toEqual(["/tramites/3/archivos/9/descarte"]);
  });
});

describe("firma digital simulada (RF-23, V11)", () => {
  it("el aprobador con autorización firma una versión del ciclo aprobado", async () => {
    sesion.yo = { id: 6, roles: ["revisor_aprobador"], autorizacion_cierre: true, nombre_visible: "Sofía" };
    const llamadas = simularApi({
      "/tramites/3": { ...tramite("aprobado"), responsable_id: 4 },
      "/tramites/3/ciclos": [ciclo],
      "/tramites/3/controles": { vigentes: [], historial: [] },
      "/usuarios/directorio": [],
      "POST /tramites/3/firma": () => [201, firma],
    });
    mostrar("resumen");
    expect(await screen.findByText(LEYENDA)).toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: "Firmar (simulación)" }));
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({ version_id: 21 });
  });

  it("sin autorización de cierre no se ofrece firmar", async () => {
    sesion.yo = { id: 6, roles: ["revisor_aprobador"], autorizacion_cierre: false, nombre_visible: "Martín" };
    simularApi({
      "/tramites/3": tramite("aprobado"),
      "/tramites/3/ciclos": [ciclo],
      "/tramites/3/controles": { vigentes: [], historial: [] },
      "/usuarios/directorio": [],
    });
    mostrar("resumen");
    expect(await screen.findByText(/Trámite aprobado/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Firmar (simulación)" })).not.toBeInTheDocument();
  });

  it("el trámite cerrado muestra la firma con su leyenda y referencia", async () => {
    simularApi({
      "/tramites/3": tramite("cerrado"),
      "/tramites/3/ciclos": [ciclo],
      "/tramites/3/controles": { vigentes: [], historial: [] },
      "/tramites/3/firma": firma,
      "/usuarios/directorio": [],
    });
    mostrar("resumen");
    expect(await screen.findByText(firma.referencia_integridad)).toBeInTheDocument();
    expect(screen.getByText(LEYENDA)).toBeInTheDocument();
    expect(screen.getByText(/Orden de compra · v1 \(ciclo 1\)/)).toBeInTheDocument();
  });
});
