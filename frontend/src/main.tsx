import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import { cargarConfiguracion } from "./lib/configuracion";

// La configuración del despliegue se carga antes de importar la aplicación: el cliente de la
// API toma su URL al crearse (DO-2026-10-23-WEB-HOST P4).
void cargarConfiguracion().then(async () => {
  const { App } = await import("./App");
  createRoot(document.getElementById("raiz")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
