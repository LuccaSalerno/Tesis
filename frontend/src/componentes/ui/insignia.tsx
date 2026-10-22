import type { ComponentProps } from "react";

import type { Tono } from "@/lib/dominio";
import { cn } from "@/lib/utilidades";

const TONOS: Record<Tono, string> = {
  neutro: "bg-neutro-suave text-tenue border-borde",
  info: "bg-info-suave text-info border-info/25",
  primario: "bg-primario-suave text-primario border-primario/25",
  exito: "bg-exito-suave text-exito border-exito/25",
  advertencia: "bg-advertencia-suave text-advertencia border-advertencia/30",
  peligro: "bg-peligro-suave text-peligro border-peligro/25",
};

export function Insignia({
  tono = "neutro",
  className,
  ...props
}: ComponentProps<"span"> & { tono?: Tono }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap [&_svg]:size-3",
        TONOS[tono],
        className,
      )}
      {...props}
    />
  );
}
