/**
 * Revisión del trámite (RF-17, RF-18, Tabla 3.VI): flujo sugerido inactivo hasta que el
 * responsable lo confirma, y ciclos de revisión con sus versiones y tareas. Las decisiones de
 * ciclos anteriores se muestran como historial, nunca como vigentes.
 */
import { ArrowRight, CheckCircle2, ListChecks, Scale, Send } from "lucide-react";
import { Fragment } from "react";
import { Link } from "react-router";

import { useCiclos, useConfirmarFlujo, useFlujoSugerido, useTransicion } from "@/api/consultas";
import type { Ciclo } from "@/api/tipos";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Cargando, ErrorConsulta, EstadoConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { ESTADO_CICLO, ESTADO_TAREA } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

/** RF-17: el flujo se sugiere con los documentos validados y no crea tareas hasta confirmarse. */
function FlujoSugerido({ tramiteId }: { tramiteId: number }) {
  const { tramite } = useContextoTramite();
  const sugerido = useFlujoSugerido(tramiteId);
  const confirmar = useConfirmarFlujo(tramiteId);
  if (sugerido.isPending) return <Cargando />;
  if (sugerido.isError) return <ErrorConsulta error={sugerido.error} />;
  const s = sugerido.data;
  const faltan = s.documentos_sin_validar;
  const nombre = (id: number) => tramite.documentos.find((d) => d.id === id)?.nombre ?? `Documento ${id}`;
  return (
    <Panel titulo="Flujo de revisión">
      {faltan.length ? (
        // La plantilla depende de la clasificación validada: hasta entonces no se sugiere ninguna.
        <Aviso tono="advertencia" titulo="Validá los documentos para ver el flujo">
          <ul className="mt-1 list-disc pl-5">
            {faltan.map((d) => (
              <li key={d}>
                <Link to={`../documentos/${d}`} className="text-primario hover:underline">{nombre(d)}</Link>
              </li>
            ))}
          </ul>
        </Aviso>
      ) : s.plantilla_id === null ? (
        <Aviso tono="advertencia" titulo={`No hay un flujo configurado para ${s.alcance === "contrato" ? "trámites con contrato" : "este tipo de trámite"}`}>
          Lo configura el administrador operativo.
        </Aviso>
      ) : (
        <>
          <p className="text-sm text-tenue">{s.plantilla_nombre} · v{s.version_plantilla}</p>
          <ol className="mt-3 space-y-2">
            {s.pasos.map((p) => (
              <li key={p.orden} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-borde px-3 py-2 text-sm">
                <span>{p.orden}. {p.nombre}</span>
                <span className="text-tenue">{p.asignada_a_id ? <Persona id={p.asignada_a_id} /> : "Sin asignar: lo asigna el administrador"}</span>
              </li>
            ))}
          </ol>
          {confirmar.isError ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(confirmar.error)} /> : null}
          <div className="mt-4 flex justify-end">
            <Boton
              disabled={confirmar.isPending}
              onClick={() => confirmar.mutate({ plantilla_id: s.plantilla_id!, version_plantilla: s.version_plantilla! })}
            >
              <ListChecks /> Confirmar el flujo y enviar a aprobación
            </Boton>
          </div>
        </>
      )}
    </Panel>
  );
}

/** Los pasos del ciclo en orden, con quién los tiene y en qué quedaron (RF-18, RF-20). */
function RecorridoCiclo({ tareas }: { tareas: Ciclo["tareas"] }) {
  const ordenadas = [...tareas].sort((a, b) => a.orden - b.orden);
  return (
    <ol className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
      {ordenadas.map((t) => (
        <Fragment key={t.id}>
          {t.orden > 1 ? (
            <li aria-hidden className="hidden self-center text-tenue sm:block"><ArrowRight className="size-4" /></li>
          ) : null}
          <li className={`flex flex-col rounded-md border p-3 text-sm sm:flex-1 ${t.estado === "pendiente" ? "border-primario" : "border-borde"}`}>
            <p className="text-xs text-tenue">Paso {t.orden}</p>
            <p className="font-medium">{t.nombre}</p>
            <p className="text-xs text-tenue">{t.asignada_a_id ? <Persona id={t.asignada_a_id} /> : "Sin asignar"}</p>
            <div className="mt-auto flex flex-col items-start gap-1.5 pt-2">
              <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
              {t.decision_id ? (
                <Link to={`/decisiones/${t.decision_id}/evidencia`} className="inline-flex items-center gap-1 text-xs text-primario hover:underline">
                  <Scale className="size-3" /> Evidencia de la decisión
                </Link>
              ) : null}
            </div>
          </li>
        </Fragment>
      ))}
    </ol>
  );
}

function TarjetaCiclo({ ciclo, ultimo }: { ciclo: Ciclo; ultimo: boolean }) {
  return (
    <Panel
      titulo={
        <span className="flex items-center gap-2">
          Ciclo {ciclo.numero} <InsigniaEstado catalogo={ESTADO_CICLO} valor={ciclo.estado} />
          {!ultimo ? <Insignia tono="neutro">Historial</Insignia> : null}
        </span>
      }
      descripcion={`Confirmado por el responsable el ${fechaHora(ciclo.confirmado_en)}${ciclo.concluido_en ? ` · concluyó el ${fechaHora(ciclo.concluido_en)}` : ""}`}
      className={!ultimo ? "opacity-90" : undefined}
    >
      <h3 className="mb-2 text-xs font-medium text-tenue uppercase">Recorrido</h3>
      <RecorridoCiclo tareas={ciclo.tareas} />
      <h3 className="mt-5 mb-2 text-xs font-medium text-tenue uppercase">Versiones consideradas</h3>
      <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        {ciclo.versiones.map((v) => (
          <li key={v.version_id}>{v.documento_nombre} · v{v.version_numero}</li>
        ))}
      </ul>
    </Panel>
  );
}

export function Revision() {
  const id = useIdTramite();
  const { tramite, esResponsable } = useContextoTramite();
  const ciclos = useCiclos(id);
  const transicion = useTransicion(id);
  return (
    <div className="space-y-6">
      {tramite.estado === "borrador" && esResponsable ? (
        <Panel titulo="Enviar a validación" descripcion="Cuando el conjunto documental esté completo.">
          <Boton disabled={transicion.isPending || tramite.documentos.length === 0} onClick={() => transicion.mutate("envio-a-validacion")}>
            <Send /> Enviar a validación
          </Boton>
          {transicion.isError ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(transicion.error)} /> : null}
        </Panel>
      ) : null}
      {tramite.estado === "pendiente_validacion" && esResponsable ? <FlujoSugerido tramiteId={id} /> : null}
      {tramite.estado === "aprobado" ? (
        <Aviso tono="info" titulo="Trámite aprobado">
          <CheckCircle2 className="mr-1 inline size-4" /> Todas las tareas del último ciclo fueron aprobadas.
        </Aviso>
      ) : null}
      <EstadoConsulta consulta={ciclos} />
      {ciclos.data?.length === 0 ? <Vacio titulo="Todavía no hay ciclos de revisión" /> : null}
      {[...(ciclos.data ?? [])].reverse().map((c, i) => (
        <TarjetaCiclo key={c.id} ciclo={c} ultimo={i === 0} />
      ))}
    </div>
  );
}
