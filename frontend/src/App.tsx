import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { createBrowserRouter, Navigate, RouterProvider, useLocation } from "react-router";

import { ErrorApi } from "@/api/cliente";
import { Marco } from "@/componentes/marco";
import { Cargando } from "@/componentes/ui/estados";
import { ProveedorSesion, useSesion } from "@/lib/sesion";
import { Administracion } from "@/paginas/Administracion";
import { Evidencia } from "@/paginas/Evidencia";
import { Ingresar } from "@/paginas/Ingresar";
import { Inicio } from "@/paginas/Inicio";
import { Tarea } from "@/paginas/Tarea";
import { Tareas } from "@/paginas/Tareas";
import { Tramites } from "@/paginas/Tramites";
import { Consulta } from "@/paginas/tramite/Consulta";
import { Documentos } from "@/paginas/tramite/Documentos";
import { EspacioValidacion } from "@/paginas/tramite/EspacioValidacion";
import { Historial } from "@/paginas/tramite/Historial";
import { MarcoTramite } from "@/paginas/tramite/MarcoTramite";
import { Resumen } from "@/paginas/tramite/Resumen";
import { Revision } from "@/paginas/tramite/Revision";
import { VinculosControles } from "@/paginas/tramite/VinculosControles";

export function crearClienteConsultas(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        // Un rechazo de permisos, una ausencia o un conflicto no se arreglan reintentando.
        retry: (intentos, error) =>
          intentos < 2 && !(error instanceof ErrorApi && [401, 403, 404, 409, 422].includes(error.estado)),
      },
    },
  });
}

function Protegida({ children }: { children: ReactNode }) {
  const { yo, cargando, salidaVoluntaria } = useSesion();
  const ubicacion = useLocation();
  if (cargando) return <Cargando texto="Recuperando la sesión…" />;
  // Si la sesión venció se vuelve a la misma pantalla; si la persona salió, se empieza por Inicio.
  if (!yo) return <Navigate to="/ingresar" state={salidaVoluntaria ? undefined : { desde: ubicacion.pathname }} replace />;
  return children;
}

export const rutas = [
  { path: "/ingresar", element: <Ingresar /> },
  {
    path: "/",
    element: (
      <Protegida>
        <Marco />
      </Protegida>
    ),
    children: [
      { index: true, element: <Inicio /> },
      { path: "tramites", element: <Tramites /> },
      {
        path: "tramites/:tramiteId",
        element: <MarcoTramite />,
        children: [
          { index: true, element: <Navigate to="resumen" replace /> },
          { path: "resumen", element: <Resumen /> },
          { path: "documentos", element: <Documentos /> },
          { path: "documentos/:documentoId", element: <EspacioValidacion /> },
          { path: "vinculos", element: <VinculosControles /> },
          { path: "consulta", element: <Consulta /> },
          { path: "revision", element: <Revision /> },
          { path: "historial", element: <Historial /> },
        ],
      },
      { path: "tareas", element: <Tareas /> },
      { path: "tareas/:tareaId", element: <Tarea /> },
      { path: "decisiones/:decisionId/evidencia", element: <Evidencia /> },
      { path: "administracion", element: <Administracion /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
];

const enrutador = createBrowserRouter(rutas);
const clienteConsultas = crearClienteConsultas();

export function App() {
  return (
    <QueryClientProvider client={clienteConsultas}>
      <ProveedorSesion>
        <RouterProvider router={enrutador} />
      </ProveedorSesion>
    </QueryClientProvider>
  );
}
