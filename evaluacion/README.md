# Arnés de medición de §6.3.1 — guía del operador

Decisión: **DO-2026-10-23-E90-MEDICION**. Código: `backend/src/atlas/evaluacion/` (fuera del
paquete Lambda). Mide **el código de producción** de ATLAS (clasificación, extracción,
procedencia, segmentación, recuperación y respuestas) llamando directamente a Textract y a
Bedrock desde la máquina del operador. La latencia IA-M08 y la carga §6.3.4 se miden contra
la API desplegada con `python -m atlas.evaluacion.operacion` (DO-2026-10-23-E90-API; ver
«Fase 2» al final).

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
- No mide §6.3.2 ni §6.3.3 (P18).
- No decide sustituciones: calcula las reglas sobre promedios y la decisión la registra el equipo.
- No usa juez automático para las respuestas.

## Fase 2: latencia IA-M08 y carga §6.3.4 contra la API

Decisión **DO-2026-10-23-E90-API**. Requiere una sesión E90A en `active`, con la semilla ya
corrida (cuentas de Cognito y de ATLAS) y `ATLAS_SEED_CLAVE_RESPONSABLE` exportada.

**Fase 0 adicional:** la concurrencia de Lambda de la cuenta (las cuentas nuevas pueden tener
10). Si no alcanza para el nivel 10, se informa; no se cambia sin aprobación (P10).

```bash
aws lambda get-account-settings --query "AccountLimit.ConcurrentExecutions"
aws bedrock get-inference-profile --inference-profile-identifier <perfil de Sonnet 4.6> --query "models[].modelArn" --output text
```

La segunda consulta da el `modelo_generativo` que acompaña al perfil de Sonnet en `demo` (las
políticas IAM autorizan el perfil y sus modelos de destino).

**Pasos**, desde `backend/`:

```bash
python -m atlas.evaluacion.operacion iniciar --campana <id> --modo oficial \
  --url-api "$URL" --version-codigo <commit desplegado> --cliente-cognito <cliente> \
  --generativos haiku=us.anthropic.claude-haiku-4-5-20251001-v1:0 sonnet=<perfil de Sonnet 4.6>
python -m atlas.evaluacion.operacion cargar --campana <id>    # un trámite por contexto (12)
python -m atlas.evaluacion.operacion red --campana <id>       # 30 GET /salud
```

Latencia, un bloque por modelo y repetición, en el orden **H1, S1 │ S2, H2 │ H3, S3**. Antes de
cada bloque de otro modelo, reaplicar `demo` con `perfil_generativo` y `modelo_generativo`
de ese modelo (plan esperado: 4 Lambda y 1 política en el lugar):

```bash
python -m atlas.evaluacion.operacion latencia --campana <id> --modelo haiku --repeticion 1
# reaplicar demo con Sonnet
python -m atlas.evaluacion.operacion latencia --campana <id> --modelo sonnet --repeticion 1
python -m atlas.evaluacion.operacion latencia --campana <id> --modelo sonnet --repeticion 2
# reaplicar demo con Haiku
python -m atlas.evaluacion.operacion latencia --campana <id> --modelo haiku --repeticion 2
python -m atlas.evaluacion.operacion latencia --campana <id> --modelo haiku --repeticion 3
# reaplicar demo con Sonnet
python -m atlas.evaluacion.operacion latencia --campana <id> --modelo sonnet --repeticion 3
# volver a Haiku (producción) antes de seguir usando la demo
```

Cada respuesta trae el perfil que la generó: si no coincide con el declarado, el informe lo
cuenta como «perfil distinto» (despliegue equivocado). Un bloque ya medido no se repite.

Carga (usa la partición de ajuste; se puede correr antes de congelar, también en una campaña
`ensayo`) y métricas:

```bash
python -m atlas.evaluacion.operacion carga --campana <id>     # niveles 1, 5 y 10
python -m atlas.evaluacion.operacion metricas --campana <id>
```

La latencia se mide en el cliente: incluye la red hasta us-east-1, que se informa aparte con
la línea de base de `GET /salud`. El encabezado `Server-Timing` de cada respuesta da los
componentes del servidor (embeddings, recuperación, generación, total) y si fue un arranque en
frío. Mediana y p95 por rango más cercano, sin excluir observaciones.

En modo `ensayo`, la latencia usa tres preguntas genéricas sobre el ajuste: sirve para probar
el ejecutor y **no es IA-M08**.
