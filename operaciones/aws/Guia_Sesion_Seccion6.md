# Guía paso a paso: sesión AWS de la sección 6 y demo (cuenta nueva)

**Para:** el operador humano (Lucca). **Fecha:** 23/10/2026. **Autoridad:** DO-2026-10-21, DO-2026-10-21-E90A, DO-2026-10-22-OPS y las decisiones de cada ejecutor. Reúne en un solo lugar lo que estaba repartido en [infra/terraform/README.md](../../infra/terraform/README.md), [evaluacion/README.md](../../evaluacion/README.md) y [README_CONFIGURACION_ETAPA_0.md](README_CONFIGURACION_ETAPA_0.md); ante una duda de detalle, esos documentos siguen valiendo.

Reglas que no cambian: todo lo ejecutás vos, con tus credenciales; nada desde GitHub ni desde el agente. Nunca pegues contraseñas, tokens ni claves en el chat ni en el repositorio. Nada de `terraform destroy` global ni `state rm`.

Tiempo total estimado: **6 a 8 horas** (la primera vez en una cuenta nueva, más). Costo: ver [RC-P10-13_Cotizacion_Sesion_E90A.md](../../docs/operacion/RC-P10-13_Cotizacion_Sesion_E90A.md) más la medición de §6.3.1 (≈ USD 12–16, ver evaluacion/README.md). La facturación empieza al aplicar `persistent`.

> **Cuenta elegida para la sesión del 24/10/2026: la ya preparada (`014574285566`, perfil `tesis`).** La cuenta nueva quedó descartada por ahora: estaba en verificación y con cuotas de Bedrock casi nulas. Con la cuenta preparada, **se saltea la Parte 0** (hecha el 21/10) y de la Parte 1 solo se hacen 1.1 y la reinicialización de `demo`; los `terraform.tfvars` ya están preparados para la sesión `e90-2026-10-24`. La cuota de Lambda de esa cuenta es **10**: el límite de procesamiento de ATLAS se bajó a **3** (`limite_concurrencia` en `demo`), §6.3.2 corre con `--limite 3` y §6.3.4 se informa con esa limitación mientras no se apruebe el aumento.

---

## Parte 0 — Cuenta AWS nueva (una sola vez por cuenta)

### 0.1 Identidad y perfil local

- [ ] Entrá con una identidad administradora **con MFA** (no root). Región: `us-east-1`.
- [ ] Configurá un perfil nuevo en tu máquina (SSO o usuario IAM, lo que use la cuenta):
  ```bash
  aws configure sso            # o: aws configure --profile tesis-nueva
  export AWS_PROFILE=tesis-nueva AWS_REGION=us-east-1
  aws sts get-caller-identity --query '{Cuenta:Account,Arn:Arn}'
  ```
  Anotá el número de cuenta (lo usan todos los `terraform.tfvars`). En cada terminal nueva, volvé a exportar `AWS_PROFILE` y `AWS_REGION`.

### 0.2 Exclusión de servicios de IA (Organizations)

- [ ] Organizations → *AI services opt-out policies* → «Opt out from all services», adjunta a la cuenta (o a la raíz). Si la cuenta es miembro de otra organización, se lo pedís a su administrador.
- [ ] Verificación:
  ```bash
  aws organizations describe-effective-policy --policy-type AISERVICES_OPT_OUT_POLICY \
    --query 'EffectivePolicy.PolicyContent' --output text
  ```

### 0.3 Bedrock: acceso a los cuatro modelos

- [ ] Bedrock → *Model catalog* en `us-east-1`: Claude Haiku 4.5, Claude Sonnet 4.6, Cohere Embed Multilingual v3 y Titan Text Embeddings V2. En Anthropic completá el formulario de primer uso si aparece (finalidad académica real).
- [ ] Verificación y perfil de Sonnet:
  ```bash
  aws bedrock list-inference-profiles --query "inferenceProfileSummaries[?contains(inferenceProfileId,'haiku-4-5') || contains(inferenceProfileId,'sonnet-4-6')].[inferenceProfileId,status]" --output text
  aws bedrock get-foundation-model --model-identifier cohere.embed-multilingual-v3 --query "modelDetails.modelLifecycle.status"
  aws bedrock get-foundation-model --model-identifier amazon.titan-embed-text-v2:0 --query "modelDetails.modelLifecycle.status"
  ```
  Anotá el perfil **us.** de Sonnet 4.6 (lo usan §6.3.1 y §6.3.4). No uses perfiles `global.`.
- [ ] *Settings → Model invocation logging*: **desactivado**, sin destino S3 ni CloudWatch.

### 0.4 Cuotas y presupuesto

- [ ] Concurrencia de Lambda. Las cuentas nuevas suelen tener **10**, que no alcanza (cinco funciones más el procesamiento en paralelo):
  ```bash
  aws lambda get-account-settings --query "AccountLimit.ConcurrentExecutions"
  ```
  Si da menos de 100, pedí el aumento en *Service Quotas → AWS Lambda → Concurrent executions* (por ejemplo, 1000) **cuanto antes**: puede tardar horas o días. Sin él, el procesamiento y la carga de §6.3.4 quedan limitados.
- [ ] AWS Budgets con alertas (solo alertan, no cortan el gasto).
- [ ] Aprobá por escrito el costo de la sesión (cotización más medición).

---

## Parte 1 — Repositorio y Terraform apuntando a la cuenta nueva

### 1.1 Repositorio limpio

```bash
cd ~/development/Tesis
git checkout fundacion/local-backend && git pull
git status --short          # debe quedar vacío
```

- [ ] Commiteá o descartá `operaciones/aws/README_CONFIGURACION_ETAPA_0.md` (está modificado en tu copia). **La medición oficial de §6.3.1 se niega a correr con cambios sin commit.**

### 1.2 Archivar el estado de la cuenta anterior (solo si cambiás de cuenta)

Con la cuenta ya preparada, en lugar de 1.2 a 1.4 alcanza con:

```bash
(cd infra/terraform/demo && terraform init -backend-config=../backend.hcl)
```


El estado de `bootstrap` es local y apunta al bucket de la cuenta vieja; las demás raíces tienen inicializado el backend viejo. Guardalos fuera del repositorio y empezá de cero:

```bash
mkdir -p ~/atlas-cuenta-anterior
mv infra/terraform/bootstrap/terraform.tfstate* ~/atlas-cuenta-anterior/ 2>/dev/null
cp infra/terraform/backend.hcl ~/atlas-cuenta-anterior/ 2>/dev/null
for r in bootstrap persistent runtime demo web evaluacion; do rm -rf infra/terraform/$r/.terraform infra/terraform/$r/*.tfplan; done
```

El bucket de estado viejo (`atlas-estado-terraform-5566`) queda en la cuenta anterior. No cuesta casi nada; si querés borrarlo, es aparte y a mano.

### 1.3 Variables de cada raíz

En **cada** `infra/terraform/<raíz>/terraform.tfvars` (copiá el `.example` si no existe) poné el número de cuenta nuevo en `cuenta_id`. El proveedor rechaza cualquier otra cuenta (`allowed_account_ids`). Usá un sufijo único nuevo para todos los buckets (por ejemplo, `lsx24`):

| Raíz | Qué completar |
|---|---|
| `bootstrap` | `cuenta_id`, `nombre_bucket_estado = "atlas-estado-terraform-<sufijo>"` |
| `web` | `cuenta_id`, `nombre_bucket = "atlas-web-<sufijo>"` |
| `persistent` | `cuenta_id`, `sesion = "e90-2026-10-24"`, `nombre_bucket_documentos = "atlas-demo-documentos-e90-2026-10-24-<sufijo>"`, `origenes_cors` (paso 2.3) |
| `runtime` | `cuenta_id`, `bucket_estado` (el de `bootstrap`) |
| `demo` | `cuenta_id`, `bucket_estado`, `nombre_bucket_artefactos = "atlas-demo-artefactos-e90-2026-10-24-<sufijo>"`, `version_codigo` (paso 2.1), `origenes_web` (paso 2.3) |
| `evaluacion` | `cuenta_id`, `campana = "e90-oficial-1"`, `nombre_bucket = "atlas-evaluacion-e90-oficial-1-<sufijo>"` |

### 1.4 Bootstrap y backend

```bash
cd infra/terraform/bootstrap
terraform init
terraform plan -out=bootstrap.tfplan      # solo el bucket de estado y sus controles
terraform apply bootstrap.tfplan
terraform output -raw bucket_estado
cd ..
cp backend.hcl.example backend.hcl        # bucket = el de la salida anterior
cd ../..
```

Respaldá `infra/terraform/bootstrap/terraform.tfstate` fuera del repositorio.

---

## Parte 2 — Encendido

Anotá la hora de inicio. Desde la raíz del repositorio.

### 2.1 Paquete Lambda

```bash
infra/empaquetado/construir_lambda.sh      # usa infra/certificados/*.pem
git rev-parse --short HEAD                 # va en version_codigo de demo
```

### 2.2 Aplicación web (CloudFront, una sola vez por cuenta)

```bash
cd infra/terraform/web
terraform init -backend-config=../backend.hcl
terraform plan -out=web.tfplan             # esperado: 8 to add
terraform apply web.tfplan                 # CloudFront tarda 5–15 min
terraform output -raw origen               # https://<id>.cloudfront.net
cd ../../.. && infra/web/publicar.sh --aplicacion
```

### 2.3 Orígenes permitidos

Poné el `origen` anterior y `http://localhost:4173` en `origenes_cors` (persistent) y `origenes_web` (demo).

### 2.4 persistent, runtime y demo

```bash
for r in persistent runtime demo; do
  (cd infra/terraform/$r && terraform init -backend-config=../backend.hcl && terraform plan -out=$r.tfplan)
done
```

Revisá cada plan y aplicá **en orden** (persistent tarda 20–30 min por RDS Multi-AZ):

```bash
(cd infra/terraform/persistent && terraform apply persistent.tfplan)
(cd infra/terraform/runtime && terraform plan -out=runtime.tfplan && terraform apply runtime.tfplan)
(cd infra/terraform/demo && terraform plan -out=demo.tfplan && terraform apply demo.tfplan)
```

`runtime` crea ahora también el endpoint de VPC `lambda` (supresión de cuentas, RF-25) y `demo`, la sexta Lambda `cuentas`.

> **Mientras RDS se crea** podés avanzar con la Parte 4.1 (§6.3.1): no usa la API.

### 2.5 Base de datos

```bash
FN=$(terraform -chdir=infra/terraform/demo output -raw funcion_operaciones)
for a in inicializar_base migrar estado_migraciones; do
  aws lambda invoke --function-name "$FN" --cli-read-timeout 320 --cli-binary-format raw-in-base64-out \
    --payload "{\"accion\":\"$a\"}" /dev/stdout; echo
done                                        # el último: al_dia true
```

`inicializar_base` es de un solo uso: si falla, **no** reintentar; pegame el error. Después, en `runtime`: `endpoint_secrets_manager = false`, plan y apply.

### 2.6 Cuentas ficticias de Cognito (siete)

Guardá las siete contraseñas en tu gestor; nunca en el chat.

```bash
POOL=$(terraform -chdir=infra/terraform/persistent output -raw cognito_user_pool_id)
for u in atlas-admin atlas-responsable atlas-revisor atlas-aprobador atlas-responsable-2 atlas-revisor-2 atlas-deshabilitada; do
  aws cognito-idp admin-create-user --user-pool-id "$POOL" --username "$u" --message-action SUPPRESS >/dev/null
  read -rs -p "Clave de $u: " CLAVE; echo
  aws cognito-idp admin-set-user-password --user-pool-id "$POOL" --username "$u" --password "$CLAVE" --permanent
done
SUB=$(aws cognito-idp admin-get-user --user-pool-id "$POOL" --username atlas-admin \
  --query "UserAttributes[?Name=='sub'].Value" --output text)
aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
  --payload "{\"accion\":\"crear_administrador\",\"identificador_externo\":\"$SUB\"}" /dev/stdout
```

En cada terminal de las partes siguientes, exportá las claves leyéndolas sin eco:

```bash
for v in ADMINISTRADOR RESPONSABLE REVISOR APROBADOR RESPONSABLE_2 REVISOR_2 DESHABILITADA; do
  read -rs -p "ATLAS_SEED_CLAVE_$v: " x; echo; export "ATLAS_SEED_CLAVE_$v=$x"
done
```

### 2.7 Configuración web, `active` y salud

```bash
infra/web/publicar.sh --configuracion
BUCKET=$(terraform -chdir=infra/terraform/persistent output -raw bucket_documentos)
URL=$(terraform -chdir=infra/terraform/demo output -raw url_api)
CLIENTE=$(terraform -chdir=infra/terraform/persistent output -raw cognito_cliente_id)
echo '{"estado":"active"}' | aws s3 cp - "s3://$BUCKET/control/mantenimiento.json" --content-type application/json
sleep 20 && curl -s "${URL}salud"           # operacion: active
```

---

## Parte 3 — Semilla y demo

```bash
cd backend
.venv/bin/python -m atlas.herramientas.sembrar_demo --url-api "$URL" --sesion e90-2026-10-24 \
  --cliente-cognito "$CLIENTE" \
  --usuarios administrador=atlas-admin responsable=atlas-responsable revisor=atlas-revisor aprobador=atlas-aprobador \
  --manifiesto ../operaciones/sesiones/e90-2026-10-24/manifiesto_seed.json
cd ..
```

Tarda 15–25 min (Textract y Bedrock reales). Deja cuatro trámites: **observado**, **en vivo**, **cerrado con firma** y **cancelado**. Si falla, volvé a `offline` y pegame el error; no la repitas sobre datos sin auditar.

- [ ] Humo en `https://<origen>` (CloudFront): ingresar con cada rol, abrir los cuatro trámites, firma visible en el cerrado, estado general en Administración.
- [ ] **Demo:** hacela acá, antes de los ejecutores que agregan datos (§6.3.2 y §6.3.3).

---

## Parte 4 — Ejecutores de la sección 6 (en este orden)

Desde `backend/`, con `AWS_PROFILE`, `AWS_REGION`, `URL`, `CLIENTE`, `BUCKET` y las claves exportadas. Cada ejecutor deja su evidencia en `evaluacion/campanas/<id>/`: **commiteala** al terminar cada parte.

### 4.1 §6.3.1 — Medición de IA (corpus congelado, modo oficial)

```bash
(cd ../infra/terraform/evaluacion && terraform init -backend-config=../backend.hcl \
  && terraform plan -out=evaluacion.tfplan && terraform apply evaluacion.tfplan)   # 6 to add
EVAL=$(terraform -chdir=../infra/terraform/evaluacion output -raw bucket)
C=e90-oficial-1
.venv/bin/python -m atlas.evaluacion iniciar --campana $C --modo oficial \
  --generativos haiku=us.anthropic.claude-haiku-4-5-20251001-v1:0 sonnet=<perfil us. de Sonnet 4.6> \
  --embeddings cohere=cohere.embed-multilingual-v3 titan=amazon.titan-embed-text-v2:0 \
  --repeticiones 3 --bucket "$EVAL"
for p in ocr medir indexar recuperar responder planillas metricas; do
  .venv/bin/python -m atlas.evaluacion $p --campana $C || break
done
```

Después (sin AWS, pueden ser otro día): cada autor completa su planilla, `discrepancias`, `consenso.csv` y `metricas --con-calificaciones` (evaluacion/README.md, «Calificación»). Retirá la raíz `evaluacion` al terminar: `terraform plan -destroy -out=retiro.tfplan` y apply.

### 4.2 Procesamiento nivel B (Textract y Bedrock reales)

Desde la **raíz del repositorio** (no desde `backend/`: ahí el `.env` local apunta al moto de desarrollo):

```bash
cd ..
MAQ=$(terraform -chdir=infra/terraform/demo output -raw maquina_procesamiento)
mkdir -p evaluacion/campanas/nivel-b
ATLAS_PRUEBAS_AWS_REAL=1 ATLAS_ENTORNO=demo ATLAS_AWS_REGION=us-east-1 \
  ATLAS_BD_NOMBRE=sin_base ATLAS_BD_USUARIO=nadie \
  ATLAS_S3_BUCKET_DOCUMENTOS="$BUCKET" ATLAS_SFN_MAQUINA_PROCESAMIENTO_ARN="$MAQ" \
  ATLAS_EVIDENCIA_AWS_REAL=evaluacion/campanas/nivel-b/procesamiento.json \
  ATLAS_EVIDENCIA_AWS_REAL_RAG=evaluacion/campanas/nivel-b/rag.json \
  backend/.venv/bin/pytest backend/tests/aws_real -q
cd backend
```

### 4.3 §6.3.4 — Latencia y carga

```bash
L=e90-latencia-1
.venv/bin/python -m atlas.evaluacion.operacion iniciar --campana $L --modo oficial --url-api "$URL" \
  --version-codigo "$(git rev-parse --short HEAD)" --cliente-cognito "$CLIENTE" \
  --generativos haiku=us.anthropic.claude-haiku-4-5-20251001-v1:0 sonnet=<perfil us. de Sonnet 4.6>
for p in cargar red; do .venv/bin/python -m atlas.evaluacion.operacion $p --campana $L; done
```

Latencia en bloques **H1, S1 │ S2, H2 │ H3, S3**. Entre bloques de distinto modelo, reaplicá `demo` cambiando `perfil_generativo` y `modelo_generativo` en su `terraform.tfvars` (plan esperado: 4 Lambda y 1 política, en el lugar):

```bash
.venv/bin/python -m atlas.evaluacion.operacion latencia --campana $L --modelo haiku --repeticion 1
#   → demo con Sonnet
.venv/bin/python -m atlas.evaluacion.operacion latencia --campana $L --modelo sonnet --repeticion 1
.venv/bin/python -m atlas.evaluacion.operacion latencia --campana $L --modelo sonnet --repeticion 2
#   → demo con Haiku
.venv/bin/python -m atlas.evaluacion.operacion latencia --campana $L --modelo haiku --repeticion 2
.venv/bin/python -m atlas.evaluacion.operacion latencia --campana $L --modelo haiku --repeticion 3
#   → demo con Sonnet
.venv/bin/python -m atlas.evaluacion.operacion latencia --campana $L --modelo sonnet --repeticion 3
#   → demo con Haiku (producción) antes de seguir
.venv/bin/python -m atlas.evaluacion.operacion carga --campana $L     # niveles 1, 5 y 10
# Con la cuota de Lambda en 10, el nivel 10 puede recibir 429: se informa tal cual, como limitación.
.venv/bin/python -m atlas.evaluacion.operacion metricas --campana $L
```

### 4.4 §6.3.2 — Confiabilidad

```bash
.venv/bin/python -m atlas.evaluacion.confiabilidad --campana e90-confiabilidad-1 --url-api "$URL" \
  --cliente-cognito "$CLIENTE" --limite 3          # el límite desplegado en demo
```

Puede tardar decenas de minutos (el reconciliador corre cada 5).

### 4.5 §6.3.3 — Seguridad (al final: agrega trámites y cuentas)

```bash
S=e90-seguridad-1
MAQ=$(terraform -chdir=../infra/terraform/demo output -raw maquina_procesamiento)
.venv/bin/python -m atlas.evaluacion.seguridad iniciar --campana $S --url-api "$URL" \
  --cliente-cognito "$CLIENTE" --bucket "$BUCKET" --maquina "$MAQ"
for p in escenario matriz configuracion; do .venv/bin/python -m atlas.evaluacion.seguridad $p --campana $S; done
sleep 300   # los registros tardan en llegar a CloudWatch
for p in marcadores informe; do .venv/bin/python -m atlas.evaluacion.seguridad $p --campana $S; done
```

---

## Parte 5 — Evidencia y cierre

```bash
echo '{"estado":"draining"}' | aws s3 cp - "s3://$BUCKET/control/mantenimiento.json" --content-type application/json
sleep 300
aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
  --payload '{"accion":"verificar_drenaje"}' /dev/stdout          # hasta drenado: true
cd backend && .venv/bin/python -m atlas.herramientas.exportar_evidencia \
  --manifiesto ../operaciones/sesiones/e90-2026-10-24/manifiesto_seed.json --cliente-cognito "$CLIENTE" \
  --usuario-responsable atlas-responsable --salida ../operaciones/sesiones/e90-2026-10-24/evidencia && cd ..
echo '{"estado":"offline"}' | aws s3 cp - "s3://$BUCKET/control/mantenimiento.json" --content-type application/json
```

- [ ] Commiteá `evaluacion/campanas/*` y la evidencia exportada **antes** de retirar: después de la Parte 6 los datos de AWS se pierden.

## Parte 6 — Retiro selectivo (`web` queda)

```bash
(cd infra/terraform/demo && terraform plan -destroy -out=retiro.tfplan)      # revisar y apply
(cd infra/terraform/runtime && terraform plan -destroy -out=retiro.tfplan)   # revisar y apply
cd infra/terraform/persistent
terraform plan -var retiro_autorizado=true -out=desproteger.tfplan           # solo quita protecciones
terraform apply desproteger.tfplan
cd ../../../backend
.venv/bin/python -m atlas.herramientas.vaciar_bucket_versionado --bucket "$BUCKET"                       # simula
.venv/bin/python -m atlas.herramientas.vaciar_bucket_versionado --bucket "$BUCKET" --confirmar "$BUCKET" --ejecutar
cd ../infra/terraform/persistent
terraform plan -destroy -var retiro_autorizado=true -out=retiro.tfplan       # RDS sin snapshot: confirmar pérdida
terraform apply retiro.tfplan
cd ../../..
```

## Parte 7 — Residuos

Corré los comandos de verificación de [infra/terraform/README.md](../../infra/terraform/README.md) (sección B.5) hasta que solo queden `bootstrap` y `web`. Agregá:

```bash
aws lambda list-functions --query "Functions[?starts_with(FunctionName,'atlas-demo')].FunctionName"
aws ec2 describe-vpc-endpoints --filters Name=tag:proyecto,Values=atlas --query "VpcEndpoints[].ServiceName"
```

Anotá la hora de fin y revisá Billing en los días siguientes.

---

## Cómo te acompaño

Pegame la salida de cada paso (sin contraseñas ni tokens). Te digo si está bien antes de seguir. Si algo falla, **no** repitas a ciegas: frená y pegame el error.
