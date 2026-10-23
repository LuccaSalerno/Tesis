/**
 * Administración operativa (Tabla 3.II, RF-19, RF-24, RF-25, RC-P03): estado general,
 * plantillas de flujo, tareas sin asignar y cuentas. Sin acceso al contenido documental.
 */
import { Plus, Trash2, UserCheck, UserX } from "lucide-react";
import { type FormEvent, useState } from "react";

import {
  useAsignar,
  useCambiarNombre,
  useCrearPlantilla,
  useCuentas,
  useEstadoGeneral,
  usePlantillas,
  useSuprimir,
  useTareasSinAsignar,
} from "@/api/consultas";
import type { Cuenta, EstadoGeneral as TipoEstadoGeneral } from "@/api/tipos";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { AbrirDialogo, CerrarDialogo, ContenidoDialogo, RaizDialogo } from "@/componentes/ui/dialogo";
import { Encabezado } from "@/componentes/marco";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Entrada, Etiqueta, Selector } from "@/componentes/ui/campos";
import { Cargando, ErrorConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { ESTADO_TAREA, ESTADO_TRABAJO, ESTADO_TRAMITE, ROL } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";
import { useSesion } from "@/lib/sesion";

function nombreCuenta(c: Cuenta) {
  return c.nombre_visible ?? `Usuario #${c.id}`;
}

function NuevaPlantilla({ revisores }: { revisores: Cuenta[] }) {
  const crear = useCrearPlantilla();
  const [nombre, setNombre] = useState("Revisión de contratos");
  const [alcance, setAlcance] = useState<"contrato" | "general">("contrato");
  const [pasos, setPasos] = useState([{ nombre: "Revisión legal", revisor: "" }, { nombre: "Aprobación final", revisor: "" }]);
  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await crear.mutateAsync({
      nombre: nombre.trim(),
      alcance,
      pasos: pasos.map((p) => ({ nombre: p.nombre.trim(), revisor_por_defecto_id: Number(p.revisor) })),
    });
  }
  return (
    <form onSubmit={enviar} className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <Etiqueta htmlFor="nombre-plantilla">Nombre</Etiqueta>
          <Entrada id="nombre-plantilla" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
        </div>
        <div className="space-y-1">
          <Etiqueta htmlFor="alcance">Se sugiere para</Etiqueta>
          <Selector id="alcance" value={alcance} onChange={(e) => setAlcance(e.target.value as "contrato" | "general")}>
            <option value="contrato">Trámites con contrato</option>
            <option value="general">Los demás trámites</option>
          </Selector>
        </div>
      </div>
      <ol className="space-y-2">
        {pasos.map((paso, i) => (
          <li key={i} className="grid gap-2 sm:grid-cols-[2rem_1fr_1fr_auto] sm:items-center">
            <span className="text-sm text-tenue">{i + 1}.</span>
            <Entrada aria-label={`Nombre del paso ${i + 1}`} value={paso.nombre} onChange={(e) => setPasos(pasos.map((p, j) => (j === i ? { ...p, nombre: e.target.value } : p)))} required />
            <Selector aria-label={`Revisor del paso ${i + 1}`} value={paso.revisor} onChange={(e) => setPasos(pasos.map((p, j) => (j === i ? { ...p, revisor: e.target.value } : p)))} required>
              <option value="">Revisor/Aprobador…</option>
              {revisores.map((r) => (
                <option key={r.id} value={r.id}>{nombreCuenta(r)}{r.autorizacion_cierre ? " (autorización de cierre)" : ""}</option>
              ))}
            </Selector>
            <Boton variante="sutil" tamano="icono" aria-label="Quitar paso" disabled={pasos.length === 1} onClick={() => setPasos(pasos.filter((_, j) => j !== i))}><Trash2 /></Boton>
          </li>
        ))}
      </ol>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Boton variante="secundario" tamano="chico" disabled={pasos.length >= 3} onClick={() => setPasos([...pasos, { nombre: "", revisor: "" }])}><Plus /> Agregar paso</Boton>
        <Boton type="submit" disabled={crear.isPending}>Crear plantilla</Boton>
      </div>
      <p className="text-xs text-tenue">De uno a tres pasos. El revisor del último paso necesita autorización de cierre. Reemplaza a la plantilla activa del mismo alcance.</p>
      {crear.isError ? <Aviso tono="peligro" titulo={mensajeDeError(crear.error)} /> : null}
      {crear.isSuccess ? <Aviso tono="info" titulo="Plantilla creada y activa" /> : null}
    </form>
  );
}

/** RF-24: conteos y metadatos; ni títulos ni contenido documental. */
function EstadoGeneral({ datos }: { datos: TipoEstadoGeneral }) {
  const conteos = (titulo: string, valores: [string, number][]) => (
    <div>
      <p className="text-xs font-medium tracking-wide text-tenue uppercase">{titulo}</p>
      <ul className="mt-1 space-y-0.5 text-sm">
        {valores.length === 0 ? <li className="text-tenue">Sin registros</li> : null}
        {valores.map(([rotulo, n]) => (
          <li key={rotulo} className="flex justify-between gap-3"><span>{rotulo}</span><span className="tabular-nums">{n}</span></li>
        ))}
      </ul>
    </div>
  );
  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-3">
        {conteos("Trámites", Object.entries(datos.tramites_por_estado).map(([e, n]) => [ESTADO_TRAMITE[e as keyof typeof ESTADO_TRAMITE]?.rotulo ?? e, n ?? 0]))}
        {conteos("Tareas", [
          ...Object.entries(datos.tareas_por_estado).map(([e, n]): [string, number] => [ESTADO_TAREA[e as keyof typeof ESTADO_TAREA]?.rotulo ?? e, n ?? 0]),
          ["Abiertas sin asignar", datos.tareas_sin_asignar],
        ])}
        {conteos("Procesamiento", Object.entries(datos.trabajos_por_estado).map(([e, n]) => [ESTADO_TRABAJO[e as keyof typeof ESTADO_TRABAJO]?.rotulo ?? e, n ?? 0]))}
      </div>
      {datos.tareas_bloqueadas.length ? (
        <Aviso tono="advertencia" titulo={`${datos.tareas_bloqueadas.length} tarea(s) asignadas a cuentas no habilitadas`}>
          Reasignalas desde la lista de tareas:{" "}
          {datos.tareas_bloqueadas.map((t) => `tarea ${t.tarea_id} (TR-${t.tramite_id})`).join(", ")}.
        </Aviso>
      ) : null}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-tenue uppercase">
            <tr>
              <th className="px-3 py-2">Trámite</th><th className="px-3 py-2">Estado</th><th className="px-3 py-2">Responsable</th>
              <th className="px-3 py-2">Documentos</th><th className="px-3 py-2">Tareas abiertas</th><th className="px-3 py-2">Actualizado</th>
            </tr>
          </thead>
          <tbody>
            {datos.tramites.map((t) => (
              <tr key={t.id} className="border-t border-borde">
                <td className="px-3 py-2">TR-{t.id}</td>
                <td className="px-3 py-2"><InsigniaEstado catalogo={ESTADO_TRAMITE} valor={t.estado} /></td>
                <td className="px-3 py-2"><Persona id={t.responsable_id} /></td>
                <td className="px-3 py-2 tabular-nums">{t.documentos}</td>
                <td className="px-3 py-2 tabular-nums">{t.tareas_abiertas}{t.tareas_sin_asignar ? ` (${t.tareas_sin_asignar} sin asignar)` : ""}</td>
                <td className="px-3 py-2 text-tenue">{fechaHora(t.actualizado_en)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** RF-25: supresión irreversible, con confirmación explícita. */
function SuprimirCuenta({ cuenta }: { cuenta: Cuenta }) {
  const suprimir = useSuprimir();
  const [abierto, setAbierto] = useState(false);
  return (
    <RaizDialogo open={abierto} onOpenChange={setAbierto}>
      <AbrirDialogo asChild>
        <Boton tamano="chico" variante="sutil" aria-label={`Suprimir la cuenta ${cuenta.id}`}><UserX /> Suprimir</Boton>
      </AbrirDialogo>
      <ContenidoDialogo
        titulo={`Suprimir la cuenta #${cuenta.id}`}
        descripcion="Elimina la cuenta de Cognito y sus datos identificatorios. Sus intervenciones quedan atribuidas al identificador interno. No se puede deshacer."
      >
        {suprimir.isError ? <Aviso className="mb-3" tono="peligro" titulo={mensajeDeError(suprimir.error)} /> : null}
        <div className="flex justify-end gap-2">
          <CerrarDialogo asChild><Boton variante="secundario">Volver</Boton></CerrarDialogo>
          <Boton variante="peligro" disabled={suprimir.isPending} onClick={() => suprimir.mutate(cuenta.id, { onSuccess: () => setAbierto(false) })}>
            Suprimir definitivamente
          </Boton>
        </div>
      </ContenidoDialogo>
    </RaizDialogo>
  );
}

function FilaCuenta({ cuenta, propia }: { cuenta: Cuenta; propia: boolean }) {
  const cambiar = useCambiarNombre();
  const [nombre, setNombre] = useState(cuenta.nombre_visible ?? "");
  if (cuenta.estado === "suprimida") {
    return (
      <tr className="border-t border-borde text-tenue">
        <td className="px-3 py-2">#{cuenta.id}</td>
        <td className="px-3 py-2">Cuenta suprimida</td>
        <td className="px-3 py-2">Sin roles</td>
        <td className="px-3 py-2"><Insignia tono="neutro">suprimida</Insignia></td>
        <td className="px-3 py-2" />
      </tr>
    );
  }
  return (
    <tr className="border-t border-borde">
      <td className="px-3 py-2">#{cuenta.id}</td>
      <td className="px-3 py-2">
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); cambiar.mutate({ usuario: cuenta.id, nombre: nombre.trim() || null }); }}>
          <Entrada aria-label={`Nombre visible de la cuenta ${cuenta.id}`} value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={120} className="h-8" />
          <Boton type="submit" tamano="chico" variante="secundario" disabled={cambiar.isPending || nombre === (cuenta.nombre_visible ?? "")}>Guardar</Boton>
        </form>
        {cambiar.isError ? <p className="mt-1 text-xs text-peligro">{mensajeDeError(cambiar.error)}</p> : null}
      </td>
      <td className="px-3 py-2 text-tenue">{cuenta.roles.map((r) => ROL[r]).join(", ") || "Sin roles"}</td>
      <td className="px-3 py-2"><Insignia tono={cuenta.estado === "habilitada" ? "exito" : "neutro"}>{cuenta.estado}</Insignia></td>
      <td className="px-3 py-2 text-right">{propia ? null : <SuprimirCuenta cuenta={cuenta} />}</td>
    </tr>
  );
}

export function Administracion() {
  const plantillas = usePlantillas(true);
  const cuentas = useCuentas(true);
  const sinAsignar = useTareasSinAsignar(true);
  const estado = useEstadoGeneral(true);
  const { yo } = useSesion();
  const asignar = useAsignar();
  const [eleccion, setEleccion] = useState<Record<number, string>>({});
  const revisores = cuentas.data?.filter((c) => c.estado === "habilitada" && c.roles.includes("revisor_aprobador")) ?? [];

  return (
    <>
      <Encabezado titulo="Administración operativa" descripcion="Coordinación del trabajo sin acceso al contenido documental." />
      <div className="space-y-6">
        <Panel titulo="Estado general" descripcion="Trámites, tareas y procesamiento, sin títulos ni contenido documental (RF-24).">
          {estado.isPending ? <Cargando /> : null}
          {estado.isError ? <ErrorConsulta error={estado.error} /> : null}
          {estado.data ? <EstadoGeneral datos={estado.data} /> : null}
        </Panel>

        <Panel titulo="Tareas sin asignar" descripcion="Por ejemplo, cuando el revisor por defecto es el propio responsable (RC-P03.3).">
          {sinAsignar.isPending ? <Cargando /> : null}
          {sinAsignar.isError ? <ErrorConsulta error={sinAsignar.error} /> : null}
          {sinAsignar.data?.length === 0 ? <Vacio titulo="No hay tareas sin asignar" /> : null}
          <ul className="divide-y divide-borde">
            {sinAsignar.data?.map((t) => (
              <li key={t.id} className="flex flex-wrap items-center gap-3 py-3 text-sm">
                <span className="min-w-56 flex-1">
                  <span className="font-medium">{t.nombre}</span> · TR-{t.tramite.id}
                  <span className="block text-xs text-tenue">Ciclo {t.ciclo.numero} · creada {fechaHora(t.creada_en)}</span>
                </span>
                <InsigniaEstado catalogo={ESTADO_TAREA} valor={t.estado} />
                <Selector aria-label="Asignar a" className="w-56" value={eleccion[t.id] ?? ""} onChange={(e) => setEleccion({ ...eleccion, [t.id]: e.target.value })}>
                  <option value="">Asignar a…</option>
                  {revisores.map((r) => <option key={r.id} value={r.id}>{nombreCuenta(r)}</option>)}
                </Selector>
                <Boton tamano="chico" disabled={!eleccion[t.id] || asignar.isPending} onClick={() => asignar.mutate({ tarea: t.id, usuario: Number(eleccion[t.id]) })}>
                  <UserCheck /> Asignar
                </Boton>
              </li>
            ))}
          </ul>
          {asignar.isError ? <Aviso tono="peligro" titulo={mensajeDeError(asignar.error)} /> : null}
        </Panel>

        <Panel titulo="Plantillas de flujo" descripcion="Versionadas e inmutables; una activa por alcance (RC-P03.1).">
          {plantillas.isPending ? <Cargando /> : null}
          <ul className="mb-6 divide-y divide-borde">
            {plantillas.data?.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-3 py-2.5 text-sm">
                <span className="min-w-56 flex-1 font-medium">{p.nombre} <span className="font-normal text-tenue">v{p.version} · {p.alcance === "contrato" ? "contratos" : "general"}</span></span>
                <span className="text-tenue">{p.pasos.map((s) => s.nombre).join(" → ")}</span>
                <Insignia tono={p.activa ? "exito" : "neutro"}>{p.activa ? "Activa" : "Inactiva"}</Insignia>
              </li>
            ))}
          </ul>
          {cuentas.data ? <NuevaPlantilla revisores={revisores} /> : null}
        </Panel>

        <Panel titulo="Cuentas" descripcion="El nombre visible identifica a las personas en la interfaz y en la evidencia.">
          {cuentas.isPending ? <Cargando /> : null}
          {cuentas.isError ? <ErrorConsulta error={cuentas.error} /> : null}
          {cuentas.data ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-tenue uppercase">
                  <tr><th className="px-3 py-2">Cuenta</th><th className="px-3 py-2">Nombre visible</th><th className="px-3 py-2">Roles</th><th className="px-3 py-2">Estado</th><th className="px-3 py-2" /></tr>
                </thead>
                <tbody>{cuentas.data.map((c) => <FilaCuenta key={c.id} cuenta={c} propia={c.id === yo?.id} />)}</tbody>
              </table>
            </div>
          ) : null}
        </Panel>
      </div>
    </>
  );
}
