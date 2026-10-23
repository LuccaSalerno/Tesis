/**
 * Cancelación del trámite por su responsable (RF-26, RN-14, DO-2026-10-23-CIERRE P10): exige
 * un motivo y advierte que es terminal; la historia se conserva.
 */
import { Ban } from "lucide-react";
import { useState } from "react";

import { useCancelar } from "@/api/consultas";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { AreaTexto, Etiqueta } from "@/componentes/ui/campos";
import { AbrirDialogo, CerrarDialogo, ContenidoDialogo, RaizDialogo } from "@/componentes/ui/dialogo";
import { mensajeDeError } from "@/componentes/ui/estados";

export function CancelarTramite({ tramiteId }: { tramiteId: number }) {
  const [abierto, setAbierto] = useState(false);
  const [motivo, setMotivo] = useState("");
  const cancelar = useCancelar(tramiteId);
  return (
    <RaizDialogo open={abierto} onOpenChange={setAbierto}>
      <AbrirDialogo asChild>
        <Boton variante="sutil">
          <Ban /> Cancelar trámite
        </Boton>
      </AbrirDialogo>
      <ContenidoDialogo
        titulo="Cancelar el trámite"
        descripcion="Es definitivo: no admite documentos, versiones, decisiones ni firma. Documentos, decisiones y eventos se conservan."
      >
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            cancelar.mutate(motivo.trim(), { onSuccess: () => setAbierto(false) });
          }}
        >
          <Etiqueta htmlFor="motivo-cancelacion">Motivo</Etiqueta>
          <AreaTexto id="motivo-cancelacion" value={motivo} onChange={(e) => setMotivo(e.target.value)} maxLength={1000} rows={3} required />
          {cancelar.isError ? <Aviso tono="peligro" titulo={mensajeDeError(cancelar.error)} /> : null}
          <div className="flex justify-end gap-2">
            <CerrarDialogo asChild>
              <Boton type="button" variante="secundario">Volver</Boton>
            </CerrarDialogo>
            <Boton type="submit" variante="peligro" disabled={!motivo.trim() || cancelar.isPending}>
              Cancelar definitivamente
            </Boton>
          </div>
        </form>
      </ContenidoDialogo>
    </RaizDialogo>
  );
}
