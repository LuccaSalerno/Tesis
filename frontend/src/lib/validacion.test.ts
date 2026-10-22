import { describe, expect, it } from "vitest";

import { claseDeCampo, errorDeFormato } from "./validacion";

describe("formatos canónicos (DO-2026-10-22-VAL P4)", () => {
  it("clasifica los campos de RC-P04", () => {
    expect(claseDeCampo("vigencia_hasta")).toBe("fecha");
    expect(claseDeCampo("fecha_emision")).toBe("fecha");
    expect(claseDeCampo("monto_total")).toBe("importe");
    expect(claseDeCampo("cuit_emisor")).toBe("cuit");
    expect(claseDeCampo("moneda")).toBe("moneda");
    expect(claseDeCampo("contraparte")).toBe("texto");
  });

  it("acepta los formatos canónicos y explica los incorrectos", () => {
    expect(errorDeFormato("vigencia_hasta", "2027-02-28")).toBeNull();
    expect(errorDeFormato("vigencia_hasta", "28/02/2027")).toMatch(/AAAA-MM-DD/);
    expect(errorDeFormato("importe_total", "1250000.00")).toBeNull();
    expect(errorDeFormato("importe_total", "1.250.000,00")).toMatch(/dos decimales/);
    expect(errorDeFormato("cuit_proveedor", "30-96472518-3")).toBeNull();
    expect(errorDeFormato("moneda", "ars")).toMatch(/ISO/);
    expect(errorDeFormato("contraparte", "   ")).toMatch(/Ingresá/);
  });
});
