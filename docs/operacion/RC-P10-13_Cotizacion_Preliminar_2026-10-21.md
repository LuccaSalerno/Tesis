**AVISO DE CAMBIO POSTERIOR: MODALIDAD E90A.** Este informe y su Excel asociado cuantifican el escenario histórico con RDS detenido y almacenamiento mensual persistente. **No usar esos totales para aprobar la demo descartable E90A.** Véanse [decisión](../decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md), [runbook](../../operaciones/aws/README_OPERACION_MANUAL.md) y [política actual](Politica_Costos_AWS.md). RC-P10-13 continúa pendiente de cotización oficial según la modalidad nueva.

# RC-P10-13 — Cotización preliminar de infraestructura AWS para ATLAS

**Fecha de investigación:** 21/10/2026. **Región:** `us-east-1` (Virginia). **Estado: PRELIMINAR, NO APROBADO**.

**Alcance de la evidencia.** Los importes corresponden a un modelo aritmético revisable basado en componentes descritos por RC-P10 y tarifas publicadas/consultadas. **No se generó un enlace público ni un PDF de AWS Pricing Calculator, no se consultó la facturación de la cuenta y no se desplegó infraestructura.** La herramienta oficial requiere que el equipo configure y confirme los parámetros finales. No llamar a este documento «cotización exacta» ni RC-P10-13 «cumplido».

## 1. Arquitectura y supuestos

- Región principal `us-east-1`, bajo demanda, **sin** beneficios del Free Tier, créditos, descuentos, impuestos ni soporte pago.
- RDS **PostgreSQL Multi-AZ DB instance** (principal + standby), **no Multi-AZ DB cluster**; tamaño hipotético `db.t4g.medium` con 2 vCPU, 4 GiB RAM; versión PostgreSQL aún por confirmar.
- RDS Proxy compartido con endpoint predeterminado y autenticación IAM; cobro de referencia supuesto de 2 vCPU.
- Tres endpoints de interfaz (Step Functions, Bedrock Runtime, Lambda) activos en **dos AZ**; endpoint gateway de S3 sin cargo de endpoint. **No NAT Gateway**. El endpoint de Secrets Manager de la inicialización se cotiza aparte cuando se conozcan sus horas/AZ.
- RDS gp3 Multi-AZ de **20 GiB** como caso ilustrativo; también se modelan **100 GiB**. El tamaño de datos, IOPS y requisitos reales siguen pendientes.
- `bootstrap` y `persistent` permanecen; `runtime` se propone eliminar al apagar; `demo` se conserva en mantenimiento. `tests` no se despliega inicialmente. **Este ciclo no fue probado**.

## 2. Tarifas unitarias de trabajo

| Rubro | Tarifa usada | Origen / calidad de la evidencia |
|---|---:|---|
| RDS PostgreSQL Multi-AZ `db.t4g.medium` | **USD 0,129/h** | Referencia regional de terceros: https://cloud-credits.org/prices/rds/db-t4g-medium ; ratificar en https://aws.amazon.com/rds/postgresql/pricing/ y Calculator |
| RDS Proxy | **USD 0,015/vCPU-h**, 2 vCPU → USD 0,030/h | https://aws.amazon.com/rds/proxy/pricing/ ; corroborar mínimo efectivo en el dimensionamiento |
| Endpoint de interfaz por AZ | **USD 0,010/h** | https://aws.amazon.com/privatelink/pricing/ ; hora parcial redondeada; más USD 0,01/GB para primer PB |
| Almacenamiento RDS gp3 Multi-AZ | **USD 0,23/GiB-mes** | Referencia para cotización: https://aws.amazon.com/rds/postgresql/pricing/ ; confirmar modalidad y requisitos gp3 exactos |
| Secrets Manager | **USD 0,40/secreto-mes** | https://aws.amazon.com/secrets-manager/pricing/ ; cantidad real por verificar |
| S3 Standard | **USD 0,023/GiB-mes** | https://aws.amazon.com/s3/pricing/ ; sin solicitudes/versiones/transferencias |
| Textract DetectDocumentText | **USD 0,0015/página** | https://aws.amazon.com/textract/pricing/ ; AnalyzeDocument tiene otra tarifa |

El costo horario básico de recursos activos es `0,129 + (2 × 0,015) + (3 × 2 × 0,010) = **USD 0,219/h**`. El almacenamiento de 20 GiB queda aprovisionado todo el mes: `20 × 0,23 = **USD 4,60/mes**`. Son precios supuestos, no una garantía de facturación.

## 3. Escenarios comparables

Suponen **despliegue y eliminación correcta de `runtime`**, detención efectiva de RDS fuera de las horas señaladas, un mes de referencia de 730 horas y **ningún reinicio inesperado de RDS**. Horas facturables incluyen arranque, mantenimiento, espera, pruebas y cierre; no solo tiempo visible de demo.

| Uso | Horas activas/mes | Cómputo + proxy + endpoints | gp3 20 GiB | Subtotal básico |
|---|---:|---:|---:|---:|
| 4 sesiones × 2 h | 8 | USD 1,75 | USD 4,60 | **USD 6,35** |
| 4 sesiones × 5 h | 20 | USD 4,38 | USD 4,60 | **USD 8,98** |
| 8 sesiones × 5 h | 40 | USD 8,76 | USD 4,60 | **USD 13,36** |
| Sesiones ampliadas | 80 | USD 17,52 | USD 4,60 | **USD 22,12** |
| 24/7 | 730 | USD 159,87 | USD 4,60 | **USD 164,47** |

Con **100 GiB gp3**, añadir USD 18,40/mes a esas cifras (20h → USD 27,38; 24/7 → USD 182,87). La planilla incluye consumos ilustrativos extra y una reserva arbitraria para simulación: **no constituyen una previsión exhaustiva**.

**Importante:** el subtotal no incluye CPU burst/credit surplus, datos transferidos, procesamiento VPCE, almacenamiento de backups/snapshots, API Gateway, Lambda, Step Functions, Scheduler, CloudWatch, KMS customer-managed keys, Cognito, CloudFront, peticiones S3, versiones, Textract avanzado ni tokens de Bedrock. El valor «0» de variables no valorizadas **no significa gratuito**.

## 4. Riesgos que pueden invalidar los escenarios de 8–40 h

1. **RDS se reinicia tras siete días detenido.** Revisarlo o recibir alertas **no previene** automáticamente ese reinicio. Si no hay un operador disponible para ejecutar a tiempo una actuación manual segura y aprobada, **no aprobar la creación** de RDS ni prometer los escenarios de pocas horas. Fuente: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html .
2. **Si RDS arranca por mantenimiento mientras `runtime` continúa eliminado**, puede facturar el cómputo RDS, pero **el proxy y los endpoints eliminados no se recrean por ese hecho**. Una semana de cómputo RDS costaría alrededor de `168 × 0,129 = USD 21,67`, no USD 36,79 salvo que el resto del runtime también estuviera aprovisionado.
3. **RDS requiere tiempo de inicio/detención**, posiblemente minutos u horas, por lo que presupuestar una sesión de exactamente dos horas solo es razonable tras medir el ciclo completo. Hay mínimos de facturación de RDS/Proxy; los endpoints redondean horas parciales.
4. **No hay apagado implementado ni ensayado** en el ZIP. El runbook describe un procedimiento propuesto; 1.0/1.1 son compuertas aún por ejecutar. Sin aprobación humana y verificación no se debe desplegar.
5. Un backup, un secreto, un endpoint de inicialización olvidado, tráfico inter-AZ o almacenamiento adicional puede elevar el costo. Reconstruir o restaurar componentes puede prolongar la sesión.
6. RDS Multi-AZ **DB instance** (primaria+standby) admite detenerse en PostgreSQL; un Multi-AZ **DB cluster** no admite el mismo procedimiento. Verificar el tipo exacto en el futuro plan Terraform.

## 5. Requisitos para una cotización oficial y autorización

En https://calculator.aws/#/ construir y **guardar/exportar** una estimación con la versión de PostgreSQL, clase, tamaño y rendimiento gp3, deployment Multi-AZ DB instance, horarios previstos, RDS Proxy, cantidad real de endpoints/AZ, bootstrap/persistent, AWS AI por modalidad/perfil, Textract por API, cómputo y tráfico, logs/retención y contingencia. Guardar **URL/exportación, fecha, parámetros y supuestos**. La calculadora no sustituye la medición en Cost Explorer después de ejecutar. Fuentes: https://docs.aws.amazon.com/pricing-calculator/latest/userguide/export-estimate.html y https://docs.aws.amazon.com/pricing-calculator/latest/userguide/save-share-estimate.html .

| Control previo | Estado actual |
|---|---|
| Modelo editable de escenarios | **DISPONIBLE**, con supuestos explícitos |
| Cotización oficial exportada/link | **PENDIENTE** |
| Importe aceptado por sesión y mes | **PENDIENTE** |
| Operador y suplente responsables | **PENDIENTE** |
| Terraform `plan` exacto y validación de recursos | **PENDIENTE: no existe Terraform** |
| Ciclo apagado/encendido y prueba de recuperación | **PENDIENTE: no implementado ni probado** |
| Inventario antes y después de sesión | **PENDIENTE: no hay infraestructura ATLAS desplegada en este ZIP** |

**Decisión:** RC-P10-13 permanece **PENDIENTE**. AWS Budgets de USD 1 y USD 20 son umbrales de alerta, nunca límites de gasto ni autorización. La política vigente conserva RC-P10 y la ejecución exclusivamente manual del equipo; no permite crear ni destruir recursos por agentes o GitHub Actions.
