import { ArrowRight } from "lucide-react";
import { Link } from "react-router";

import { useTareas, useTareasSinAsignar, useTramites } from "@/api/consultas";
import type { Tramite } from "@/api/tipos";
import { InsigniaEstado } from "@/componentes/dominio";
import { Encabezado } from "@/componentes/marco";
import { Panel } from "@/componentes/ui/panel";
import { Cargando, ErrorConsulta, Vacio } from "@/componentes/ui/estados";
import { ESTADO_TAREA, ESTADO_TRAMITE } from "@/lib/dominio";
import { useSesion } from "@/lib/sesion";

import { TablaTramites } from "./Tramites";

/** Próxima acción del responsable según el estado del trámite (§3.4.1). */
const PROXIMA: Partial<Record<Tramite["estado"], string>> = {
  borrador: "Incorporar y validar la documentación; luego enviar a validación",
  pendiente_validacion: "Completar las validaciones y confirmar el flujo de revisión",
  pendiente_aprobacion: "En revisión por los aprobadores",
  observado: "Revisar la observación y subsanar",
};

export function Inicio() {
  const { yo, tiene } = useSesion();
  const tramites = useTramites();
  const tareas = useTareas();
  const sinAsignar = useTareasSinAsignar(tiene("administrador_operativo"));
  const abiertas = tareas.data?.filter((t) => t.estado === "pendiente") ?? [];
  const accionables = tramites.data?.filter((t) => t.responsable_id === yo?.id && PROXIMA[t.estado]) ?? [];

  return (
    <>
      <Encabezado titulo={`Hola${yo?.nombre_visible ? `, ${yo.nombre_visible.split(" ")[0]}` : ""}`} descripcion="Lo que requiere tu atención." />
      <div className="grid gap-6 lg:grid-cols-2">
        {tiene("revisor_aprobador") ? (
          <Panel titulo="Tareas pendientes de decisión" acciones={<Link to="/tareas" className="text-sm text-primario hover:underline">Ver bandeja</Link>}>
            {tareas.isPending ? <Cargando /> : null}
            {tareas.isError ? <ErrorConsulta error={tareas.error} /> : null}
            {tareas.data && abiertas.length === 0 ? <Vacio titulo="No tenés tareas pendientes" /> : null}
            <ul className="divide-y divide-borde">
              {abiertas.map((t) => (
                <li key={t.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{t.nombre}</p>
                    <p className="text-sm text-tenue">{t.tramite.titulo}</p>
                  </div>
                  <Link to={`/tareas/${t.id}`} className="inline-flex items-center gap-1 text-sm text-primario hover:underline">
                    Revisar <ArrowRight className="size-3.5" />
                  </Link>
                </li>
              ))}
            </ul>
          </Panel>
        ) : null}
        {tiene("responsable_tramite") ? (
          <Panel titulo="Trámites con una acción tuya">
            {tramites.isPending ? <Cargando /> : null}
            {tramites.data && accionables.length === 0 ? <Vacio titulo="Nada pendiente" /> : null}
            <ul className="divide-y divide-borde">
              {accionables.map((t) => (
                <li key={t.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <Link to={`/tramites/${t.id}`} className="font-medium text-primario hover:underline">{t.titulo}</Link>
                    <p className="text-sm text-tenue">{PROXIMA[t.estado]}</p>
                  </div>
                  <InsigniaEstado catalogo={ESTADO_TRAMITE} valor={t.estado} />
                </li>
              ))}
            </ul>
          </Panel>
        ) : null}
        {tiene("administrador_operativo") ? (
          <Panel titulo="Coordinación" descripcion="Sin acceso al contenido documental (RF-24)." acciones={<Link to="/administracion" className="text-sm text-primario hover:underline">Administración</Link>}>
            {sinAsignar.isPending ? <Cargando /> : null}
            {sinAsignar.data?.length === 0 ? <Vacio titulo="No hay tareas sin asignar" /> : null}
            <ul className="divide-y divide-borde">
              {sinAsignar.data?.map((t) => (
                <li key={t.id} className="flex items-center justify-between gap-3 py-3">
                  <span>
                    {t.nombre} · <span className="text-tenue">TR-{t.tramite.id}</span>
                  </span>
                  <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
                </li>
              ))}
            </ul>
          </Panel>
        ) : null}
      </div>
      {tiene("responsable_tramite") && tramites.data?.length ? (
        <div className="mt-8">
          <h2 className="mb-3 text-lg">Todos tus trámites</h2>
          <TablaTramites tramites={tramites.data} />
        </div>
      ) : null}
    </>
  );
}
