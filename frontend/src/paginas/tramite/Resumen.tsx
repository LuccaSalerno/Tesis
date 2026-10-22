import { ArrowRight, Scale, Send, Wrench } from "lucide-react";
import { Link } from "react-router";

import { useCiclos, useControles, useTransicion } from "@/api/consultas";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Cargando, mensajeDeError } from "@/componentes/ui/estados";
import { Dato, Panel } from "@/componentes/ui/panel";
import { DECISION, ESTADO_CICLO, ESTADO_TAREA, TIPO_DOCUMENTAL } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

const PROXIMA = {
  borrador: "Incorporá y validá la documentación. Cuando el conjunto esté completo, envialo a validación.",
  pendiente_validacion: "Completá la validación de cada documento y confirmá el flujo de revisión sugerido.",
  pendiente_aprobacion: "Los revisores asignados están resolviendo sus tareas.",
  observado: "Un revisor registró una observación. Revisá el motivo y subsaná el trámite.",
  aprobado: "Trámite aprobado.",
  cerrado: "Trámite cerrado.",
  cancelado: "Trámite cancelado.",
} as const;

export function Resumen() {
  const id = useIdTramite();
  const { tramite, esResponsable } = useContextoTramite();
  const ciclos = useCiclos(id);
  const controles = useControles(id);
  const transicion = useTransicion(id);
  const advertencias = controles.data?.vigentes.filter((c) => c.resultado === "advertencia") ?? [];
  const ultimo = ciclos.data?.at(-1);

  return (
    <div className="grid gap-6 xl:grid-cols-3">
      <div className="space-y-6 xl:col-span-2">
        <Panel titulo="Próxima acción">
          <p className="text-sm">{PROXIMA[tramite.estado]}</p>
          {esResponsable && (tramite.estado === "borrador" || tramite.estado === "observado") ? (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {tramite.estado === "borrador" ? (
                <Boton disabled={transicion.isPending || tramite.documentos.length === 0} onClick={() => transicion.mutate("envio-a-validacion")}>
                  <Send /> Enviar a validación
                </Boton>
              ) : (
                <Boton variante="advertencia" disabled={transicion.isPending} onClick={() => transicion.mutate("subsanacion")}>
                  <Wrench /> Subsanar y volver a validación
                </Boton>
              )}
              {tramite.estado === "borrador" && tramite.documentos.length === 0 ? (
                <span className="text-sm text-tenue">Hace falta al menos un documento incorporado.</span>
              ) : null}
            </div>
          ) : null}
          {tramite.estado === "pendiente_validacion" && esResponsable ? (
            <Link to="../revision" className="mt-3 inline-flex items-center gap-1 text-sm text-primario hover:underline">
              Ir a la confirmación del flujo <ArrowRight className="size-3.5" />
            </Link>
          ) : null}
          {transicion.isError ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(transicion.error)} /> : null}
        </Panel>

        <Panel titulo="Documentación vigente" acciones={<Link to="../documentos" className="text-sm text-primario hover:underline">Ver documentos</Link>}>
          {tramite.documentos.length === 0 ? <p className="text-sm text-tenue">Sin documentos incorporados.</p> : null}
          <ul className="divide-y divide-borde">
            {tramite.documentos.map((d) => (
              <li key={d.id} className="flex items-center justify-between py-2.5 text-sm">
                <span className="font-medium">{d.nombre}</span>
                <span className="text-tenue">
                  {d.tipo ? TIPO_DOCUMENTAL[d.tipo] : "Clasificación sin validar"} · v{d.version_vigente.numero} vigente
                </span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="space-y-6">
        <Panel titulo="Controles de consistencia">
          {controles.isPending ? <Cargando /> : null}
          {controles.data ? (
            advertencias.length ? (
              <Aviso tono="advertencia" titulo={`${advertencias.length} advertencia${advertencias.length > 1 ? "s" : ""}`}>
                Información de apoyo para la revisión: no decide el trámite.
                <Link to="../vinculos" className="mt-1 block text-primario hover:underline">Ver el detalle</Link>
              </Aviso>
            ) : (
              <p className="text-sm text-tenue">Sin advertencias vigentes.</p>
            )
          ) : null}
        </Panel>
        <Panel titulo="Revisión">
          {ciclos.isPending ? <Cargando /> : null}
          {ciclos.data?.length === 0 ? <p className="text-sm text-tenue">Todavía no se confirmó un flujo de revisión.</p> : null}
          {ultimo ? (
            <dl className="space-y-3">
              <Dato rotulo={`Ciclo ${ultimo.numero}`}>
                <InsigniaEstado catalogo={ESTADO_CICLO} valor={ultimo.estado} />
              </Dato>
              {ultimo.tareas.map((t) => (
                <div key={t.id} className="flex items-start justify-between gap-2 text-sm">
                  <div>
                    <p className="font-medium">{t.nombre}</p>
                    <p className="text-xs text-tenue">
                      {t.asignada_a_id ? <Persona id={t.asignada_a_id} /> : "Sin asignar"} · {fechaHora(t.actualizada_en)}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
                    {t.decision_id ? (
                      <Link to={`/decisiones/${t.decision_id}/evidencia`} className="inline-flex items-center gap-1 text-xs text-primario hover:underline">
                        <Scale className="size-3" /> Evidencia
                      </Link>
                    ) : null}
                  </div>
                </div>
              ))}
            </dl>
          ) : null}
          <p className="mt-4 text-xs text-tenue">Decisiones posibles: {DECISION.aprobacion.rotulo} u {DECISION.observacion.rotulo.toLowerCase()} con motivo.</p>
        </Panel>
      </div>
    </div>
  );
}
