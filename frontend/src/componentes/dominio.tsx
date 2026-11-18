/**
 * Piezas visuales del dominio con un vocabulario fijo:
 * - la sugerencia de la IA va con borde punteado y el rótulo «Sugerido»;
 * - el valor validado, con borde sólido, quién lo validó y cuándo;
 * - una advertencia de consistencia es información de apoyo, nunca una decisión.
 */
import { BadgeCheck, Bot, FileSearch, FlaskConical, MapPin } from "lucide-react";
import type { ReactNode } from "react";

import { useNombre } from "@/api/directorio";
import type { Control, Localizador, ResultadoRegla } from "@/api/tipos";
import { Insignia } from "@/componentes/ui/insignia";
import type { Fuente } from "@/componentes/visor";
import { esSimulado, MOTIVO_AUSENCIA, RESULTADO_REGLA, rotuloCampo, TIPO_VALIDACION, type Tono } from "@/lib/dominio";
import { fechaHora, valorLegible } from "@/lib/formatos";
import { cn } from "@/lib/utilidades";

export function InsigniaEstado<K extends string>({
  catalogo,
  valor,
}: {
  catalogo: Record<K, { rotulo: string; tono: Tono }>;
  valor: K;
}) {
  const entrada = catalogo[valor];
  return <Insignia tono={entrada?.tono ?? "neutro"}>{entrada?.rotulo ?? valor}</Insignia>;
}

export function Persona({ id, sistema = false }: { id: number | null | undefined; sistema?: boolean }) {
  const { data: nombre } = useNombre(sistema ? null : id);
  if (sistema || id == null) return <span className="text-tenue">Sistema</span>;
  return <span>{nombre ?? `Usuario #${id}`}</span>;
}

export function InsigniaSimulacion() {
  return (
    <Insignia tono="peligro" title="Sugerencia generada por el procesamiento simulado de desarrollo (no es IA real)">
      <FlaskConical /> Simulación local
    </Insignia>
  );
}

export function TextoLocalizador({ localizador }: { localizador: Localizador | null | undefined }) {
  if (!localizador) return <span className="text-tenue">Sin localizador verificable</span>;
  const partes = [
    localizador.pagina ? `Página ${localizador.pagina}` : null,
    localizador.seccion ? `Sección «${localizador.seccion}»` : null,
  ].filter(Boolean);
  return (
    <span className="inline-flex items-center gap-1">
      <MapPin className="size-3.5 text-tenue" aria-hidden />
      {partes.join(" · ") || "Fragmento citado"}
    </span>
  );
}

export function ValorSugerido({
  campo,
  valor,
  modelo,
  children,
}: {
  campo: string;
  valor: string;
  modelo?: string | null;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-md border border-dashed border-borde-fuerte bg-superficie px-3 py-2">
      <div className="flex flex-wrap items-center gap-2 text-xs text-tenue">
        <Insignia tono="neutro">
          <Bot /> Sugerido
        </Insignia>
        {esSimulado(modelo) ? <InsigniaSimulacion /> : null}
      </div>
      <p className="mt-1 font-medium">{valorLegible(campo, valor)}</p>
      {children}
    </div>
  );
}

export function ValorValidado({
  campo,
  validacion,
  className,
}: {
  campo: string;
  validacion: {
    valor_validado?: string | null;
    tipo: keyof typeof TIPO_VALIDACION;
    motivo_ausencia?: keyof typeof MOTIVO_AUSENCIA | null;
    validador_id: number;
    validado_en: string;
  };
  className?: string;
}) {
  const tipo = TIPO_VALIDACION[validacion.tipo];
  return (
    <div className={cn("rounded-md border border-exito/30 bg-exito-suave/40 px-3 py-2", className)}>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <Insignia tono={tipo.tono}>
          <BadgeCheck /> {tipo.rotulo}
        </Insignia>
        <span className="text-tenue">
          <Persona id={validacion.validador_id} /> · {fechaHora(validacion.validado_en)}
        </span>
      </div>
      <p className="mt-1 font-medium">
        {validacion.tipo === "ausente" && validacion.motivo_ausencia
          ? MOTIVO_AUSENCIA[validacion.motivo_ausencia]
          : valorLegible(campo, validacion.valor_validado)}
      </p>
    </div>
  );
}

export function ResultadoControl({ resultado }: { resultado: ResultadoRegla }) {
  return <InsigniaEstado catalogo={RESULTADO_REGLA} valor={resultado} />;
}

export function BotonFuente({ onClick, children = "Ver en el documento" }: { onClick: () => void; children?: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 text-xs font-medium text-primario hover:underline"
    >
      <FileSearch className="size-3.5" aria-hidden /> {children}
    </button>
  );
}

/** Un control con su regla, las versiones y los valores comparados, y el acceso a cada documento (RF-16). */
export function TarjetaControl({ control, alVerFuente }: { control: Control; alVerFuente: (f: Fuente) => void }) {
  const ejecucion = control.ejecucion;
  return (
    <li className={cn("rounded-md border px-4 py-3 text-sm", control.resultado === "advertencia" ? "border-advertencia/40 bg-advertencia-suave/40" : "border-borde")}>
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium">{control.descripcion}</p>
        <ResultadoControl resultado={control.resultado} />
      </div>
      <p className="mt-1 text-tenue">{control.explicacion}</p>
      {ejecucion ? (
        <>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {ejecucion.versiones.map((v) => {
              const titulo = `${v.documento_nombre} · v${v.version_numero}`;
              return (
                <div key={v.version_id} className="rounded border border-borde bg-superficie px-3 py-2 text-xs">
                  <p className="font-medium">{titulo}</p>
                  {ejecucion.valores.filter((x) => x.version_id === v.version_id).map((x) => (
                    <p key={x.validacion_id}>
                      {rotuloCampo(x.campo)}: <span className="font-medium">{x.tipo === "ausente" ? "declarado ausente" : valorLegible(x.campo, x.valor_validado)}</span>
                    </p>
                  ))}
                  <BotonFuente onClick={() => alVerFuente({ versionId: v.version_id, titulo })}>Ver documento</BotonFuente>
                </div>
              );
            })}
          </div>
          <p className="mt-2 text-xs text-tenue">Regla {ejecucion.version_regla} · ejecutada {fechaHora(ejecucion.ejecutada_en)}</p>
        </>
      ) : null}
    </li>
  );
}
