import { CalendarClock, UserRound } from "lucide-react";
import { NavLink, Outlet, useOutletContext, useParams } from "react-router";

import { useTramite } from "@/api/consultas";
import type { TramiteDetalle } from "@/api/tipos";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { Cargando, ErrorConsulta } from "@/componentes/ui/estados";
import { ESTADO_TRAMITE } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";
import { useSesion } from "@/lib/sesion";
import { cn } from "@/lib/utilidades";

export interface ContextoTramite {
  tramite: TramiteDetalle;
  esResponsable: boolean;
}

export function useContextoTramite(): ContextoTramite {
  return useOutletContext<ContextoTramite>();
}

export function useIdTramite(): number {
  return Number(useParams().tramiteId);
}

/** Seis áreas en lugar de las ocho pestañas de los mockups: validar y ver la fuente van juntos. */
const SECCIONES = [
  ["resumen", "Resumen"],
  ["documentos", "Documentos y datos"],
  ["vinculos", "Vínculos y controles"],
  ["consulta", "Consulta"],
  ["revision", "Revisión"],
  ["historial", "Historial"],
] as const;

export function MarcoTramite() {
  const id = useIdTramite();
  const { yo } = useSesion();
  const tramite = useTramite(id);
  if (tramite.isPending) return <Cargando />;
  if (tramite.isError) return <ErrorConsulta error={tramite.error} reintentar={() => void tramite.refetch()} />;
  const t = tramite.data;
  const contexto: ContextoTramite = { tramite: t, esResponsable: t.responsable_id === yo?.id };
  return (
    <>
      <header className="mb-5">
        <p className="text-xs text-tenue">TR-{t.id}</p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl">{t.titulo}</h1>
          <InsigniaEstado catalogo={ESTADO_TRAMITE} valor={t.estado} />
        </div>
        <p className="mt-2 flex flex-wrap gap-4 text-sm text-tenue">
          <span className="inline-flex items-center gap-1.5">
            <UserRound className="size-4" aria-hidden /> Responsable: <Persona id={t.responsable_id} />
          </span>
          <span className="inline-flex items-center gap-1.5">
            <CalendarClock className="size-4" aria-hidden /> Actualizado {fechaHora(t.actualizado_en)}
          </span>
        </p>
      </header>
      <nav aria-label="Secciones del trámite" className="mb-6 flex gap-1 overflow-x-auto border-b border-borde">
        {SECCIONES.map(([ruta, rotulo]) => (
          <NavLink
            key={ruta}
            to={ruta}
            className={({ isActive }) =>
              cn(
                "-mb-px border-b-2 px-3 py-2 text-sm whitespace-nowrap",
                isActive ? "border-primario font-medium text-primario" : "border-transparent text-tenue hover:text-texto",
              )
            }
          >
            {rotulo}
          </NavLink>
        ))}
      </nav>
      <Outlet context={contexto} />
    </>
  );
}
