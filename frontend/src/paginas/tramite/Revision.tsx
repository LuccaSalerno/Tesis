/**
 * Revisión del trámite (RF-17, RF-18, Tabla 3.VI): flujo sugerido inactivo hasta que el
 * responsable lo confirma, y ciclos de revisión con sus versiones y tareas. Las decisiones de
 * ciclos anteriores se muestran como historial, nunca como vigentes.
 */
import { CheckCircle2, ListChecks, Scale, Send } from "lucide-react";
import { Link } from "react-router";

import { useCiclos, useConfirmarFlujo, useFlujoSugerido, useTransicion } from "@/api/consultas";
import type { Ciclo } from "@/api/tipos";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Cargando, ErrorConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { ESTADO_CICLO, ESTADO_TAREA } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

function FlujoSugerido({ tramiteId }: { tramiteId: number }) {
  const { tramite } = useContextoTramite();
  const sugerido = useFlujoSugerido(tramiteId, true);
  const confirmar = useConfirmarFlujo(tramiteId);
  if (sugerido.isPending) return <Cargando />;
  if (sugerido.isError) return <ErrorConsulta error={sugerido.error} />;
  const s = sugerido.data;
  const faltan = s.documentos_sin_validar;
  const nombre = (id: number) => tramite.documentos.find((d) => d.id === id)?.nombre ?? `Documento ${id}`;
  return (
    <Panel titulo="Flujo de revisión sugerido" descripcion="Se calcula según los tipos documentales y no crea tareas hasta que lo confirmás (RF-17).">
      {s.plantilla_id === null ? (
        <Aviso tono="advertencia" titulo="No hay una plantilla de flujo activa para este trámite">
          El administrador operativo debe configurar la plantilla {s.alcance === "contrato" ? "de contratos" : "general"}.
        </Aviso>
      ) : (
        <>
          <p className="text-sm">
            Plantilla <span className="font-medium">{s.plantilla_nombre}</span> (versión {s.version_plantilla})
          </p>
          <ol className="mt-3 space-y-2">
            {s.pasos.map((p) => (
              <li key={p.orden} className="flex items-center justify-between gap-3 rounded-md border border-borde px-3 py-2 text-sm">
                <span>{p.orden}. {p.nombre}</span>
                <span className="text-tenue">{p.asignada_a_id ? <Persona id={p.asignada_a_id} /> : "Sin asignar: lo asigna el administrador"}</span>
              </li>
            ))}
          </ol>
        </>
      )}
      {faltan.length ? (
        <Aviso className="mt-4" tono="advertencia" titulo="Faltan datos por resolver antes de confirmar">
          <ul className="mt-1 list-disc pl-5">
            {faltan.map((d) => (
              <li key={d}>
                <Link to={`../documentos/${d}`} className="text-primario hover:underline">{nombre(d)}</Link>: clasificación o campos sin validar o declarar ausentes.
              </li>
            ))}
          </ul>
        </Aviso>
      ) : null}
      {confirmar.isError ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(confirmar.error)} /> : null}
      <div className="mt-4 flex justify-end">
        <Boton
          disabled={s.plantilla_id === null || faltan.length > 0 || confirmar.isPending}
          onClick={() => confirmar.mutate({ plantilla_id: s.plantilla_id!, version_plantilla: s.version_plantilla! })}
        >
          <ListChecks /> Confirmar el flujo y enviar a aprobación
        </Boton>
      </div>
    </Panel>
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
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="mb-2 text-xs font-medium text-tenue uppercase">Versiones consideradas</h3>
          <ul className="space-y-1 text-sm">
            {ciclo.versiones.map((v) => (
              <li key={v.version_id}>{v.documento_nombre} · v{v.version_numero}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mb-2 text-xs font-medium text-tenue uppercase">Tareas</h3>
          <ul className="space-y-2">
            {ciclo.tareas.map((t) => (
              <li key={t.id} className="flex items-start justify-between gap-2 text-sm">
                <div>
                  <p className="font-medium">{t.orden}. {t.nombre}</p>
                  <p className="text-xs text-tenue">{t.asignada_a_id ? <Persona id={t.asignada_a_id} /> : "Sin asignar"}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
                  {t.decision_id ? (
                    <Link to={`/decisiones/${t.decision_id}/evidencia`} className="inline-flex items-center gap-1 text-xs text-primario hover:underline">
                      <Scale className="size-3" /> Evidencia de la decisión
                    </Link>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
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
        <Panel titulo="Enviar a validación" descripcion="Cuando el conjunto documental esté completo (Tabla 3.VI).">
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
      {ciclos.isPending ? <Cargando /> : null}
      {ciclos.isError ? <ErrorConsulta error={ciclos.error} /> : null}
      {ciclos.data?.length === 0 ? <Vacio titulo="Todavía no hay ciclos de revisión" /> : null}
      {[...(ciclos.data ?? [])].reverse().map((c, i) => (
        <TarjetaCiclo key={c.id} ciclo={c} ultimo={i === 0} />
      ))}
    </div>
  );
}
