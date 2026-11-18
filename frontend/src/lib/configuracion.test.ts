import { describe, expect, it } from "vitest";

import { aplicarConfiguracion, cargarConfiguracion, CONFIGURACION } from "./configuracion";

const VALIDA = {
  apiUrl: "https://abc123.execute-api.us-east-1.amazonaws.com",
  autenticacion: "cognito",
  cognitoRegion: "us-east-1",
  cognitoCliente: "6l0rjm8dfnhdoej099oem8fb7l",
};

function respuesta(cuerpo: unknown, tipo = "application/json", estado = 200): typeof fetch {
  return async () =>
    new Response(typeof cuerpo === "string" ? cuerpo : JSON.stringify(cuerpo), {
      status: estado,
      headers: { "content-type": tipo },
    });
}

describe("configuración publicada", () => {
  it("aplica la configuración válida de configuracion.json", async () => {
    const anterior = { ...CONFIGURACION };
    expect(await cargarConfiguracion(respuesta(VALIDA))).toBe(true);
    expect(CONFIGURACION).toEqual(VALIDA);
    Object.assign(CONFIGURACION, anterior);
  });

  it("sin el archivo conserva las variables del build", async () => {
    const anterior = { ...CONFIGURACION };
    expect(await cargarConfiguracion(respuesta("<!doctype html>", "text/html"))).toBe(false);
    expect(await cargarConfiguracion(respuesta({}, "application/json", 404))).toBe(false);
    expect(await cargarConfiguracion(async () => Promise.reject(new TypeError("sin red")))).toBe(false);
    expect(CONFIGURACION).toEqual(anterior);
  });

  it("descarta entera una configuración inválida o con campos extra", () => {
    const anterior = { ...CONFIGURACION };
    expect(aplicarConfiguracion({ ...VALIDA, apiUrl: "http://inseguro" })).toBe(false);
    expect(aplicarConfiguracion({ ...VALIDA, autenticacion: "otra" })).toBe(false);
    expect(aplicarConfiguracion({ ...VALIDA, extra: 1 })).toBe(false);
    expect(CONFIGURACION).toEqual(anterior);
  });
});
