import { AlertTriangle, CircleAlert, Info, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";

import type { Tono } from "@/lib/dominio";
import { cn } from "@/lib/utilidades";

const ESTILO: Partial<Record<Tono, { clase: string; icono: ReactNode }>> = {
  info: { clase: "border-info/25 bg-info-suave text-info", icono: <Info /> },
  advertencia: {
    clase: "border-advertencia/30 bg-advertencia-suave text-advertencia",
    icono: <AlertTriangle />,
  },
  peligro: { clase: "border-peligro/25 bg-peligro-suave text-peligro", icono: <CircleAlert /> },
  neutro: { clase: "border-borde bg-neutro-suave text-tenue", icono: <ShieldAlert /> },
};

export function Aviso({
  tono = "info",
  titulo,
  children,
  accion,
  className,
}: {
  tono?: "info" | "advertencia" | "peligro" | "neutro";
  titulo?: ReactNode;
  children?: ReactNode;
  accion?: ReactNode;
  className?: string;
}) {
  const estilo = ESTILO[tono] ?? ESTILO.info!;
  return (
    <div
      role={tono === "peligro" ? "alert" : "status"}
      className={cn("flex gap-3 rounded-md border px-4 py-3 text-sm [&>svg]:mt-0.5 [&>svg]:size-4 [&>svg]:shrink-0", estilo.clase, className)}
    >
      {estilo.icono}
      <div className="min-w-0 flex-1">
        {titulo ? <p className="font-medium">{titulo}</p> : null}
        {children ? <div className="text-texto/90">{children}</div> : null}
      </div>
      {accion}
    </div>
  );
}
