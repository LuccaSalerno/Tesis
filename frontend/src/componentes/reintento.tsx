/**
 * Intento nuevo del procesamiento tras una falla técnica (RNF-06, RC-P08.4;
 * DO-2026-10-23-REC P7). Solo lo ofrece la pantalla al responsable; el backend lo vuelve a
 * exigir. El nuevo intento puede quedar en espera de capacidad, que no es un error.
 */
import { RotateCcw } from "lucide-react";

import { useReintentar } from "@/api/consultas";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { mensajeDeError } from "@/componentes/ui/estados";

export function ReintentarProcesamiento({ tramiteId, archivoId }: { tramiteId: number; archivoId: number }) {
  const reintentar = useReintentar(tramiteId);
  return (
    <>
      <Boton variante="secundario" disabled={reintentar.isPending} onClick={() => reintentar.mutate(archivoId)}>
        <RotateCcw className="size-4" aria-hidden /> Reintentar procesamiento
      </Boton>
      {reintentar.isError ? <Aviso className="w-full" tono="peligro" titulo={mensajeDeError(reintentar.error)} /> : null}
    </>
  );
}
