# Arnés de medición de §6.3.1 — guía del operador

Decisión: **DO-2026-10-23-E90-MEDICION**. Código: `backend/src/atlas/evaluacion/` (fuera del
paquete Lambda). Mide **el código de producción** de ATLAS (clasificación, extracción,
procedencia, segmentación, recuperación y respuestas) llamando directamente a Textract y a
Bedrock desde la máquina del operador. La latencia IA-M08 y la carga §6.3.4 se miden contra
la API desplegada en la fase 2 (P17), todavía no implementada.

**Lo ejecuta solo el operador autorizado**, con el plan y el costo aprobados (DO-2026-10-21).
Ningún agente, push ni GitHub Action lo corre contra AWS.

## Compuerta (P4)

| Modo | Documentos | Preguntas RAG | Para qué |
|---|---|---|---|
| `ensayo` | Los 15 de **ajuste** | Ninguna | Probar el arnés y los servicios; el informe dice **NO REPORTABLE** |
| `oficial` | Los 50 de **medición** | Las 30 | Resultados de §6.3.1; exige oráculos `CONGELADO` y revisados por los autores |

Nadie ve resultados de la medición antes de congelar. El arnés se niega a una campaña
oficial si los oráculos no están congelados, si hay cambios sin commit o si un archivo del
corpus no coincide con su huella. Una vez creada, la campaña se niega a seguir si cambian el
corpus, los oráculos, las instrucciones, los esquemas o la segmentación: eso exige una
campaña nueva.

## Qué queda en `evaluacion/campanas/<id>/`

- `manifiesto.json`: commit, modelos y perfiles, región, límites, temperatura y huellas.
- `ocr.jsonl`, `clasificacion_extraccion.jsonl`, `recuperacion.jsonl`, `respuestas.jsonl`:
  una fila por llamada, con salida, tokens, duración, errores e intentos. Se versionan (datos
  sintéticos). Una campaña interrumpida se retoma sin repetir lo registrado.
- `indices/<alias>.json`: el índice congelado de cada modelo de embeddings, con su huella.
- `planillas/autor_a.csv`, `autor_b.csv`, `discrepancias.csv`, `consenso.csv` (IA-M06).
- `metricas.json` e `informe.md`.

El OCR se guarda en `evaluacion/cache_ocr/` por huella del archivo y se reutiliza en todas
las repeticiones, modelos y campañas (RC-P07.5).

## Antes de la primera campaña (fase 0)

```bash
export AWS_PROFILE=tesis AWS_REGION=us-east-1
aws bedrock list-inference-profiles --query "inferenceProfileSummaries[?contains(inferenceProfileId,'haiku-4-5') || contains(inferenceProfileId,'sonnet-4-6')].[inferenceProfileId,status]" --output text
aws bedrock get-foundation-model --model-identifier amazon.titan-embed-text-v2:0 --query "modelDetails.modelLifecycle.status"
aws bedrock get-foundation-model --model-identifier cohere.embed-multilingual-v3 --query "modelDetails.modelLifecycle.status"
```

El perfil de Sonnet 4.6 que se usa es el que devuelve la primera consulta (P12); queda
registrado en el manifiesto.

## Bucket de la campaña (raíz `infra/terraform/evaluacion`)

Un solo bucket, sin RDS ni VPC: cifrado, bloqueo público, solo TLS y ciclo de vida de un día.
Solo recibe copias del corpus sintético; por eso admite `force_destroy`.

```bash
cd infra/terraform/evaluacion
cp terraform.tfvars.example terraform.tfvars        # completar; no se versiona
terraform init -backend-config=../backend.hcl
terraform plan -out=evaluacion.tfplan               # esperado: 6 to add
terraform apply evaluacion.tfplan
```

Al terminar la campaña: `terraform plan -destroy -out=retiro.tfplan` (6 to destroy) y apply.

## Pasos de una campaña

Desde `backend/`, con el entorno exportado:

```bash
python -m atlas.evaluacion iniciar --campana <id> --modo ensayo \
  --generativos haiku=us.anthropic.claude-haiku-4-5-20251001-v1:0 sonnet=<perfil de Sonnet 4.6> \
  --embeddings cohere=cohere.embed-multilingual-v3 titan=amazon.titan-embed-text-v2:0 \
  --repeticiones 3 --bucket <bucket de la raíz evaluacion>
python -m atlas.evaluacion ocr --campana <id>         # Textract, una vez por PDF
python -m atlas.evaluacion medir --campana <id>       # clasificación y extracción, 3 × 2 modelos
python -m atlas.evaluacion indexar --campana <id>     # un índice por modelo de embeddings
python -m atlas.evaluacion recuperar --campana <id>   # Recall@5 y MRR (solo oficial)
python -m atlas.evaluacion responder --campana <id>   # respuestas con citas (solo oficial)
python -m atlas.evaluacion planillas --campana <id>   # planillas en blanco para los autores
python -m atlas.evaluacion metricas --campana <id>    # informe sin IA-M06
```

El primer alias de `--generativos` y de `--embeddings` es el de producción (Haiku, Cohere): las
respuestas usan los fragmentos que recupera Cohere, idénticos para ambos modelos generativos.

## Calificación de las respuestas (IA-M06)

1. Cada autor completa **su** planilla sin ver la del otro: `calificacion` (`correcta`,
   `parcial`, `incorrecta`; en las sin respuesta, `abstencion_correcta` o
   `abstencion_incorrecta`), `afirmaciones_sustantivas` y `afirmaciones_respaldadas`. Rúbrica:
   RC-P06.2.10. Las respuestas idénticas aparecen una sola vez, con sus ocurrencias.
2. `python -m atlas.evaluacion discrepancias --campana <id>` escribe `discrepancias.csv`.
3. Los autores resuelven juntos cada discrepancia y guardan el resultado como `consenso.csv`
   (mismas columnas). Las planillas individuales no se modifican.
4. `python -m atlas.evaluacion metricas --campana <id> --con-calificaciones`.

## Costo orientativo (ratificar con las tarifas vigentes, RC-P10-13)

| Partida | Ensayo (ajuste) | Oficial (medición) |
|---|---|---|
| Textract TABLES + LAYOUT | 12 páginas ≈ USD 0,25 | 73 páginas ≈ USD 1,40 |
| Clasificación y extracción, 3 repeticiones | Haiku + Sonnet ≈ USD 2 | Haiku + Sonnet ≈ USD 8–12 |
| Respuestas, 30 × 3 × 2 | — | ≈ USD 1–2 |
| Embeddings (Cohere y Titan) | centavos | centavos |
| Bucket | centavos | centavos |

## Qué no hace

- No congela ni revisa oráculos: eso es de los autores.
- No mide la latencia ni la carga (fase 2) ni §6.3.2/§6.3.3 (P18).
- No decide sustituciones: calcula las reglas sobre promedios y la decisión la registra el equipo.
- No usa juez automático para las respuestas.
