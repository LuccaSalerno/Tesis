/// <reference types="vitest/config" />
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// En desarrollo, /api se reenvía al backend local (uvicorn): sin CORS ni servicios nuevos.
// En la demo, VITE_ATLAS_API_URL apunta a API Gateway (DO-2026-10-22-WEB F7).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: process.env.ATLAS_API_LOCAL ?? "http://127.0.0.1:8000",
        rewrite: (ruta) => ruta.replace(/^\/api/, ""),
      },
    },
  },
  preview: { port: 4173, strictPort: true },
  build: { sourcemap: false },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["src/pruebas/configuracion.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
    env: { VITE_ATLAS_API_URL: "http://localhost/api", VITE_ATLAS_AUTENTICACION: "local" },
  },
});
