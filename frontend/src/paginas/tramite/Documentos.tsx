import { CheckCircle2, FileUp, Layers, Loader2, PencilLine, Trash2, TriangleAlert } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router";

import { type Etapa, useCargarArchivo } from "@/api/cargas";
import { useArchivos, useDescartar, useIncorporar, useIncorporarVersion } from "@/api/consultas";
import type { Archivo } from "@/api/tipos";
import { InsigniaEstado } from "@/componentes/dominio";
import { ReintentarProcesamiento } from "@/componentes/reintento";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Entrada } from "@/componentes/ui/campos";
import { EstadoConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { CRITERIO_VERSION, ESTADO_TRABAJO, rotuloCampo, TIPO_DOCUMENTAL } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

const ETAPAS: Record<Etapa, string> = {
  autorizando: "Autorizando la carga…",
  transfiriendo: "Transfiriendo el archivo…",
  confirmando: "Verificando el archivo recibido…",
};

function Carga({ tramiteId }: { tramiteId: number }) {
  const [etapa, setEtapa] = useState<Etapa | null>(null);
  const [progreso, setProgreso] = useState<{ actual: number; total: number; nombre: string } | null>(null);
  const [resultado, setResultado] = useState<{ recibidos: number; fallidos: { nombre: string; motivo: string }[] } | null>(null);
  const entrada = useRef<HTMLInputElement>(null);
  const cargar = useCargarArchivo(tramiteId, setEtapa);

  // Varios archivos a la vez: se cargan de a uno, en el orden elegido, y un fallo no detiene
  // a los demás. Cada archivo sigue su propia autorización, transferencia y confirmación.
  async function cargarVarios(archivos: File[]) {
    setResultado(null);
    const fallidos: { nombre: string; motivo: string }[] = [];
    for (const [i, archivo] of archivos.entries()) {
      setProgreso({ actual: i + 1, total: archivos.length, nombre: archivo.name });
      try {
        await cargar.mutateAsync(archivo);
      } catch (error) {
        fallidos.push({ nombre: archivo.name, motivo: mensajeDeError(error) });
      } finally {
        setEtapa(null);
      }
    }
    setProgreso(null);
    setResultado({ recibidos: archivos.length - fallidos.length, fallidos });
  }

  return (
    <div className="rounded-md border border-dashed border-borde-fuerte bg-neutro-suave/40 px-4 py-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium">Cargar archivos</p>
          <p className="text-sm text-tenue">PDF o DOCX, hasta 20 MB cada uno. Podés elegir varios a la vez; el procesamiento sigue en segundo plano.</p>
        </div>
        <Boton onClick={() => entrada.current?.click()} disabled={progreso !== null}>
          {progreso ? <Loader2 className="animate-spin" /> : <FileUp />} Elegir archivos
        </Boton>
        <input
          ref={entrada}
          type="file"
          multiple
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="sr-only"
          aria-label="Archivos a cargar"
          onChange={(e) => {
            const archivos = Array.from(e.target.files ?? []);
            e.target.value = "";
            if (archivos.length) void cargarVarios(archivos);
          }}
        />
      </div>
      {progreso ? (
        <p className="mt-3 text-sm text-tenue" aria-live="polite">
          {progreso.total > 1 ? `Archivo ${progreso.actual} de ${progreso.total}, ${progreso.nombre}. ` : null}
          {etapa ? ETAPAS[etapa] : null}
        </p>
      ) : null}
      {resultado?.fallidos.map((f) => <Aviso key={f.nombre} className="mt-3" tono="peligro" titulo={`${f.nombre}: ${f.motivo}`} />)}
      {resultado && resultado.recibidos > 0 ? (
        <Aviso className="mt-3" tono="info" titulo={resultado.recibidos === 1 ? "Archivo recibido" : `${resultado.recibidos} archivos recibidos`}>
          {resultado.recibidos === 1 ? "Quedó pendiente" : "Quedaron pendientes"} de incorporación; podés seguir trabajando mientras se procesa.
        </Aviso>
      ) : null}
    </div>
  );
}

function Pendiente({ archivo, tramiteId }: { archivo: Archivo; tramiteId: number }) {
  const [nombre, setNombre] = useState(archivo.nombre.replace(/\.(pdf|docx)$/i, ""));
  const incorporar = useIncorporar(tramiteId);
  const comoVersion = useIncorporarVersion(tramiteId);
  const descartar = useDescartar(tramiteId);
  const trabajo = archivo.trabajo;
  const sugerida = archivo.sugerencia_version?.estado === "pendiente" ? archivo.sugerencia_version : null;
  const ocupado = incorporar.isPending || comoVersion.isPending || descartar.isPending;
  const error = incorporar.error ?? comoVersion.error ?? descartar.error;
  return (
    <li className="flex flex-wrap items-center gap-3 py-3">
      <div className="min-w-48 flex-1">
        <p className="font-medium">{archivo.nombre}</p>
        <p className="text-xs text-tenue">Cargado {fechaHora(archivo.cargado_en)} · vence {fechaHora(archivo.vence_en)}</p>
      </div>
      {trabajo ? <InsigniaEstado catalogo={ESTADO_TRABAJO} valor={trabajo.estado} /> : null}
      {trabajo?.estado === "fallido" ? <ReintentarProcesamiento tramiteId={tramiteId} archivoId={archivo.id} /> : null}
      {sugerida ? (
        <Aviso
          className="w-full"
          tono="info"
          titulo={`Posible versión nueva de «${sugerida.documento_nombre}»`}
          accion={
            <Boton tamano="chico" disabled={ocupado} onClick={() => comoVersion.mutate(archivo.id)}>
              <Layers /> Incorporar como versión nueva
            </Boton>
          }
        >
          Sugerencia del sistema: {CRITERIO_VERSION[sugerida.criterio]} ({rotuloCampo(sugerida.campo)}) con el valor validado del
          documento. Si es un documento distinto, incorporalo como documento nuevo. Confirmar la versión devuelve el trámite a
          Borrador y desplaza el ciclo en curso.
        </Aviso>
      ) : null}
      <label className="sr-only" htmlFor={`nombre-${archivo.id}`}>Nombre del documento</label>
      <Entrada id={`nombre-${archivo.id}`} value={nombre} onChange={(e) => setNombre(e.target.value)} className="w-64" />
      <Boton variante="secundario" disabled={!nombre.trim() || ocupado} onClick={() => incorporar.mutate({ archivo: archivo.id, nombre: nombre.trim() })}>
        Incorporar como documento nuevo
      </Boton>
      <Boton variante="sutil" disabled={ocupado} onClick={() => descartar.mutate(archivo.id)}>
        <Trash2 /> Descartar
      </Boton>
      {error ? <Aviso className="w-full" tono="peligro" titulo={mensajeDeError(error)} /> : null}
    </li>
  );
}

export function Documentos() {
  const id = useIdTramite();
  const { tramite, esResponsable } = useContextoTramite();
  const archivos = useArchivos(id);
  const terminal = tramite.estado === "cerrado" || tramite.estado === "cancelado";
  const pendientes = archivos.data?.filter((a) => a.estado_incorporacion === "pendiente") ?? [];
  const estadoTecnico = new Map(archivos.data?.map((a) => [a.id, a.trabajo?.estado]) ?? []);

  return (
    <div className="space-y-6">
      <Panel titulo="Documentos" descripcion="Cada documento conserva sus versiones; los datos se validan sobre la versión vigente.">
        {tramite.documentos.length === 0 ? <Vacio titulo="Sin documentos incorporados" /> : null}
        <ul className="divide-y divide-borde">
          {tramite.documentos.map((d) => {
            const estado = estadoTecnico.get(d.version_vigente.archivo_id);
            return (
              <li key={d.id} className="flex flex-wrap items-center gap-3 py-3">
                <div className="min-w-48 flex-1">
                  <p className="font-medium">{d.nombre}</p>
                  <p className="text-sm text-tenue">{d.tipo ? TIPO_DOCUMENTAL[d.tipo] : "Clasificación pendiente de validar"}</p>
                </div>
                <Insignia tono="primario">v{d.version_vigente.numero} vigente</Insignia>
                {estado ? <InsigniaEstado catalogo={ESTADO_TRABAJO} valor={estado} /> : null}
                {d.tipo ? <CheckCircle2 className="size-4 text-exito" aria-label="Clasificación validada" /> : <TriangleAlert className="size-4 text-advertencia" aria-label="Clasificación sin validar" />}
                <Boton variante="secundario" tamano="chico" comoHijo>
                  <Link to={`${d.id}`}>
                    <PencilLine /> {esResponsable ? "Validar datos" : "Ver datos y fuentes"}
                  </Link>
                </Boton>
              </li>
            );
          })}
        </ul>
      </Panel>

      {esResponsable && !terminal ? (
        <Panel titulo="Cargas" descripcion="Los archivos cargados no producen efectos hasta que confirmás su incorporación.">
          <Carga tramiteId={id} />
          <EstadoConsulta consulta={archivos} />
          {pendientes.length ? (
            <ul className="mt-4 divide-y divide-borde">
              {pendientes.map((a) => (
                <Pendiente key={a.id} archivo={a} tramiteId={id} />
              ))}
            </ul>
          ) : null}
        </Panel>
      ) : null}
    </div>
  );
}
