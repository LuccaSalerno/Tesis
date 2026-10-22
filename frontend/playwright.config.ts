import { defineConfig, devices } from "@playwright/test";

/**
 * Recorridos críticos contra el stack local real (API, PostgreSQL y moto) con la semilla
 * local (procesamiento simulado). No corren en la CI: necesitan los servicios levantados.
 * Ver frontend/README.md.
 */
export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: process.env.ATLAS_E2E_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 900 },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
