import { FileText, Scale } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { useCiclos, useLineaTiempo } from "@/api/consultas";
import type { Hito } from "@/api/tipos";
import { Persona } from "@/componentes/dominio";
import { DialogoFuente, type Fuente } from "@/componentes/visor";
import { Insignia } from "@/componentes/ui/insignia";
import { Selector } from "@/componentes/ui/campos";
import { Cargando, ErrorConsulta, Vacio } from "@/componentes/ui/estados";
import { Panel } from "@/componentes/ui/panel";
import { rotuloAccion } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useIdTramite } from "./MarcoTramite";

const FILTROS = {
  todo: "Todos los eventos",
  documentos: "Documentos y versiones",
  datos: "Validaciones y controles",
  revision: "Revisión y decisiones",
} as const;

function categoria(hito: Hito): keyof typeof FILTROS {
  if (["documento", "archivo"].includes(hito.entidad_tipo)) return "documentos";
  if (["validacion_humana", "ejecucion_regla", "vinculo_documental"].includes(hito.entidad_tipo)) return "datos";
  if (["tarea", "decision", "ciclo_revision"].includes(hito.entidad_tipo) || hito.accion.startsWith("tramite_")) return "revision";
  return "todo";
}

/** RF-22: historial del trámite con acceso a la versión de cada evento y a la evidencia. */
export function Historial() {
  const id = useIdTramite();
  const linea = useLineaTiempo(id);
  const ciclos = useCiclos(id);
  const [filtro, setFiltro] = useState<keyof typeof FILTROS>("todo");
  const [fuente, setFuente] = useState<Fuente | null>(null);

  // Decisiones visibles para quien consulta: solo a ellas se enlaza la evidencia (PD-03).
  const decisiones = useMemo(
    () => new Set((ciclos.data ?? []).flatMap((c) => c.tareas.map((t) => t.decision_id))),
    [ciclos.data],
  );

  if (linea.isPending) return <Cargando />;
  if (linea.isError) return <ErrorConsulta error={linea.error} reintentar={() => void linea.refetch()} />;
  const hitos = [...linea.data].reverse().filter((h) => filtro === "todo" || categoria(h) === filtro);

  return (
    <Panel
      titulo="Historial del trámite"
      descripcion="Cada acción registrada con su actor, instante, resultado y versión relacionada."
      acciones={
        <Selector aria-label="Filtrar eventos" value={filtro} onChange={(e) => setFiltro(e.target.value as keyof typeof FILTROS)} className="w-56">
          {Object.entries(FILTROS).map(([clave, rotulo]) => (
            <option key={clave} value={clave}>{rotulo}</option>
          ))}
        </Selector>
      }
    >
      {hitos.length === 0 ? <Vacio titulo="Sin eventos para este filtro" /> : null}
      <ol className="relative space-y-1 border-l border-borde pl-5">
        {hitos.map((h) => (
          <li key={h.id} className="relative py-2">
            <span className="absolute top-3.5 -left-[1.5rem] size-2.5 rounded-full border-2 border-superficie bg-borde-fuerte" aria-hidden />
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm">
                <span className="font-medium">{rotuloAccion(h.accion)}</span>
                <span className="text-tenue"> · <Persona id={h.actor_id} sistema={h.actor_tipo === "sistema"} /></span>
                {h.resultado !== "exito" ? <Insignia tono="peligro" className="ml-2">Rechazada</Insignia> : null}
              </p>
              <time className="text-xs text-tenue" dateTime={h.ocurrido_en}>{fechaHora(h.ocurrido_en)}</time>
            </div>
            <div className="mt-1 flex flex-wrap gap-3 text-xs">
              {h.version ? (
                <button type="button" className="inline-flex items-center gap-1 text-primario hover:underline" onClick={() => setFuente({ versionId: h.version!.version_id, titulo: `Versión v${h.version!.version_numero}` })}>
                  <FileText className="size-3.5" aria-hidden /> Versión v{h.version.version_numero}
                </button>
              ) : null}
              {h.entidad_tipo === "decision" && decisiones.has(h.entidad_id) ? (
                <Link to={`/decisiones/${h.entidad_id}/evidencia`} className="inline-flex items-center gap-1 font-medium text-primario hover:underline">
                  <Scale className="size-3.5" aria-hidden /> Evidencia de la decisión
                </Link>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
      <DialogoFuente tramiteId={id} fuente={fuente} alCerrar={() => setFuente(null)} />
    </Panel>
  );
}
