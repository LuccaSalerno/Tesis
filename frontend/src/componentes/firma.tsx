/**
 * Firma digital simulada (RF-23, V11, DO-2026-10-23-VER P5 a P7). La interfaz la rotula
 * siempre como simulación sin validez jurídica y muestra lo necesario para recalcular la
 * referencia de integridad: el registro canónico y su SHA-256.
 */
import { PenLine, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { useFirmar } from "@/api/consultas";
import type { Ciclo, Firma } from "@/api/tipos";
import { Persona } from "@/componentes/dominio";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { mensajeDeError } from "@/componentes/ui/estados";
import { Dato } from "@/componentes/ui/panel";
import { LEYENDA_FIRMA } from "@/lib/dominio";
import { fechaHora } from "@/lib/formatos";

function Leyenda() {
  return (
    <p className="inline-flex items-center gap-1.5 rounded-md border border-advertencia/40 bg-advertencia-suave px-2 py-1 text-xs font-medium text-advertencia">
      <ShieldAlert className="size-3.5" aria-hidden /> {LEYENDA_FIRMA}
    </p>
  );
}

export function FirmaAplicada({ firma, documento }: { firma: Firma; documento?: string }) {
  return (
    <div className="space-y-3">
      <Leyenda />
      <dl className="grid gap-3 sm:grid-cols-2">
        <Dato rotulo="Versión firmada">
          {documento ?? `Documento ${firma.documento_id}`} · v{firma.version_numero} (ciclo {firma.ciclo_numero})
        </Dato>
        <Dato rotulo="Firmante">
          <Persona id={firma.firmante_id} /> · {fechaHora(firma.firmada_en)}
        </Dato>
        <Dato rotulo={`Referencia de integridad (${firma.algoritmo})`} className="sm:col-span-2">
          <code className="text-xs break-all">{firma.referencia_integridad}</code>
        </Dato>
        <Dato rotulo="Registro canónico" className="sm:col-span-2">
          <code className="text-xs break-all">{firma.registro_canonico}</code>
        </Dato>
      </dl>
    </div>
  );
}

/** Para el revisor/aprobador con autorización de cierre, sobre el ciclo aprobado. */
export function Firmar({ tramiteId, ciclo }: { tramiteId: number; ciclo: Ciclo }) {
  const [version, setVersion] = useState(ciclo.versiones[0]?.version_id);
  const firmar = useFirmar(tramiteId);
  return (
    <div className="space-y-3">
      <Leyenda />
      <p className="text-sm">
        Elegí la versión del ciclo {ciclo.numero} aprobado. Firmar deja el trámite <span className="font-medium">Cerrado</span>: no
        admite documentos, versiones ni decisiones nuevas.
      </p>
      <label className="block text-sm" htmlFor="version-a-firmar">
        Versión
      </label>
      <select
        id="version-a-firmar"
        className="h-9 w-full rounded-[var(--radius-ui)] border border-borde-fuerte bg-superficie px-2 text-sm"
        value={version}
        onChange={(e) => setVersion(Number(e.target.value))}
      >
        {ciclo.versiones.map((v) => (
          <option key={v.version_id} value={v.version_id}>
            {v.documento_nombre} · v{v.version_numero}
          </option>
        ))}
      </select>
      <Boton disabled={version === undefined || firmar.isPending} onClick={() => version !== undefined && firmar.mutate(version)}>
        <PenLine /> Firmar (simulación)
      </Boton>
      {firmar.isError ? <Aviso tono="peligro" titulo={mensajeDeError(firmar.error)} /> : null}
    </div>
  );
}
