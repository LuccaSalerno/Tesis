**HISTÓRICO, SUSTITUIDO: NO EJECUTAR.** Runbook anterior basado en RDS detenido, reemplazado por DO-2026-10-21-E90A. Se conserva solo por trazabilidad.

# ATLAS — Despliegue y operación manual de AWS

**Fecha:** 21/10/2026. **Base:** DO-2026-10-21; RC-P10-07 a 13 y 15; RC-P08; RNF-01 a 04, RNF-06 y RNF-09.
**Estado:** procedimiento propuesto, sin Terraform ni funciones operativas implementadas y sin ciclo AWS ejecutado o verificado. Este documento no acredita apagado seguro ni cumplimiento de aceptación.

**Documento económico de apoyo:** [RC-P10-13 — Cotización preliminar](../../docs/operacion/RC-P10-13_Cotizacion_Preliminar_2026-10-21.md), con tarifas editables en [planilla](../../docs/operacion/RC-P10-13_Modelo_Costos_2026-10-21.xlsx). No reemplaza un cálculo oficial ni habilita operaciones AWS.

## 1. Alcance y responsables

Solo un integrante autorizado ejecuta manualmente las operaciones de infraestructura, despliegue, encendido, apagado, recuperación, reinicialización y migración remota. El equipo revisa y aprueba el plan exacto, impacto y costos antes de cada operación. Los agentes preparan archivos y validaciones locales. Un push, merge, aprobación de PR o workflow manual no ejecuta ni autoriza operaciones AWS.

GitHub Actions queda limitado a CI sin AWS. Sin proveedor OIDC de GitHub, roles para Actions, access keys ni secretos AWS en GitHub. Los roles de ejecución de la aplicación y la autenticación Cognito se mantienen. El procesamiento funcional asíncrono aprobado (Lambda, Step Functions, reconciliador de trabajos) funciona solo dentro de las sesiones habilitadas; sus roles no administran infraestructura. Las campañas automatizadas de API se lanzan y supervisan por el operador fuera de GitHub Actions.

Antes de abrir una ventana, designar operador, revisor, responsable de apagado y suplente, con disponibilidad para atender fallos y el reinicio de RDS a los siete días. No se deja una sesión abierta sin relevo. No se crean automatizaciones de encendido o detención; RC-P10-14 está suspendida.

## 2. Registro obligatorio por operación

Completar en el destino restringido de evidencia operativa elegido por el equipo (pendiente de designar), y versionar solo el resumen saneado:

| Campo | Dato requerido, todavía sin ejecución registrada |
|---|---|
| Solicitud y objetivo | ID de operación, requisitos, tipo (despliegue, migración, encendido, apagado o recuperación) |
| Destino | Cuenta verificada, región `us-east-1`, entorno y raíces/recursos exactos |
| Versiones | Commit, artefactos y huellas; versión de Terraform/proveedores y Alembic cuando existan |
| Plan | Archivo de plan revisado, huella, fecha, cambios, dependencias y ausencia de reemplazos persistentes |
| Economía | Estimación RC-P10-13, límite aceptado para la sesión y residuales, margen para fallos/recuperación |
| Autorización | Persona que aprueba, alcance exacto y fecha; autorización adicional para retirada destructiva de `runtime` |
| Ejecución | Operador, inicio/fin con zona horaria, pasos realizados y resultados; sin credenciales ni contenido documental |
| Verificaciones | Inventario antes/después, esperado/observado, evidencias y fallos; pendientes y responsable |
| Seguimiento | Próxima revisión de costos, detención efectiva de RDS, reinicio previsto y responsable/suplente |

Conservar planes y estados en acceso restringido: pueden contener información sensible aunque sus outputs no muestren secretos. No subirlos a GitHub. Un plan alterado, antiguo o que no corresponde al estado actual exige nueva revisión/aprobación; no usar aplicación automática ni aprobar cambios desconocidos mediante una opción general.

## 3. Antes del primer recurso facturable

1. Confirmar documentos rectores, corpus ficticio y sus bloqueos, región, identidad humana con MFA y alcance mínimo autorizado. Revisar el registro de destinos y retención. Consolidar evidencias de Etapa 0: los reportes del equipo no se convierten en capturas fabricadas.
2. Completar y aprobar la [cotización y presupuesto](../../docs/operacion/Politica_Costos_AWS.md), incluyendo el costo de esta primera prueba de operación y posibles fallos. Preparar inventario previsto de todos los recursos y sus propietarios de estado.
3. Cumplir 1.0 del plan: mantenimiento independiente de PostgreSQL, denegación por defecto, bloqueo de nuevas cargas/confirmaciones, drenaje, conservación de trabajos, recuperación idempotente y control manual del Scheduler. Si no están implementados y validados localmente, no crear infraestructura facturable.
4. Preparar planes de creación y de retirada/recreación limitada a `runtime`; verificar protecciones persistentes, dependencias y ausencia de destrucción o reemplazo de RDS, buckets, Cognito y backend remoto. No usar destrucción general ni `state rm` como atajo.
5. Aprobar la ventana técnica y el procedimiento ante fallo. El primer despliegue queda en `offline`, con ambos reconciliadores deshabilitados donde existan. Ninguna demo se anuncia como operable hasta verificar las compuertas de 1.1.

## 4. Despliegue inicial y migraciones

El operador aplica manualmente el plan aprobado de cada raíz, en orden `bootstrap → persistent → runtime → demo/tests`, verificando el resultado antes de avanzar. `bootstrap` crea el backend remoto una sola vez mediante un procedimiento inicial revisado: restringir y proteger el estado inicial y transferirlo al backend S3 cifrado, versionado y con bloqueo nativo antes de gestionar las demás raíces; comprobar bloqueo y recuperación del estado. Su implementación sigue pendiente. No hay Terraform para ejecutar en esta tarea.

En Etapa 1 se despliega solo `demo`; `pfi_tests` y sus usuarios se inicializan, pero su aplicación se despliega en Etapa 2. No confundir base creada con entorno funcional verificado. Conservar los cinco estados previstos y no crear recursos no aprobados como NAT, bastiones o bases públicas para facilitar administración.

La Lambda privada de inicialización conecta directamente a RDS y usa la credencial maestra administrada en Secrets Manager solo para crear bases, usuarios, esquemas, pgvector y privilegios. El operador invoca esa función manualmente dentro del alcance aprobado. El endpoint temporal de Secrets Manager se inventaría y retira con aprobación cuando deja de ser necesario.

Cada migración requiere revisión de versión actual, entorno/base/usuario exactos, impacto, respaldo previo cuando corresponda y plan de recuperación. El operador invoca la función privada de Alembic con IAM y el usuario de migración del entorno, conexión directa a RDS, TLS y bloqueo de migración. Aplicar solo pendientes y validar el esquema esperado; registrar solo revisión e IDs técnicos. Ni el runner ni el equipo abren SQL público. Ante fallo, mantener `offline`, inspeccionar qué se confirmó y revisar la recuperación; no repetir a ciegas ni habilitar una aplicación incompatible. Demo y tests migran independientemente.

## 5. Encendido de una sesión

1. Confirmar autorización, costo actualizado, inventario, estado remoto y bloqueo, cuenta/región/identidad y disponibilidad del operador de apagado. Ambos entornos desplegados permanecen `offline` y sus schedules deshabilitados.
2. El operador inicia RDS y verifica disponibilidad real, TLS y salud. Preservar Multi-AZ. Registrar tiempos facturables; la disponibilidad puede demorar y no se garantiza un tiempo de arranque.
3. Aplicar manualmente el plan de `runtime` revisado (endpoints necesarios y proxy). Verificar destino saludable y obtener de AWS el `DbiResourceId`, el nuevo `prx-…` y DNS, sin inventarlos.
4. Revisar y aplicar los planes de consumidores desplegados (`demo` y, cuando exista, `tests`) con endpoint y políticas IAM vigentes. Esperar propagación y verificar conectividad permitida y denegada entre usuarios/bases. Sin permisos cruzados ni privilegios temporales amplios para sortear fallos.
5. Ejecutar únicamente migraciones pendientes autorizadas y verificar salud de API, S3, Step Functions y Bedrock mediante pruebas previamente presupuestadas. Ninguna prueba de IA se invoca desde CI ni por el agente.
6. Verificar en `offline` el rechazo de operaciones, salud técnica y dependencias; preparar el cotejo de evidencia y recuperación. Para probar operaciones funcionales por API, el operador debe autorizar y pasar explícitamente a `active` en una **ventana técnica cerrada**, solo con las identidades de prueba autorizadas y sin participantes de demo. No se agrega un bypass del mantenimiento ni un parámetro de petición para elegir entorno. Registrar hora y límite de esa ventana; el otro entorno puede permanecer cerrado.
7. Dentro de esa ventana, comparar por API autenticada la evidencia sintética previa a la detención: mismos trámites, versiones y huellas, decisiones → tareas → ciclos → versiones, validaciones y `DECISION_CONTROL`, auditoría intacta. SQL sirve como diagnóstico, no reemplaza el oráculo funcional. Revisar trabajos en espera, en curso o de inicio incierto y referencias Textract/Step Functions; habilitar manualmente el reconciliador solo si su control de mantenimiento ya se verificó y recuperar el mismo intento conforme RC-P08 sin duplicar efectos ni generar intentos nuevos automáticos tras fallo definitivo. Guardar esperado/observado de los casos sintéticos cerrados de 1.1, sin emitir contenido en logs.
8. Solo tras esos resultados satisfactorios se admite la sesión de demo con sus participantes. Si falla una verificación funcional, el operador cierra la admisión, drena y mantiene el entorno cerrado según §6/§7; no se anuncia la demo como disponible. Ningún trabajo arranca mientras siga `offline`; el paso a `active` técnico no equivale a verificación superada ni autoriza una sesión abierta.

## 6. Apagado controlado

1. Revisar y aprobar la retirada exacta de `runtime` y detención de RDS, su impacto compartido y costos residuales. Avisar a participantes de la sesión por los medios del equipo. Ambos entornos desplegados deben poder cerrarse; si uno sigue activo no retirar recursos compartidos.
2. El operador pone ambos en `draining`: API deniega nuevas operaciones sin consultar PostgreSQL, no emite URLs ni admite confirmaciones. Deshabilita manualmente los reconciliadores y verifica su estado efectivo; Terraform no debe reactivarlos accidentalmente.
3. Cotejar trabajos registrados y ejecuciones reales de Step Functions. Completar operaciones críticas o aprobar interrupción con recuperación explícita. Conservar trabajo/intento, ejecución, objetos de resultados y JobId de Textract; detener Step Functions no detiene un análisis Textract ya iniciado. No borrar pendientes ni evidencia.
4. Esperar el vencimiento de las URLs emitidas (cinco minutos inicialmente) y revisar transferencias iniciadas, pendientes y objetos recibidos. Una carga puede continuar tras vencer su URL: registrar su reconciliación y confirmar que no causa incorporación ni nuevos trabajos fuera de `active`. No deducir drenaje solo del reloj.
5. Conservar una referencia de integridad antes del apagado y confirmar que no hay transacciones críticas activas ni trabajos sin decisión documentada de recuperación. Pasar a `offline` y verificar rechazo por defecto incluso sin PostgreSQL disponible.
6. El operador retira solo los recursos temporales aprobados de `runtime`, incluido cualquier endpoint de inicialización remanente. Revisar el plan antes de ejecutar: jamás afectar recursos de `bootstrap` o `persistent` ni destruir globalmente. Esperar y comprobar la eliminación efectiva.
7. El operador detiene RDS y espera estado `stopped`; registrar hora efectiva y reinicio previsto. Conservar bases, originales, auditoría, snapshots y controles de retención. Registrar recursos que no se pudieron retirar y costo de mantenerlos hasta la recuperación.
8. Cerrar contra el inventario real: proxy ausente, todos los endpoints de interfaz temporales ausentes y sin ENI huérfanas asociadas, RDS detenido, schedules deshabilitados, sin ejecuciones activas no justificadas ni recursos de recuperación olvidados. Conservar VPC, SG y gateway S3. No borrar ENI o recursos desconocidos: identificarlos y revisar su propietario/dependencia.
9. Contrastar inventario con estado remoto y listados de servicio; etiquetas solas no demuestran ausencia de recursos. Registrar residuales y revisar facturación cuando se actualice. El cierre económico permanece pendiente si una consulta falla o quedan discrepancias.

## 7. Fallo intermedio y recuperación

| Fallo | Conducta manual supervisada |
|---|---|
| Creación/aplicación parcial o bloqueo de estado | Mantener `offline`; detener la secuencia, conservar diagnóstico saneado, comparar estado remoto y recursos reales. No forzar desbloqueo sin comprobar que no hay otra operación. Nuevo plan/costo/aprobación antes de reparar. |
| RDS disponible pero proxy/endpoints incompletos | No habilitar consumidores; reparar `runtime`, actualizar consumidores y verificar IAM/TLS. Si se abandona la sesión, aprobar retirada parcial y detener RDS tras drenar. |
| Migración o chequeo de integridad fallido | No abrir la demo. Registrar falla y revisar recuperación con respaldos; no revertir esquema ni restaurar automáticamente. Una restauración crea recursos y requiere nueva estimación/aprobación. |
| Drenaje no converge, carga o trabajo incierto | Mantener `draining` con dependencias disponibles; registrar costo adicional y escalar al equipo. No retirar proxy/RDS hasta completar o autorizar recuperación de cada operación crítica. |
| Retirada parcial de `runtime` o detención de RDS fallida | Mantener `offline`, inventariar lo que sigue facturando y revisar nuevo plan. No declarar apagado ni resolver destruyendo datos. Reintentos solo manuales tras verificar el estado real. |
| Reapertura falla por proxy recreado | Reparar primero `runtime`; reaplicar consumidores con identificadores vigentes. Repetir conectividad, aislamiento, integridad y recuperación antes de `active`. |

Después de una restauración autorizada, RC-P10-12 exige comparar registros/objetos/huellas, versiones históricas y sus decisiones, validaciones y auditoría. No restaurar ni reinicializar demo como si fuera tests. La reinicialización técnica de `pfi_tests` requiere autorización independiente, identidad restringida y comparación de demo antes/después (ver diseño RC-P10 §9).

## 8. Inactividad y evidencia de cierre

RDS reinicia automáticamente después de siete días consecutivos detenido. Registrar ese límite y controles humanos antes y después; el operador revisa periódicamente el estado y los costos. Si reinicia, mantener la aplicación cerrada, evaluar mantenimiento de AWS y aprobar una nueva detención manual cuando sea posible. No se promete que la inactividad suprima todos los cargos ni que Budgets alerte a tiempo.

El inventario y el costo residual se revisan después de cada sesión, reinicio o recuperación. Si no hay responsable disponible para ese seguimiento, no aprobar la creación de RDS. No eliminar datos para reducir la factura. Las verificaciones B/C/E/V-RP/V-MT/V-TF/V-CO/IAM y el resto de A–F se registran por su alcance real: **No ejecutado** hasta contrastarlas con oráculo y conservar evidencia.
