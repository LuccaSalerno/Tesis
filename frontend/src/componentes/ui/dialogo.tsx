import { X } from "lucide-react";
import { Dialog } from "radix-ui";
import type { ReactNode } from "react";

import { cn } from "@/lib/utilidades";

export const RaizDialogo = Dialog.Root;
export const AbrirDialogo = Dialog.Trigger;
export const CerrarDialogo = Dialog.Close;

export function ContenidoDialogo({
  titulo,
  descripcion,
  children,
  className,
}: {
  titulo: string;
  descripcion?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-40 bg-texto/30" />
      <Dialog.Content
        className={cn(
          "fixed top-1/2 left-1/2 z-50 w-[min(34rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-borde bg-superficie p-6 shadow-lg",
          className,
        )}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <Dialog.Title className="text-lg font-semibold">{titulo}</Dialog.Title>
            {descripcion ? (
              <Dialog.Description className="mt-1 text-sm text-tenue">{descripcion}</Dialog.Description>
            ) : (
              <Dialog.Description className="sr-only">{titulo}</Dialog.Description>
            )}
          </div>
          <Dialog.Close className="rounded p-1 text-tenue hover:bg-neutro-suave" aria-label="Cerrar">
            <X className="size-4" />
          </Dialog.Close>
        </div>
        {children}
      </Dialog.Content>
    </Dialog.Portal>
  );
}
