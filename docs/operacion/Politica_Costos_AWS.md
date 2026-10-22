# Política de costos AWS — RC-P10-13 / DO-2026-10-21

**Fecha:** 21/10/2026. **Estado:** política operativa expresa del equipo; estimación y presupuesto de la arquitectura pendientes. No se ejecutaron consultas de cuenta ni operaciones AWS en esta tarea.

**DO-2026-10-21-E90A (decisión posterior):** E90 usa una **demo totalmente descartable** por sesión: crear, sembrar corpus sintético, probar y eliminar manualmente la infraestructura de demo, incluida RDS. **No se detiene RDS durante la inactividad ni se conservan sus datos/snapshots entre sesiones.** Se conserva únicamente `bootstrap` y controles administrativos, más corpus/evidencia locales.

**ATLAS no funcionará permanentemente en AWS durante el desarrollo de la tesis.** Se habilita en sesiones controladas de pruebas, evaluación y defensa, ejecutadas y supervisadas por operadores humanos. Crear recursos facturables requiere aprobación expresa previa de impacto y costos. Terraform, PostgreSQL Multi-AZ, RDS Proxy, endpoints privados, servicios IA, aislamiento y controles de la tesis permanecen.

### Cotización por sesión E90A (22/10/2026, preliminar)

[RC-P10-13_Cotizacion_Sesion_E90A.md](RC-P10-13_Cotizacion_Sesion_E90A.md) lista los recursos facturables que crea el Terraform preparado y la fórmula por hora y por sesión (≈ USD 0,21/h de base con tarifas de referencia). Textract `AnalyzeDocument` y Bedrock siguen sin cotizar. **No es la cotización oficial ni autoriza gasto.**

### Referencia de costos investigados (no aprobados)

Se incorporaron [el informe numérico preliminar RC-P10-13](RC-P10-13_Cotizacion_Preliminar_2026-10-21.md) y [el modelo editable](RC-P10-13_Modelo_Costos_2026-10-21.xlsx). Las tarifas de referencia son hipótesis de investigación para `us-east-1`, no precios contractuales, importes facturados ni presupuesto autorizado. **Las tablas de 20/40/80 horas que sumaban almacenamiento RDS para el mes completo corresponden al escenario anterior RDS `stopped` y NO son la estimación de E90A.** El escenario A exige prorratear el tiempo realmente aprovisionado y contemplar mínimos y eliminación efectiva. RC-P10-13 permanece **PENDIENTE** hasta configurar el cálculo oficial con la infraestructura definitiva, exportarlo y aprobarlo expresamente. No interpretar el total básico de los escenarios como costo completo del sistema.

**Nueva modalidad E90A:** la operación elegida ya **no contempla** dejar RDS en `stopped`; el cierre aprobado elimina RDS y no crea un snapshot final. El reinicio automático tras siete días solo aplica a la modalidad previa, conservada como antecedente. La eliminación es irreversible, requiere advertencia y aprobación humanas, y no garantiza ausencia de residuos como snapshots manuales previos, S3 versionado o secretos pendientes.

## 1. Presupuestos existentes comunicados por el equipo

Revisados por el equipo el **21/10/2026**; capturas formales pendientes de consolidación. No constituyen verificación independiente del agente ni evidencia de entrega de notificaciones.

| Nombre | Importe mensual | Alertas de gasto real | Alerta prevista/proyectada |
|---|---|---|---|
| `tesis-dinero-real` | USD 1 | 50 % | 100 % |
| `tesis-uso-mensual` | USD 20 | 50 %, 80 %, 100 % | 100 % |

Ambos sin filtros por servicio o región; destinatarios con estado `Active (legacy)`. El nombre `tesis-uso-mensual` no permite inferir una unidad diferente de los USD comunicados. Pendiente consolidar capturas saneadas y comprobar recepción efectiva.

Estos presupuestos **no son límites automáticos de gasto**, no garantizan notificaciones inmediatas y no autorizan despliegues. AWS describe demoras de actualización y notificación en [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html). No se configuran acciones automáticas sobre infraestructura. **No se afirma que USD 20 alcance para la arquitectura completa.** El importe aceptado para ATLAS se registra por separado, tras cotización.

## 2. Condiciones previas al primer despliegue

El equipo debe completar y aprobar RC-P10-13 con precios oficiales vigentes para **us-east-1** y fecha de consulta. `db.t4g.medium` Multi-AZ es solo hipótesis inicial, no dimensionamiento aprobado por medición.

| Partida a cotizar | Unidades y condiciones que registrar | Importe |
|---|---|---|
| RDS PostgreSQL Multi-AZ | Clase, versión, horas, primaria/reserva, almacenamiento/IOPS, backups/snapshots, créditos CPU ilimitados, soporte extendido si aplica | PENDIENTE |
| RDS Proxy | Capacidad facturable y mínimo; duración desde creación hasta eliminación efectiva | PENDIENTE |
| Endpoints de interfaz | Servicio, cantidad de AZ, horas redondeadas y GB; incluir Secrets Manager temporal | PENDIENTE |
| S3 y estado remoto | GB-mes, versiones, solicitudes y transferencia; originales/intermedios/estado | PENDIENTE |
| Lambda / API Gateway / Step Functions / Scheduler | Solicitudes, cómputo, transiciones, reintentos, drenaje y reconciliación | PENDIENTE |
| Textract / Bedrock | Páginas/operaciones, modelo/perfil, tokens, embeddings, repeticiones; sin duplicar OCR reutilizado | PENDIENTE |
| Cognito / CloudFront / observabilidad / claves y secretos | Uso, almacenamiento/retención, solicitudes y otros cargos aplicables a la configuración elegida | PENDIENTE |
| Recuperación y contingencia | Arranque/cierre, fallo parcial, snapshots y restauración temporal; impuestos/cargos y créditos por separado | PENDIENTE |

Conservar referencia/exportación de [AWS Pricing Calculator](https://calculator.aws/) y tarifas oficiales de cada servicio; no deducir gratuidad por bajo uso o Free Tier. Para perfiles geográficos registrar la modalidad y tarifa aplicable, sin confundir destino de inferencia con recursos desplegados en otra región.

Calcular costo **por hora aprovisionada**, **por sesión completa** (creación, migraciones, seed, pruebas, drenaje, eliminación efectiva, mínimos) y **mensual** (número/duración de sesiones, temporales olvidados y residuales reales). Fórmula de trabajo: costo mensual = sesiones con sus mínimos/redondeos + almacenamiento y demás residuales del período + contingencia; evitar contar dos veces las partidas compartidas. Separar estimado, observado pendiente de facturación y facturado conciliado.

Registro de aprobación aún vacío: importe aceptado por sesión/mes, tolerancia de contingencia, supuestos, operador/revisor, fecha, referencia al plan exacto y límite de duración. Sin esos datos no hay autorización económica. Antes de cada sesión actualizar cambios de tarifa, configuración, uso previsto y margen de recuperación.

## 3. Inactividad, mínimos y redondeos

- E90A **elimina** la instancia RDS tras cada sesión con confirmación de pérdida definitiva; no incurre en almacenamiento aprovisionado de esa instancia **después de la eliminación efectiva**, pero sí durante todo el tiempo de creación/uso/drenaje/destrucción. Snapshots manuales o backups retenidos, si existieran por excepción, pueden seguir cobrando. [Eliminación RDS](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DeleteDBInstance.html).
- PostgreSQL bajo demanda factura fracciones por segundo con mínimo de diez minutos tras un cambio facturable como creación o inicio; cotizar Multi-AZ con una reserva. [Tarifas RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/).
- RDS Proxy provisionado se tarifa por vCPU/hora, por segundo y mínimo de diez minutos tras cambio facturable. El endpoint predeterminado está incluido; no crear endpoints adicionales no previstos. [Tarifas RDS Proxy](https://aws.amazon.com/rds/proxy/pricing/).
- Cada endpoint de interfaz factura por AZ mientras está aprovisionado, aunque no tenga tráfico; una fracción de hora se cobra como hora completa, más datos procesados. Incluir cada recreación y el endpoint temporal de inicialización. [Tarifas PrivateLink](https://aws.amazon.com/privatelink/pricing/).
- Permanecen S3 y versiones/estado remoto, logs y respaldos retenidos, secretos y claves aplicables; registrar sus cargos según configuración. Recursos de aplicación conservados pueden generar consumo por solicitudes o disparadores accidentales; `offline` y Scheduler deshabilitado deben verificarse. No habilitar capacidad aprovisionada u otros cargos continuos sin decisión expresa.

Estas reglas públicas se consultaron el 21/10/2026; no son una cotización completa ni costos medidos. Revalidarlas al aprobar cada plan.

## 4. Inventario y cierre económico

Mantener inventario verificable por recurso: ID seguro/referencia restringida, servicio, región/AZ, entorno, estado propietario Terraform, persistente/temporal, condición esperada encendido/apagado, unidad facturable, tarifa/fecha, estado real/hora, evidencia, responsable y próxima revisión. **Todavía no hay inventario real de infraestructura ATLAS consolidado**; no inventar IDs ni ausencia de recursos a partir de esta tarea local.

Después de cada **eliminación de sesión E90A**, cotejar listados reales y estados Terraform: RDS **eliminado**, proxy y endpoints ausentes, buckets de demo y **todas sus versiones** eliminados, Cognito de demo y frontend retirados, sin temporales de recuperación olvidados; solo `bootstrap` y controles de cuenta protegidos. No asumir que todos los servicios desaparecen instantáneamente. Una consulta fallida deja la verificación pendiente.

Registrar costos residuales, hora de inicio y fin efectivo de cada recurso y verificaciones de eliminación, responsable y revisor. Revisar costos después de cada sesión y nuevamente cuando se actualice la facturación; contrastar con RC-P10-13, documentar desvíos y exigir nueva aprobación antes de ampliar el consumo. El [runbook manual](../../operaciones/aws/README_OPERACION_MANUAL.md) define orden y tratamiento de fallos. **Apagado seguro todavía no implementado ni probado.**
