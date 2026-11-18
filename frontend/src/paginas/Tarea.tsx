/**
 * Revisión de una tarea (Fig. 3.8, RF-20, RN-08). Reúne el contexto para decidir: las
 * versiones del ciclo, los controles que se registrarán con la decisión y las advertencias,
 * presentadas como información de apoyo y separadas del panel de decisión. La observación
 * exige un motivo. El backend vuelve a verificar quién puede decidir.
 */
import { ArrowLeft, Check, FileText, MessageSquareWarning, Scale } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useParams } from "react-router";

import { useDecidir, useTarea } from "@/api/consultas";
import type { TareaDetalle } from "@/api/tipos";
import { BotonFuente, InsigniaEstado, Persona, TarjetaControl } from "@/componentes/dominio";
import { DialogoFuente, type Fuente } from "@/componentes/visor";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { AreaTexto, Ayuda, Etiqueta } from "@/componentes/ui/campos";
import { ContenidoDialogo, RaizDialogo } from "@/componentes/ui/dialogo";
import { Cargando, ErrorConsulta, mensajeDeError } from "@/componentes/ui/estados";
import { Dato, Panel } from "@/componentes/ui/panel";
import { DECISION, ESTADO_CICLO, ESTADO_TAREA, ESTADO_TRAMITE } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";
import { useSesion } from "@/lib/sesion";

function PanelDecision({ tarea }: { tarea: TareaDetalle }) {
  const decidir = useDecidir(tarea.id);
  const [observando, setObservando] = useState(false);
  const [motivo, setMotivo] = useState("");

  async function observar(evento: FormEvent) {
    evento.preventDefault();
    await decidir.mutateAsync({ tipo: "observacion", motivo: motivo.trim() });
    setObservando(false);
  }

  return (
    <Panel titulo="Decisión" descripcion="Las advertencias informan; la decisión es tuya.">
      <div className="flex flex-wrap gap-3">
        <Boton variante="advertencia" onClick={() => setObservando(true)} disabled={decidir.isPending}>
          <MessageSquareWarning /> Observar
        </Boton>
        <Boton onClick={() => decidir.mutate({ tipo: "aprobacion" })} disabled={decidir.isPending}>
          <Check /> {decidir.isPending ? "Registrando…" : "Aprobar"}
        </Boton>
      </div>
      {decidir.isError && !observando ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(decidir.error)} /> : null}
      <RaizDialogo open={observando} onOpenChange={setObservando}>
        <ContenidoDialogo titulo="Observar la tarea" descripcion="Solicitá una corrección sobre las versiones evaluadas. El motivo queda registrado.">
          <form onSubmit={observar} className="space-y-4">
            <div className="text-sm">
              <p className="text-xs font-medium text-tenue uppercase">Versiones consideradas</p>
              <p className="mt-1">{tarea.versiones.map((v) => `${v.documento_nombre} v${v.version_numero}`).join(" · ")}</p>
            </div>
            <div className="space-y-1.5">
              <Etiqueta htmlFor="motivo">Motivo de la observación</Etiqueta>
              <AreaTexto id="motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} required maxLength={5000} />
              <Ayuda>Obligatorio.</Ayuda>
            </div>
            {decidir.isError ? <Aviso tono="peligro" titulo={mensajeDeError(decidir.error)} /> : null}
            <div className="flex justify-end gap-2">
              <Boton variante="sutil" onClick={() => setObservando(false)}>Cancelar</Boton>
              <Boton type="submit" variante="advertencia" disabled={!motivo.trim() || decidir.isPending}>Registrar observación</Boton>
            </div>
          </form>
        </ContenidoDialogo>
      </RaizDialogo>
    </Panel>
  );
}

export function Tarea() {
  const id = Number(useParams().tareaId);
  const { yo } = useSesion();
  const tarea = useTarea(id);
  const [fuente, setFuente] = useState<Fuente | null>(null);
  if (tarea.isPending) return <Cargando />;
  if (tarea.isError) return <ErrorConsulta error={tarea.error} reintentar={() => void tarea.refetch()} />;
  const t = tarea.data;
  const advertencias = t.controles.filter((c) => c.resultado === "advertencia");
  const puedeDecidir = t.estado === "pendiente" && t.asignada_a_id === yo?.id && t.ciclo.estado === "en_curso";

  return (
    <div className="space-y-6">
      <div>
        <Link to="/tareas" className="inline-flex items-center gap-1 text-sm text-tenue hover:text-texto">
          <ArrowLeft className="size-4" /> Mis tareas
        </Link>
        <p className="mt-2 text-xs text-tenue uppercase">Tarea de revisión · paso {t.orden}</p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl">{t.nombre}</h1>
          <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
        </div>
        <p className="mt-1 text-sm">
          <Link to={`/tramites/${t.tramite.id}`} className="text-primario hover:underline">{t.tramite.titulo}</Link>{" "}
          <InsigniaEstado catalogo={ESTADO_TRAMITE} valor={t.tramite.estado} />
        </p>
      </div>

      {t.estado === "anulada" ? (
        <Aviso tono="neutro" titulo="La documentación del trámite cambió; esta tarea ya no admite decisiones" />
      ) : null}

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Panel titulo="Contexto para decidir">
            <dl className="grid gap-4 sm:grid-cols-3">
              <Dato rotulo="Ciclo">{t.ciclo.numero} · <InsigniaEstado catalogo={ESTADO_CICLO} valor={t.ciclo.estado} /></Dato>
              <Dato rotulo="Asignada a">{t.asignada_a_id ? <Persona id={t.asignada_a_id} /> : "Sin asignar"}</Dato>
              <Dato rotulo="Controles">{t.controles_pendientes ? "Pendientes" : `${t.controles.length} considerados`}</Dato>
            </dl>
            <h3 className="mt-5 mb-2 text-xs font-medium text-tenue uppercase">Documentos del ciclo</h3>
            <ul className="divide-y divide-borde text-sm">
              {t.versiones.map((v) => (
                <li key={v.version_id} className="flex items-center justify-between py-2">
                  <span className="inline-flex items-center gap-2"><FileText className="size-4 text-tenue" /> {v.documento_nombre} · v{v.version_numero}</span>
                  <BotonFuente onClick={() => setFuente({ versionId: v.version_id, titulo: v.documento_nombre })}>Ver</BotonFuente>
                </li>
              ))}
            </ul>
            <Link to={`/tramites/${t.tramite.id}/documentos`} className="mt-3 inline-block text-sm text-primario hover:underline">
              Ver los datos validados y sus fuentes
            </Link>
          </Panel>

          {advertencias.length ? (
            <Aviso tono="advertencia" titulo={`${advertencias.length} advertencia${advertencias.length > 1 ? "s" : ""} de consistencia`}>
              Información de apoyo: no aprueba ni observa por sí sola.
            </Aviso>
          ) : null}
          <Panel titulo={t.decision ? "Controles registrados con la decisión" : "Controles que se registrarán con tu decisión"}>
            {t.controles.length === 0 ? <p className="text-sm text-tenue">No hay reglas aplicables a este conjunto.</p> : null}
            <ul className="space-y-3">
              {t.controles.map((c) => (
                <TarjetaControl key={`${c.codigo_regla}-${c.vinculo_id}-${c.ejecucion?.id}`} control={c} alVerFuente={setFuente} />
              ))}
            </ul>
          </Panel>
        </div>

        <div className="space-y-6">
          {t.decision ? (
            <Panel titulo="Decisión registrada">
              <dl className="space-y-3">
                <Dato rotulo="Resultado">{DECISION[t.decision.tipo].rotulo}</Dato>
                <Dato rotulo="Quién y cuándo"><Persona id={t.decision.actor_id} /> · {fechaHora(t.decision.decidida_en)}</Dato>
                {t.decision.motivo ? <Dato rotulo="Motivo">{t.decision.motivo}</Dato> : null}
              </dl>
              <Boton comoHijo variante="secundario" className="mt-4 w-full">
                <Link to={`/decisiones/${t.decision.id}/evidencia`}><Scale /> Evidencia de la decisión</Link>
              </Boton>
            </Panel>
          ) : puedeDecidir ? (
            <PanelDecision tarea={t} />
          ) : (
            <Panel titulo="Decisión">
              <p className="text-sm text-tenue">
                {t.estado === "en_espera" ? "Se habilita cuando se apruebe la tarea anterior." : "Esta tarea no admite decisiones en su estado actual."}
              </p>
            </Panel>
          )}
        </div>
      </div>
      <DialogoFuente tramiteId={t.tramite.id} fuente={fuente} alCerrar={() => setFuente(null)} />
    </div>
  );
}
