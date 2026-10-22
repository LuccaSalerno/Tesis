import { Link } from "react-router";

import { useTareas } from "@/api/consultas";
import { InsigniaEstado } from "@/componentes/dominio";
import { Encabezado } from "@/componentes/marco";
import { Cargando, ErrorConsulta, Vacio } from "@/componentes/ui/estados";
import { ESTADO_TAREA, ESTADO_TRAMITE } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

/** Bandeja del revisor/aprobador (§3.4.1): primero lo que admite decisión. */
export function Tareas() {
  const tareas = useTareas();
  const orden = (estado: string) => (estado === "pendiente" ? 0 : estado === "en_espera" ? 1 : 2);
  const lista = [...(tareas.data ?? [])].sort((a, b) => orden(a.estado) - orden(b.estado) || b.id - a.id);
  return (
    <>
      <Encabezado titulo="Mis tareas" descripcion="Tareas asignadas a vos en los ciclos de revisión." />
      {tareas.isPending ? <Cargando /> : null}
      {tareas.isError ? <ErrorConsulta error={tareas.error} reintentar={() => void tareas.refetch()} /> : null}
      {tareas.data?.length === 0 ? <Vacio titulo="No tenés tareas asignadas" /> : null}
      {lista.length ? (
        <div className="overflow-x-auto rounded-lg border border-borde bg-superficie">
          <table className="w-full text-sm">
            <thead className="border-b border-borde bg-neutro-suave/60 text-left text-xs text-tenue uppercase">
              <tr>
                <th className="px-4 py-2.5 font-medium">Tarea</th>
                <th className="px-4 py-2.5 font-medium">Trámite</th>
                <th className="px-4 py-2.5 font-medium">Estado</th>
                <th className="px-4 py-2.5 font-medium">Actualizada</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((t) => (
                <tr key={t.id} className="border-b border-borde last:border-0">
                  <td className="px-4 py-3">
                    <Link to={`/tareas/${t.id}`} className="font-medium text-primario hover:underline">{t.nombre}</Link>
                    <span className="ml-2 text-xs text-tenue">ciclo {t.ciclo.numero}</span>
                  </td>
                  <td className="px-4 py-3">
                    {t.tramite.titulo} <span className="ml-1"><InsigniaEstado catalogo={ESTADO_TRAMITE} valor={t.tramite.estado} /></span>
                  </td>
                  <td className="px-4 py-3"><InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} /></td>
                  <td className="px-4 py-3 text-tenue">{fechaHora(t.actualizada_en)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
