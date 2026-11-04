/**
 * Nombres visibles de las personas (WEB F5). Los pedidos de un mismo ciclo de renderizado se
 * agrupan en una sola llamada a `/usuarios/directorio`.
 */
import { useQuery } from "@tanstack/react-query";

import { api, exigir } from "./cliente";

type Resolver = (nombre: string | null) => void;

let pendientes = new Map<number, Resolver[]>();
let programado = false;

async function despachar(): Promise<void> {
  const lote = pendientes;
  pendientes = new Map();
  programado = false;
  const ids = [...lote.keys()];
  let nombres = new Map<number, string | null>();
  try {
    for (let i = 0; i < ids.length; i += 100) {
      const parte = await exigir(
        api.GET("/usuarios/directorio", { params: { query: { ids: ids.slice(i, i + 100) } } }),
      );
      // RF-25: la cuenta suprimida no conserva datos identificatorios, solo su id interno.
      const nombre = (e: (typeof parte)[number]) => (e.suprimida ? `Cuenta suprimida #${e.id}` : e.nombre_visible);
      nombres = new Map([...nombres, ...parte.map((e) => [e.id, nombre(e)] as const)]);
    }
  } catch {
    // Sin directorio se muestra el identificador: no bloquea la pantalla.
  }
  for (const [id, resolvers] of lote) resolvers.forEach((r) => r(nombres.get(id) ?? null));
}

function nombreDe(id: number): Promise<string | null> {
  return new Promise((resolver) => {
    pendientes.set(id, [...(pendientes.get(id) ?? []), resolver]);
    if (!programado) {
      programado = true;
      setTimeout(() => void despachar(), 0);
    }
  });
}

export function useNombre(id: number | null | undefined) {
  return useQuery({
    queryKey: ["directorio", id],
    enabled: id != null,
    staleTime: 5 * 60_000,
    queryFn: () => nombreDe(id as number),
  });
}
