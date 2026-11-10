/**
 * Visor del original de una versión (HU-04, RF-11, DO-2026-10-22-WEB F4). Pide a la API una
 * URL de lectura de 5 minutos (con las mismas reglas de acceso que el resto del trámite), salta
 * a la página del localizador y resalta el fragmento citado si el texto coincide. Si no
 * coincide, igual muestra la página y el fragmento citado aparte: nunca inventa una ubicación.
 */
import { ChevronLeft, ChevronRight, ExternalLink, FileText } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

import { useArchivoVersion } from "@/api/consultas";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Cargando, ErrorConsulta } from "@/componentes/ui/estados";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const normalizar = (texto: string) => texto.toLocaleLowerCase("es").replace(/\s+/g, " ").trim();

import type { Fuente } from "./visor";

export function VisorDocumento({ tramiteId, fuente }: { tramiteId: number; fuente: Fuente }) {
  const archivo = useArchivoVersion(tramiteId, fuente.versionId);
  const [paginas, setPaginas] = useState(0);
  const [pagina, setPagina] = useState(fuente.pagina ?? 1);
  const [ancho, setAncho] = useState(640);

  // Cada consulta firma una URL nueva para el mismo archivo. El PDF se carga con la primera de
  // la versión y no se vuelve a descargar cuando la consulta se refresca (por ejemplo, después
  // de validar un dato); el enlace «Abrir el original» sí usa la más reciente.
  const [origen, setOrigen] = useState<{ version: number; url: string } | null>(null);
  if (archivo.data && origen?.version !== fuente.versionId) {
    setOrigen({ version: fuente.versionId, url: archivo.data.url });
  }
  // Ver otra fuente del mismo documento salta a su página sin recargar el PDF.
  const [ubicacion, setUbicacion] = useState({ pagina: fuente.pagina, fragmento: fuente.fragmento });
  if (ubicacion.pagina !== fuente.pagina || ubicacion.fragmento !== fuente.fragmento) {
    setUbicacion({ pagina: fuente.pagina, fragmento: fuente.fragmento });
    setPagina(Math.min(fuente.pagina ?? 1, paginas || Infinity));
  }

  const medir = useCallback((nodo: HTMLDivElement | null) => {
    if (nodo) setAncho(Math.max(320, nodo.clientWidth - 16));
  }, []);

  const buscado = useMemo(() => normalizar(fuente.fragmento ?? ""), [fuente.fragmento]);
  const resaltar = useCallback(
    ({ str }: { str: string }) => {
      const item = normalizar(str);
      // Ítems cortos («Moneda») coinciden por casualidad: se exige un tramo significativo.
      const coincide =
        buscado.length >= 3 &&
        ((item.length >= 12 && buscado.includes(item)) || (item.length >= 3 && item.includes(buscado)));
      const seguro = str.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
      // La capa de texto es transparente: el resaltado solo pinta el fondo sobre la imagen.
      return coincide
        ? `<mark style="background: rgb(154 98 0 / 0.28); color: transparent; border-radius: 2px">${seguro}</mark>`
        : seguro;
    },
    [buscado],
  );

  if (archivo.isPending) return <Cargando texto="Abriendo el documento…" />;
  if (archivo.isError) return <ErrorConsulta error={archivo.error} reintentar={() => void archivo.refetch()} />;

  const datos = archivo.data;
  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <span className="inline-flex items-center gap-2 font-medium">
          <FileText className="size-4 text-tenue" aria-hidden /> {datos.nombre}
        </span>
        <a
          href={datos.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-xs text-primario hover:underline"
        >
          Abrir el original <ExternalLink className="size-3" aria-hidden />
        </a>
      </div>
      {fuente.fragmento ? (
        <blockquote className="rounded-md border-l-4 border-advertencia bg-advertencia-suave/60 px-3 py-2 text-sm">
          «{fuente.fragmento}»
          {fuente.pagina ? <span className="ml-2 text-xs text-tenue">(página {fuente.pagina})</span> : null}
        </blockquote>
      ) : null}
      {datos.formato !== "pdf" ? (
        <Aviso tono="neutro" titulo="Los DOCX no tienen visor en la aplicación">
          Se muestra el fragmento citado; el original se abre con el enlace de arriba.
        </Aviso>
      ) : (
        <div ref={medir} className="min-h-0 flex-1 overflow-auto rounded-md border border-borde bg-neutro-suave p-2">
          <Document
            file={origen?.url ?? datos.url}
            onLoadSuccess={({ numPages }) => {
              setPaginas(numPages);
              setPagina((actual) => Math.min(Math.max(1, actual), numPages));
            }}
            loading={<Cargando texto="Cargando páginas…" />}
            error={<Aviso tono="peligro" titulo="No se pudo mostrar el PDF. Usá «Abrir el original»." />}
          >
            <Page pageNumber={pagina} width={ancho} customTextRenderer={resaltar} renderAnnotationLayer={false} />
          </Document>
        </div>
      )}
      {datos.formato === "pdf" && paginas > 1 ? (
        <div className="flex items-center justify-center gap-3 text-sm">
          <Boton variante="secundario" tamano="icono" aria-label="Página anterior" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
            <ChevronLeft />
          </Boton>
          <span>
            Página {pagina} de {paginas}
          </span>
          <Boton variante="secundario" tamano="icono" aria-label="Página siguiente" disabled={pagina >= paginas} onClick={() => setPagina(pagina + 1)}>
            <ChevronRight />
          </Boton>
        </div>
      ) : null}
    </div>
  );
}

export default VisorDocumento;
