import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/utilidades";

/** Contenedor de sección: borde fino y título; evita la sobrecarga de tarjetas anidadas. */
export function Panel({
  titulo,
  descripcion,
  acciones,
  children,
  className,
  ...props
}: Omit<ComponentProps<"section">, "title"> & {
  titulo?: ReactNode;
  descripcion?: ReactNode;
  acciones?: ReactNode;
}) {
  return (
    <section className={cn("rounded-lg border border-borde bg-superficie", className)} {...props}>
      {titulo || acciones ? (
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-borde px-5 py-3">
          <div>
            {titulo ? <h2 className="text-base">{titulo}</h2> : null}
            {descripcion ? <p className="mt-0.5 text-sm text-tenue">{descripcion}</p> : null}
          </div>
          {acciones ? <div className="flex items-center gap-2">{acciones}</div> : null}
        </header>
      ) : null}
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

export function Dato({ rotulo, children, className }: { rotulo: ReactNode; children: ReactNode; className?: string }) {
  return (
    <div className={cn("min-w-0", className)}>
      <dt className="text-xs font-medium tracking-wide text-tenue uppercase">{rotulo}</dt>
      <dd className="mt-0.5 text-sm break-words">{children}</dd>
    </div>
  );
}
