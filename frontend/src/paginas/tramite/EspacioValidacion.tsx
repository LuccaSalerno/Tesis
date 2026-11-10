/**
 * Espacio de validación (Fig. 3.6, RF-09 a RF-12): el documento a la izquierda y la
 * clasificación y los campos a la derecha. Cada dato muestra la sugerencia de la IA (punteada)
 * separada del valor validado (sólido), con su fuente en el documento. Nunca se valida sin
 * una acción explícita de la persona; un dato ausente se declara, no se inventa (WEB F10).
 */
import { ArrowLeft, Check, ChevronDown, History, PencilLine, Plus } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useParams } from "react-router";

import { useArchivos, useRegistrarValidacion, useValidaciones } from "@/api/consultas";
import { ReintentarProcesamiento } from "@/componentes/reintento";
import type { DatoValidacion, MotivoAusencia } from "@/api/tipos";
import { BotonFuente, InsigniaEstado, TextoLocalizador, ValorSugerido, ValorValidado } from "@/componentes/dominio";
import { VisorDocumento, type Fuente } from "@/componentes/visor";
import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { Ayuda, Entrada, Selector } from "@/componentes/ui/campos";
import { Cargando, ErrorConsulta, mensajeDeError } from "@/componentes/ui/estados";
import { Insignia } from "@/componentes/ui/insignia";
import { ESTADO_TRABAJO, MOTIVO_AUSENCIA, rotuloCampo, TIPO_DOCUMENTAL } from "@/lib/dominio";
import { valorLegible } from "@/lib/formatos";
import { AYUDA, claseDeCampo, errorDeFormato } from "@/lib/validacion";

import { useContextoTramite, useIdTramite } from "./MarcoTramite";

const ESTADOS_QUE_ADMITEN = new Set(["borrador", "pendiente_validacion"]);

type Edicion = { modo: "valor"; valor: string } | { modo: "ausente"; motivo: MotivoAusencia } | null;

function Dato({
  dato,
  editable,
  alVerFuente,
  registrar,
}: {
  dato: DatoValidacion;
  editable: boolean;
  alVerFuente: (fuente: Omit<Fuente, "versionId">) => void;
  registrar: ReturnType<typeof useRegistrarValidacion>;
}) {
  const [edicion, setEdicion] = useState<Edicion>(null);
  const [verHistorial, setVerHistorial] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esClasificacion = dato.campo === "tipo_documental";
  const sugerencia = dato.sugerencia;
  const vigente = dato.vigente;
  const confirmable = !!sugerencia && (!vigente || vigente.valor_validado !== sugerencia.valor || vigente.valor_sugerido_id !== sugerencia.id);

  async function enviar(cuerpo: { valor_validado?: string; ausente?: MotivoAusencia }) {
    setError(null);
    try {
      await registrar.mutateAsync({
        campo: dato.campo,
        valor_sugerido_id: sugerencia?.id ?? null,
        reemplaza_a_id: vigente?.id ?? null,
        ...cuerpo,
      });
      setEdicion(null);
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  function guardar(evento: FormEvent) {
    evento.preventDefault();
    if (edicion?.modo === "valor") {
      const problema = esClasificacion ? null : errorDeFormato(dato.campo, edicion.valor);
      if (problema) return setError(problema);
      void enviar({ valor_validado: edicion.valor.trim() });
    } else if (edicion?.modo === "ausente") {
      void enviar({ ausente: edicion.motivo });
    }
  }

  return (
    <li className="py-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{rotuloCampo(dato.campo)}</h3>
        {vigente ? null : <Insignia tono="advertencia">Sin validar</Insignia>}
      </div>
      <div className="grid gap-2">
        {sugerencia ? (
          <ValorSugerido campo={dato.campo} valor={sugerencia.valor} modelo={sugerencia.modelo}>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-tenue">
              <TextoLocalizador localizador={sugerencia.localizador} />
              {sugerencia.localizador ? (
                <BotonFuente onClick={() => alVerFuente({ pagina: sugerencia.localizador?.pagina, fragmento: sugerencia.localizador?.fragmento, titulo: rotuloCampo(dato.campo) })} />
              ) : null}
            </div>
          </ValorSugerido>
        ) : (
          <p className="text-xs text-tenue">Sin sugerencia automática para este dato.</p>
        )}
        {vigente ? (
          <ValorValidado campo={dato.campo} validacion={vigente} />
        ) : null}
      </div>

      {editable && edicion === null ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {confirmable ? (
            <Boton tamano="chico" disabled={registrar.isPending} onClick={() => void enviar({ valor_validado: sugerencia!.valor })}>
              <Check /> Confirmar sugerencia
            </Boton>
          ) : null}
          <Boton tamano="chico" variante="secundario" onClick={() => setEdicion({ modo: "valor", valor: vigente?.valor_validado ?? sugerencia?.valor ?? "" })}>
            {sugerencia || vigente ? <PencilLine /> : <Plus />} {sugerencia || vigente ? "Corregir" : "Registrar valor"}
          </Boton>
          {!esClasificacion ? (
            <Boton tamano="chico" variante="sutil" onClick={() => setEdicion({ modo: "ausente", motivo: "no_consta" })}>
              No consta / no aplica
            </Boton>
          ) : null}
        </div>
      ) : null}

      {edicion ? (
        <form onSubmit={guardar} className="mt-3 space-y-2 rounded-md border border-borde bg-neutro-suave/50 p-3">
          {edicion.modo === "valor" ? (
            esClasificacion ? (
              <Selector aria-label="Tipo documental" value={edicion.valor} onChange={(e) => setEdicion({ modo: "valor", valor: e.target.value })}>
                <option value="" disabled>Elegí un tipo</option>
                {Object.entries(TIPO_DOCUMENTAL).map(([valor, rotulo]) => (
                  <option key={valor} value={valor}>{rotulo}</option>
                ))}
              </Selector>
            ) : (
              <>
                <Entrada aria-label={`Valor de ${rotuloCampo(dato.campo)}`} value={edicion.valor} onChange={(e) => setEdicion({ modo: "valor", valor: e.target.value })} autoFocus aria-invalid={!!error} />
                <Ayuda>Formato: {AYUDA[claseDeCampo(dato.campo)]}</Ayuda>
              </>
            )
          ) : (
            <fieldset className="space-y-1 text-sm">
              <legend className="mb-1 font-medium">¿Por qué no tiene valor?</legend>
              {(Object.keys(MOTIVO_AUSENCIA) as MotivoAusencia[]).map((motivo) => (
                <label key={motivo} className="flex items-center gap-2">
                  <input type="radio" name={`motivo-${dato.campo}`} checked={edicion.motivo === motivo} onChange={() => setEdicion({ modo: "ausente", motivo })} />
                  {MOTIVO_AUSENCIA[motivo]}
                </label>
              ))}
              <Ayuda>Queda registrado quién lo declaró y cuándo; no se inventa un valor.</Ayuda>
            </fieldset>
          )}
          <div className="flex gap-2">
            <Boton type="submit" tamano="chico" disabled={registrar.isPending || (edicion.modo === "valor" && !edicion.valor.trim())}>
              Guardar
            </Boton>
            <Boton tamano="chico" variante="sutil" onClick={() => { setEdicion(null); setError(null); }}>
              Cancelar
            </Boton>
          </div>
        </form>
      ) : null}
      {error ? <Aviso className="mt-2" tono="peligro" titulo={error} /> : null}

      {dato.historial.length > 1 ? (
        <div className="mt-2">
          <button type="button" className="inline-flex items-center gap-1 text-xs text-tenue hover:text-texto" onClick={() => setVerHistorial(!verHistorial)} aria-expanded={verHistorial}>
            <History className="size-3.5" /> Historial ({dato.historial.length}) <ChevronDown className="size-3" />
          </button>
          {verHistorial ? (
            <ol className="mt-2 space-y-1 border-l border-borde pl-3 text-xs text-tenue">
              {dato.historial.map((v) => (
                <li key={v.id}>
                  {v.tipo === "ausente" ? MOTIVO_AUSENCIA[v.motivo_ausencia ?? "no_consta"] : valorLegible(dato.campo, v.valor_validado)}
                  {v.id === vigente?.id ? " (vigente)" : " (reemplazada)"}
                </li>
              ))}
            </ol>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}

export function EspacioValidacion() {
  const id = useIdTramite();
  const documentoId = Number(useParams().documentoId);
  const { tramite, esResponsable } = useContextoTramite();
  const validaciones = useValidaciones(id, documentoId);
  const archivos = useArchivos(id);
  const registrar = useRegistrarValidacion(id, documentoId);
  const [fuente, setFuente] = useState<Omit<Fuente, "versionId"> | null>(null);

  if (validaciones.isPending) return <Cargando />;
  if (validaciones.isError) return <ErrorConsulta error={validaciones.error} reintentar={() => void validaciones.refetch()} />;
  const datos = validaciones.data;
  const documento = tramite.documentos.find((d) => d.id === documentoId);
  const trabajo = archivos.data?.find((a) => a.id === datos.version.archivo_id)?.trabajo;
  const editable = esResponsable && ESTADOS_QUE_ADMITEN.has(tramite.estado);
  const resueltos = datos.campos.filter((c) => c.vigente).length;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link to=".." relative="path" className="inline-flex items-center gap-1 text-sm text-tenue hover:text-texto">
            <ArrowLeft className="size-4" /> Documentos
          </Link>
          <h2 className="text-lg">{documento?.nombre ?? `Documento ${documentoId}`}</h2>
          <Insignia tono="primario">v{datos.version.numero} vigente</Insignia>
          {trabajo ? <InsigniaEstado catalogo={ESTADO_TRABAJO} valor={trabajo.estado} /> : null}
        </div>
        {datos.tipo_validado ? (
          <p className="text-sm text-tenue">{resueltos} de {datos.campos.length} campos resueltos</p>
        ) : null}
      </div>
      {!editable && esResponsable ? (
        <Aviso tono="neutro" className="mb-4" titulo="El estado del trámite no admite validar datos">
          Se valida en Borrador o Pendiente de validación; si fue observado, primero se subsana.
        </Aviso>
      ) : null}
      {trabajo && (trabajo.estado === "pendiente" || trabajo.estado === "en_ejecucion") ? (
        <Aviso tono="info" className="mb-4" titulo="El documento se está procesando">Las sugerencias aparecerán al terminar; podés registrar valores igualmente.</Aviso>
      ) : null}
      {trabajo?.estado === "en_espera" ? (
        <Aviso tono="neutro" className="mb-4" titulo="En espera de capacidad de procesamiento">El procesamiento empezará solo cuando haya capacidad; podés registrar valores igualmente.</Aviso>
      ) : null}
      {trabajo?.estado === "fallido" ? (
        <Aviso tono="advertencia" className="mb-4" titulo="El procesamiento automático falló">
          No hay sugerencias: los datos se registran manualmente con su fuente en el documento.
          {esResponsable ? (
            <span className="mt-2 flex flex-wrap gap-2">
              <ReintentarProcesamiento tramiteId={id} archivoId={datos.version.archivo_id} />
            </span>
          ) : null}
        </Aviso>
      ) : null}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(22rem,1fr)]">
        <div className="h-[calc(100vh-14rem)] min-h-[32rem] rounded-lg border border-borde bg-superficie p-4 lg:sticky lg:top-4">
          <VisorDocumento tramiteId={id} fuente={{ versionId: datos.version.id, ...fuente }} />
        </div>
        <div className="rounded-lg border border-borde bg-superficie px-5">
          <ul className="divide-y divide-borde">
            <Dato dato={datos.clasificacion} editable={editable} alVerFuente={setFuente} registrar={registrar} />
            {datos.tipo_validado ? (
              datos.campos.map((c) => <Dato key={c.campo} dato={c} editable={editable} alVerFuente={setFuente} registrar={registrar} />)
            ) : (
              <li className="py-4 text-sm text-tenue">Los campos se presentan después de validar la clasificación.</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
