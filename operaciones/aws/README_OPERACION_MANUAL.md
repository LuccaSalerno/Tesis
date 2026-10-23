# ATLAS — Runbook manual E90A: demo AWS descartable

**Fecha:** 21/10/2026. **Estado:** diseño del procedimiento, **no implementado ni probado**. **Autoridad:** DO-2026-10-21-E90A (decisiones técnicas), RC-P10, AGENTS.md. [Versión anterior histórica](../../docs/operacion/Runbook_RDS_Detenido_HISTORICO_2026-10-21.md) — no ejecutar.

> **Para la próxima sesión, seguí la [guía paso a paso de la sección 6](Guia_Sesion_Seccion6.md)** (23/10/2026): reúne la cuenta nueva, el encendido, la demo, los ejecutores de §6.3 y el retiro.

## Procedimiento concreto (DO-2026-10-22-OPS, 22/10/2026)

Los comandos de cada paso, las raíces de Terraform, la Lambda privada de operaciones, la semilla, la exportación de evidencia y el vaciado de buckets están en [infra/terraform/README.md](../../infra/terraform/README.md). Cotización por sesión: [RC-P10-13_Cotizacion_Sesion_E90A.md](../../docs/operacion/RC-P10-13_Cotizacion_Sesion_E90A.md). Todo está **preparado y validado sin AWS**; nada se ejecutó contra una cuenta.

**Precisión del paso A.4:** la semilla usa la API, así que exige el estado `active`. Se pasa a `active` antes de sembrar, con solo las cuentas ficticias del operador (Cognito no admite registro propio), y la demo se abre a participantes recién después del paso A.6.

## Alcance y límites inviolables

Una sesión E90 **crea una infraestructura nueva de demo, la puebla con corpus sintético, la evalúa y elimina todos sus recursos AWS** (incluida RDS). No se conserva ningún trámite/documento/usuario/historial en AWS entre sesiones; la aplicación sigue prohibiendo el borrado funcional de estos elementos. El repositorio local, evidencias académicas saneadas, Budgets, cuenta/Organizations, exclusión de contenido IA y `bootstrap` (estado remoto Terraform) **no** se eliminan. Ninguna acción se ejecuta desde GitHub Actions o agente; un humano autorizado administra AWS.

Se mantiene la arquitectura de procesamiento real (RDS Multi-AZ, Proxy, Step Functions, Textract y Bedrock). El seed no falsifica eventos históricos ni simula resultados IA si se pretende validar IA real. No construir un borrado sin saber cuál recurso pertenece a la sesión.

## Lista previa a cualquier creación AWS (bloqueante)

- [ ] Evidencia de aprobación por responsable y revisor humano, identificación de cuenta, región `us-east-1`, entorno `demo`, ventana de trabajo, responsable del cierre y presupuesto aprobado para **todo el ciclo**, incluido tiempo de eliminación.
- [ ] Cotización RC-P10-13 de crear/migrar/sembrar/procesar/drenar/destruir, mínimos, margen de error y residuos. AWS Budgets USD 1/20 **no** es un límite de gasto.
- [ ] `bootstrap` existente, cifrado, con estado remoto bloqueado y respaldado; no se incluye en ningún plan de destrucción.
- [ ] `persistent`, `runtime` y `demo` identificados como raíces **de sesión** para E90A, plan de creación y **plan de destrucción selectiva** revisados. No compartir recursos con tests/u otros entornos; no usar `terraform destroy` global, `state rm` o desactivar protecciones globalmente.
- [ ] Guion y oráculo del seed local versionados, documentos exclusivamente ficticios, identidades de prueba, SHA-256 de corpus y ausencia de secretos en repo/logs.
- [ ] Prueba local de semilla y de drenaje; plan de fallos y mecanismo para exportar evidencia saneada antes de borrar recursos; procedimiento de vaciado **versionado** de S3 definido.

## A. Encendido: operador humano, recursos NUEVOS

1. Registrar hora, operador y autorización; comprobar estados remotos y que no existan recursos olvidados de una sesión anterior.
2. Aplicar **manualmente** `persistent → runtime → demo` con Terraform bajo planes previamente aprobados (una vez configurado `bootstrap`). Inicialmente `offline` y Scheduler deshabilitado; esperar convergencia AWS, DNS y recursos de IAM. No se ejecuta nada automáticamente desde GitHub.
3. Crear la instancia RDS PostgreSQL Multi-AZ aprobada, inicializar pgvector, bases/usuarios, permisos y ejecutar migraciones Alembic **mediante función privada** y operación humana autorizada. Verificar IAM/TLS y que cada aplicación usa base correcta. En E90 solo demo.
4. Ejecutar el **seed sintético** conforme a `docs/operacion/Seed_Demo_E90_Especificacion.md`, después de crear identidades ficticias. Verificar por API cada trámite, documento, versión, validación y evento, y registrar mapeo de IDs de la sesión actual. No cargar datos anteriores ni insertar directamente eventos auditables.
5. Habilitar temporalmente invocaciones reales de Textract/Bedrock **solo** tras autorización y presupuesto. Esperar y comprobar procesamiento, advertencias, fuentes, permisos y respuesta RAG según hitos implementados; el seed no acredita automáticamente requisitos funcionales ni métricas experimentales.
6. Ejecutar pruebas de salud y negativas de autorización. Solo con resultados aceptables pasar a `active` y abrir demo a participantes.

## B. Cierre: drenar, evidenciar y DESTRUIR recursos de sesión

1. Poner demo en `draining`, deshabilitar reconciliador y no emitir URLs prefirmadas nuevas. Comprobar que no quedan cargas, ejecuciones Step Functions ni operaciones Textract activas o con resultado incierto. Una URL vencida **no** confirma que una transferencia anterior haya terminado.
2. Completar o resolver los trabajos pendientes sin borrar evidencia de manera funcional mientras la sesión exista. Si no converge, mantener entorno cerrado y registrar el costo de espera; no iniciar destrucción a ciegas.
3. Exportar resultados de pruebas, capturas saneadas y referencias de código/corpus/oráculo **a medios locales del equipo**. No exportar documentos reales ni secretos. Comprobar que se obtuvo todo lo necesario, porque los datos AWS se perderán permanentemente.
4. Poner entorno en `offline`. Preparar por separado planes selectivos de retiro en orden de dependencias **`demo → runtime → persistent`**; inspeccionar cada recurso, dependencia, bucket versionado, backups/snapshots, secretos, CDN y recursos de logging asociados. Excluir `bootstrap` y recursos no identificados como propiedad de esa sesión.
5. Confirmar por escrito la pérdida irreversible: **RDS y datos se eliminan, sin snapshot final y sin backups retenidos**. Si hay requisitos académicos pendientes que precisan la misma evidencia después de la destrucción, no marcar esos criterios como cumplidos.
6. Operador humano ejecuta manualmente cada plan autorizado y gestiona explícitamente el vaciado real de todas las versiones de buckets S3 de la demo. Nunca activar `force_destroy` universal ni borrar depósitos de Terraform. Eliminar solo logs, secretos y recursos de sesión expresamente revisados, considerando ventanas de recuperación obligatorias o facturación residual.
7. Verificar por consultas de AWS y estado remoto que la instancia RDS, RDS Proxy, endpoints privados, Lambdas y API de demo, buckets/objetos versionados, Cognito y recursos restantes **no continúan aprovisionados**. Algunas eliminaciones son asincrónicas: revalidar hasta convergencia. Anotar cualquier componente retenido/pendiente y estimar su costo.
8. Cerrar acta: hora de inicio/cierre facturable, inventario esperado/observado, plan aprobado/ejecutado, incidencias, estado final de recursos y revisión posterior de Billing. No declarar «costo cero» porque puede haber cargos diferidos o residuos.

## C. Fallos, independencia y seguridad

- Si Terraform presenta drift o un bloqueo de estado, detener el procedimiento, comparar estado con AWS y resolver mediante revisión humana. Nunca borrar el estado remoto para forzar la retirada.
- Si un recurso no se elimina o quedan `pending` en AWS, **no** declarar apagado completo; continuar la verificación y documentar costos.
- Si falla el seed, mantener `offline`: comparar entradas/observado y corregir solo mediante el código y API autorizados; no fabricar cumplimiento ni insertar historial en DB.
- Si hay una base/identidad/bucket compartida con `tests` u otro entorno, no destruirla; revisar diseño de aislamiento antes de habilitar modalidad descartable.
- La prueba de persistencia entre sesiones con los **mismos** registros (B original) no es compatible con E90A y permanece pendiente o requiere un ensayo independiente de recuperación.

**Referencia:** [decisión E90A](../../docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md), [diseño](../../docs/diseno/RC-P10_Diseno_Infraestructura.md), [seed](../../docs/operacion/Seed_Demo_E90_Especificacion.md), [política de costos](../../docs/operacion/Politica_Costos_AWS.md).
