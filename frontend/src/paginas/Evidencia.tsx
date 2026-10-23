/**
 * «Evidencia de la decisión» (PD-03, PD-06, V1 a V4). Parte de una decisión concreta y
 * recorre sus relaciones: tarea → ciclo → versiones consideradas → datos validados vigentes
 * al decidir → controles registrados en DECISION_CONTROL. Todo proviene de un único
 * `GET /decisiones/{id}/evidencia`: la vista no infiere relaciones que la API no devuelva.
 */
import { ArrowLeft, ChevronRight, Download, FileText, Info, Scale } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { Link, useParams } from "react-router";

import { useEvidencia } from "@/api/consultas";
import type { Ejecucion, Evidencia as TipoEvidencia, ValidacionEvidencia } from "@/api/tipos";
import { BotonFuente, InsigniaEstado, Persona, ResultadoControl, TextoLocalizador } from "@/componentes/dominio";
import { FirmaAplicada } from "@/componentes/firma";
import { DialogoFuente, type Fuente } from "@/componentes/visor";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Cargando, ErrorConsulta } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Dato, Panel } from "@/componentes/ui/panel";
import { DECISION, ESTADO_CICLO, ESTADO_TAREA, MOTIVO_AUSENCIA, rotuloAccion, rotuloCampo, TIPO_DOCUMENTAL, TIPO_VALIDACION, type Tono } from "@/lib/dominio";
import { fechaHora, valorLegible } from "@/lib/formatos";
import { cn } from "@/lib/utilidades";

function descargar(evidencia: TipoEvidencia) {
  const blob = new Blob([JSON.stringify(evidencia, null, 2)], { type: "application/json" });
  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(blob);
  enlace.download = `evidencia-decision-${evidencia.decision.id}.json`;
  enlace.click();
  URL.revokeObjectURL(enlace.href);
}

function valorMostrado(v: ValidacionEvidencia): string {
  if (v.tipo === "ausente") return MOTIVO_AUSENCIA[v.motivo_ausencia ?? "no_consta"];
  if (v.campo === "tipo_documental" && v.valor_validado) return TIPO_DOCUMENTAL[v.valor_validado as keyof typeof TIPO_DOCUMENTAL] ?? v.valor_validado;
  return valorLegible(v.campo, v.valor_validado);
}

const PASOS = [
  ["decision", "Decisión"],
  ["tarea", "Tarea"],
  ["ciclo", "Ciclo"],
  ["versiones", "Versiones"],
  ["datos", "Datos validados"],
  ["controles", "Controles"],
] as const;

export function Evidencia() {
  const id = Number(useParams().decisionId);
  const evidencia = useEvidencia(id);
  const [controlElegido, setControlElegido] = useState<number | null>(null);
  const [fuente, setFuente] = useState<Fuente | null>(null);

  const entradasElegidas = useMemo(() => {
    const control = evidencia.data?.controles.find((c) => c.id === controlElegido);
    return new Set(control?.valores.map((v) => v.validacion_id) ?? []);
  }, [evidencia.data, controlElegido]);
  const versionesElegidas = useMemo(() => {
    const control = evidencia.data?.controles.find((c) => c.id === controlElegido);
    return new Set(control?.versiones.map((v) => v.version_id) ?? []);
  }, [evidencia.data, controlElegido]);

  if (evidencia.isPending) return <Cargando texto="Reconstruyendo la evidencia…" />;
  if (evidencia.isError) return <ErrorConsulta error={evidencia.error} reintentar={() => void evidencia.refetch()} />;
  const e = evidencia.data;
  const decision = DECISION[e.decision.tipo];
  const advertencias = e.controles.filter((c) => c.resultado === "advertencia");
  const porDocumento = new Map<number, ValidacionEvidencia[]>();
  for (const v of e.validaciones) porDocumento.set(v.documento_id, [...(porDocumento.get(v.documento_id) ?? []), v]);
  const nombreDocumento = new Map(e.versiones.map((v) => [v.documento_id, v.documento_nombre]));
  const conteos: Record<(typeof PASOS)[number][0], string> = {
    decision: decision.rotulo,
    tarea: e.tarea.nombre,
    ciclo: `Ciclo ${e.ciclo.numero}`,
    versiones: String(e.versiones.length),
    datos: String(e.validaciones.length),
    controles: String(e.controles.length),
  };

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/tramites/${e.tramite.id}/historial`} className="inline-flex items-center gap-1 text-sm text-tenue hover:text-texto">
          <ArrowLeft className="size-4" /> {e.tramite.titulo}
        </Link>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <h1 className="inline-flex items-center gap-2 text-2xl">
            <Scale className="size-6 text-primario" aria-hidden /> Evidencia de la decisión
          </h1>
          <Boton variante="secundario" onClick={() => descargar(e)}>
            <Download /> Exportar JSON
          </Boton>
        </div>
      </div>

      <Aviso tono="info" titulo="Reconstrucción al momento de decidir">
        Versiones, datos validados y controles son los que existían cuando se tomó esta decisión; los
        cambios posteriores no la modifican.
        {e.ciclo.estado === "desplazado" ? " Después, un cambio documental desplazó este ciclo." : ""}
      </Aviso>

      {/* Ficha: responde quién, cuándo, qué, por qué y sobre qué información. */}
      <Panel>
        <dl className="grid gap-x-8 gap-y-4 sm:grid-cols-2 lg:grid-cols-4">
          <Dato rotulo="Decisión"><Insignia tono={decision.tono as Tono}>{decision.rotulo}</Insignia></Dato>
          <Dato rotulo="Quién decidió"><Persona id={e.decision.actor_id} /></Dato>
          <Dato rotulo="Cuándo">{fechaHora(e.decision.decidida_en)}</Dato>
          <Dato rotulo="Tarea">{e.tarea.nombre} (paso {e.tarea.orden})</Dato>
          <Dato rotulo="Motivo" className="sm:col-span-2 lg:col-span-4">
            {e.decision.motivo ?? <span className="text-tenue">Sin motivo registrado (no es obligatorio al aprobar)</span>}
          </Dato>
          <Dato rotulo="Ciclo de revisión">Ciclo {e.ciclo.numero} · <InsigniaEstado catalogo={ESTADO_CICLO} valor={e.ciclo.estado} /></Dato>
          <Dato rotulo="Versiones consideradas">{e.versiones.length}</Dato>
          <Dato rotulo="Datos validados">{e.validaciones.length}</Dato>
          <Dato rotulo="Advertencias a la vista">{advertencias.length ? <Insignia tono="advertencia">{advertencias.length}</Insignia> : "Ninguna"}</Dato>
        </dl>
      </Panel>

      {/* Cadena navegable: cada eslabón lleva a su sección. */}
      <nav aria-label="Cadena de la evidencia" className="flex flex-wrap items-center gap-1 rounded-lg border border-borde bg-superficie px-4 py-3 text-sm">
        {PASOS.map(([ancla, rotulo], i) => (
          <Fragment key={ancla}>
            {i > 0 ? <ChevronRight className="size-4 text-tenue" aria-hidden /> : null}
            <a href={`#${ancla}`} className="rounded-md px-2 py-1 hover:bg-neutro-suave">
              <span className="text-tenue">{rotulo}:</span> <span className="font-medium">{conteos[ancla]}</span>
            </a>
          </Fragment>
        ))}
      </nav>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel id="tarea" titulo="Tarea y ciclo">
          <ul id="ciclo" className="divide-y divide-borde">
            {e.tareas_del_ciclo.map((t) => (
              <li key={t.id} className={cn("flex items-center justify-between gap-3 py-2.5 text-sm", t.id === e.tarea.id && "font-medium")}>
                <span>
                  {t.orden}. {t.nombre} · <span className="text-tenue">{t.asignada_a_id ? <Persona id={t.asignada_a_id} /> : "Sin asignar"}</span>
                </span>
                <span className="flex items-center gap-2">
                  <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
                  {t.decision_id && t.decision_id !== e.decision.id ? (
                    <Link to={`/decisiones/${t.decision_id}/evidencia`} className="text-xs text-primario hover:underline">Ver su evidencia</Link>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel id="versiones" titulo="Versiones consideradas" descripcion="El conjunto exacto del ciclo, no las versiones vigentes hoy (V1).">
          <ul className="divide-y divide-borde">
            {e.versiones.map((v) => (
              <li key={v.version_id} className={cn("flex items-center justify-between gap-3 py-2.5 text-sm", versionesElegidas.has(v.version_id) && "bg-primario-suave/60")}>
                <span className="inline-flex items-center gap-2">
                  <FileText className="size-4 text-tenue" aria-hidden /> {v.documento_nombre}
                  <Insignia tono="neutro">v{v.version_numero}</Insignia>
                </span>
                <BotonFuente onClick={() => setFuente({ versionId: v.version_id, titulo: `${v.documento_nombre} · v${v.version_numero}` })}>Ver original</BotonFuente>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel id="controles" titulo="Controles considerados" descripcion="Ejecuciones registradas en DECISION_CONTROL al decidir (V4). Elegí una para ver sus entradas resaltadas.">
        {e.controles.length === 0 ? <p className="text-sm text-tenue">No había reglas aplicables al decidir (PD-02.4).</p> : null}
        <ul className="grid gap-3 md:grid-cols-2">
          {[...e.controles].sort((a, b) => a.codigo_regla.localeCompare(b.codigo_regla)).map((c: Ejecucion) => (
            <li key={c.id}>
              <button
                type="button"
                aria-pressed={controlElegido === c.id}
                onClick={() => setControlElegido(controlElegido === c.id ? null : c.id)}
                className={cn(
                  "w-full rounded-md border px-4 py-3 text-left text-sm transition-colors",
                  controlElegido === c.id ? "border-primario bg-primario-suave/50" : "border-borde hover:bg-neutro-suave/60",
                )}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="font-medium">{c.codigo_regla.split("-")[0]} · {c.descripcion}</span>
                  <ResultadoControl resultado={c.resultado} />
                </span>
                <span className="mt-1 block text-tenue">{c.explicacion}</span>
                <span className="mt-1 block text-xs text-tenue">Versión de regla {c.version_regla} · {fechaHora(c.ejecutada_en)}</span>
              </button>
            </li>
          ))}
        </ul>
        {advertencias.length ? (
          <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-tenue">
            <Info className="size-3.5" aria-hidden /> Las advertencias son información de apoyo: la decisión la tomó una persona.
          </p>
        ) : null}
      </Panel>

      <Panel id="datos" titulo="Datos validados al decidir" descripcion="Valor sugerido, valor validado, quién lo validó, cuándo, en qué versión y con qué fuente (V2).">
        <div className="space-y-6">
          {[...porDocumento.entries()].map(([documentoId, validaciones]) => (
            <div key={documentoId}>
              <h3 className="mb-2 text-sm font-semibold">{nombreDocumento.get(documentoId) ?? `Documento ${documentoId}`}</h3>
              <div className="overflow-x-auto rounded-md border border-borde">
                <table className="w-full text-sm">
                  <thead className="bg-neutro-suave/60 text-left text-xs text-tenue uppercase">
                    <tr>
                      <th className="px-3 py-2 font-medium">Dato</th>
                      <th className="px-3 py-2 font-medium">Sugerido</th>
                      <th className="px-3 py-2 font-medium">Validado</th>
                      <th className="px-3 py-2 font-medium">Quién y cuándo</th>
                      <th className="px-3 py-2 font-medium">Fuente</th>
                    </tr>
                  </thead>
                  <tbody>
                    {validaciones.map((v) => {
                      const localizador = v.localizador_validado ?? v.localizador_sugerido;
                      return (
                        <tr key={v.validacion_id} className={cn("border-t border-borde", entradasElegidas.has(v.validacion_id) && "bg-advertencia-suave")}>
                          <td className="px-3 py-2 font-medium">{rotuloCampo(v.campo)}</td>
                          <td className="px-3 py-2 text-tenue">
                            {v.valor_sugerido ? (v.campo === "tipo_documental" ? TIPO_DOCUMENTAL[v.valor_sugerido as keyof typeof TIPO_DOCUMENTAL] ?? v.valor_sugerido : valorLegible(v.campo, v.valor_sugerido)) : "—"}
                          </td>
                          <td className="px-3 py-2">
                            <span className="font-medium">{valorMostrado(v)}</span>{" "}
                            <Insignia tono={TIPO_VALIDACION[v.tipo].tono}>{TIPO_VALIDACION[v.tipo].rotulo}</Insignia>
                          </td>
                          <td className="px-3 py-2 text-tenue">
                            <Persona id={v.validador_id} /> · {fechaHora(v.validado_en)}
                          </td>
                          <td className="px-3 py-2">
                            <span className="flex flex-col gap-1 text-xs">
                              <TextoLocalizador localizador={localizador} />
                              {localizador ? (
                                <BotonFuente onClick={() => setFuente({ versionId: v.version_id, pagina: localizador.pagina, fragmento: localizador.fragmento, titulo: rotuloCampo(v.campo) })} />
                              ) : null}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {e.firma ? (
        <Panel titulo="Firma digital simulada" descripcion="Aplicada a una versión de este ciclo aprobado (RF-23, V11).">
          <FirmaAplicada firma={e.firma} documento={e.versiones.find((v) => v.version_id === e.firma?.version_id)?.documento_nombre} />
        </Panel>
      ) : null}

      <Panel titulo="Eventos relacionados" descripcion="Registros de auditoría del ciclo, sus tareas y decisiones, y de los datos y controles listados.">
        <ol className="space-y-1.5 text-sm">
          {e.eventos.map((ev) => (
            <li key={ev.id} className="flex flex-wrap justify-between gap-2">
              <span>
                {rotuloAccion(ev.accion)} · <span className="text-tenue"><Persona id={ev.actor_id} sistema={ev.actor_tipo === "sistema"} /></span>
              </span>
              <time className="text-xs text-tenue" dateTime={ev.ocurrido_en}>{fechaHora(ev.ocurrido_en)}</time>
            </li>
          ))}
        </ol>
      </Panel>

      <DialogoFuente tramiteId={e.tramite.id} fuente={fuente} alCerrar={() => setFuente(null)} />
    </div>
  );
}
