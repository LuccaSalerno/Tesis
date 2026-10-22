/**
 * Cliente tipado de la API (openapi-fetch sobre el contrato generado). Agrega el token de la
 * sesión y convierte toda respuesta no exitosa en `ErrorApi`, con un mensaje para la persona
 * que nunca incluye el cuerpo técnico completo.
 */
import createClient, { type Middleware } from "openapi-fetch";

import { CONFIGURACION } from "@/lib/configuracion";

import type { paths } from "./esquema";

export class ErrorApi extends Error {
  readonly estado: number;
  readonly detalle: string;

  constructor(estado: number, detalle: string) {
    super(detalle);
    this.name = "ErrorApi";
    this.estado = estado;
    this.detalle = detalle;
  }

  get esMantenimiento(): boolean {
    return this.estado === 503;
  }
}

type ProveedorToken = () => Promise<string | null>;

let proveedorToken: ProveedorToken = async () => null;
let alPerderSesion: () => void = () => undefined;

export function conectarSesion(proveedor: ProveedorToken, perdida: () => void): void {
  proveedorToken = proveedor;
  alPerderSesion = perdida;
}

const autenticacion: Middleware = {
  async onRequest({ request }) {
    const token = await proveedorToken();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
  async onResponse({ response }) {
    if (response.status === 401) alPerderSesion();
    return response;
  },
};

// `fetch` se resuelve en cada llamada (permite sustituirlo en las pruebas de componentes).
export const api = createClient<paths>({
  baseUrl: CONFIGURACION.apiUrl,
  fetch: (pedido) => globalThis.fetch(pedido),
});
api.use(autenticacion);

const MENSAJES: Record<number, string> = {
  401: "Tu sesión venció. Volvé a ingresar.",
  403: "No tenés permiso para esta operación.",
  404: "No existe o no tenés acceso.",
  503: "El servicio no está disponible en este momento. Reintentá en unos minutos.",
};

function detalleDe(estado: number, error: unknown): string {
  const detalle = (error as { detalle?: unknown; detail?: unknown } | undefined) ?? {};
  if (typeof detalle.detalle === "string") return detalle.detalle;
  if (Array.isArray(detalle.detail)) return "Los datos enviados no tienen el formato esperado.";
  return MENSAJES[estado] ?? "Ocurrió un error inesperado.";
}

/** Devuelve los datos de una respuesta exitosa o lanza `ErrorApi`. */
export async function exigir<T>(
  promesa: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await promesa;
  if (!response.ok) throw new ErrorApi(response.status, detalleDe(response.status, error));
  return data as T;
}
