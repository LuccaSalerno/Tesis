import { Inbox, Loader2, RotateCw } from "lucide-react";
import type { ReactNode } from "react";

import { ErrorApi } from "@/api/cliente";

import { Aviso } from "./aviso";
import { Boton } from "./boton";

export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  return (
    <div role="status" className="flex items-center gap-2 py-6 text-sm text-tenue">
      <Loader2 className="size-4 animate-spin" aria-hidden />
      {texto}
    </div>
  );
}

export function Vacio({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 py-10 text-center text-sm text-tenue">
      <Inbox className="size-6" aria-hidden />
      <p className="font-medium text-texto">{titulo}</p>
      {children}
    </div>
  );
}

export function ErrorConsulta({ error, reintentar }: { error: unknown; reintentar?: () => void }) {
  const mensaje =
    error instanceof ErrorApi ? error.detalle : "No se pudo obtener la información.";
  return (
    <Aviso
      tono={error instanceof ErrorApi && error.estado === 503 ? "advertencia" : "peligro"}
      titulo={mensaje}
      accion={
        reintentar ? (
          <Boton variante="secundario" tamano="chico" onClick={reintentar}>
            <RotateCw /> Reintentar
          </Boton>
        ) : null
      }
    />
  );
}

export function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorApi) return error.detalle;
  if (error instanceof Error) return error.message;
  return "Ocurrió un error inesperado.";
}
