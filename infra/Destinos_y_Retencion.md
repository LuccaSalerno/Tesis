# Destinos y retención (RNF-03)

Servicios que reciben o guardan contenido documental en el entorno demo, con su región y la retención que configura el código de este repositorio. Se actualiza en el mismo cambio que agrega un destino o modifica una retención. Es la configuración declarada: la efectiva se comprueba en cada sesión AWS.

| Destino | ¿Contenido documental? | Región | Retención | Dónde se configura |
|---|---|---|---|---|
| S3 documental: `documentos/` | Sí: los originales incorporados | us-east-1 | Sin expiración. Versionado activo; se retira con la sesión | `terraform/persistent/almacenamiento.tf` |
| S3 documental: `cargas-temporales/` | Sí: las cargas sin incorporar | us-east-1 | Vencen a las 24 h; la limpieza las borra con todas sus versiones. Respaldo con S3 Lifecycle a los 2 días | `atlas.configuracion` (`carga_vigencia_pendiente_s`), `terraform/persistent/almacenamiento.tf` |
| S3 documental: `resultados/` | Sí: salidas de Textract, contenido normalizado y extracciones | us-east-1 | Mientras exista el archivo; se borran con la carga vencida | `atlas.integraciones.ciclo_vida_s3` |
| RDS PostgreSQL | Sí: valores validados, fragmentos y embeddings | us-east-1, Multi-AZ | Backups de 7 días. Se destruye con la sesión, sin snapshot final | `terraform/persistent/rds.tf` |
| Textract | Sí, en procesamiento | us-east-1 | Resultados asíncronos administrados por AWS, 7 días | Servicio |
| Bedrock: Claude Haiku 4.5 | Sí: contenido, preguntas y respuestas | Perfil `us.`: origen us-east-1; destinos us-east-1, us-east-2 y us-west-2 | Sin registro de invocaciones | `terraform/demo/variables.tf`, configuración de la cuenta |
| Bedrock: Cohere Embed Multilingual v3 | Sí: fragmentos y preguntas | us-east-1 | Sin registro de invocaciones | `terraform/demo/variables.tf` |
| Lambda y RDS Proxy | En tránsito | us-east-1 | No guardan contenido | `terraform/demo/`, `terraform/runtime/` |
| CloudWatch Logs | No: solo identificadores y metadatos técnicos (RNF-09) | us-east-1 | 7 días | `terraform/demo/funciones.tf` (`retencion_registros_dias`) |
| Step Functions y EventBridge Scheduler | No: solo identificadores | us-east-1 | Sin registro de ejecuciones | `terraform/demo/` |
| API Gateway | En tránsito, autenticado | us-east-1 | Sin registro de acceso | `terraform/demo/` |
| Cognito | No: solo identidades | us-east-1 | Mientras dure la sesión | `terraform/persistent/cognito.tf` |
| S3 web y CloudFront | No: solo la aplicación compilada y `configuracion.json` | S3 us-east-1; CloudFront global | Entre sesiones; se retira al cerrar el proyecto | `terraform/web/` |
| S3 de estado de Terraform | No | us-east-1 | Versiones anteriores, 90 días | `terraform/bootstrap/main.tf` |

En el navegador, los originales se leen con URL prefirmadas de 5 minutos. Solo se guarda el token de sesión, en `sessionStorage`. No hay analítica ni servicios externos.
