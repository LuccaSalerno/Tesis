import { describe, expect, it, vi } from "vitest";

import { simularApi } from "@/pruebas/entorno";

import { api, conectarSesion, ErrorApi, exigir } from "./cliente";

describe("cliente de la API", () => {
  it("agrega el token de la sesión y devuelve los datos", async () => {
    const llamadas = simularApi({ "/salud": { estado: "ok", entorno: "tests", operacion: "active" } });
    conectarSesion(async () => "token-de-prueba", () => undefined);
    const salud = await exigir(api.GET("/salud"));
    expect(salud.operacion).toBe("active");
    expect(llamadas[0]?.ruta).toBe("/salud");
    const pedido = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0]?.[0] as Request;
    expect(pedido.headers.get("Authorization")).toBe("Bearer token-de-prueba");
  });

  it("convierte los rechazos en ErrorApi y avisa la pérdida de sesión ante un 401", async () => {
    const perdida = vi.fn();
    conectarSesion(async () => null, perdida);
    simularApi({
      "/usuarios/yo": () => [401, { detalle: "No autenticado" }],
      "/tramites": () => [422, { detail: [{ msg: "x" }] }],
      "/salud": () => [503, {}],
    });
    await expect(exigir(api.GET("/usuarios/yo"))).rejects.toMatchObject({ estado: 401, detalle: "No autenticado" });
    expect(perdida).toHaveBeenCalled();
    await expect(exigir(api.GET("/tramites"))).rejects.toMatchObject({ detalle: "Los datos enviados no tienen el formato esperado." });
    const caido = await exigir(api.GET("/salud")).catch((e: ErrorApi) => e);
    expect(caido).toBeInstanceOf(ErrorApi);
    expect((caido as ErrorApi).esMantenimiento).toBe(true);
  });
});
