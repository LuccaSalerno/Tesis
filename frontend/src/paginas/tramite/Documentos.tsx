import { CheckCircle2, FileUp, Loader2, PencilLine, TriangleAlert } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router";

import { type Etapa, useCargarArchivo } from "@/api/cargas";
import { useArchivos, useIncorporar } from "@/api/consultas";
import type { Archivo } from "@/api/tipos";
import { InsigniaEstado } from "@/componentes/dominio";
import { ReintentarProcesamiento } from "@/componentes/reintento";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Entrada } from "@/componentes/ui/campos";
import { Cargando, ErrorConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { ESTADO_TRABAJO, TIPO_DOCUMENTAL } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

const ETAPAS: Record<Etapa, string> = {
  autorizando: "Autorizando la carga…",
  transfiriendo: "Transfiriendo el archivo…",
  confirmando: "Verificando el archivo recibido…",
};

function Carga({ tramiteId }: { tramiteId: number }) {
  const [etapa, setEtapa] = useState<Etapa | null>(null);
  const entrada = useRef<HTMLInputElement>(null);
  const cargar = useCargarArchivo(tramiteId, setEtapa);
  return (
    <div className="rounded-md border border-dashed border-borde-fuerte bg-neutro-suave/40 px-4 py-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium">Cargar un archivo</p>
          <p className="text-sm text-tenue">PDF o DOCX, hasta 20 MB. El procesamiento sigue en segundo plano.</p>
        </div>
        <Boton onClick={() => entrada.current?.click()} disabled={cargar.isPending}>
          {cargar.isPending ? <Loader2 className="animate-spin" /> : <FileUp />} Elegir archivo
        </Boton>
        <input
          ref={entrada}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="sr-only"
          aria-label="Archivo a cargar"
          onChange={(e) => {
            const archivo = e.target.files?.[0];
            if (archivo) cargar.mutate(archivo, { onSettled: () => setEtapa(null) });
            e.target.value = "";
          }}
        />
      </div>
      {cargar.isPending && etapa ? <p className="mt-3 text-sm text-tenue">{ETAPAS[etapa]}</p> : null}
      {cargar.isError ? <Aviso className="mt-3" tono="peligro" titulo={mensajeDeError(cargar.error)} /> : null}
      {cargar.isSuccess ? (
        <Aviso className="mt-3" tono="info" titulo="Archivo recibido">
          Quedó pendiente de incorporación; podés seguir trabajando mientras se procesa.
        </Aviso>
      ) : null}
    </div>
  );
}

function Pendiente({ archivo, tramiteId }: { archivo: Archivo; tramiteId: number }) {
  const [nombre, setNombre] = useState(archivo.nombre.replace(/\.(pdf|docx)$/i, ""));
  const incorporar = useIncorporar(tramiteId);
  const trabajo = archivo.trabajo;
  return (
    <li className="flex flex-wrap items-center gap-3 py-3">
      <div className="min-w-48 flex-1">
        <p className="font-medium">{archivo.nombre}</p>
        <p className="text-xs text-tenue">Cargado {fechaHora(archivo.cargado_en)} · vence {fechaHora(archivo.vence_en)}</p>
      </div>
      {trabajo ? <InsigniaEstado catalogo={ESTADO_TRABAJO} valor={trabajo.estado} /> : null}
      {trabajo?.estado === "fallido" ? <ReintentarProcesamiento tramiteId={tramiteId} archivoId={archivo.id} /> : null}
      <label className="sr-only" htmlFor={`nombre-${archivo.id}`}>Nombre del documento</label>
      <Entrada id={`nombre-${archivo.id}`} value={nombre} onChange={(e) => setNombre(e.target.value)} className="w-64" />
      <Boton variante="secundario" disabled={!nombre.trim() || incorporar.isPending} onClick={() => incorporar.mutate({ archivo: archivo.id, nombre: nombre.trim() })}>
        Incorporar como documento nuevo
      </Boton>
      {incorporar.isError ? <Aviso className="w-full" tono="peligro" titulo={mensajeDeError(incorporar.error)} /> : null}
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
        <Panel titulo="Cargas" descripcion="Los archivos cargados no producen efectos hasta que confirmás su incorporación (RF-04, RF-07).">
          <Carga tramiteId={id} />
          {archivos.isPending ? <Cargando /> : null}
          {archivos.isError ? <ErrorConsulta error={archivos.error} /> : null}
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
