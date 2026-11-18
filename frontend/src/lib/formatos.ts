/** Presentación de fechas, importes y valores canónicos. */
import type { TipoDocumental } from "@/api/tipos";
import { TIPO_DOCUMENTAL } from "@/lib/dominio";

const FECHA_HORA = new Intl.DateTimeFormat("es-AR", {
  dateStyle: "medium",
  timeStyle: "short",
});
const FECHA = new Intl.DateTimeFormat("es-AR", { dateStyle: "medium", timeZone: "UTC" });

export function fechaHora(iso: string | null | undefined): string {
  return iso ? FECHA_HORA.format(new Date(iso)) : "—";
}

/** Fechas canónicas AAAA-MM-DD: se muestran sin desplazamiento de zona horaria. */
export function fechaCanonica(valor: string): string {
  return /^\d{4}-\d{2}-\d{2}$/.test(valor) ? FECHA.format(new Date(`${valor}T00:00:00Z`)) : valor;
}

export function importeCanonico(valor: string): string {
  if (!/^-?\d+\.\d{2}$/.test(valor)) return valor;
  const [entero, decimales] = valor.split(".");
  return `${Number(entero).toLocaleString("es-AR")},${decimales}`;
}

/** Muestra un valor validado según el tipo de dato que sugiere su nombre de campo. */
export function valorLegible(campo: string, valor: string | null | undefined): string {
  if (valor == null) return "—";
  if (campo === "tipo_documental") return TIPO_DOCUMENTAL[valor as TipoDocumental] ?? valor;
  if (/fecha|vigencia/.test(campo)) return fechaCanonica(valor);
  if (/importe|monto/.test(campo)) return importeCanonico(valor);
  return valor;
}
