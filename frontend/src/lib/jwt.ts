/** Lectura de la carga de un token propio (ya firmado por su emisor): no valida la firma. */
export function cargaDelToken(token: string): { sub?: string; exp?: number } | null {
  const partes = token.split(".");
  if (partes.length !== 3 || !partes[1]) return null;
  try {
    const base = partes[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base + "=".repeat((4 - (base.length % 4)) % 4)));
  } catch {
    return null;
  }
}
