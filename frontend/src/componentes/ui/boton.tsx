import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utilidades";

const variantes = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-ui)] text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variante: {
        primario: "bg-primario text-white hover:bg-primario-oscuro",
        secundario: "border border-borde-fuerte bg-superficie text-texto hover:bg-neutro-suave",
        sutil: "text-texto hover:bg-neutro-suave",
        peligro: "bg-peligro text-white hover:opacity-90",
        advertencia: "border border-advertencia/40 bg-advertencia-suave text-advertencia hover:bg-advertencia-suave/70",
        enlace: "h-auto px-0 text-primario underline-offset-4 hover:underline",
      },
      tamano: {
        normal: "h-9 px-4",
        chico: "h-8 px-3 text-xs",
        icono: "size-8",
      },
    },
    defaultVariants: { variante: "primario", tamano: "normal" },
  },
);

export interface PropsBoton extends ComponentProps<"button">, VariantProps<typeof variantes> {
  comoHijo?: boolean;
}

export function Boton({ className, variante, tamano, comoHijo, type, ...props }: PropsBoton) {
  const Componente = comoHijo ? Slot.Root : "button";
  return (
    <Componente
      type={comoHijo ? undefined : (type ?? "button")}
      className={cn(variantes({ variante, tamano }), className)}
      {...props}
    />
  );
}
