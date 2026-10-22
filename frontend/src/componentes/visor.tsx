/**
 * Puntos de entrada del visor de documentos. pdf.js pesa más que el resto de la aplicación:
 * se carga recién cuando alguien abre un documento.
 */
import { lazy, Suspense } from "react";

import { ContenidoDialogo, RaizDialogo } from "@/componentes/ui/dialogo";
import { Cargando } from "@/componentes/ui/estados";

export interface Fuente {
  versionId: number;
  pagina?: number | null;
  fragmento?: string | null;
  titulo?: string;
}

const VisorPdf = lazy(() => import("./visor-pdf"));

export function VisorDocumento(props: { tramiteId: number; fuente: Fuente }) {
  return (
    <Suspense fallback={<Cargando texto="Preparando el visor…" />}>
      <VisorPdf {...props} />
    </Suspense>
  );
}

export function DialogoFuente({
  tramiteId,
  fuente,
  alCerrar,
}: {
  tramiteId: number;
  fuente: Fuente | null;
  alCerrar: () => void;
}) {
  return (
    <RaizDialogo open={fuente !== null} onOpenChange={(abierto) => (abierto ? null : alCerrar())}>
      {fuente ? (
        <ContenidoDialogo titulo={fuente.titulo ?? "Fuente del dato"} className="h-[min(90vh,60rem)] w-[min(60rem,calc(100vw-2rem))]">
          <div className="h-[calc(100%-3.5rem)]">
            <VisorDocumento tramiteId={tramiteId} fuente={fuente} />
          </div>
        </ContenidoDialogo>
      ) : null}
    </RaizDialogo>
  );
}
