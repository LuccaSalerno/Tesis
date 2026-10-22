import type { ComponentProps } from "react";

import { cn } from "@/lib/utilidades";

const BASE =
  "w-full rounded-[var(--radius-ui)] border border-borde-fuerte bg-superficie px-3 text-sm text-texto placeholder:text-tenue/70 focus-visible:outline-2 focus-visible:outline-primario disabled:bg-neutro-suave aria-[invalid=true]:border-peligro";

export function Entrada({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(BASE, "h-9", className)} {...props} />;
}

export function AreaTexto({ className, ...props }: ComponentProps<"textarea">) {
  return <textarea className={cn(BASE, "min-h-24 py-2", className)} {...props} />;
}

export function Selector({ className, ...props }: ComponentProps<"select">) {
  return <select className={cn(BASE, "h-9 pr-8", className)} {...props} />;
}

export function Etiqueta({ className, ...props }: ComponentProps<"label">) {
  return <label className={cn("text-sm font-medium text-texto", className)} {...props} />;
}

export function Ayuda({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("text-xs text-tenue", className)} {...props} />;
}
