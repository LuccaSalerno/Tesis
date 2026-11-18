/**
 * Configuración de la aplicación, fijada por el despliegue (nunca elegida por el usuario).
 *
 * Servida con S3 y CloudFront, la aplicación lee `configuracion.json` al iniciar: así una
 * sesión nueva solo publica ese archivo, sin recompilar. Sin el
 * archivo (desarrollo local, `npm run preview`), valen las variables `VITE_*` del build.
 */
import { z } from "zod";

export type ModoAutenticacion = "cognito" | "local";

export const CONFIGURACION = {
  apiUrl: (import.meta.env.VITE_ATLAS_API_URL as string | undefined) ?? "/api",
  autenticacion: ((import.meta.env.VITE_ATLAS_AUTENTICACION as string | undefined) ??
    "local") as ModoAutenticacion,
  cognitoRegion: (import.meta.env.VITE_ATLAS_COGNITO_REGION as string | undefined) ?? "us-east-1",
  cognitoCliente: (import.meta.env.VITE_ATLAS_COGNITO_CLIENTE as string | undefined) ?? "",
};

const Publicada = z
  .object({
    apiUrl: z.string().url().startsWith("https://"),
    autenticacion: z.enum(["cognito", "local"]),
    cognitoRegion: z.string().regex(/^[a-z]{2}-[a-z]+-\d$/),
    cognitoCliente: z.string().regex(/^[a-z0-9]+$/),
  })
  .strict();

/** Aplica la configuración publicada; una inválida se descarta entera, sin mezclarla. */
export function aplicarConfiguracion(datos: unknown): boolean {
  const resultado = Publicada.safeParse(datos);
  if (!resultado.success) return false;
  Object.assign(CONFIGURACION, resultado.data);
  return true;
}

export async function cargarConfiguracion(obtener: typeof fetch = (...a) => globalThis.fetch(...a)): Promise<boolean> {
  try {
    const respuesta = await obtener("/configuracion.json", { cache: "no-store" });
    // Sin el archivo, CloudFront responde index.html (rutas de React): no es JSON.
    if (!respuesta.ok || !respuesta.headers.get("content-type")?.includes("application/json")) return false;
    return aplicarConfiguracion(await respuesta.json());
  } catch {
    return false;
  }
}
