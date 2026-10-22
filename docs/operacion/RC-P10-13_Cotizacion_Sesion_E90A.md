# RC-P10-13 — Cotización por sesión E90A (preliminar, no oficial)

**Fecha:** 22/10/2026. **Estado: PRELIMINAR, NO APROBADO.** Base: DO-2026-10-22-OPS (P13), el
Terraform de `infra/terraform/` y las tarifas de referencia del
[informe preliminar](RC-P10-13_Cotizacion_Preliminar_2026-10-21.md) (consultadas el
21/10/2026, sin Pricing Calculator). **No autoriza gasto ni despliegue.** Para aprobar hace
falta: exportación oficial de AWS Pricing Calculator con esta configuración, importe aceptado
por sesión y por mes, operador y revisor ([política de costos](Politica_Costos_AWS.md)).

## 1. Inventario facturable que crea el Terraform

| Raíz | Recurso | Unidad facturable | Tarifa de referencia | Fuente / calidad |
|---|---|---|---|---|
| persistent | RDS PostgreSQL `db.t4g.medium` **Multi-AZ** | hora (por segundo, mínimo 10 min) | USD 0,129/h | Terceros; ratificar |
| persistent | Almacenamiento gp3 Multi-AZ, 20 GiB | GiB-mes prorrateado | USD 0,23/GiB-mes → 0,0063/h | Referencia; ratificar |
| persistent | Backups automáticos (7 días) | GiB-mes por encima del tamaño de la base | ≈ 0 en una sesión; se borran al retirar | Ratificar |
| persistent | Créditos de CPU T4g (modo ilimitado) | vCPU-hora excedente | Variable: medir `CPUSurplusCreditsCharged` | Pendiente |
| persistent | Secreto maestro administrado por RDS | secreto-mes prorrateado | USD 0,40/mes → 0,0005/h | Oficial; ratificar |
| persistent | Bucket documental (versionado) | GiB-mes y solicitudes | ≈ 0 (algunos MB) | — |
| persistent | Cognito (4 usuarios ficticios) | usuarios activos mensuales | ≈ 0; ratificar el plan de Cognito | Pendiente |
| persistent | VPC, subredes, rutas, grupos, gateway S3 | — | Sin cargo | Oficial |
| runtime | RDS Proxy | vCPU de la instancia × hora (mínimo 10 min) | 2 × USD 0,015 = 0,030/h | Oficial; ratificar |
| runtime | Endpoints de interfaz (2 AZ cada uno) | hora por AZ (fracción = hora completa) + GB | USD 0,010/h por AZ | Oficial; ratificar |
| | · Step Functions + Bedrock Runtime | | 2 × 2 × 0,010 = 0,040/h | |
| | · Secrets Manager (solo durante la inicialización) | | 2 × 0,010 = 0,020/h, ≥ 1 h | |
| demo | Lambda (4 funciones, arm64) | solicitudes y GB-s | Céntimos por sesión | Ratificar |
| demo | API Gateway HTTP API | millón de solicitudes | Céntimos | Ratificar |
| demo | Step Functions Standard | transiciones de estado | ≈ 30 por documento: céntimos | Ratificar |
| demo | CloudWatch Logs (7 días) | GB ingeridos y almacenados | Céntimos | Ratificar |
| demo | Bucket de artefactos (zip de 36 MB) | GiB-mes | ≈ 0 | — |
| uso | Textract `AnalyzeDocument` (TABLES + LAYOUT) | página | **PENDIENTE**: el informe solo cotiza `DetectDocumentText` | Cotizar |
| uso | Bedrock Claude Haiku 4.5 (perfil US) | tokens de entrada y salida | **PENDIENTE** | Cotizar |
| uso | Bedrock Cohere Embed Multilingual v3 | tokens | **PENDIENTE** | Cotizar |

No se crean (P9): NAT Gateway, CloudFront/S3 web, Scheduler, endpoint de Lambda ni claves KMS
propias.

## 2. Fórmula por sesión

```
C_sesión = H × (RDS + almacenamiento + proxy + endpoints + secreto)
         + mínimos y redondeos (RDS y proxy 10 min; cada endpoint, horas completas por AZ)
         + 1 h del endpoint de Secrets Manager
         + uso (Textract por página + Bedrock por token + Lambda/API/Step Functions/logs)
         + créditos de CPU excedentes
         + contingencia
```

`H` es el tiempo **aprovisionado** de punta a punta: desde que se crea RDS hasta que su
eliminación termina, incluidos la creación Multi-AZ (≈ 20–30 min), las esperas, el drenaje y el
retiro (≈ 15–40 min, más la liberación de ENI).

Costo horario base con las tarifas de referencia: `0,129 + 0,0063 + 0,030 + 0,040 + 0,0005 ≈
USD 0,21/h`.

| Escenario | H | Base | Secrets Manager | Uso (estimación gruesa) | Subtotal | Con 50 % de contingencia |
|---|---|---|---|---|---|---|
| Ensayo técnico (1.1) | 4 h | 0,84 | 0,02 | < 0,50 | ≈ 1,36 | ≈ 2,0 |
| Sesión de demo | 8 h | 1,68 | 0,02 | < 0,50 | ≈ 2,20 | ≈ 3,3 |
| Sesión larga | 12 h | 2,52 | 0,02 | < 1,00 | ≈ 3,54 | ≈ 5,3 |

**Uso de la semilla:** dos trámites con C-v1 (10 páginas), O-v1 y F-v1 (1 página cada una):
24 páginas de Textract y del orden de 50.000 tokens de entrada en Bedrock por sesión. El
importe queda **pendiente** hasta cotizar `AnalyzeDocument` y los modelos; la cota «< USD 0,50»
es una hipótesis a confirmar, no una tarifa.

**Mensual:** `N sesiones × C_sesión + residuales del período` (snapshots manuales, versiones S3
olvidadas, secretos con borrado diferido, logs). Con el retiro verificado, los residuales
esperados son cercanos a cero, pero se comprueban en la factura.

## 3. Frente a los presupuestos existentes

Los presupuestos comunicados son alertas, no límites: `tesis-dinero-real` (USD 1) se supera con
**un solo ensayo de 4 h**; `tesis-uso-mensual` (USD 20) admite unas 5–6 sesiones de 8 h con
contingencia. **No se afirma que alcance**: decide el equipo tras la cotización oficial.

## 4. Para cerrar RC-P10-13 (equipo)

1. Cargar esta configuración en AWS Pricing Calculator (us-east-1) y exportarla.
2. Cotizar Textract `AnalyzeDocument` (TABLES + LAYOUT), Haiku 4.5 con perfil geográfico y
   Cohere Embed Multilingual v3.
3. Registrar el importe aceptado por sesión y por mes, la contingencia, el operador y el revisor.
4. Después de cada sesión, conciliar con Billing (hora de inicio y fin efectivo de cada recurso).
