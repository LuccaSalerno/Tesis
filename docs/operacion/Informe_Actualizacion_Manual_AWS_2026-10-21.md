**HISTÓRICO — antes de la decisión E90A:** la detención de RDS y conservación entre sesiones descritas aquí fueron reemplazadas por la modalidad de demo descartable DO-2026-10-21-E90A. Consultar el [runbook vigente](../../operaciones/aws/README_OPERACION_MANUAL.md). No ejecutar los pasos de este informe como instrucciones actuales.

# Informe de actualización — Operaciones AWS manuales

**Fecha:** 21/10/2026. **Rama:** `codex/aws-manual-costos`. **Resultado:** cambios documentales y retirada de plantilla local realizados; infraestructura, procedimientos y aceptación AWS pendientes de implementación/ejecución. Sin commit, push, merge, despliegue, consulta de cuenta AWS ni ejecución de Terraform durante esta tarea.

**Adenda de auditoría del ZIP:** [Informe_Auditoria_ZIP_2026-10-21.md](Informe_Auditoria_ZIP_2026-10-21.md). Conservamos este informe como registro del trabajo anterior: algunas observaciones de su sección de pendientes fueron abordadas en el ZIP actual y se actualizan en la auditoría nueva. La cotización preliminar se documentó por separado y RC-P10-13 no está cerrado.

## 1. Tarea y alcance

**Tarea:** Etapa 0.6/0.7 y ajuste de dependencias de Etapas 1–4 para operación manual y control económico.
**Requisitos trazados, sin declarar cumplimiento funcional:** RC-P02; RC-P09; RC-P10-07 a 15; RC-P08; RNF-01 a 04, RNF-06 y RNF-09; preservación de RN-10 y EVD-01.
**Decisiones delegadas tomadas:** ninguna. DO-2026-10-21 registra una decisión expresa del equipo, no una elección autónoma del agente.

Se leyeron AGENTS.md, la tesis disponible, decisiones, aceptación integral, EVD-01, diseño y plan, en su orden de precedencia, y los archivos operativos existentes. Se inspeccionaron los pasajes pertinentes de §§3.3, 5.4 y 6 y la Figura 5.6. No se encontró código de aplicación anterior, Terraform, `.github/workflows/` ni scripts de despliegue ejecutables; solo el script de auditoría AWS de lectura y la plantilla de trust OIDC. No se creó CI nuevo ni se retiraron pruebas.

## 2. Lista exacta de archivos intervenidos

Clasificación respecto del contenido presente antes de esta tarea; la mayoría de estos archivos ya estaban sin seguimiento en Git. No se atribuyen al agente los archivos del corpus ni el PDF aportados por el equipo.

| Estado | Archivo | Cambio |
|---|---|---|
| Modificado | `AGENTS.md` | Operación AWS solo humana, sin autorización de ejecución para agentes/workflows; sin OIDC/credenciales AWS para Actions; CI sin AWS, costos previos, protección de persistent/bootstrap. |
| Modificado | `README.md` | Entrada al repositorio y enlaces a política manual, costos y estado real de preparación. |
| Modificado | `README_PRIMERO.md` | Retira preparación OIDC, reconoce tesis presente y verificaciones comunicadas; mantiene bloqueos y nuevas compuertas. |
| Modificado | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` | DO-2026-10-21 con fecha, motivo e historia; RC-P02.6, RC-P10-11/15, RC-P10-13 previo, RC-P10-14 suspendida y secuencia inicial. Corrige nombre real del contrato v1.1. |
| Modificado | `docs/diseno/RC-P10_Diseno_Infraestructura.md` | Sustituye acceso de runners por ejecución humana; conserva cinco estados, red privada e IAM; encendido/apagado propuestos, control de fallos, mantenimiento y presupuesto antes de demo. |
| Modificado | `docs/operacion/Registro_Destinos_y_Retencion.md` | Registra observaciones del equipo de Organizations/logging/modelos, perfiles/destinos, tokens y dimensiones; agrega Sonnet/Titan y destinos previstos; evidencia y retención no comprobadas quedan pendientes. |
| Modificado | `docs/plan/Plan_Implementacion_por_Etapas.md` | 0.6 exige cotización/presupuesto y 0.7 preparación manual; nuevo 1.0 y compuerta 1.1; Etapas 2/3 amplían operación y aislamiento; Etapa 4 mide costos sin diferir estimación inicial. |
| Modificado | `docs/tesis/README_FALTA_TESIS_VIGENTE.md` | Conserva el aviso como antecedente y registra que main.pdf está presente; congelación formal por el equipo pendiente. |
| Modificado | `operaciones/aws/README_CONFIGURACION_ETAPA_0.md` | Retira pasos de crear proveedor/roles OIDC; actualiza estado reportado por equipo, presupuestos y procedimiento de entrega al operador. |
| Modificado | `operaciones/aws/auditoria_lectura_ETAPA0.sh` | Solo comentario de ejecución humana y prohibición de integrarlo en Actions/automatizaciones; conserva exactamente las operaciones de lectura existentes. No se ejecutó. |
| Creado | `docs/operacion/Politica_Costos_AWS.md` | Sesiones controladas, budgets reportados, estimación hora/sesión/mes, residuales, mínimos/redondeos con fuentes oficiales, inventario y cierre económico. Importes de arquitectura pendientes. |
| Creado | `operaciones/aws/README_OPERACION_MANUAL.md` | Procedimiento propuesto de autorización, despliegue, migraciones privadas, encendido/apagado, verificación de integridad, recuperación y control de reinicio RDS. |
| Creado | `docs/operacion/Informe_Actualizacion_Manual_AWS_2026-10-21.md` | Este informe: alcance, inventario de cambios, contradicciones, validaciones y pendientes. |
| Retirado | `operaciones/aws/trust_demo_oidc_PLANTILLA.json` | Retirada local de la plantilla incompatible; no se aplicó ni se eliminó ningún proveedor o rol de la cuenta AWS. Antecedente conservado en DO-2026-10-21. |

**Totales:** 10 modificados, 3 creados y 1 retirado. Tesis PDF, ambos contratos de aceptación, corpus, oráculos, generador y registro de decisiones delegadas conservados sin cambios.

## 3. Decisión operativa y contradicciones

**DO-2026-10-21:** minimizar costos inesperados y mantener control humano. Sin proveedor OIDC de GitHub, roles para Actions ni credenciales AWS en GitHub. Ninguna operación de infraestructura por workflows, push, merge, agentes o automatizaciones; ejecución manual por operador con plan, impacto y costos aprobados. Terraform y arquitectura aprobada conservados. Aprobar un plan no autoriza al agente a ejecutarlo.

| Contradicción previa | Resolución documentada |
|---|---|
| AGENTS.md/RC-P02 exigían OIDC y RC-P10 permitía despliegues desde Actions | CI sin AWS; toda operación AWS administrativa pasa al operador. Incluso `workflow_dispatch` queda excluido. |
| Migraciones podían solicitarse desde un runner con rol OIDC | El operador invoca manualmente las funciones privadas con IAM y usuarios de migración separados; conserva red privada y acceso directo a RDS. |
| La Etapa 1 exponía demo antes del mantenimiento/apagado de Etapa 3 | 1.0 prepara controles antes del primer recurso facturable; 1.1 verifica el ciclo cerrado y, con el recorte funcional disponible, persistencia/recuperación sintéticas antes de habilitar puntos de demo. |
| RC-P10-14 seguía como automatización diferida | Suspendida: seguimiento de siete días y detención humana, sin permiso implícito de automatizar después. |
| Cotización aparecía junto con mediciones tardías de Etapa 4 | Cotización y presupuesto aceptado son previos al primer despliegue; luego se actualizan con costos reales. |
| Avisos decían que faltaba tesis y que nada de AWS estaba comprobado | Se reconoce main.pdf presente y se registran únicamente las comprobaciones comunicadas por el equipo, con capturas pendientes. |
| El diseño afirmaba idempotencia del ciclo sin ejecución | Se cambia a una propiedad que debe implementarse y verificarse; no se acredita el ciclo. |
| Versión abreviada del nombre del contrato no coincidía con el archivo | Se referencia el archivo real con sufijo `_v1_1.md`. |

**Compatibilidad con la tesis:** no se encontró una obligación de OIDC de GitHub/CD automático. OIDC/OAuth2 funcional con Cognito y la ejecución declarativa manual de Terraform se conservan. El PDF, RF/RN/RNF, relaciones del modelo y umbrales de evaluación no se modificaron.

**Ambigüedad que no se resuelve cambiando la tesis:** si «ninguna invocación automática de servicios AWS» se pretendiera extender al procesamiento funcional, sería incompatible con Step Functions, Lambda y el reconciliador exigidos en §§5.3.1, 5.4.2 y 6.3.2. La actualización aplica la prohibición a operación/despliegue administrativo y conserva el procesamiento académico dentro de sesiones autorizadas. Propuesta para ratificación del equipo antes de implementar: explicitar ese alcance. Si el equipo pretende una prohibición funcional más amplia, elevar una corrección académica separada antes de construir, sin sustituir servicios ni pruebas.

## 4. Referencias legítimas conservadas

- Antecedentes de OIDC de GitHub y del runner de migración: bloque **Antecedentes sustituidos** de DO-2026-10-21 y RC-P10-14 suspendida, todos rotulados como no vigentes. Los README remiten a ese antecedente; no conservan instrucciones de configuración.
- Menciones de OIDC/Actions en las prohibiciones actuales definen controles; no son autorizaciones.
- OIDC/OAuth2 de Cognito permanece en la tesis y en el inventario, como autenticación de usuarios.
- EVD-01, reintentos y reconciliación funcional, backups y monitoreo de la arquitectura siguen previstos; no administran despliegues. La suite sigue automatizada, pero las campañas AWS se inician y supervisan por humanos fuera de GitHub Actions. La referencia de aceptación al mecanismo de CI es un ejemplo de repetibilidad, no obliga a darle acceso AWS al runner.

## 5. Procedimiento propuesto

El detalle está en [operación manual](../../operaciones/aws/README_OPERACION_MANUAL.md); **todavía no está implementado ni probado**.

1. Antes de crear: estimación oficial, presupuesto aceptado, operador/suplente, inventario, controles locales de mantenimiento/drenaje, planes de creación y retirada limitada a temporales, aprobación del plan exacto.
2. Desplegar manualmente `bootstrap → persistent → runtime → demo/tests`, inicialmente `offline`; Etapa 1 solo despliega demo. Inicializar y migrar con funciones privadas e identidades del entorno.
3. Encender RDS, reconstruir runtime, actualizar consumidores y políticas del proxy, migrar si corresponde y probar TLS/aislamiento/salud en mantenimiento. Luego el operador abre una ventana técnica cerrada en `active` para verificar integridad por API y recuperación, sin bypass de mantenimiento. Solo tras resultados satisfactorios se admite a los participantes de demo.
4. Apagar ambos entornos desplegados: `draining`, detener schedules, resolver trabajos/cargas inciertos, `offline`, retirar runtime y detener RDS. Conservar datos, auditoría y protecciones persistentes.
5. Comprobar inventario real, recursos temporales ausentes, residuales y estado remoto; revisar cargos al actualizarse y controlar humanamente el reinicio RDS a los siete días. Ante fallo parcial mantener mantenimiento y aprobar recuperación, sin destrucción general.

Las reglas públicas de cobro y enlaces oficiales están en la [política de costos](Politica_Costos_AWS.md). Son insumos de la cotización pendiente, no una estimación numérica ni costos observados de ATLAS.

## 6. Validaciones locales y revisión del diff

- Se ejecutó una validación local con Python 3: hashes contra copia previa, ausencia de Terraform/workflows nuevos, retirada exacta de plantilla, rama correcta, enlaces y tablas Markdown, lista de siete operaciones de lectura del script y búsqueda de instrucciones sustituidas. Resultado: satisfactorio.
- `bash -n operaciones/aws/auditoria_lectura_ETAPA0.sh`: código 0. No se ejecutó el script ni sus llamadas AWS.
- `git diff --check`: código 0. Revisión del diff seguido de README realizada.
- `git diff --no-index` contra una copia previa local y `--check` por archivo: sin errores de espacios. Se revisó además el contenido de los documentos nuevos y los cambios de decisiones/diseño/plan/runbooks. La mayor parte del material inicial estaba **sin seguimiento**: `git diff` ordinario no muestra esos archivos, por eso se usó la copia previa y no se agregó material del equipo al índice para simular un diff completo.
- Búsqueda con `rg` de OIDC, runners, GitHub, despliegue y automatización: las referencias restantes corresponden a prohibiciones, antecedentes rotulados o comportamiento funcional de la tesis. Se inspeccionó la Figura 5.6 renderizada localmente; el PDF se conserva byte a byte.
- Ninguna prueba funcional, experimental o de infraestructura AWS ejecutada: no hay aplicación/Terraform implementados. No se marca ningún criterio de aceptación como `Cumple`. No se fabrican capturas ni resultados.

La evidencia local de trabajo (snapshot, diff y salida estructurada de validaciones) está bajo `/tmp/atlas_manual_20261021_antes`, `/tmp/atlas_manual_diff.patch` y `/tmp/atlas_manual_validaciones.json`, respectivamente. Es evidencia local de esta revisión, no evidencia AWS ni un nuevo servicio de almacenamiento aprobado.

## 7. Pendientes y aprobaciones antes del primer despliegue

- Completar y aceptar RC-P10-13 con tarifas de us-east-1, costo por hora/sesión/mes, inactividad, residuales, mínimos y contingencia. Registrar importe aceptado y aprobación; USD 20 no se presume suficiente.
- Seleccionar operadores, revisor y suplente, identidad humana/MFA/privilegios, ventana, responsable de apagado y seguimiento del reinicio RDS; designar destino restringido de evidencia.
- Preparar e implementar Terraform con las protecciones y backend remoto, controles de mantenimiento/drenaje/recuperación y funciones privadas de inicialización/migración; revisar planes exactos, incluida retirada de temporales, antes de ejecutarlos manualmente.
- Ejecutar en ventana técnica aprobada los chequeos tempranos de mantenimiento, persistencia, recuperación, IAM/TLS, referencias de proxy y cierre económico. Ampliarlos al desplegar tests y completar luego A–F y el resto de RC-P10; conservar oráculos y evidencia.
- Consolidar capturas de Organizations, logging, perfiles/modelos y Budgets; comprobar recepción de alertas, retención efectiva y destinos reales. La prueba de Titan 256 no reemplaza la configuración comparable de 1024 dimensiones.
- Completar inventario verificable de recursos; no se ha constatado si existen proveedores/roles OIDC previos en la cuenta. Si aparecen, su retirada requiere un cambio humano separado y aprobado.
- Congelar versión contractual de la tesis y corpus/oráculo; consulta oficial ARCA sigue pendiente. No ejecutar AWS ni subir documentos para resolver esos pendientes durante esta tarea.

**Preguntas para el equipo:** ninguna necesaria para finalizar estos cambios locales. Antes de implementar, ratificar el alcance administrativo de la prohibición de automatizaciones indicado en §3 y resolver las aprobaciones anteriores. Este informe no solicita ni concede permiso para desplegar.
