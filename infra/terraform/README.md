# Terraform de ATLAS — procedimiento manual de una sesión E90A

**Estado:** código preparado y validado sin AWS (`terraform validate -backend=false`,
22/10/2026). **Nunca se aplicó ni se planificó contra una cuenta.** Base: RC-P10,
DO-2026-10-21, DO-2026-10-21-E90A y DO-2026-10-22-OPS.

**Quién ejecuta:** solo el operador humano autorizado, después de aprobar el plan exacto, el
impacto y el costo de la sesión.
Ningún agente, push ni GitHub Action ejecuta estos pasos.

## Raíces y orden

| Raíz | Contiene | Ciclo |
|---|---|---|
| `bootstrap` | Bucket del estado remoto (versionado, cifrado, solo TLS, `prevent_destroy`) | Una vez; **nunca** se destruye |
| `persistent` | VPC sin NAT, subredes, grupos de seguridad, gateway S3, RDS Multi-AZ, bucket documental con el objeto de control (`offline`), Cognito | Por sesión |
| `runtime` | RDS Proxy con IAM de extremo a extremo, su rol, endpoints Step Functions, Bedrock Runtime y Secrets Manager (temporal) | Por sesión |
| `demo` | Bucket de artefactos y paquete, cinco Lambda (incluido el reconciliador), roles mínimos, Step Functions, EventBridge Scheduler del reconciliador, API Gateway con JWT | Por sesión |
| `tests` | Solo documentación: no se despliega en E90 | — |
| `web` | Aplicación web: bucket privado y CloudFront con OAC y encabezados de seguridad (DO-2026-10-23-WEB-HOST) | **Persistente entre sesiones** (URL estable); se retira al cerrar el proyecto |

Creación: `persistent → runtime → demo` (`web` se crea una sola vez, antes). Retiro: `demo → runtime → persistent` (`web` queda).
Versiones fijas: Terraform ≥ 1.10 (validado con 1.16.5), proveedor AWS 6.67.0, http 3.6.2.
Los `.terraform.lock.hcl` traen hashes de `linux_amd64`; en otra plataforma:
`terraform providers lock -platform=<plataforma>` antes de `init`.

## Aplicación web en CloudFront (una sola vez)

```bash
cd infra/terraform/web
cp terraform.tfvars.example terraform.tfvars        # completar; no se versiona
terraform init -backend-config=../backend.hcl
terraform plan -out=web.tfplan                      # esperado: 8 to add
terraform apply web.tfplan                          # CloudFront tarda de 5 a 15 min
terraform output -raw origen                        # https://<id>.cloudfront.net
cd ../../.. && infra/web/publicar.sh --aplicacion
```

El valor de `origen` va en `origenes_cors` (`persistent`) y `origenes_web` (`demo`), junto a
`http://localhost:4173`. En cada sesión, después de aplicar `demo`:
`infra/web/publicar.sh --configuracion`. Al cerrar el proyecto: `terraform plan -destroy` de `web`.

## A. Encendido

Antes de empezar: checklist bloqueante del runbook, identidad humana con MFA, región
`us-east-1`, `terraform`, AWS CLI y Docker. Anotar la hora de inicio (comienza la facturación).

1. **Bootstrap (una sola vez por cuenta).**
   ```bash
   cd infra/terraform/bootstrap
   cp terraform.tfvars.example terraform.tfvars   # completar; no se versiona
   terraform init
   terraform plan -out=bootstrap.tfplan           # revisar: solo el bucket y sus controles
   terraform apply bootstrap.tfplan
   ```
   El estado de `bootstrap` queda en la máquina del operador: respaldarlo fuera del repositorio.
   Copiar `../backend.hcl.example` como `../backend.hcl` con el bucket de la salida.

2. **Paquete Lambda.** Con `rds-global-bundle.pem` y `amazon-trust-raices.pem` de `infra/certificados/` descargados por el
   equipo (ver su README): `infra/empaquetado/construir_lambda.sh`. Anotar el SHA-256 y el commit.

3. **persistent** (RDS Multi-AZ tarda unos 20–30 min):
   ```bash
   cd infra/terraform/persistent
   cp terraform.tfvars.example terraform.tfvars
   terraform init -backend-config=../backend.hcl
   terraform plan -out=persistent.tfplan
   terraform apply persistent.tfplan
   ```
4. **runtime** y **demo**: igual, cada una con su `terraform.tfvars` (`version_codigo` = commit
   del paquete). Si `runtime` se recrea, **reaplicar `demo`** antes de habilitar (RC-P10-04).

5. **Base de datos** (Lambda privada de operaciones, RC-P10-15):
   ```bash
   FN=$(terraform -chdir=infra/terraform/demo output -raw funcion_operaciones)
   aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
     --payload '{"accion":"inicializar_base"}' /dev/stdout
   aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
     --payload '{"accion":"migrar"}' /dev/stdout
   aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
     --payload '{"accion":"estado_migraciones"}' /dev/stdout   # al_dia: true
   ```
   El CLI corta a los 60 s: agregar `--cli-read-timeout 320` (la Lambda admite 300 s).
   `inicializar_base` es de **un solo uso**: al terminar, RDS exige IAM al maestro (DIF-95) y la
   credencial maestra deja de servir con contraseña. Si falla a mitad de camino, no reintentar:
   revisar el log de RDS (`aws rds download-db-log-file-portion`) y decidir con el equipo.
   Luego retirar el endpoint temporal: en `runtime`, `endpoint_secrets_manager = false`, plan y apply.

6. **Cuentas ficticias** (P10). Por cada usuario (`atlas-admin`, `atlas-responsable`,
   `atlas-revisor`, `atlas-aprobador`), con la contraseña leída en la terminal (`read -s`):
   ```bash
   POOL=$(terraform -chdir=infra/terraform/persistent output -raw cognito_user_pool_id)
   aws cognito-idp admin-create-user --user-pool-id "$POOL" --username atlas-admin --message-action SUPPRESS
   aws cognito-idp admin-set-user-password --user-pool-id "$POOL" --username atlas-admin \
     --password "$ATLAS_SEED_CLAVE_ADMINISTRADOR" --permanent
   SUB=$(aws cognito-idp admin-get-user --user-pool-id "$POOL" --username atlas-admin \
     --query "UserAttributes[?Name=='sub'].Value" --output text)
   aws lambda invoke --function-name "$FN" --cli-binary-format raw-in-base64-out \
     --payload "{\"accion\":\"crear_administrador\",\"identificador_externo\":\"$SUB\"}" /dev/stdout
   ```
   Las demás cuentas las da de alta la semilla por la API.

   **Aplicación web (DO-2026-10-22-WEB F7):** corre en la máquina del presentador
   (`frontend/README.md`, sección «Demo»). Su origen (`http://localhost:4173`) va en
   `origenes_cors` (`persistent`) y en `origenes_web` (`demo`) antes de aplicar esas raíces.

7. **Pasar a `active`** solo con cuentas ficticias (la demo todavía no se abre):
   ```bash
   BUCKET=$(terraform -chdir=infra/terraform/persistent output -raw bucket_documentos)
   echo '{"estado":"active"}' | aws s3 cp - "s3://$BUCKET/control/mantenimiento.json" --content-type application/json
   curl -s "$(terraform -chdir=infra/terraform/demo output -raw url_api)salud"   # operacion: active (≤ 15 s)
   ```
8. **Semilla** (consume Textract y Bedrock reales: autorizar antes):
   ```bash
   cd backend && .venv/bin/python -m atlas.herramientas.sembrar_demo --url-api "<url_api>" \
     --sesion "<sesion>" --cliente-cognito "<cognito_cliente_id>" \
     --usuarios administrador=atlas-admin responsable=atlas-responsable revisor=atlas-revisor aprobador=atlas-aprobador \
     --manifiesto ../operaciones/sesiones/<sesion>/manifiesto_seed.json
   ```
   Si falla: volver a `offline`, revisar el manifiesto y no repetir sobre datos sin auditar.
9. Humo del recorrido, pruebas negativas y verificaciones de RC-P10 (A, B-E90, IAM, V-DB…).
   Recién entonces abrir la demo.

## B. Cierre y retiro selectivo

1. `draining` (mismo comando que el paso 7). Esperar 5 min (URLs prefirmadas) y verificar:
   `{"accion":"verificar_drenaje"}` hasta `drenado: true`. Una carga sin incorporar bloquea el
   drenaje: incorporarla o registrar la decisión; no destruir a ciegas.
2. **Exportar evidencia** (con la API en `draining`):
   `python -m atlas.herramientas.exportar_evidencia --manifiesto … --cliente-cognito … --usuario-responsable atlas-responsable --salida ../operaciones/sesiones/<sesion>/evidencia`.
   Comprobar el índice SHA-256. Pasar a `offline`.
3. **demo** y **runtime**: `terraform plan -destroy -out=retiro.tfplan`, revisar que solo
   aparezcan recursos de la sesión y aplicar. Las ENI de las Lambda en la VPC pueden tardar
   decenas de minutos en liberarse.
4. **persistent**, en tres pasos con confirmación humana explícita de la pérdida irreversible:
   1. `terraform plan -var retiro_autorizado=true -out=desproteger.tfplan`: el plan solo debe
      quitar `deletion_protection` de RDS y Cognito. Aplicar.
   2. Vaciar el bucket documental: primero
      `python -m atlas.herramientas.vaciar_bucket_versionado --bucket "$BUCKET"` (simula) y después
      con `--confirmar "$BUCKET" --ejecutar`.
   3. `terraform plan -destroy -var retiro_autorizado=true -out=retiro.tfplan`, revisar (RDS
      sin snapshot final ni backups retenidos) y aplicar.
5. **Verificar residuos**, por servicio y hasta que converjan:
   ```bash
   aws rds describe-db-instances --query "DBInstances[?starts_with(DBInstanceIdentifier,'atlas-demo')]"
   aws rds describe-db-proxies --query "DBProxies[?starts_with(DBProxyName,'atlas-demo')]"
   aws rds describe-db-snapshots --snapshot-type manual
   aws ec2 describe-vpc-endpoints --filters Name=tag:proyecto,Values=atlas
   aws ec2 describe-vpcs --filters Name=tag:proyecto,Values=atlas
   aws lambda list-functions --query "Functions[?starts_with(FunctionName,'atlas-demo')].FunctionName"
   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/atlas-demo
   aws cognito-idp list-user-pools --max-results 20
   aws secretsmanager list-secrets --include-planned-deletion
   aws s3api list-buckets --query "Buckets[?starts_with(Name,'atlas-demo')]"
   ```
   Solo debe quedar `bootstrap`. Cerrar el acta y revisar Billing en los días siguientes.

## Protecciones

- `bootstrap`: `prevent_destroy`. No hay plan de retiro para esta raíz.
- RDS y Cognito: protección de borrado salvo con `retiro_autorizado = true`, que solo se usa
  en el paso B.4 y queda visible en el plan.
- Buckets sin `force_destroy`: el vaciado es un paso explícito con confirmación del nombre y
  etiquetas `proyecto=atlas`, `entorno=demo` (rechaza el estado remoto).
- Prohibido: `terraform destroy` global, `state rm`, desactivar protecciones fuera de B.4.
