/**
 * Vínculos y controles (Fig. 5.8, RF-14 a RF-16): los vínculos sugeridos se presentan aparte
 * y no rigen hasta confirmarse (RN-05); cada control muestra la regla, las versiones, los
 * valores validados comparados y su resultado, y permite abrir el documento de origen.
 */
import { Link2, Plus, Sparkles, Trash2, X } from "lucide-react";
import { type FormEvent, useState } from "react";

import { useControles, useCrearVinculo, useResolverVinculo, useVinculos } from "@/api/consultas";
import type { Vinculo } from "@/api/tipos";
import { TarjetaControl } from "@/componentes/dominio";
import { DialogoFuente, type Fuente } from "@/componentes/visor";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Entrada, Etiqueta, Selector } from "@/componentes/ui/campos";
import { EstadoConsulta, mensajeDeError, Vacio } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { Panel } from "@/componentes/ui/panel";
import { RESULTADO_REGLA } from "@/lib/dominio";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

function NuevoVinculo({ tramiteId }: { tramiteId: number }) {
  const { tramite } = useContextoTramite();
  const crear = useCrearVinculo(tramiteId);
  const [origen, setOrigen] = useState("");
  const [destino, setDestino] = useState("");
  const [justificacion, setJustificacion] = useState("");
  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await crear.mutateAsync({
      documento_origen_id: Number(origen),
      documento_destino_id: Number(destino),
      tipo: "campos",
      justificacion: justificacion.trim(),
    });
    setOrigen("");
    setDestino("");
    setJustificacion("");
  }
  return (
    <form onSubmit={enviar} className="mt-4 grid gap-3 rounded-md border border-borde bg-neutro-suave/40 p-4 md:grid-cols-[1fr_1fr_2fr_auto] md:items-end">
      <div className="space-y-1">
        <Etiqueta htmlFor="origen">Documento</Etiqueta>
        <Selector id="origen" value={origen} onChange={(e) => setOrigen(e.target.value)} required>
          <option value="">Elegí…</option>
          {tramite.documentos.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
        </Selector>
      </div>
      <div className="space-y-1">
        <Etiqueta htmlFor="destino">Relacionado con</Etiqueta>
        <Selector id="destino" value={destino} onChange={(e) => setDestino(e.target.value)} required>
          <option value="">Elegí…</option>
          {tramite.documentos.filter((d) => String(d.id) !== origen).map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
        </Selector>
      </div>
      <div className="space-y-1">
        <Etiqueta htmlFor="justificacion">Justificación</Etiqueta>
        <Entrada id="justificacion" value={justificacion} onChange={(e) => setJustificacion(e.target.value)} required maxLength={2000} placeholder="Por ejemplo: comparten el CUIT del proveedor" />
      </div>
      <Boton type="submit" disabled={crear.isPending}><Plus /> Vincular</Boton>
      {crear.isError ? <Aviso className="md:col-span-4" tono="peligro" titulo={mensajeDeError(crear.error)} /> : null}
    </form>
  );
}

function FilaVinculo({ vinculo, editable, tramiteId }: { vinculo: Vinculo; editable: boolean; tramiteId: number }) {
  const { tramite } = useContextoTramite();
  const resolver = useResolverVinculo(tramiteId);
  const nombre = (id: number) => tramite.documentos.find((d) => d.id === id)?.nombre ?? `Documento ${id}`;
  return (
    <li className="flex flex-wrap items-center gap-3 py-3 text-sm">
      <span className="min-w-56 flex-1">
        <span className="font-medium">{nombre(vinculo.documento_origen_id)}</span>
        <Link2 className="mx-2 inline size-4 text-tenue" aria-label="vinculado con" />
        <span className="font-medium">{nombre(vinculo.documento_destino_id)}</span>
        <span className="block text-xs text-tenue">{vinculo.justificacion}</span>
      </span>
      {vinculo.origen === "automatico" ? <Insignia tono="neutro"><Sparkles /> Sugerido por el sistema</Insignia> : <Insignia tono="neutro">Manual</Insignia>}
      {editable && vinculo.estado === "pendiente" ? (
        <>
          <Boton tamano="chico" onClick={() => resolver.mutate({ vinculo: vinculo.id, accion: "confirmacion" })} disabled={resolver.isPending}>Confirmar</Boton>
          <Boton tamano="chico" variante="secundario" onClick={() => resolver.mutate({ vinculo: vinculo.id, accion: "rechazo" })} disabled={resolver.isPending}><X /> Rechazar</Boton>
        </>
      ) : null}
      {editable && vinculo.estado === "confirmado" ? (
        <Boton tamano="chico" variante="sutil" aria-label="Eliminar vínculo" onClick={() => resolver.mutate({ vinculo: vinculo.id, accion: "eliminacion" })} disabled={resolver.isPending}><Trash2 /></Boton>
      ) : null}
      {resolver.isError ? <Aviso className="w-full" tono="peligro" titulo={mensajeDeError(resolver.error)} /> : null}
    </li>
  );
}

export function VinculosControles() {
  const id = useIdTramite();
  const { tramite, esResponsable } = useContextoTramite();
  const vinculos = useVinculos(id);
  const controles = useControles(id);
  const [fuente, setFuente] = useState<Fuente | null>(null);
  const editable = esResponsable && (tramite.estado === "borrador" || tramite.estado === "pendiente_validacion");
  const resumen = controles.data?.vigentes.reduce<Record<string, number>>((acc, c) => ({ ...acc, [c.resultado]: (acc[c.resultado] ?? 0) + 1 }), {}) ?? {};

  return (
    <div className="space-y-6">
      <Panel titulo="Vínculos entre documentos" descripcion="Los sugeridos no rigen hasta que el responsable los confirma.">
        <EstadoConsulta consulta={vinculos} />
        {vinculos.data ? (
          <>
            {vinculos.data.sugeridos.length ? (
              <>
                <h3 className="text-xs font-medium text-tenue uppercase">Sugeridos, pendientes de confirmación</h3>
                <ul className="mb-4 divide-y divide-borde">
                  {vinculos.data.sugeridos.map((v) => <FilaVinculo key={v.id} vinculo={v} editable={editable} tramiteId={id} />)}
                </ul>
              </>
            ) : null}
            <h3 className="text-xs font-medium text-tenue uppercase">Vigentes</h3>
            {vinculos.data.confirmados.length === 0 ? <Vacio titulo="Sin vínculos confirmados" /> : null}
            <ul className="divide-y divide-borde">
              {vinculos.data.confirmados.map((v) => <FilaVinculo key={v.id} vinculo={v} editable={editable} tramiteId={id} />)}
            </ul>
          </>
        ) : null}
        {editable && tramite.documentos.length > 1 ? <NuevoVinculo tramiteId={id} /> : null}
      </Panel>

      <Panel
        titulo="Controles de consistencia"
        descripcion="Reglas explícitas sobre valores validados. Producen advertencias explicables, no decisiones."
        acciones={
          <span className="flex flex-wrap gap-1">
            {Object.entries(resumen).map(([resultado, n]) => (
              <Insignia key={resultado} tono={RESULTADO_REGLA[resultado as keyof typeof RESULTADO_REGLA].tono}>
                {n} {RESULTADO_REGLA[resultado as keyof typeof RESULTADO_REGLA].rotulo.toLowerCase()}
              </Insignia>
            ))}
          </span>
        }
      >
        <EstadoConsulta consulta={controles} />
        <ul className="space-y-3">
          {controles.data?.vigentes.map((c) => (
            <TarjetaControl key={`${c.codigo_regla}-${c.vinculo_id ?? "sin"}`} control={c} alVerFuente={setFuente} />
          ))}
        </ul>
      </Panel>
      <DialogoFuente tramiteId={id} fuente={fuente} alCerrar={() => setFuente(null)} />
    </div>
  );
}
