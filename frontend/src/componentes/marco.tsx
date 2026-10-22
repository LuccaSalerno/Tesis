import { ClipboardCheck, FolderKanban, Home, LogOut, Settings2 } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { useSalud } from "@/api/consultas";
import { Aviso } from "@/componentes/ui/aviso";
import { ROL } from "@/lib/dominio";
import { useSesion } from "@/lib/sesion";
import { cn } from "@/lib/utilidades";

function Enlace({ a, icono, children }: { a: string; icono: React.ReactNode; children: string }) {
  return (
    <NavLink
      to={a}
      end={a === "/"}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm [&_svg]:size-4",
          isActive ? "bg-primario-suave font-medium text-primario" : "text-tenue hover:bg-neutro-suave hover:text-texto",
        )
      }
    >
      {icono}
      {children}
    </NavLink>
  );
}

/** Estructura de primer nivel (§3.4.1): inicio, trámites, tareas propias y administración. */
export function Marco() {
  const { yo, tiene, salir } = useSesion();
  const salud = useSalud();
  const operacion = salud.data?.operacion;
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-borde bg-superficie">
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="grid size-8 place-items-center rounded-md bg-primario text-sm font-bold text-white">A</span>
          <div>
            <p className="text-sm font-semibold">ATLAS</p>
            <p className="text-xs text-tenue">Documentos y contratos</p>
          </div>
        </div>
        <nav aria-label="Principal" className="flex flex-1 flex-col gap-1 px-3">
          <Enlace a="/" icono={<Home />}>Inicio</Enlace>
          {tiene("responsable_tramite") || tiene("revisor_aprobador") ? (
            <Enlace a="/tramites" icono={<FolderKanban />}>Trámites</Enlace>
          ) : null}
          {tiene("revisor_aprobador") ? <Enlace a="/tareas" icono={<ClipboardCheck />}>Mis tareas</Enlace> : null}
          {tiene("administrador_operativo") ? (
            <Enlace a="/administracion" icono={<Settings2 />}>Administración</Enlace>
          ) : null}
        </nav>
        <div className="border-t border-borde px-4 py-4">
          <p className="truncate text-sm font-medium">{yo?.nombre_visible ?? `Usuario #${yo?.id}`}</p>
          <p className="truncate text-xs text-tenue">{yo?.roles.map((r) => ROL[r]).join(" · ")}</p>
          <button type="button" onClick={salir} className="mt-3 inline-flex items-center gap-1.5 text-xs text-tenue hover:text-texto">
            <LogOut className="size-3.5" aria-hidden /> Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1">
        {operacion && operacion !== "active" ? (
          <Aviso tono="advertencia" className="m-4 mb-0" titulo={operacion === "draining" ? "ATLAS está cerrando la sesión (drenaje)" : "ATLAS está en mantenimiento"}>
            {operacion === "draining"
              ? "Podés consultar la información; las operaciones que modifican datos están suspendidas."
              : "Las operaciones están suspendidas temporalmente."}
          </Aviso>
        ) : null}
        <div className="mx-auto max-w-[90rem] px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export function Encabezado({ titulo, descripcion, acciones }: { titulo: React.ReactNode; descripcion?: React.ReactNode; acciones?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl">{titulo}</h1>
        {descripcion ? <p className="mt-1 text-sm text-tenue">{descripcion}</p> : null}
      </div>
      {acciones ? <div className="flex flex-wrap gap-2">{acciones}</div> : null}
    </div>
  );
}
