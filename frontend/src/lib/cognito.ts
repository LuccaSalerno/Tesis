/**
 * Inicio de sesión con Cognito sin SDK: `InitiateAuth` con
 * USER_PASSWORD_AUTH y renovación con REFRESH_TOKEN_AUTH. La contraseña solo viaja a Cognito.
 */
import { CONFIGURACION } from "./configuracion";

export interface TokensCognito {
  acceso: string;
  refresco: string | null;
  expiraEn: number; // epoch en segundos
}

async function iniciar(flujo: string, parametros: Record<string, string>): Promise<TokensCognito> {
  const respuesta = await fetch(
    `https://cognito-idp.${CONFIGURACION.cognitoRegion}.amazonaws.com/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
      },
      body: JSON.stringify({
        AuthFlow: flujo,
        ClientId: CONFIGURACION.cognitoCliente,
        AuthParameters: parametros,
      }),
    },
  );
  const cuerpo = (await respuesta.json().catch(() => ({}))) as {
    AuthenticationResult?: { AccessToken: string; RefreshToken?: string; ExpiresIn: number };
    ChallengeName?: string;
    __type?: string;
  };
  if (!respuesta.ok) {
    throw new Error(
      cuerpo.__type?.includes("NotAuthorized")
        ? "Usuario o contraseña incorrectos."
        : "No se pudo iniciar sesión. Reintentá en unos minutos.",
    );
  }
  if (cuerpo.ChallengeName || !cuerpo.AuthenticationResult) {
    throw new Error("La cuenta requiere un paso adicional que la demo no admite; avisá al operador.");
  }
  const resultado = cuerpo.AuthenticationResult;
  return {
    acceso: resultado.AccessToken,
    refresco: resultado.RefreshToken ?? null,
    expiraEn: Math.floor(Date.now() / 1000) + resultado.ExpiresIn,
  };
}

export function ingresarConCognito(usuario: string, clave: string): Promise<TokensCognito> {
  return iniciar("USER_PASSWORD_AUTH", { USERNAME: usuario, PASSWORD: clave });
}

export function renovarConCognito(refresco: string): Promise<TokensCognito> {
  return iniciar("REFRESH_TOKEN_AUTH", { REFRESH_TOKEN: refresco });
}
