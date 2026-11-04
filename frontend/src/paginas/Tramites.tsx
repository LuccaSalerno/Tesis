import { Plus } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";

import { useCrearTramite, useTramites } from "@/api/consultas";
import type { Tramite } from "@/api/tipos";
import { InsigniaEstado, Persona } from "@/componentes/dominio";
import { Encabezado } from "@/componentes/marco";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { AreaTexto, Entrada, Etiqueta } from "@/componentes/ui/campos";
import { AbrirDialogo, ContenidoDialogo, RaizDialogo } from "@/componentes/ui/dialogo";
import { EstadoConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { ESTADO_TRAMITE } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";
import { useSesion } from "@/lib/sesion";

export function TablaTramites({ tramites }: { tramites: Tramite[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-borde bg-superficie">
      <table className="w-full text-sm">
        <thead className="border-b border-borde bg-neutro-suave/60 text-left text-xs text-tenue uppercase">
          <tr>
            <th className="px-4 py-2.5 font-medium">Trámite</th>
            <th className="px-4 py-2.5 font-medium">Estado</th>
            <th className="px-4 py-2.5 font-medium">Responsable</th>
            <th className="px-4 py-2.5 font-medium">Actualizado</th>
          </tr>
        </thead>
        <tbody>
          {tramites.map((t) => (
            <tr key={t.id} className="border-b border-borde last:border-0 hover:bg-neutro-suave/40">
              <td className="px-4 py-3">
                <Link to={`/tramites/${t.id}`} className="font-medium text-primario hover:underline">
                  {t.titulo}
                </Link>
                <span className="ml-2 text-xs text-tenue">TR-{t.id}</span>
              </td>
              <td className="px-4 py-3">
                <InsigniaEstado catalogo={ESTADO_TRAMITE} valor={t.estado} />
              </td>
              <td className="px-4 py-3">
                <Persona id={t.responsable_id} />
              </td>
              <td className="px-4 py-3 text-tenue">{fechaHora(t.actualizado_en)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NuevoTramite() {
  const [abierto, setAbierto] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const crear = useCrearTramite();
  const navegar = useNavigate();

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    const tramite = await crear.mutateAsync({ titulo: titulo.trim(), descripcion: descripcion.trim() || null });
    setAbierto(false);
    navegar(`/tramites/${tramite.id}/documentos`);
  }

  return (
    <RaizDialogo open={abierto} onOpenChange={setAbierto}>
      <AbrirDialogo asChild>
        <Boton>
          <Plus /> Nuevo trámite
        </Boton>
      </AbrirDialogo>
      <ContenidoDialogo titulo="Nuevo trámite" descripcion="Reúne en un mismo contexto la documentación de una contratación.">
        <form onSubmit={enviar} className="space-y-4">
          <div className="space-y-1.5">
            <Etiqueta htmlFor="titulo">Título</Etiqueta>
            <Entrada id="titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} maxLength={200} required />
          </div>
          <div className="space-y-1.5">
            <Etiqueta htmlFor="descripcion">Descripción (opcional)</Etiqueta>
            <AreaTexto id="descripcion" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} maxLength={5000} />
          </div>
          {crear.isError ? <Aviso tono="peligro" titulo={mensajeDeError(crear.error)} /> : null}
          <div className="flex justify-end">
            <Boton type="submit" disabled={crear.isPending || !titulo.trim()}>
              {crear.isPending ? "Creando…" : "Crear trámite"}
            </Boton>
          </div>
        </form>
      </ContenidoDialogo>
    </RaizDialogo>
  );
}

export function Tramites() {
  const { tiene } = useSesion();
  const tramites = useTramites();
  return (
    <>
      <Encabezado
        titulo="Trámites"
        descripcion={tiene("responsable_tramite") ? "Los trámites a tu cargo y aquellos en los que tenés tareas." : "Los trámites en los que tenés tareas asignadas."}
        acciones={tiene("responsable_tramite") ? <NuevoTramite /> : null}
      />
      <EstadoConsulta consulta={tramites} reintentar={() => void tramites.refetch()} />
      {tramites.data?.length === 0 ? <Vacio titulo="Todavía no hay trámites" /> : null}
      {tramites.data?.length ? <TablaTramites tramites={tramites.data} /> : null}
    </>
  );
}
