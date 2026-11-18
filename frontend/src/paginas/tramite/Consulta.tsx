/**
 * Consulta asistida (Fig. 3.7, RF-13, RN-04): respuestas con cita a fragmentos de las
 * versiones autorizadas o abstención explícita cuando no hay evidencia suficiente. El
 * historial muestra las consultas propias.
 */
import { Quote, Send } from "lucide-react";
import { type FormEvent, useState } from "react";

import { useConsultar, useConsultas } from "@/api/consultas";
import type { Consulta as TipoConsulta } from "@/api/tipos";
import { BotonFuente } from "@/componentes/dominio";
import { DialogoFuente, type Fuente } from "@/componentes/visor";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { AreaTexto } from "@/componentes/ui/campos";
import { EstadoConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Panel } from "@/componentes/ui/panel";
import { esSimulado } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useIdTramite } from "./MarcoTramite";

const ABSTENCION = {
  evidencia_insuficiente: "La documentación autorizada no contiene evidencia suficiente para responder.",
  sin_citas_validas: "La respuesta no pudo sustentarse con citas verificables, así que no se muestra.",
  sin_fragmentos: "No hay documentación procesada e indexada para consultar en este trámite.",
} as const;

function Respuesta({ consulta, alVerFuente }: { consulta: TipoConsulta; alVerFuente: (f: Fuente) => void }) {
  const modelo = esSimulado(consulta.modelo_generacion) ? "simulación local" : consulta.modelo_generacion ?? "sin invocar el modelo";
  return (
    <article className="space-y-3 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-medium">{consulta.pregunta}</p>
        <time className="text-xs text-tenue">{fechaHora(consulta.creado_en)}</time>
      </div>
      {consulta.suficiente ? (
        <div className="space-y-3">
          {consulta.afirmaciones.map((a, i) => (
            <div key={i} className="rounded-md border border-info/25 bg-info-suave/50 px-4 py-3 text-sm">
              <p>{a.texto}</p>
              <ul className="mt-2 space-y-2">
                {a.referencias.map((r) => (
                  <li key={r.fragmento_id} className="rounded border border-borde bg-superficie px-3 py-2 text-xs">
                    <p className="flex items-center gap-1 font-medium">
                      <Quote className="size-3" aria-hidden /> {r.documento_nombre} · v{r.version_numero}
                      {r.pagina ? ` · página ${r.pagina}` : ""}
                    </p>
                    <p className="mt-1 line-clamp-3 text-tenue">{r.contenido}</p>
                    <BotonFuente onClick={() => alVerFuente({ versionId: r.version_id, pagina: r.pagina, fragmento: r.contenido.slice(0, 120), titulo: r.documento_nombre })} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <Aviso tono="advertencia" titulo="No hay evidencia suficiente para responder">
          {consulta.motivo_abstencion ? ABSTENCION[consulta.motivo_abstencion] : null} Reformulá la pregunta o incorporá la documentación que la sustente.
        </Aviso>
      )}
      <p className="text-xs text-tenue">
        {consulta.fragmentos_recuperados} fragmentos recuperados · {modelo}
      </p>
    </article>
  );
}

export function Consulta() {
  const id = useIdTramite();
  const historial = useConsultas(id);
  const consultar = useConsultar(id);
  const [pregunta, setPregunta] = useState("");
  const [fuente, setFuente] = useState<Fuente | null>(null);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await consultar.mutateAsync(pregunta.trim());
    setPregunta("");
  }

  return (
    <div className="space-y-6">
      <Panel titulo="Consulta documental" descripcion="Preguntá sobre las versiones vigentes autorizadas de este trámite. Cada afirmación muestra su fuente.">
        <form onSubmit={enviar} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="sr-only" htmlFor="pregunta">Pregunta</label>
          <AreaTexto id="pregunta" value={pregunta} onChange={(e) => setPregunta(e.target.value)} placeholder="Por ejemplo: ¿hasta cuándo está vigente el contrato?" maxLength={2000} className="min-h-12" />
          <Boton type="submit" disabled={!pregunta.trim() || consultar.isPending}>
            <Send /> {consultar.isPending ? "Consultando…" : "Consultar"}
          </Boton>
        </form>
        {consultar.isError ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(consultar.error)} /> : null}
      </Panel>
      <Panel titulo="Tus consultas">
        <EstadoConsulta consulta={historial} />
        {historial.data?.length === 0 ? <Vacio titulo="Todavía no hiciste consultas" /> : null}
        <div className="divide-y divide-borde">
          {historial.data?.map((c) => <Respuesta key={c.id} consulta={c} alVerFuente={setFuente} />)}
        </div>
      </Panel>
      <DialogoFuente tramiteId={id} fuente={fuente} alCerrar={() => setFuente(null)} />
    </div>
  );
}
