/**
 * Carga de un archivo como en §5.3.1: autorización de la API, transferencia directa a S3 con
 * la URL prefirmada (el binario no pasa por la API) y confirmación técnica.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, ErrorApi, exigir } from "./cliente";
import { claves } from "./consultas";

export type Etapa = "autorizando" | "transfiriendo" | "confirmando";

function formatoDe(archivo: File): "pdf" | "docx" | null {
  const nombre = archivo.name.toLowerCase();
  if (nombre.endsWith(".pdf")) return "pdf";
  if (nombre.endsWith(".docx")) return "docx";
  return null;
}

export function useCargarArchivo(t: number, alAvanzar?: (etapa: Etapa) => void) {
  const cliente = useQueryClient();
  return useMutation({
    mutationFn: async (archivo: File) => {
      const formato = formatoDe(archivo);
      if (!formato) throw new ErrorApi(422, "Solo se admiten archivos PDF o DOCX.");
      alAvanzar?.("autorizando");
      const carga = await exigir(
        api.POST("/tramites/{tramite_id}/cargas", {
          params: { path: { tramite_id: t } },
          body: { nombre: archivo.name, formato, tamano_bytes: archivo.size },
        }),
      );
      alAvanzar?.("transfiriendo");
      const transferencia = await fetch(carga.url, {
        method: carga.metodo,
        headers: carga.encabezados,
        body: archivo,
      }).catch(() => null);
      if (!transferencia?.ok) {
        throw new ErrorApi(502, "No se pudo transferir el archivo al almacenamiento. Reintentá la carga.");
      }
      alAvanzar?.("confirmando");
      return exigir(
        api.POST("/tramites/{tramite_id}/cargas/{carga_id}/confirmacion", {
          params: { path: { tramite_id: t, carga_id: carga.id } },
        }),
      );
    },
    onSettled: () => cliente.invalidateQueries({ queryKey: claves.archivos(t) }),
  });
}
