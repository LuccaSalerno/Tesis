/**
 * Administración operativa (Tabla 3.II, RF-19, RF-24, RF-25): estado general,
 * plantillas de flujo, tareas sin asignar y cuentas. Sin acceso al contenido documental.
 */
import { ArrowDown, ArrowRight, ArrowUp, Pencil, Plus, RotateCcw, Trash2, UserCheck, UserX } from "lucide-react";
import { type FormEvent, Fragment, useState } from "react";

import {
  useAsignar,
  useCambiarCierre,
  useCambiarNombre,
  useCrearPlantilla,
  useCuentas,
  useEstadoGeneral,
  usePlantillas,
  useSuprimir,
  useTareasSinAsignar,
} from "@/api/consultas";
import type { Cuenta, EstadoGeneral as TipoEstadoGeneral, Plantilla } from "@/api/tipos";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { AbrirDialogo, CerrarDialogo, ContenidoDialogo, RaizDialogo } from "@/componentes/ui/dialogo";
import { Encabezado } from "@/componentes/marco";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Entrada, Etiqueta, Selector } from "@/componentes/ui/campos";
import { Cargando, EstadoConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { ESTADO_TAREA, ESTADO_TRABAJO, ESTADO_TRAMITE, ROL } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";
import { useSesion } from "@/lib/sesion";

function nombreCuenta(c: Cuenta) {
  return c.nombre_visible ?? `Usuario #${c.id}`;
}

const ALCANCES = [
  { alcance: "contrato", titulo: "Trámites con contrato" },
  { alcance: "general", titulo: "Demás trámites" },
] as const;

type Paso = { nombre: string; revisor: string };

/** Los pasos de una plantilla, en orden, con quién resuelve cada uno. */
function PasosPlantilla({ plantilla }: { plantilla: Plantilla }) {
  return (
    <ol className="flex flex-wrap items-center gap-2 text-sm">
      {plantilla.pasos.map((paso) => (
        <Fragment key={paso.orden}>
          {paso.orden > 1 ? <ArrowRight className="size-4 text-tenue" aria-hidden /> : null}
          <li className="rounded-md border border-borde px-3 py-1.5">
            <span className="font-medium">{paso.nombre}</span> · <Persona id={paso.revisor_por_defecto_id} />
          </li>
        </Fragment>
      ))}
    </ol>
  );
}

/**
 * Las plantillas son inmutables: editar crea la versión siguiente y
 * reemplaza a la activa. De uno a tres pasos; el último lo resuelve alguien con cierre.
 */
function EditorPlantilla({
  alcance,
  base,
  version,
  revisores,
  alTerminar,
}: {
  alcance: Plantilla["alcance"];
  base: Plantilla | undefined;
  version: number;
  revisores: Cuenta[];
  alTerminar: () => void;
}) {
  const crear = useCrearPlantilla();
  const [nombre, setNombre] = useState(base?.nombre ?? "");
  const [pasos, setPasos] = useState<Paso[]>(
    base?.pasos.map((p) => ({ nombre: p.nombre, revisor: String(p.revisor_por_defecto_id) })) ?? [{ nombre: "", revisor: "" }],
  );
  const cambiar = (i: number, cambio: Partial<Paso>) => setPasos(pasos.map((p, j) => (j === i ? { ...p, ...cambio } : p)));
  const mover = (i: number, destino: number) => {
    const copia = [...pasos];
    [copia[i], copia[destino]] = [copia[destino]!, copia[i]!];
    setPasos(copia);
  };
  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await crear.mutateAsync({
      nombre: nombre.trim(),
      alcance,
      pasos: pasos.map((p) => ({ nombre: p.nombre.trim(), revisor_por_defecto_id: Number(p.revisor) })),
    });
    alTerminar();
  }
  return (
    <form onSubmit={enviar} className="space-y-3">
      <div className="max-w-sm space-y-1">
        <Etiqueta htmlFor={`nombre-${alcance}`}>Nombre del flujo</Etiqueta>
        <Entrada id={`nombre-${alcance}`} value={nombre} onChange={(e) => setNombre(e.target.value)} required />
      </div>
      <ol className="space-y-2">
        {pasos.map((paso, i) => {
          // Solo quien tiene autorización de cierre puede resolver el último paso.
          const elegibles = i === pasos.length - 1 ? revisores.filter((r) => r.autorizacion_cierre) : revisores;
          const valor = elegibles.some((r) => String(r.id) === paso.revisor) ? paso.revisor : "";
          return (
            <li key={i} className="flex flex-wrap items-center gap-2">
              <span className="w-5 text-sm text-tenue">{i + 1}.</span>
              <Entrada className="min-w-40 flex-1" aria-label={`Nombre del paso ${i + 1}`} placeholder="Nombre del paso" value={paso.nombre} onChange={(e) => cambiar(i, { nombre: e.target.value })} required />
              <Selector className="min-w-40 flex-1" aria-label={`Quién resuelve el paso ${i + 1}`} value={valor} onChange={(e) => cambiar(i, { revisor: e.target.value })} required>
                <option value="">Elegí a alguien…</option>
                {elegibles.map((r) => <option key={r.id} value={r.id}>{nombreCuenta(r)}</option>)}
              </Selector>
              <span className="flex">
                <Boton variante="sutil" tamano="icono" aria-label={`Subir el paso ${i + 1}`} disabled={i === 0} onClick={() => mover(i, i - 1)}><ArrowUp /></Boton>
                <Boton variante="sutil" tamano="icono" aria-label={`Bajar el paso ${i + 1}`} disabled={i === pasos.length - 1} onClick={() => mover(i, i + 1)}><ArrowDown /></Boton>
                <Boton variante="sutil" tamano="icono" aria-label={`Quitar el paso ${i + 1}`} disabled={pasos.length === 1} onClick={() => setPasos(pasos.filter((_, j) => j !== i))}><Trash2 /></Boton>
              </span>
            </li>
          );
        })}
      </ol>
      {crear.isError ? <Aviso tono="peligro" titulo={mensajeDeError(crear.error)} /> : null}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Boton variante="secundario" tamano="chico" disabled={pasos.length >= 3} onClick={() => setPasos([...pasos, { nombre: "", revisor: "" }])}><Plus /> Agregar paso</Boton>
        <span className="flex gap-2">
          <Boton variante="sutil" onClick={alTerminar}>Cancelar</Boton>
          <Boton type="submit" disabled={crear.isPending}>{base ? `Guardar como versión ${version}` : "Crear flujo"}</Boton>
        </span>
      </div>
    </form>
  );
}

/** Una plantilla de una versión anterior vuelve a regir como versión nueva, con los mismos pasos. */
function VolverAUsar({ plantilla, version }: { plantilla: Plantilla; version: number }) {
  const crear = useCrearPlantilla();
  return (
    <>
      <Boton
        tamano="chico"
        variante="sutil"
        disabled={crear.isPending}
        onClick={() =>
          crear.mutate({
            nombre: plantilla.nombre,
            alcance: plantilla.alcance,
            pasos: plantilla.pasos.map((p) => ({ nombre: p.nombre, revisor_por_defecto_id: p.revisor_por_defecto_id })),
          })
        }
      >
        <RotateCcw /> Volver a usar como v{version}
      </Boton>
      {crear.isError ? <p className="w-full text-xs text-peligro">{mensajeDeError(crear.error)}</p> : null}
    </>
  );
}

/** El flujo vigente de un alcance, su edición y sus versiones anteriores. */
function FlujoDelAlcance({ alcance, titulo, plantillas, revisores }: { alcance: Plantilla["alcance"]; titulo: string; plantillas: Plantilla[]; revisores: Cuenta[] }) {
  const [editando, setEditando] = useState(false);
  const versiones = plantillas.filter((p) => p.alcance === alcance).sort((a, b) => b.version - a.version);
  const activa = versiones.find((p) => p.activa);
  const anteriores = versiones.filter((p) => !p.activa);
  const siguiente = (versiones[0]?.version ?? 0) + 1;
  return (
    <section className="rounded-md border border-borde p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-medium">
          {titulo}
          {activa ? <span className="ml-2 text-sm font-normal text-tenue">{activa.nombre} · v{activa.version}</span> : null}
        </h3>
        {!editando ? (
          <Boton tamano="chico" variante="secundario" onClick={() => setEditando(true)}>
            {activa ? <><Pencil /> Editar</> : <><Plus /> Crear flujo</>}
          </Boton>
        ) : null}
      </div>
      <div className="mt-3">
        {editando ? (
          <EditorPlantilla alcance={alcance} base={activa} version={siguiente} revisores={revisores} alTerminar={() => setEditando(false)} />
        ) : activa ? (
          <PasosPlantilla plantilla={activa} />
        ) : (
          <p className="text-sm text-tenue">Sin flujo configurado.</p>
        )}
      </div>
      {anteriores.length && !editando ? (
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-tenue">Versiones anteriores ({anteriores.length})</summary>
          <ul className="mt-2 space-y-3">
            {anteriores.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-2">
                <span className="w-full text-tenue">{p.nombre} · v{p.version}</span>
                <PasosPlantilla plantilla={p} />
                <VolverAUsar plantilla={p} version={siguiente} />
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}

/** RF-25: permiso adicional para aplicar la firma simulada y cerrar; lo otorga el administrador. */
function AutorizacionCierre({ cuenta }: { cuenta: Cuenta }) {
  const cambiar = useCambiarCierre();
  if (cuenta.estado !== "habilitada" || !cuenta.roles.includes("revisor_aprobador")) {
    return <span className="text-tenue">—</span>;
  }
  return (
    <div className="flex items-center gap-2">
      <Insignia tono={cuenta.autorizacion_cierre ? "exito" : "neutro"}>{cuenta.autorizacion_cierre ? "Otorgada" : "No"}</Insignia>
      <Boton
        tamano="chico"
        variante="sutil"
        disabled={cambiar.isPending}
        aria-label={`${cuenta.autorizacion_cierre ? "Retirar" : "Otorgar"} la autorización de cierre a ${nombreCuenta(cuenta)}`}
        onClick={() => cambiar.mutate({ usuario: cuenta.id, otorgada: !cuenta.autorizacion_cierre })}
      >
        {cuenta.autorizacion_cierre ? "Retirar" : "Otorgar"}
      </Boton>
      {cambiar.isError ? <span className="text-xs text-peligro">{mensajeDeError(cambiar.error)}</span> : null}
    </div>
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
        <td className="px-3 py-2">—</td>
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
          <Entrada aria-label={`Nombre visible de la cuenta ${cuenta.id}`} value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={120} className="h-8 w-44" />
          <Boton type="submit" tamano="chico" variante="secundario" disabled={cambiar.isPending || nombre === (cuenta.nombre_visible ?? "")}>Guardar</Boton>
        </form>
        {cambiar.isError ? <p className="mt-1 text-xs text-peligro">{mensajeDeError(cambiar.error)}</p> : null}
      </td>
      <td className="px-3 py-2 text-tenue">{cuenta.roles.map((r) => ROL[r]).join(", ") || "Sin roles"}</td>
      <td className="px-3 py-2"><AutorizacionCierre cuenta={cuenta} /></td>
      <td className="px-3 py-2"><Insignia tono={cuenta.estado === "habilitada" ? "exito" : "neutro"}>{cuenta.estado}</Insignia></td>
      <td className="px-3 py-2 text-right">{propia ? null : <SuprimirCuenta cuenta={cuenta} />}</td>
    </tr>
  );
}

export function Administracion() {
  const plantillas = usePlantillas();
  const cuentas = useCuentas();
  const sinAsignar = useTareasSinAsignar(true);
  const estado = useEstadoGeneral();
  const { yo } = useSesion();
  const asignar = useAsignar();
  const [eleccion, setEleccion] = useState<Record<number, string>>({});
  const revisores = cuentas.data?.filter((c) => c.estado === "habilitada" && c.roles.includes("revisor_aprobador")) ?? [];

  return (
    <>
      <Encabezado titulo="Administración operativa" descripcion="Coordinación del trabajo sin acceso al contenido documental." />
      <div className="space-y-6">
        <Panel titulo="Estado general" descripcion="Trámites, tareas y procesamiento, sin títulos ni contenido documental.">
          <EstadoConsulta consulta={estado} />
          {estado.data ? <EstadoGeneral datos={estado.data} /> : null}
        </Panel>

        <Panel titulo="Tareas sin asignar" descripcion="Por ejemplo, cuando el revisor por defecto es el propio responsable.">
          <EstadoConsulta consulta={sinAsignar} />
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

        <Panel titulo="Flujos de revisión" descripcion="Quién revisa cada tipo de trámite y en qué orden.">
          {plantillas.isPending ? <Cargando /> : null}
          {plantillas.data ? (
            <div className="space-y-4">
              {ALCANCES.map(({ alcance, titulo }) => (
                <FlujoDelAlcance key={alcance} alcance={alcance} titulo={titulo} plantillas={plantillas.data} revisores={revisores} />
              ))}
            </div>
          ) : null}
        </Panel>

        <Panel titulo="Cuentas" descripcion="El nombre visible identifica a las personas en la interfaz y en la evidencia.">
          <EstadoConsulta consulta={cuentas} />
          {cuentas.data ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[46rem] text-sm">
                <thead className="text-left text-xs text-tenue uppercase">
                  <tr><th className="px-3 py-2">Cuenta</th><th className="px-3 py-2">Nombre visible</th><th className="px-3 py-2">Roles</th><th className="px-3 py-2">Autorización de cierre</th><th className="px-3 py-2">Estado</th><th className="px-3 py-2" /></tr>
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
