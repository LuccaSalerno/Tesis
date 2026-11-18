/**
 * Formatos canónicos de los valores validados, verificados antes de
 * enviar. El backend vuelve a validarlos: esto solo evita un viaje y explica el formato.
 */
import { z } from "zod";

export type ClaseCampo = "fecha" | "importe" | "cuit" | "moneda" | "texto";

export function claseDeCampo(campo: string): ClaseCampo {
  if (/^(fecha|vigencia)/.test(campo)) return "fecha";
  if (/^(importe|monto)/.test(campo)) return "importe";
  if (campo.startsWith("cuit")) return "cuit";
  if (campo === "moneda") return "moneda";
  return "texto";
}

const ESQUEMAS: Record<ClaseCampo, z.ZodType<string>> = {
  fecha: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Usá el formato AAAA-MM-DD, por ejemplo 2027-02-28."),
  importe: z.string().regex(/^\d+\.\d{2}$/, "Usá dígitos y dos decimales con punto, por ejemplo 1250000.00."),
  cuit: z.string().regex(/^\d{2}-\d{8}-\d$/, "Usá el formato ##-########-#."),
  moneda: z.string().regex(/^[A-Z]{3}$/, "Usá el código ISO de tres letras, por ejemplo ARS."),
  texto: z.string().min(1, "Ingresá un valor."),
};

export const AYUDA: Record<ClaseCampo, string> = {
  fecha: "AAAA-MM-DD",
  importe: "1250000.00",
  cuit: "##-########-#",
  moneda: "ARS",
  texto: "Texto tal como figura en el documento",
};

/** Devuelve el mensaje de error o `null` si el valor tiene el formato canónico. */
export function errorDeFormato(campo: string, valor: string): string | null {
  const resultado = ESQUEMAS[claseDeCampo(campo)].safeParse(valor.trim());
  return resultado.success ? null : (resultado.error.issues[0]?.message ?? "Formato inválido.");
}
