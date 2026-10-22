/** Configuración de la aplicación, fijada al construirla (nunca elegida por el usuario). */

export type ModoAutenticacion = "cognito" | "local";

export const CONFIGURACION = {
  apiUrl: (import.meta.env.VITE_ATLAS_API_URL as string | undefined) ?? "/api",
  autenticacion: ((import.meta.env.VITE_ATLAS_AUTENTICACION as string | undefined) ??
    "local") as ModoAutenticacion,
  cognitoRegion: (import.meta.env.VITE_ATLAS_COGNITO_REGION as string | undefined) ?? "us-east-1",
  cognitoCliente: (import.meta.env.VITE_ATLAS_COGNITO_CLIENTE as string | undefined) ?? "",
};
