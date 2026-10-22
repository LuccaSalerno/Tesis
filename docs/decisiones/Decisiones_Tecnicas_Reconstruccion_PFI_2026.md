# Decisiones técnicas — Reconstrucción del prototipo ATLAS (PFI UADE 2026)

**Estado del documento:** registro vivo de decisiones. Se actualiza a medida que se cierra cada decisión.
**Última actualización:** 21/10/2026. Además de las decisiones de operación manual y demo descartable, el equipo aprobó DO-2026-10-21-E90-CORPUS para ajustar **solo el protocolo documental de medición**: 50 sintéticos, 3 casos adversariales incluidos y ajuste separado. No modifica RF/RN/RNF ni umbrales. El PDF más reciente incorporado en este paquete ya contempla 50 documentos; resta integrar la propuesta de redacción 6.0–6.3 en LaTeX por sus autores. RC-P10-13 y las verificaciones de ejecución siguen pendientes.

---

## 0. Reglas generales de la reconstrucción

1. **La tesis es el contrato.** Ningún RF, RN, RNF, relación del modelo de datos (Sección 5.2) ni umbral de la Sección 6 se modifica para facilitar la construcción. Si algo no está especificado, se registra aquí como decisión, sin atribuirlo a la tesis.
2. **Reconstrucción desde cero.** No se reutiliza el código del prototipo anterior. Si existe en el repositorio, es material histórico y no una base válida.
3. **Documentos de referencia obligatorios:**
   - Tesis vigente (`main.pdf` o sus fuentes LaTeX).
   - `docs/aceptacion/Contrato_Aceptacion_Integral_Reconstruccion_PFI_2026-10-20_v1_1.md` (v1.1): cómo se verifica cada RF, RN y RNF.
   - `EVD-01_Criterios_Aceptacion_Reconstruccion_APROBADO_2026-10-20.md`: criterios V1–V11 y recorridos EVD-A, EVD-B, EVD-C y EVD-N12.
   - Informe de diseño de RC-P10 y su revisión complementaria: referencia de diseño de la infraestructura AWS.
   - Este documento.
4. **Orden de construcción:** primero la cadena de evidencia (V1, V2, V3, V4, V7 y V9); después el resto de los RF y RN; las pruebas acompañan la construcción desde el inicio.
5. **Demo:** gira alrededor de un **contrato**, no de una factura (pedido de los evaluadores en la defensa anterior).

---

## 1. Decisiones cerradas

### PD-01 — Catálogo de reglas de consistencia

**Base en la tesis:** Sección 5.3.5, RF-16, RN-02 y RN-06. Las reglas son explícitas y deterministas, operan solo sobre campos **validados** de documentos **vinculados**, conservan la versión de la regla, los valores, las versiones documentales, el resultado y una explicación, y nunca aprueban ni observan por sí solas.

**Catálogo:**

| Código | Regla | Si no se cumple |
|---|---|---|
| **R1** | CUIT del emisor de la factura = CUIT del proveedor de la orden de compra vinculada | Advertencia |
| **R2** | CUIT del proveedor de la orden de compra = CUIT de la contraparte del contrato vinculado | Advertencia |
| **R3** | Fecha de la orden de compra dentro de la vigencia del contrato vinculado (vigencia desde ≤ fecha ≤ vigencia hasta) | Advertencia |
| **R4** | Importe total de la factura ≤ importe total de la orden de compra vinculada, con la misma moneda | Advertencia |

**Resultados posibles** (los cuatro que define la tesis): cumplimiento, advertencia, falta de datos, no aplicable.

**Reglas comunes:**
- Si algún campo necesario no está validado → **falta de datos**. Nunca se usa un valor sugerido.
- Si los documentos no están vinculados o el tipo documental no corresponde → **no aplicable**.
- R4: si las monedas difieren → **no aplicable**; si falta validar la moneda → **falta de datos**.
- Cada regla tiene código y versión (por ejemplo, `R3-VIGENCIA-OC-CONTRATO v1`).
- Al incorporarse una versión nueva, se vuelven a ejecutar las reglas pertinentes sin modificar las ejecuciones históricas.

**Escenario de prueba EVD-01:** orden de compra por 10.000 y factura por 10.500 → R4 produce advertencia.

---

### PD-02 — Registro de los controles considerados por cada decisión (`DECISION_CONTROL`)

**Base en la tesis:** modelo lógico (Figura 5.4), RF-16, RF-20; criterio V4 de EVD-01.

**Decisión:** registro **automático**.

1. Cuando el revisor/aprobador aprueba u observa, el sistema guarda en `DECISION_CONTROL` las **ejecuciones de reglas que se le mostraban en esa tarea**: las últimas ejecuciones sobre el conjunto de versiones del ciclo de revisión.
2. Se guardan los **identificadores de esas ejecuciones concretas**, no una consulta del tipo «última ejecución». Las ejecuciones posteriores (por ejemplo, tras una versión nueva) no alteran lo registrado en decisiones anteriores.
3. **No se puede decidir con controles pendientes.** Si hay reglas aplicables en ejecución sobre las versiones del ciclo, la tarea muestra «controles pendientes» y no admite aprobar ni observar hasta que terminen.
4. Si no hay reglas aplicables (por ejemplo, sin documentos vinculados), la decisión se registra sin controles asociados.

---

### PD-03 — Reconstrucción de la evidencia desde una decisión

**Base en la tesis:** RF-21, RF-22; criterios V1–V4 de EVD-01; Sección 6.2.

**Decisión:**

1. **Vista dedicada «Evidencia de la decisión»**, accesible desde la línea de tiempo y desde la tarea.
2. **Un único endpoint** que devuelve la cadena completa (nombre ilustrativo: `GET /decisiones/{id}/evidencia`):
   - decisión: actor, fecha, resultado (aprobación u observación) y motivo si corresponde;
   - tarea y ciclo de revisión;
   - conjunto exacto de versiones consideradas en el ciclo;
   - validaciones de los campos usados: valor sugerido, valor validado, actor, fecha, versión y fuente/localizador;
   - ejecuciones de reglas registradas en `DECISION_CONTROL`: código, versión, entradas, resultado y explicación;
   - eventos de auditoría relacionados.
3. **Acceso:** responsable del trámite y revisor/aprobador con tarea asignada. El administrador operativo no accede (RF-24).
4. El mismo endpoint sirve para la pantalla, las pruebas automatizadas de EVD-01 y la demo.

**Impacto en la tesis (lote aparte):** agregar un mockup de esta vista en la Sección 3.4.

---

### PD-05 — Versión nueva con tareas abiertas y concurrencia

**Base en la tesis:** RN-12; recorrido EVD-N12.

**Decisión:**

1. **Operación atómica:** confirmar la versión nueva, cerrar el ciclo anterior, anular sus tareas abiertas, volver el trámite a Borrador y registrar el evento ocurren en una única transacción. O pasa todo, o nada.
2. **Operaciones del trámite serializadas:** las operaciones que cambian el estado de un trámite (confirmar versiones, decidir tareas, cancelar) bloquean el trámite mientras se ejecutan. Si dos llegan a la vez, la segunda espera.
3. **Rechazo de la decisión tardía:** si el revisor decide sobre una tarea ya anulada, el sistema responde «la documentación del trámite cambió; esta tarea ya no admite decisiones» y no registra nada.
4. **Tareas anuladas visibles:** quedan con estado «anulada por cambio documental» en el historial. Es un estado de la **tarea**, no del trámite; no altera los siete estados de la tesis.
5. Una carga todavía **pendiente de confirmación** no dispara estos efectos.

---

### RC-P04 — Campos por tipo documental, formatos y límites

**Base en la tesis:** Secciones 5.3.2 y 6.3.1, RF-04, RF-10, RNF-06.

**Campos a extraer y validar:**

| Tipo | Campos |
|---|---|
| **Contrato** | Contraparte (razón social), CUIT de la contraparte, fecha de celebración, vigencia desde, vigencia hasta, monto total, moneda |
| **Orden de compra** | Número, fecha, proveedor (razón social), CUIT del proveedor, importe total, moneda |
| **Factura** | Número, fecha de emisión, emisor (razón social), CUIT del emisor, importe total, moneda |
| **Presupuesto** | Número, fecha, proveedor (razón social), CUIT del proveedor, importe total, moneda |
| **Comprobante** | Número, fecha, contraparte (razón social), CUIT de la contraparte, importe, moneda |

Los cuatro campos críticos de la Sección 6.3.1 (importe total, fecha, número de documento y CUIT de la contraparte) están en los cinco tipos. En el contrato, la fecha es la de celebración y el importe es el monto total.

**Formatos y límites:**
- Se admiten exclusivamente **PDF** (digitales, escaneados o generados a partir de fotografías) y **DOCX**. Los demás formatos se rechazan con un mensaje explicativo.
- Tamaño máximo configurable de **20 MB** por archivo y **50 páginas** para PDF.
- Para DOCX se aplica el límite de tamaño y un límite configurable de texto extraído de **150.000 caracteres**.
- Todos los límites se administran por configuración, sin modificar el código.

**Validación:**
- La API realiza comprobaciones preliminares antes de autorizar la carga.
- Una vez recibido el archivo en S3, el sistema verifica su tipo real por contenido (no por extensión) y su estructura antes de permitir el procesamiento.
- Los archivos inválidos se rechazan sin producir efectos sobre las versiones ni los estados del trámite.
- Los PDF protegidos con contraseña y los archivos dañados o incompatibles se rechazan con un mensaje que identifica la causa y la acción necesaria.

---

### RC-P05 — Corpus de evaluación (Sección 6.3.1; revisión E90)

**Decisión vigente según DO-2026-10-21-E90-CORPUS:** la medición se realiza exclusivamente con **50 documentos sintéticos**, diez por cada uno de los cinco tipos; **tres de los 50** contienen intentos de *prompt injection*. Se mantiene un grupo **independiente de ajuste**, con **2–3 documentos por tipo** (10–15 en total), fuera de las métricas de medición y con al menos una plantilla de cada tipo reservada a medición. Se conservan las 30 preguntas RAG (seis sin respuesta), las métricas y los umbrales de la tesis. **No se requieren 16 documentos adicionales ni conjuntos públicos o empresariales de contraste** para estas métricas. El protocolo completo se encuentra en `docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md`.

**Trazabilidad actualizada para este paquete:** el PDF `docs/tesis/main.pdf` fue reemplazado por una versión más reciente proporcionada por los autores que expresa 50 sintéticos y ajuste independiente. La propuesta de 6.0–6.3 en Markdown todavía debe integrarse en la fuente LaTeX. Esta revisión es una **decisión expresa del equipo sobre el conjunto de evaluación**, no una autorización para rebajar requisitos funcionales o umbrales.

---

### DO-2026-10-21-E90-CORPUS — Evaluación sintética y validación operativa separadas

**Fecha:** 21/10/2026. **Estado:** decisión metodológica cerrada por el equipo; corpus ampliado, oráculos y campañas aún no ejecutados. **Ámbito:** dataset/procedimiento de evaluación y resguardo de documentación operativa. No modifica alcance funcional, RF, RN, RNF, umbrales ni arquitectura.

1. **Medición §6.3.1:** 50 documentos **sintéticos** (10 contratos, 10 presupuestos, 10 órdenes de compra, 10 facturas y 10 comprobantes), con diversidad de diseños/formatos y **tres documentos con instrucciones maliciosas** dentro de esos 50. Eliminar como obligaciones activas los 16 casos adicionales y los 10–15 documentos públicos. Se conservan 2–3 documentos de ajuste **por tipo**, independientes, sin contaminación con el conjunto de medición; al menos una plantilla por tipo exclusiva de medición.
2. **RAG:** 30 preguntas, seis sin respuesta; oráculo fijado previamente; evaluación independiente de ambos autores; métricas, umbrales y reglas de comparación de modelos/embeddings **sin cambios**. Las pruebas adversariales complementan, no reemplazan, la evaluación cuantitativa general; tres casos no prueban inmunidad general.
3. **Validación funcional/operativa §6.4:** constituye una línea de evidencia **separada** de la cuantificación sintética. Puede involucrar documentos propios del entorno operativo real, bajo autorización y controles de privacidad/transferencias aplicables. **No se importan, copian ni publican** dichos documentos en el repositorio, el corpus sintético, la CI ni el agente de código. Se documentan solo resultados y evidencias no confidenciales aprobados; no se atribuyen métricas sintéticas a este recorrido.
4. **Demo AWS E90A:** continúa siendo **descartable y exclusivamente sintética** con seed PD-07. La validación operativa real es independiente de esa demo y **no autoriza** cargar documentos reales a la cuenta AWS de pruebas; cualquier tratamiento externo requiere revisión específica de permisos, destino y política RNF-03/RC-P09 antes de efectuarse.
5. **Tesis:** la redacción y actualización de su fuente corresponden a los autores, no al agente. Escribir el texto académico final como trabajo concluido **solo cuando existan pruebas realmente ejecutadas y evidencia**; los estados pendientes se registran en el repositorio operativo, nunca como resultados ficticios.

**Referencias:** `docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md`, `docs/aceptacion/Contrato_Aceptacion_Integral_Reconstruccion_PFI_2026-10-20_v1_1.md` (sección 5.1 revisada), PD-07, RC-P06.2, DO-2026-10-21-E90A.

### RC-P02 — Estrategia y herramientas de pruebas

**Decisión:**

1. **Backend y API:** pytest para pruebas unitarias, de integración y de API (dominio, autorización, estados, transacciones, versionado, validaciones, tareas, decisiones y auditoría).
2. **PostgreSQL:** PostgreSQL con pgvector real en desarrollo y como servicio temporal en GitHub Actions para las pruebas de persistencia. Docker solo como herramienta auxiliar para esa base; el despliegue del prototipo en AWS no cambia. No se usa SQLite como sustituto.
3. **OCR e IA:** se usan los servicios reales (Amazon Textract, Claude Haiku 4.5 y Cohere Embed Multilingual v3 mediante Amazon Bedrock) en las pruebas que los requieran. Sin simuladores por ahora; se revisará si los costos lo justifican.
4. **EVD-01:** los cuatro recorridos se ejecutan contra la API real desplegada, con usuarios autenticados de prueba. Los valores extraídos **siempre se confirman o corrigen con los del oráculo** antes de ejecutar las reglas. Así, la cadena de evidencia (Sección 6.2) se verifica independientemente de la calidad de extracción (Sección 6.3.1).
5. **Interfaz:** Playwright para los recorridos críticos y el escenario de demostración, no para todas las pantallas.
6. **Integración continua:** GitHub Actions exclusivamente sin acceso a AWS: linting, análisis estático, unitarias, cobertura y PostgreSQL temporal con pgvector. Sin proveedor OIDC de GitHub, roles para Actions, credenciales AWS ni workflows de despliegue, aunque tengan disparador manual. Las campañas contra AWS (OCR, IA y EVD-01 desplegado) las inicia y supervisa un operador del equipo desde una sesión autorizada, con costos aprobados y evidencia; no se ejecutan desde CI. Se conserva la automatización de las aserciones exigida por EVD-01. Sustituye la estrategia OIDC anterior por DO-2026-10-21.
7. **Cobertura:** pytest-cov con objetivo mínimo del **85 %** (E75), con atención a la lógica crítica del dominio.
8. **Separación de datos:** las pruebas y la demo usan bases y almacenamiento separados (`pfi_tests` y `pfi_demo`); el mecanismo se define en RC-P10.

---

### RC-P10 — Infraestructura AWS, aislamiento y encendido/apagado

**Estado:** diseño aprobado (RC-P10-01 a RC-P10-12 y RC-P10-15). RC-P10-13 pendiente; RC-P10-14 suspendida por DO-2026-10-21 (sin automatización operativa). **La aprobación corresponde exclusivamente al diseño: ninguna verificación técnica se considera cumplida hasta ejecutarla.** No se implementa infraestructura todavía.

**Referencia de diseño:** informe principal de RC-P10 y su revisión complementaria (21/10/2026).

**Decisiones aprobadas:**

| ID | Decisión |
|---|---|
| **RC-P10-01** | Una cuenta AWS, región principal us-east-1, con los entornos demo y pruebas separados lógicamente. |
| **RC-P10-02** | Una VPC y una instancia RDS PostgreSQL Multi-AZ (primaria y reserva) compartidas. Sin NAT Gateway, como establece la tesis. |
| **RC-P10-03** | Bases `pfi_demo` y `pfi_tests` con usuarios separados (aplicación y migraciones por entorno), privilegios SQL mínimos, permisos por defecto revocados y conexiones cruzadas denegadas. |
| **RC-P10-04** | Un RDS Proxy compartido con autenticación IAM de extremo a extremo. Los identificadores del proxy (`prx-…`) y de la instancia (`db-…`) se obtienen dinámicamente de AWS; nunca se escriben a mano. Cada recreación del proxy obliga a reaplicar los estados de demo y pruebas y a superar las pruebas de conectividad y aislamiento antes de habilitar operaciones. Secrets Manager para la autenticación del proxy queda solo como alternativa ante una incompatibilidad comprobada. |
| **RC-P10-05** | Lambda, API Gateway, Step Functions, EventBridge Scheduler y Cognito (dos User Pools) separados por entorno. El mismo código, desplegado dos veces con identidades, configuración y datos propios. La separación se establece por despliegue y configuración del servidor, nunca por un parámetro de la petición, incluida la cadena asíncrona. |
| **RC-P10-06** | Buckets documentales separados por entorno, sin permisos IAM cruzados. Las URLs prefirmadas solo apuntan al bucket del propio entorno. |
| **RC-P10-07** | Terraform con `bootstrap` (estado remoto) y cuatro estados operativos: `persistent`, `runtime`, `demo` y `tests`, con dependencias explícitas, grupos de seguridad estables en `persistent` y un orden obligatorio de aplicación y retirada. Estado remoto en S3 cifrado, versionado y con bloqueo nativo. |
| **RC-P10-08 (E90A)** | El operador humano crea una **demo descartable** por sesión y, tras drenaje, evidencia exportada y aprobación destructiva explícita, elimina RDS y los demás recursos **propios de la sesión**. No se usa RDS `stopped`, no se retienen snapshots entre sesiones y no se destruye `bootstrap` ni nada ajeno. Véase DO-2026-10-21-E90A. |
| **RC-P10-09 (E90A)** | Ciclo manual **crear → migrar → semilla sintética → pruebas → drenar → exportar evidencia → eliminar**. Modo mantenimiento independiente de PostgreSQL con estados `active`, `draining` y `offline` **durante cada sesión**; no prometer recuperación de pendientes tras destruir infraestructura. URLs prefirmadas de cinco minutos, con comprobación de transferencias en curso. |
| **RC-P10-10** | La reinicialización de `pfi_tests` es exclusivamente una operación técnica de administración, con una identidad limitada a los recursos de pruebas. La aplicación no expone operaciones para eliminar trámites, versiones ni eventos de auditoría (RNF-04, RN-10). |
| **RC-P10-11** | Ningún entorno admite despliegues automáticos ni desde GitHub Actions. El operador autorizado ejecuta manualmente el plan aprobado, con versión y artefactos identificables, impacto y costo revisados. Demo congelada antes de la defensa; un push o merge no despliega. |
| **RC-P10-12** | Backups automáticos de RDS (retención inicial propuesta de siete días), versionado de S3 y verificación de integridad entre PostgreSQL y S3 tras una recuperación. |
| **RC-P10-15** | Inicialización de PostgreSQL (bases, usuarios, esquemas, extensión pgvector y privilegios) mediante una Lambda privada con acceso directo a RDS. Migraciones con Alembic, ejecutadas por funciones privadas con autenticación IAM y usuarios separados por entorno. Solo el operador autorizado invoca manualmente las funciones privadas de inicialización y migración; ningún runner de GitHub Actions tiene acceso a AWS ni acceso SQL a RDS. |

**Precisiones registradas:**

1. **Credencial maestra:** la credencial maestra administrada mediante Secrets Manager se utiliza exclusivamente para la inicialización y la administración privilegiada. No sustituye la autenticación IAM de extremo a extremo de las aplicaciones.
2. **Frecuencia de recreación:** el procedimiento de encendido y apagado contempla la facturación mínima de RDS Proxy y las fracciones horarias de los endpoints de interfaz, para evitar recreaciones demasiado frecuentes.
3. **Configuración de mantenimiento:** el objeto de control de mantenimiento almacenado en S3 queda protegido y excluido de las operaciones de reinicialización de `pfi_tests`.
4. **Etapas de implementación:** antes del primer despliegue facturable: cotización, presupuesto aceptado, inventario previsto y apagado preparado. Se adelantan mantenimiento, drenaje, recuperación y operación manual a 1.0/1.1, antes de habilitar cargas y demo. El primer ciclo controlado verifica persistencia, aislamiento, apagado y costos residuales; la Etapa 3 amplía las pruebas. No se autoriza automatizar encendido/apagado. Ver el plan actualizado y DO-2026-10-21.
5. **Dependencia con RC-P09 (resuelta):** la región y el modo de invocación de Bedrock quedan definidos en RC-P09, conforme a la Sección 5.4.3 de la tesis.

**Criterios obligatorios de implementación (pendientes de ejecución):**

| ID | Verificación |
|---|---|
| **A** | Aislamiento efectivo: usuarios, funciones, roles IAM y procesos asíncronos de pruebas no pueden consultar, modificar ni eliminar recursos de demo, comprobado con pruebas negativas reales. |
| **B/B-E90** | Criterio B original **no acreditable con modalidad A**; B-E90 verifica versiones, historial, validaciones y auditoría persistidos y recuperables por API **durante una misma sesión**. Si la tesis exige durabilidad tras apagar, registrar limitación y planificar prueba separada. |
| **C** | Recuperación idempotente de trabajos dentro de la sesión, no entre sesiones destruidas. |
| **D** | Reinicialización segura de `pfi_tests` sin alterar entidades, versiones, auditoría ni documentos de demo. |
| **E** | Tras retiro manual deben desaparecer RDS, proxy, endpoints y recursos de la sesión; comprobar costos residuales y ausencia de recursos huérfanos. |
| **F** | Protocolo de defensa: encendido con margen suficiente, despliegues de demo congelados y prueba de humo del recorrido completo del contrato antes de la defensa. |
| **V-RP** | Recreación del proxy: nuevo identificador, políticas y configuraciones actualizadas, conexión desde demo y pruebas sin permisos cruzados. |
| **V-DB** | Inicialización y migraciones: creación de bases, usuarios, esquemas y pgvector desde una ejecución autorizada dentro de la VPC, y migración independiente de ambos entornos. |
| **V-MT** | Mantenimiento y drenaje: bloqueo de nuevas operaciones sin consultar PostgreSQL, gestión de cargas prefirmadas pendientes y trabajos conservados sin pérdidas ni duplicaciones. |
| **V-TF** | Recreación de la demo y repoblado de escenario nuevo, tras eliminación selectiva de las raíces de sesión, conservando solo `bootstrap`; no recuperación de la misma evidencia. |
| **V-CO** | Control económico: recursos activos e inactivos verificados, créditos de CPU registrados y cotización oficial antes de cerrar RC-P10-13. |
| **IAM** | Conectividad IAM: las funciones de cada entorno conectan con su usuario y su base, y se les deniega el usuario y la base del otro entorno. |


### DO-2026-10-21-E90A — Modalidad A: demo AWS descartable y repoblable (decisión posterior del equipo)

**Fecha:** 21/10/2026. **Alcance:** operación de la demo de ATLAS para el hito E90. **Estado:** decisión operativa acordada, implementación y pruebas **pendientes**. **Prevalece sobre la operación por detención de RDS de RC-P10-08/09 y DO-2026-10-21 exclusivamente para el ciclo de vida de la demo E90.** No sustituye RF, RN, RNF ni la evaluación académica.

- El equipo elige la **modalidad A, descartable**. Cada sesión comienza con una infraestructura AWS de demo creada manualmente desde Terraform, base PostgreSQL nueva, migraciones y **semilla sintética determinista**. El equipo prueba y documenta los recorridos, y al finalizar **retira completamente los recursos del entorno de demo**, incluida RDS PostgreSQL Multi-AZ, en vez de dejarla en `stopped` o restaurarla mediante snapshots entre sesiones.
- **No se conservan datos, documentos, usuarios ni historial de la demo entre sesiones**. No se permiten documentos reales. La persistencia del trámite, las versiones, decisiones y auditoría **dentro de una sesión activa** sigue siendo obligatoria y comprobable por API con el contrato de aceptación y oráculo. El script de semilla crea un escenario nuevo en cada despliegue; no restaura datos anteriores ni constituye una prueba de durabilidad entre despliegues.
- Se conserva solamente una base **administrativa mínima y protegida fuera del entorno descartable**: cuenta y organización, Budgets, configuración de privacidad, backend remoto de Terraform y los archivos locales del repositorio/corpus y evidencias saneadas. **No eliminar** esa base para “apagar todo”. El resto de infraestructura AWS propiedad de la demo es efímero (incluidos RDS, proxy, endpoints, API, Lambdas, Cognito, buckets de demo, logs de demo, CloudFront y recursos auxiliares si fueron creados para esa sesión). Evitar activos compartidos entre demo y tests al retirar la sesión; por ahora desplegar solo demo.
- Terraform puede conservar las raíces históricas `bootstrap`, `persistent`, `runtime`, `demo` y `tests` para minimizar cambios de diseño, **pero el nombre `persistent` ya no significa persistencia entre sesiones E90**: todos los recursos de esa raíz que pertenezcan exclusivamente a la demo son descartables, **excepto el backend y controles de `bootstrap`**. Antes de implementar se verifican dependencias y se evalúa renombrar raíces para evitar ambigüedad; no cambiar estados Terraform remotamente a ciegas.
- **No ejecutar `terraform destroy` global o indiscriminado.** El operador humano, después de inventario y aprobación de planes, retira las raíces de sesión por orden inverso de dependencias (`demo → runtime → persistent`), sin tocar `bootstrap` ni recursos ajenos. Las políticas `prevent_destroy`/`deletion_protection` deben proteger contra errores y requerir un paso manual autorizado y reversible en la configuración antes de retirar únicamente lo efímero; nunca desactivar protecciones globalmente o usar `state rm` para saltarse el control. Un plan destructivo distinto exige nueva aprobación.
- Al borrar RDS **no se crea snapshot final ni se retienen backups** de la demo descartable, una vez verificado que no se requiere conservar ningún dato de la sesión y que la evidencia de evaluación ya fue exportada y saneada fuera de AWS. Es **irreversible**. Los snapshots manuales antiguos pueden persistir y facturar y requieren inventario y decisión explícita de eliminación; secretos con ventana de eliminación, logs, versiones S3 y servicios de control pueden conservar cargos temporales. AWS puede tardar en eliminar recursos; el cierre requiere verificación por servicio, no solo estado de Terraform.
- La semilla (`seed`) se ejecuta **manualmente y una sola vez por despliegue lógico**, tras migraciones y configuración de usuarios/roles. Debe ser versionada, determinista en el escenario esperado, reproducible y validada por API contra el oráculo aprobado. Carga PDF/DOCX sintéticos desde `corpus/`, crea identidades ficticias y relaciones de negocio mediante las interfaces autorizadas, sin insertar auditoría ficticia directamente en tablas. Evitar llamar Bedrock/Textract de manera inesperada: los pasos reales de IA se ejecutan con presupuesto y confirmación humana dentro de la sesión.
- El apagado sigue siendo ordenado: impedir nuevas operaciones, drenar/terminar trabajos críticos de Step Functions y Textract, gestionar URLs prefirmadas, exportar evidencias de pruebas, quitar recursos **solo de la sesión autorizada**, verificar ausencia de residuos facturables y registrar costos. No se promete recuperación de trabajos pendientes de una sesión destruida. Si quedan trabajos indeterminados no se destruye hasta resolver su efecto/costo.
- **Cambios en criterios RC-P10 propios:** B (persistencia a través del apagado) deja de ser demostrable con esta modalidad y se sustituye para E90 por B-E90 (persistencia/auditoría durante la sesión); C aplica a interrupciones/reintentos **durante** la sesión; E comprueba eliminación de recursos de sesión, no RDS `stopped`; V-TF cubre recreación desde cero y seed, no conservación de identidades ni datos. **No declarar cumplidos los criterios originales B/V-TF por el nuevo ciclo**. Si la tesis o el jurado exigen durabilidad tras apagado de infraestructura, registrar limitación y planificar una prueba separada con respaldo/restauración para el 100 %.
- No OIDC, no despliegues en GitHub Actions, no agentes operando AWS. Presupuesto aceptado y cotización actualizada para *crear + inicializar + usar + drenar + destruir* la sesión, incluidos cargos residuales. La planilla RC-P10-13 basada en RDS detenido y almacenamiento persistente es **histórica/no válida como total de la modalidad A**; recalcular con duración real de cada recurso y mínimo de facturación.

**Arquitectura funcional preservada:** RDS Multi-AZ, RDS Proxy, IAM, aislamiento, API, Step Functions, Textract y Bedrock siguen siendo reales durante una sesión desplegada. Cambia la política de retención/operación entre sesiones, no se simula la implementación ni se alteran RF/RN/RNF.

**Fuentes oficiales de control:** [RDS DeleteDBInstance](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DeleteDBInstance.html); [backups retenidos](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.Retaining.html); [versiones de objetos S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html). La posibilidad de eliminar sin snapshot no significa que desaparezcan automáticamente snapshots anteriores, versiones S3 o cargos ya incurridos.

**Aplicación documental:** `docs/diseno/RC-P10_Diseno_Infraestructura.md`, `docs/plan/Plan_Implementacion_por_Etapas.md`, `operaciones/aws/README_OPERACION_MANUAL.md`, `docs/operacion/Politica_Costos_AWS.md`, `docs/operacion/Seed_Demo_E90_Especificacion.md` y `AGENTS.md`.

### DO-2026-10-21 — Operaciones AWS manuales y control previo de costos (antecedente operativo)

**Actualización posterior:** DO-2026-10-21-E90A reemplaza **solo** la detención/reutilización de RDS y la permanencia de recursos `persistent` de la demo E90. Las reglas de operación manual, no OIDC, presupuesto y prohibición de destruir `bootstrap` siguen vigentes. Las frases de este antecedente sobre no destruir nunca `persistent`, preservar datos entre sesiones o reinicio a siete días no son instrucciones vigentes para E90A.

**Origen y fecha:** decisión expresa del equipo, 21/10/2026, solicitada en esta tarea. **Justificación:** minimizar costos inesperados y mantener control humano de las operaciones AWS. No es una decisión delegada al agente.

- No se configura GitHub OIDC ni roles IAM para GitHub Actions, ni credenciales AWS en GitHub. Ningún workflow, push, merge, agente ni automatización crea, modifica, despliega, inicia, detiene o elimina infraestructura, ejecuta migraciones remotas o invocaciones operativas de AWS. El operador humano autorizado ejecuta cada operación tras aprobación expresa de su alcance y costos; aprobar un plan no delega su ejecución al agente.
- Terraform y sus estados `bootstrap`, `persistent`, `runtime`, `demo`, `tests` permanecen; igual las dependencias, aislamiento, cifrado, bloqueo remoto y protecciones persistentes. Preparar un plan local no implica aprobación. Se revisa el plan exacto antes de la ejecución manual; los cambios destructivos requieren autorización adicional y nunca se destruye `persistent` ni se hace un apagado con destrucción general.
- **RC-P10-13:** antes del primer recurso facturable se exige cotización oficial de `us-east-1`, costo por hora/sesión/mes con inactividad y residuales, inventario, responsable de apagado y presupuesto aceptado por el equipo. Las mediciones posteriores complementan la estimación, no la reemplazan como condición previa. No se supone que USD 20 cubra la arquitectura.
- ATLAS no permanece funcionando en AWS durante el desarrollo; se usa en sesiones controladas de pruebas, evaluación y defensa. Encendido, apagado, recuperación y control de RDS después de siete días son manuales, verificables y supervisados. RC-P10-14 queda suspendida, no como mejora automáticamente autorizada.
- CI conserva pruebas sin AWS. Las suites funcionales automatizadas y el procesamiento asíncrono de la tesis conservan su arquitectura y oráculos: se ejecutan dentro de sesiones aprobadas, sin facultad para administrar infraestructura. Prohibir también el procesamiento funcional automático contradiría §§5.3.1, 5.4.2 y 6.3.2; requeriría elevar un cambio académico al equipo. Esta decisión regula despliegue y administración, sin alterar RF/RN/RNF.

**Antecedentes sustituidos (solo históricos, no instrucciones vigentes):** RC-P02.6 preveía OIDC y roles para Actions; RC-P10 §2.5 permitía flujos de despliegue por entorno; RC-P10-15 preveía solicitar migraciones desde un runner con rol OIDC; Etapa 0.7 exigía crear esa confianza; RC-P10-14 difería automatizar la detención de RDS. La plantilla local `operaciones/aws/trust_demo_oidc_PLANTILLA.json` se retira sin aplicar. El plan anterior difería mantenimiento y apagado a Etapa 3; se adelantan como prerrequisitos, con verificación inicial antes de habilitar la demo.

**Contraste contractual:** no se encontró exigencia de GitHub OIDC o CD automático en la tesis vigente. OIDC/OAuth2 en la Figura 5.2 y Tabla 5.I corresponde a identidad de usuarios con Cognito y se conserva. Terraform declarativo sigue siendo compatible con su ejecución manual. No se modifica la tesis ni los contratos de aceptación.

**Procedimientos y registros:** `operaciones/aws/README_OPERACION_MANUAL.md` y `docs/operacion/Politica_Costos_AWS.md`. Diseño documentado, todavía sin implementación ni pruebas del ciclo AWS.

---

### RC-P03 — Roles, tareas y estados

**Base en la tesis:** matriz de permisos (Tabla 3.II), transiciones (Tabla 3.VI), RF-17 a RF-20 y RF-23. El acceso a un trámite se deriva de ser su responsable o de tener una tarea asignada en él.

**Estado:** cerrada.

**RC-P03.1 — Flujo de tareas (cerrada):**
1. Flujos **secuenciales** de una a tres tareas; sin tareas en paralelo.
2. **Plantillas de flujo** configuradas por el administrador operativo (por ejemplo, para un trámite con contrato: «revisión legal» y luego «aprobación final»), con un revisor/aprobador asignado por defecto en cada paso.
3. Al confirmar el flujo, las tareas se crean **ya asignadas** al revisor por defecto de cada paso, porque esa asignación proviene de la configuración del administrador. El administrador puede reasignar en cualquier momento y toda asignación queda registrada (RF-19).
4. La sugerencia del flujo (RF-17) elige la plantilla según los tipos documentales del trámite: con contrato, la plantilla de contratos; si no, una plantilla general. El responsable la confirma antes de que se active.

**RC-P03.2 — Autorización de cierre (cerrada):**
1. Es un **permiso adicional de la cuenta**, otorgado o retirado por el administrador operativo, como la habilitación de roles (RF-25). Cada cambio se registra como evento de auditoría.
2. Para firmar un trámite concreto, la persona debe tener además **acceso a ese trámite**: haber tenido una tarea asignada en el ciclo de revisión aprobado.
3. El firmante **elige la versión** a firmar entre las versiones vigentes incluidas en el ciclo aprobado (en la demo, el contrato).
4. **Una sola firma** deja el trámite en estado Cerrado (RF-23); después no se admiten versiones nuevas ni otras operaciones (RN-15).
5. En las plantillas, el revisor por defecto del paso de aprobación final es una persona con autorización de cierre.

**RC-P03.3 — Separación de funciones (cerrada):**
1. Una tarea de un trámite **no puede asignarse a su responsable**, ni por la asignación por defecto de la plantilla ni por una reasignación manual.
2. Si al confirmar el flujo el revisor por defecto de un paso es el propio responsable, esa tarea se crea **sin asignar** y queda señalada al administrador operativo para su asignación; el resto del flujo no se bloquea.
3. Una persona puede reunir ambos roles y ser responsable de unos trámites y revisora de otros.

**Estado de RC-P03:** cerrada completa (RC-P03.1, RC-P03.2 y RC-P03.3).

---

### RC-P09 — Tratamiento documental y controles de los servicios de IA

**Base en la tesis:** Sección 5.4.3, RNF-03, RNF-09, Sección 6.3.1 y Sección 2.1.3 (Ley N.º 25.326). La tesis ya establece que el contenido documental solo se envía a Amazon Textract y Amazon Bedrock, invocados desde us-east-1, en modalidad bajo demanda; que Claude Haiku 4.5 se invoca mediante un perfil de inferencia geográfico de Estados Unidos (sin perfiles globales); y que la configuración se documenta y comprueba antes de procesar documentación real.

**Estado:** cerrada. Resuelve además la dependencia de RC-P10 sobre la región de Bedrock.

**Decisiones:**

1. **Exclusión del uso de contenido por servicios de IA:** la cuenta AWS se incorpora a una organización de AWS Organizations (aunque sea la única cuenta) para aplicar la política de exclusión que cubre a Amazon Textract. La política efectiva se registra antes de procesar documentos. La exclusión no impide el procesamiento ni el almacenamiento temporal propios del servicio.
2. **Registro de invocaciones de Bedrock desactivado,** verificando su estado real en la cuenta y no solo el valor predeterminado. Se verifica la retención aplicable a cada modelo y modalidad utilizados, sin generalizar que todos los modelos de Bedrock tienen retención cero.
3. **Documentos utilizados (actualización DO-2026-10-21-E90-CORPUS):**
   - **La evaluación cuantitativa §6.3.1 usa únicamente documentos sintéticos:** 50 de medición (3 adversariales incluidos) y 10–15 de ajuste separados, sin lote de contraste público/empresarial. Los oráculos y umbrales continúan vigentes.
   - **La demo descartable AWS E90A y las pruebas EVD-01** utilizan solo corpus sintético PD-07. Se admite adaptar plantillas públicas autorizadas con datos ficticios; no incorporar documentos auténticos a la demo.
   - **La validación funcional en entorno operativo real §6.4 es distinta** y puede utilizar documentación propia de ese entorno en un procedimiento autorizado a cargo del equipo. Se evalúan específicamente permisos, confidencialidad, protección de datos y transferencias/retención según destinos RNF-03/RC-P09. No se cargan documentos auténticos, aunque estén anonimizados, a este repositorio, agente, GitHub, CI ni demo AWS E90A.
   - Los originales y datos de identificación del entorno **no se divulgan**; solamente se documentan resultados y evidencias no confidenciales aprobados. No se extrapolan métricas sintéticas al escenario real ni se afirma ejecución sin evidencia.
   - La autorización para utilizar documentos operativos y para procesarlos en servicios externos **son cuestiones distintas**: no inferir una de la otra; si el destino AWS requiere decisiones específicas, obtenerlas antes de ejecutar.
4. **Registro de destinos y retención (RNF-03):** archivo versionado en el repositorio que documenta cada destino que almacena o procesa información (S3, RDS, Textract, Bedrock y servicios de ejecución y observabilidad), indicando cuáles pueden contener documentos o fragmentos y cuáles solo metadatos técnicos, con región o perfil, finalidad, retención, controles de exclusión y evidencia de verificación.
5. **Modelos de Bedrock:** antes de usarlos, se comprueba la disponibilidad e invocación efectiva de Claude Haiku 4.5, Claude Sonnet 4.6, Cohere Embed Multilingual v3 y Amazon Titan Text Embeddings V2, incluidos permisos, acuerdos o pasos de primer uso requeridos por el proveedor y perfiles de inferencia. Los destinos de cada perfil geográfico se validan mediante la API (`GetInferenceProfile`), no por el prefijo del identificador.

---

### RC-P08 — Fallos, reintentos y concurrencia en el procesamiento asíncrono

**Base en la tesis:** Secciones 5.3.1 y 5.4.4, RNF-06. La tesis ya define la confirmación de carga y del trabajo en una transacción, la coordinación con Step Functions Standard, el reconciliador programado, el nombre de ejecución derivado del trabajo y su número de intento, la unicidad de un trabajo por archivo, los reintentos acotados con esperas crecientes, el estado de fallo técnico sin afectar el estado funcional del trámite, la continuidad manual ante fallos de los servicios de IA y la exclusión del contenido documental de los registros.

**Estado:** cerrada a nivel de diseño. Las verificaciones de concurrencia, recuperación e idempotencia quedan pendientes para la implementación. Todos los valores son **parámetros iniciales configurables**, no resultados experimentales ni garantías de rendimiento.

**Decisiones:**

1. **Reintentos automáticos:** hasta tres reintentos por operación ante errores transitorios (hasta cuatro invocaciones en total), con intervalos base de 2, 4 y 8 segundos y jitter, mediante el mecanismo de reintento de Step Functions. Se aplican por operación técnica, sin repetir etapas ya completadas. Los errores permanentes no se reintentan y pasan a fallo técnico.
2. **Textract:** se mantiene el mecanismo de consultas periódicas de la tesis, con un intervalo configurable de 10 a 15 segundos y tratamiento del throttling. Límite configurable de **30 minutos** para el procesamiento completo de un trabajo, ajustable según mediciones por etapa. No se incorporan SNS ni SQS en esta fase.
3. **Reconciliador:** se ejecuta cada cinco minutos. Para recuperar inicios fallidos o inciertos examina trabajos con más de dos minutos sin inicio confirmado y verifica el identificador y el estado real de la ejecución antes de iniciarla o recuperarla, para no crear una segunda ejecución si la solicitud anterior fue aceptada. Se deshabilita durante el apagado (RC-P10) y se reactiva de forma controlada.
4. **Intentos nuevos solo manuales:** tras un fallo definitivo, el responsable del trámite inicia explícitamente un nuevo intento (RNF-06). Se distinguen tres conceptos: el reintento automático repite una operación transitoria dentro del mismo intento; la reconciliación recupera el inicio del mismo intento; el intento nuevo es una acción explícita del responsable.
5. **Concurrencia:** límites iniciales configurables de **cinco trabajos simultáneos en pruebas y diez en demo**, aplicados a trabajos completos (no solo a la concurrencia de Lambda) y revisados contra las cuotas de Textract y Bedrock y la capacidad de RDS.
6. **Resultados obsoletos:** la persistencia verifica **dentro de la misma transacción** que el número de intento recibido coincide con el intento vigente y que el trabajo admite la transición. Los resultados de intentos anteriores no modifican resultados aplicables, datos, versiones ni estados; su descarte se registra como evento técnico, sin contenido documental.
7. **Idempotencia en Textract:** el inicio del análisis usa una clave estable por trabajo e intento (`ClientRequestToken`) para no duplicar análisis ante respuestas inciertas. Los resultados intermedios de cada intento se guardan en claves S3 separadas por trabajo e intento.

**Estado técnico «En espera» y admisión de trabajos:**

8. Cuando se alcanza el límite de concurrencia, el trabajo queda registrado como **«En espera»**, sin fallar ni impedir la carga del archivo. Es un estado del procesamiento técnico y no modifica el estado funcional del trámite.
9. La admisión de trabajos se controla **transaccionalmente en PostgreSQL**, respetando los límites configurables, evitando sobreasignaciones ante concurrencia y permitiendo recuperar los cupos de ejecuciones fallidas o interrumpidas.
10. El reconciliador también admite trabajos en espera cuando hay capacidad, respetando preferentemente su antigüedad, y diferencia estos trabajos de los que requieren reconciliar un inicio fallido o incierto de Step Functions.
11. La admisión automática de un trabajo en espera **no constituye un nuevo intento manual**. Los intentos nuevos tras un fallo definitivo siguen requiriendo una acción explícita del responsable.
12. Durante el mantenimiento definido en RC-P10 no se admiten trabajos nuevos. Al volver a activar el entorno, los pendientes se recuperan de manera controlada.
13. La interfaz muestra claramente los estados técnicos y **no presenta la espera por capacidad como un error**.

**Verificaciones pendientes para la implementación:** admisión sin sobreasignación ante cargas simultáneas; recuperación de cupos tras fallos o interrupciones; reconciliación sin ejecuciones duplicadas; descarte de resultados de intentos obsoletos; idempotencia del inicio de Textract; comportamiento de «En espera» y reanudación tras el mantenimiento. Estas pruebas alimentan la Sección 6.3.2.

---

### PD-07 — Documentos y oráculo de EVD-01 y de la demostración

**Base en la tesis:** Sección 6.2 (EVD-01, criterios V1–V11), RN-06, RN-12, RN-13; decisiones PD-01, RC-P02, RC-P04, RC-P09 y RC-P10.

**Estado:** cerrada a nivel de diseño. La generación material de los documentos, la elección y comprobación del CUIT, la fijación de hashes y localizadores y la ejecución de las pruebas quedan pendientes para la implementación.

**Decisiones:**

1. **Corpus de cinco documentos sintéticos:**

| Documento | Contenido clave |
|---|---|
| Contrato C-v1 | Prestación de servicios de mantenimiento; contraparte ficticia («Servicios Integrales del Sur S.A.»); vigencia del 01/03/2026 al 28/02/2027; de 8 a 12 páginas con cláusulas de objeto, plazo, precio, forma de pago, confidencialidad y rescisión |
| Orden de compra O-v1 | Mismo proveedor y CUIT; fecha de emisión 15/03/2027 (fuera de la vigencia); $ 1.250.000 |
| Orden de compra O-v2 | Versión corregida; fecha de emisión 15/09/2026 (dentro de la vigencia); $ 1.250.000 |
| Factura F-v1 | Mismo proveedor; $ 1.312.500 |
| Factura F-v2 | Versión corregida; $ 1.250.000 |

   Resultados esperados de las reglas:

| Conjunto | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| C-v1 + O-v1 + F-v2 | Cumple | Cumple | **Advertencia** | Cumple |
| C-v1 + O-v2 + F-v1 | Cumple | Cumple | Cumple | **Advertencia** |
| C-v1 + O-v2 + F-v2 | Cumple | Cumple | Cumple | Cumple |

2. **Formalización de R1–R4** con sus condiciones exactas, campos comparados y resultados esperados. R3 compara la fecha de emisión de la orden con el intervalo de vigencia del contrato, **incluidos sus extremos**. R4 compara importes totales en ARS sobre la misma base impositiva.
3. **EVD-B** sigue el recorrido de la demo: C-v1 + O-v1 + F-v2 → advertencia de vigencia (R3) → observación del revisor con motivo → incorporación de O-v2 → nuevo ciclo → aprobación → cierre con firma simulada.
4. **EVD-A** comienza con C-v1 + O-v2 + F-v1: la advertencia de importe (R4) no bloquea la aprobación humana. La incorporación posterior de F-v2, antes del cierre, obliga a un nuevo ciclo y una nueva decisión, conservando la anterior como historial.
5. **EVD-C** verifica la corrección de un valor validado sin modificar el contenido documental ni crear una versión nueva, registrando la nueva validación, los controles correspondientes y la continuidad prevista por RN-13.
6. **EVD-N12** verifica que una tarea del ciclo anterior no admite decisiones después de confirmar una versión nueva que modifica el conjunto documental.
7. **El oráculo** se versiona antes de las ejecuciones e incluye: campos esperados y procedencia (página en PDF; localizador estructural en DOCX), vínculos, resultados de reglas, versiones de cada ciclo, tareas y decisiones de cada ciclo, valores sugeridos y validados, ejecuciones y entradas que sustentan cada advertencia, controles considerados por cada decisión (V4), registros históricos que deben conservarse, auditoría y la operación que debe rechazarse en EVD-N12. Las aserciones se ejecutan contra la API real y verifican información persistente recuperable, no solo respuestas HTTP.
8. **Construcción reproducible:** los documentos se generan desde fuentes reproducibles (plantillas DOCX exportadas a PDF digital) y sus versiones finales se identifican mediante hash. Los localizadores de página se fijan respecto del PDF generado y verificado. Las sugerencias reales de IA se confirman o corrigen según el oráculo antes de evaluar reglas y flujo (RC-P02).
9. **Mismo corpus, ejecuciones aisladas:** la demo y las pruebas usan el mismo corpus y oráculo versionados, con ejecuciones y persistencia separadas (RC-P10). Las pruebas automatizadas no pueden modificar los datos preparados para la defensa.
10. **No reemplaza la evaluación de 6.3.1:** este corpus es funcional (EVD-01 y demo). Se mantienen los documentos, casos especiales, preguntas y criterios de aceptación de la Sección 6.3.1.
11. **Datos ficticios:** identificadores fiscales, partes y operaciones ficticios. Pueden adaptarse plantillas contractuales públicas o facilitadas con autorización, eliminando información personal o confidencial.
12. **Importes e IVA:** O-v1 y O-v2, $ 1.250.000 IVA incluido; F-v1, $ 1.312.500 IVA incluido; F-v2, $ 1.250.000 IVA incluido. R4 compara estos totales en ARS y debe detectar una diferencia de $ 62.500 (5 %) exclusivamente en F-v1. Los documentos indican expresamente que los importes incluyen IVA y todo desglose impositivo es aritméticamente consistente.
13. **Identificador fiscal ficticio:** antes de generar el corpus definitivo se selecciona un CUIT sintético con estructura y dígito verificador correctos, se consulta en los servicios públicos de ARCA para descartar coincidencias conocidas y se documentan la fecha y el resultado. La ausencia de resultados no se interpreta como garantía absoluta de que el número no fue asignado. Todos los documentos se identifican como «DOCUMENTO FICTICIO — SIN VALIDEZ COMERCIAL NI FISCAL» y no reproducen códigos de autorización fiscal que puedan confundirse con comprobantes reales.

---

### PD-08 — Ejecuciones y variantes de EVD-01

**Base en la tesis:** Sección 6.2 (criterios V1–V11), RN-09, RN-12; decisiones PD-05, PD-07, RC-P02 y RC-P10.

**Estado:** cerrada a nivel de diseño. La generación de las pruebas, su ejecución efectiva y la evidencia de resultados quedan pendientes de implementación.

**Volumen por campaña:** 12 ejecuciones principales, 2 pruebas de orden forzado, 2 consultas negativas de acceso y 10 carreras concurrentes.

**Decisiones:**

1. **Tres ejecuciones independientes** de cada recorrido (EVD-A, EVD-B, EVD-C y EVD-N12): doce ejecuciones principales por campaña, con los documentos y el oráculo versionados de PD-07.
2. **Ejecuciones limpias:** cada ejecución usa datos aislados o un entorno de pruebas reinicializado mediante operaciones técnicas autorizadas. No se incorporan endpoints funcionales para eliminar trámites, versiones ni auditoría.
3. **Variante negativa de autorización (V10):** un revisor sin tarea ni acceso al trámite y un administrador operativo sin permiso de consulta documental intentan reconstruir la evidencia; ambas solicitudes se deniegan sin exponer información. Se verifica también el acceso positivo del actor autorizado.
4. **Prueba de concurrencia sobre EVD-N12:** diez repeticiones iniciales enfrentando la aprobación de una tarea con la confirmación de una versión nueva. El criterio **no** es que solo una operación se registre: si la aprobación se confirma primero, se conserva como decisión histórica antes de que la versión nueva invalide el ciclo; si la versión se confirma primero, la aprobación posterior se rechaza. En todos los casos el resultado equivale a una secuencia válida, sin aprobaciones aplicables sobre ciclos invalidados, sin decisiones duplicadas y sin pérdida de trazabilidad.
5. **Cobertura de V1 a V11:** V1–V4, V7 y V9 en EVD-A y EVD-B; V5 en todos los recorridos; V6 en EVD-A (aprobación con advertencia); V8 en EVD-A y EVD-B; V10 en la variante negativa; V11 en EVD-B (firma simulada). Se verifican expresamente la relación recuperable entre decisiones y controles considerados (V4), la no transferencia de aprobaciones entre ciclos, la autorización de consulta y el cierre.
6. **IA no determinista:** las ejecuciones verifican los valores validados y las relaciones del oráculo. Las salidas de IA no se convierten en aserciones textuales exactas; se corrigen mediante las operaciones humanas previstas. La precisión de los modelos se evalúa por separado en la Sección 6.3.1.
7. **Criterio de aceptación:** todas las ejecuciones y verificaciones obligatorias resultan satisfactorias, sin violaciones esenciales. Toda falla se documenta con su evidencia y causa; no se descartan ejecuciones fallidas ni se repiten selectivamente para mostrar solo resultados exitosos. Tras corregir una causa, se ejecuta una nueva campaña identificable.
8. **Cuándo se ejecuta una campaña:** antes de cada entrega académica relevante y después de cambios que afecten ciclos, versiones, tareas, decisiones, reglas, autorizaciones o los mecanismos de persistencia involucrados.
9. **Registro de cada campaña:** versión del software, configuración, oráculo, identificadores de correlación, resultados esperados y observados y evidencias recuperadas mediante la API autenticada.
10. **Cobertura determinista y concurrente de RN-12:**
    - **Dos pruebas con orden controlado,** con resultados esperados explícitos en el oráculo: (a) primero la versión nueva, que invalida las tareas del ciclo anterior, y la aprobación posterior se rechaza; (b) primero la aprobación, que se registra válidamente, y la versión nueva posterior la conserva como historial, invalida la continuidad del ciclo y exige uno nuevo.
    - **Diez carreras concurrentes reales** con datos independientes, cada una con resultado equivalente a una secuencia válida.
    - La verificación identifica los resultados efectivamente confirmados contrastando las respuestas de la API, los eventos de auditoría y las relaciones persistentes recuperadas; **no depende exclusivamente** del orden de timestamps ni de identificadores de eventos.

---

### RC-P06 — Protocolo de corpus y preguntas RAG (revisión E90)

**Estado vigente:** por DO-2026-10-21-E90-CORPUS se **retira la selección RC-P06.1 entre un contraste empresarial y otro público**. No existe un grupo de contraste adicional en la evaluación cuantitativa de 6.3.1. La documentación operativa de una organización no pasa a formar parte del dataset de medición y su uso tiene condiciones distintas (ver protocolo).

**Antecedente supersedido:** la versión anterior contemplaba una opción A de diez documentos empresariales anonimizados y una opción B de diez a quince públicos. Ambas opciones dejan de ser tareas vigentes para E90; no sustituirlas por otro conjunto de medición. Se conserva RC-P06.2 para las preguntas RAG y los criterios de evaluación sin cambios.

**RC-P06.2 — Oráculo de las 30 preguntas de consulta asistida (cerrada a nivel de diseño):**

La elaboración de las preguntas, la identificación de sus fuentes y las mediciones quedan pendientes de implementación.

1. Se mantienen las **30 preguntas** de la Sección 6.3.1: 24 con respuesta documental disponible y 6 sin evidencia suficiente.
2. **Distribución inicial:** 10 de localización directa de datos, 8 de comprensión de condiciones y cláusulas, 6 multidocumento dentro del mismo trámite y 6 sin respuesta suficiente. Se procura representar los cinco tipos documentales y los formatos de entrada relevantes. Las preguntas sin respuesta cubren información ausente, ambigüedad que impide responder y datos fuera del conjunto autorizado, y no pueden responderse legítimamente con conocimiento general del modelo.
3. **Formato del oráculo:** archivo estructurado y versionado (YAML o JSON), con un registro por pregunta: identificador estable (Q01–Q30), categoría, consulta exacta, contexto documental autorizado, resultado esperado, respuesta canónica, afirmaciones esperadas, referencias a documento, versión, fragmento y localizador, y motivo de insuficiencia cuando corresponda.
4. **Referencias:** la referencia principal es el fragmento verificable del documento original con su localizador. Para evaluar la recuperación se mapea a los chunks de la indexación congelada, sin convertir los identificadores internos de chunks en la única referencia.
5. **Congelamiento:** antes de congelar el oráculo, todos los documentos, versiones, respuestas y fuentes están completos y verificados. No se modifican para favorecer el resultado de una ejecución.
6. **Métricas y umbrales de la tesis:** Recall@5 ≥ 0,80 (sobre las 24 preguntas respondibles); respuestas correctas ≥ 80 % (mínimo 20 de 24); afirmaciones respaldadas por sus citas ≥ 90 %; abstenciones correctas ≥ 80 % (mínimo 5 de 6). MRR se informa sin umbral propio.
7. **Evaluación independiente:** ambos autores califican cada respuesta y comprueban el respaldo de las afirmaciones. Se conservan las evaluaciones individuales y el resultado acordado tras resolver discrepancias, sin sobrescribir las originales.
8. **Mismo oráculo para todas las comparaciones** de modelos y embeddings. Repeticiones, configuración experimental e instrumentación de tiempos se definen en RC-P07.
9. Las preguntas se aplican al **conjunto de medición**, no al grupo de ajuste. No se reformula el oráculo según los resultados de las pruebas.
10. **Rúbrica de evaluación de respuestas,** fijada antes de medir y basada en las afirmaciones esperadas:
    - **Correcta:** contiene todas las afirmaciones esperadas y ninguna falsa.
    - **Parcial:** contiene algunas afirmaciones esperadas, pero no todas, y ninguna falsa.
    - **Incorrecta:** contiene alguna afirmación falsa o ninguna de las esperadas.
    Las equivalencias semánticas se aceptan sin exigir coincidencia textual. **Las parciales no cuentan como correctas** para el umbral del 80 %. Las 6 preguntas sin respuesta se evalúan por separado: una abstención correcta reconoce la insuficiencia de evidencia sin inventar información ni usar fuentes no autorizadas. El respaldo de las afirmaciones por las citas se evalúa de forma independiente (umbral del 90 %).
11. **Formulación natural y revisión:** las preguntas se formulan como consultas plausibles de usuarios, sin copiar innecesariamente las frases exactas que contienen la respuesta; se admite el uso natural de términos como CUIT, factura, contrato, importe o vigencia. Antes de congelar el oráculo, el otro autor revisa las preguntas para detectar formulaciones artificiales, coincidencias textuales innecesarias o pistas que faciliten indebidamente la recuperación. Una vez congeladas, no se reformulan selectivamente según los resultados.

---

### RC-P07 — Comparación de modelos y embeddings

**Base en la tesis:** Secciones 5.4.1 y 6.3.1. Haiku 4.5 se compara con Sonnet 4.6 con los mismos documentos, instrucciones, esquemas, fragmentos recuperados y criterios. Cohere Embed Multilingual v3 se compara con Amazon Titan Text Embeddings V2 con los mismos fragmentos, consultas y restricciones. Latencia de la consulta asistida: mediana ≤ 5 s y percentil 95 ≤ 10 s, desde la recepción de la solicitud hasta la entrega de la respuesta.

**Estado:** cerrada a nivel de diseño. Quedan pendientes la implementación, las verificaciones de servicios y las mediciones experimentales.

**Decisiones:**

1. **Repeticiones y métricas:** tres repeticiones de clasificación, extracción y consulta asistida con los modelos generativos, con una configuración de muestreo mínima, fija y compatible con ambos modelos. Cada métrica se calcula sobre el conjunto completo en cada repetición; se registran los valores individuales, el promedio y la dispersión. Las reglas de sustitución se aplican sobre los promedios, nunca sobre la mejor repetición.
2. **Haiku frente a Sonnet:** mismos documentos, contenido OCR, instrucciones, esquemas de salida, fragmentos recuperados y criterios de evaluación. Misma región de origen (us-east-1), modalidad de inferencia geográfica de Estados Unidos y API compatible, verificando los perfiles efectivos (RC-P09). Ejecuciones intercaladas, **alternando el orden** Haiku/Sonnet.
3. **Embeddings:** misma segmentación documental, con fragmentos compatibles con las restricciones de ambos modelos; vectores de 1024 dimensiones, distancia coseno y búsqueda exacta (sin índice aproximado). Un conjunto de vectores por modelo. Se respetan los parámetros nativos: en Cohere, `search_document` para los fragmentos y `search_query` para las consultas; en Titan, la configuración equivalente, con 1024 dimensiones y normalización fijadas explícitamente. Mismos filtros de autorización, documentos candidatos y `k = 5`. Sin truncamiento silencioso. Una indexación congelada por modelo para la comparación principal.
4. **Latencia:** las 30 consultas, tres veces por modelo generativo (90 muestras por modelo). La medición principal comprende el tiempo completo desde la recepción en la API hasta la respuesta completa, **incluidos los arranques en frío**; no se excluyen selectivamente solicitudes lentas. Las comprobaciones iniciales de conectividad no se usan para descartar observaciones. Se informan por separado, cuando sea posible, inicialización, recuperación, generación y demás componentes, además de errores, throttling, timeouts y reintentos (que no se cuentan como respuestas exitosas).
5. **Costos y observabilidad:** se registran por operación el modelo y perfil, el identificador de ejecución, los tokens de entrada y salida (desde las respuestas de la API, sin habilitar el registro de invocaciones de Bedrock), las unidades de embeddings, las páginas y operaciones de Textract, la duración, los errores y los reintentos, sin contenido documental. Los costos se estiman con las tarifas vigentes a la fecha de medición y alimentan RC-P10-13. El OCR reutilizado en comparaciones no se cuenta dos veces.
6. **Reglas de sustitución (Sección 6.3.1):** Sonnet sustituye a Haiku solo si alcanza un criterio que Haiku incumple sin introducir nuevos incumplimientos, o si mejora el F1 macro de extracción en al menos **0,05 absolutos** (promedio no ponderado de los cinco tipos documentales), manteniendo los límites de latencia y calidad. Titan sustituye a Cohere solo si mejora el Recall@5 en al menos **0,05 absolutos** sin incumplir el mínimo de recuperación.
7. **Congelación y trazabilidad:** antes de medir se congelan corpus, oráculos, instrucciones, esquemas, segmentación y configuración experimental. Cada campaña tiene identificador propio, versiones de modelos, configuración, resultados individuales y métricas consolidadas. No se repiten campañas selectivamente para obtener una sustitución favorable. Los incumplimientos se informan sin modificar los umbrales de la tesis.

**Riesgo de implementación registrado — latencia por arranques en frío de AWS Lambda:**
- La medición principal conserva todas las latencias válidas, incluidos los arranques en frío, conforme al criterio de experiencia completa de la tesis. Con 90 observaciones, el percentil 95 depende aproximadamente de las cinco más lentas (según el método de cálculo); el incumplimiento solo ocurre si esas observaciones efectivamente superan los 10 segundos.
- Si la mediana o el percentil 95 incumplen sus umbrales, se informan los resultados sin excluir observaciones desfavorables.
- Las causas se identifican mediante instrumentación, distinguiendo cuando sea posible inicialización de Lambda, recuperación documental, invocación de Bedrock y procesamiento restante.
- Si los arranques en frío resultan relevantes, puede evaluarse la concurrencia aprovisionada de Lambda u otras optimizaciones compatibles con la arquitectura aprobada, frente a sus costos y a las causas reales de la latencia. Toda optimización con costo adicional se incorpora a RC-P10-13.
- Si se modifica la configuración después de una campaña, se realiza una nueva campaña identificable y se conservan ambos resultados para compararlos.

---

### DO-2026-10-22-BDD — Runner de aceptación BDD/Gherkin

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada.

1. Los escenarios de aceptación en Gherkin (Dado–Cuando–Entonces) se automatizan con **`pytest-bdd`**, integrado con pytest (RC-P02).
2. Playwright se conserva para las verificaciones de interfaz, en especial RNF-07.
3. Los escenarios EVD-01 siguen verificando sus invariantes mediante la **API autenticada y autorizada**. Un `.feature` no acredita cumplimiento: el escenario debe ejecutarse contra su oráculo y conservar la evidencia (AGENTS.md §7).
4. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-22-CARGAS — Vencimiento de cargas pendientes y limpieza en S3

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada para implementación local; su despliegue en AWS requiere aprobación aparte.

1. Una carga pendiente tiene **24 horas** desde su creación para confirmarse. Después se considera vencida y **no puede incorporarse** al trámite. El vencimiento lo comprueba la aplicación al operar, sin depender de la limpieza.
2. Las URL prefirmadas vencen a los **5 minutos**.
3. Los objetos vencidos se limpian de forma **segura e idempotente**, comprobando antes que no hayan sido confirmados.
4. Como respaldo, una regla de **S3 Lifecycle de 2 días** actúa sobre el **prefijo exclusivo de cargas temporales**. No se depende de ella para el vencimiento exacto.
5. Los documentos y versiones confirmados quedan fuera de esa eliminación: al incorporarse, el original se traslada a un prefijo definitivo y se verifica su huella.
6. El proceso contempla las **versiones residuales de S3** (versiones anteriores y marcadores de eliminación) y las **cargas multiparte incompletas**.
7. No modifica RF, RN, RNF ni criterios de aceptación, y no autoriza despliegues AWS adicionales.

**Implementación local:** ver `docs/decisiones/Decisiones_Delegadas.md` (DT-CARGA-01) y `docs/operacion/Registro_Destinos_y_Retencion.md`.

### DO-2026-10-22-PROC — Diseño y pruebas del procesamiento con Textract y Bedrock (hito 1.4)

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada; la ejecución contra AWS sigue sujeta a DO-2026-10-21 (sesión manual, costos aprobados).

1. **P1 — Alcance de RC-P02.3:** la CI admite respuestas fijas (construidas a mano y, más adelante, grabadas en sesiones reales con documentos sintéticos) **solo para probar la lógica propia**: normalización, armado de instrucciones, validación de respuestas, verificación de procedencia, normalización de valores y persistencia. La calidad de Textract y de los modelos se verifica únicamente con los servicios reales, en sesiones AWS autorizadas que ejecuta el equipo (pruebas `aws_real`), y en la evaluación de §6.3.
2. **P2 — Cliente:** `boto3` con la API **Converse** de Amazon Bedrock, uso de herramienta forzado con esquema JSON y validación de la respuesta en el backend. No se incorpora el SDK `anthropic`.
3. **P3 — Resultados intermedios:** el contenido normalizado y las respuestas de los servicios se guardan en S3 bajo `resultados/{trabajo}/{intento}/`. Se conservan mientras exista el archivo y se eliminan, con todas sus versiones, cuando la carga vence (DO-2026-10-22-CARGAS).
4. **P4 — Textract:** `StartDocumentAnalysis` con `TABLES` y `LAYOUT`. El costo por página se incorpora a RC-P10-13 antes de la primera sesión.
5. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-22-VAL — Validación humana de clasificación y campos (hito 1.5)

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** RF-09, RF-10, RF-12, RN-02, RN-03, RN-09, §5.3.3, Tabla 3.VI.

1. **P1:** se valida solo la **versión vigente** de cada documento. Las versiones anteriores conservan sus validaciones en el historial.
2. **P2:** se admite validar con el trámite en **Borrador** o **Pendiente de validación**. En **Observado** se admitirá junto con la transición de subsanación a Pendiente de validación (RN-13, hito 1.8). En Pendiente de aprobación, Aprobado, Cerrado y Cancelado se rechaza.
3. **P3:** los campos se validan **después de validar la clasificación**, y se presentan los del esquema del tipo validado (RF-10).
   - Si el tipo se corrige, las validaciones de campos que no pertenecen al nuevo esquema quedan en el historial sin ser aplicables.
   - Los campos del nuevo tipo sin sugerencia del mismo esquema se registran manualmente.
   - Volver a extraer con el tipo corregido queda para una decisión posterior.
4. **P4:** el valor validado se exige en formato canónico, porque alimenta las reglas R1 a R4: fecha `AAAA-MM-DD`, importe decimal con dos cifras, CUIT `##-########-#` y moneda ISO 4217 de tres letras. Un dígito verificador de CUIT inválido produce una **advertencia**, no un rechazo.
5. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-22-RAG — Consulta asistida con recuperación autorizada (hito 1.6)

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** RF-13, RN-04, §5.3.4, RC-P06.2, RC-P07.3.

1. **P1:** las consultas recuperan solo fragmentos de las **versiones vigentes** de documentos incorporados del trámite. El alcance lo determina el backend a partir de los permisos y no puede ampliarse desde el cliente. Las versiones históricas quedan para una decisión posterior.
2. **P2:** cada consulta se **conserva en la base** con la pregunta, la respuesta o la abstención, los fragmentos recuperados y citados, el modelo de generación, la versión de las instrucciones y el modelo de embeddings. Sin borrado. Nunca se escribe en los registros técnicos.
3. **P3:** la **abstención la decide el modelo**. El backend descarta las afirmaciones sin una cita válida a los fragmentos recuperados y, si no queda ninguna, la respuesta se convierte en abstención. **Sin umbral de similitud** hasta definirlo con el corpus de ajuste.
4. **P4:** los embeddings se generan en el **procesamiento**, en la etapa `Indexar` (§5.3.1).
5. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-22-REG — Vínculos documentales y reglas de consistencia (hito 1.7)

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** RF-14, RF-15, RF-16, RN-02, RN-05, RN-06, §5.3.5, PD-01, PD-02, PD-07.

1. **P1 — Tipo de vínculo:** indica qué lo justifica: `referencia` (un documento cita al otro; admite una fuente en el documento de origen) o `campos` (comparten datos validados). Las reglas dependen de los tipos documentales validados, no del tipo de vínculo.
2. **P2 — Eliminación:** baja lógica (`eliminado`). La fila, su justificación y las ejecuciones de reglas quedan en el historial; las ejecuciones dejan de mostrarse como vigentes.
3. **P3 — Sugerencias (RF-15):** deterministas y solo con valores validados: CUIT del emisor de la factura = CUIT del proveedor de la orden, o CUIT del proveedor de la orden = CUIT de la contraparte del contrato. Se generan al validar, quedan pendientes y sin efecto hasta su confirmación y se atribuyen al sistema. Un par que ya tuvo un vínculo, en cualquier estado, no se vuelve a sugerir.
4. **P4 — Ejecución síncrona:** en la misma transacción que crear o confirmar un vínculo o validar un dato. Se registra una ejecución nueva solo si cambiaron las versiones o validaciones de entrada; las anteriores no se modifican. La situación de «controles pendientes» de PD-02.3 no se presenta.
5. **P5 — Pertinencia:** cada regla se evalúa por vínculo confirmado cuyos documentos tienen tipos validados que corresponden a la regla, en cualquier dirección. Una regla sin vínculo pertinente se presenta como «no aplicable», calculado y no guardado (coherente con PD-02.4). R4 con monedas distintas registra una ejecución «no aplicable». Sin clasificación validada, la regla no se ejecuta hasta validarla.
6. **P6 — Evaluación:** versión vigente de cada documento y su validación vigente. Falta validar un campo necesario → falta de datos, con las entradas que existen y la explicación de lo que falta. R4 revisa primero la moneda (sin validar → falta de datos; distinta → no aplicable) y luego los importes (cumple si factura ≤ orden). R3 incluye los extremos de la vigencia. CUIT en formato canónico. La explicación es una plantilla con los valores, guardada solo en la base.
7. **P7 — Estados y permisos:** el responsable crea, confirma, rechaza y elimina vínculos con el trámite en Borrador o Pendiente de validación (Observado con RN-13, hito 1.8). Vínculos y controles se consultan en cualquier estado; el revisor con tarea asignada, en el hito 1.8. Las reglas nunca cambian el estado del trámite (RN-06).
8. No modifica RF, RN, RNF ni criterios de aceptación.

---

## 2. Decisiones en curso

Ninguna en este momento.

---

## 3. Decisiones pendientes

| ID | Tema |
|---|---|
| **RC-P06 (protocolo E90)** | Congelar los 50 sintéticos de medición y los 10–15 de ajuste con partición/plantillas independientes, tres casos adversariales internos, hashes y oráculos antes de medir |
| **RC-P10-13** | Dimensionamiento y presupuesto definitivo de AWS (clase `db.t4g.medium` como hipótesis inicial, créditos de CPU incluidos). Existe [investigación numérica preliminar](../operacion/RC-P10-13_Cotizacion_Preliminar_2026-10-21.md) con [modelo editable](../operacion/RC-P10-13_Modelo_Costos_2026-10-21.xlsx); **PENDIENTE** cotización oficial/export, aprobación económica, dimensionamiento y mediciones. El informe preliminar no modifica RC-P10 aprobado ni autoriza crear recursos. |
| **RC-P10-14** | Antecedente suspendido por DO-2026-10-21: automatización de detención prolongada de RDS no autorizada. DO-2026-10-21-E90A **suprime esa necesidad** en E90 porque RDS se elimina tras cada sesión; el control del reinicio a siete días corresponde solo a la modalidad histórica con RDS detenido. |

---

## 3 bis. Decisiones delegadas al agente de código

Estas decisiones son de implementación y se derivan directamente de la tesis y de las decisiones de este documento. Las toma el agente de código durante la construcción, bajo estas reglas:

| ID | Tema |
|---|---|
| **PD-04** | Detalles físicos del modelo de datos (tipos, fechas, índices y restricciones no detallados en la Figura 5.4) |
| **PD-06** | Formato de respuesta del endpoint de reconstrucción de evidencia (estructura definida en PD-03) |
| **RC-P01** | Rutas y esquemas del resto de la API (FastAPI genera la especificación OpenAPI a partir del código) |

**Reglas:**
1. No pueden contradecir la tesis (RF, RN, RNF, modelo de la Sección 5.2) ni las decisiones cerradas de este documento.
2. Cada decisión se documenta en el repositorio en el momento de tomarla (migraciones de Alembic para el modelo físico; la especificación OpenAPI generada para la API), con una breve justificación cuando no sea evidente.
3. Toda entidad y relación de la Figura 5.4 debe existir en el modelo físico; se pueden agregar columnas técnicas, pero no quitar ni renombrar conceptos de la tesis.
4. Los nombres de endpoints y campos se mantienen en un idioma consistente en todo el proyecto.
5. El equipo revisa estas decisiones antes de dar por terminado cada bloque de construcción.

---

## 4. Impactos pendientes en la tesis

Cambios a evaluar en lotes separados, sin modificar requisitos:

1. Mockup de la vista «Evidencia de la decisión» en la Sección 3.4 (PD-03).
2. Revisión de la Sección 5.5 para que coincida con lo implementado y con la demo.
3. Posible mención del catálogo de reglas R1–R4 y de la moneda como campo validado en la Sección 5.3.5 (PD-01, RC-P04).
4. Posible aclaración en las Secciones 5.4.2 y 5.4.3 de que la credencial maestra administrada mediante Secrets Manager se usa solo para inicialización y administración privilegiada, mientras que las aplicaciones usan autenticación IAM de extremo a extremo (RC-P10).
5. Incorporar la restricción de separación de funciones (una tarea no puede asignarse al responsable del mismo trámite) como aclaración junto a la Tabla 3.II (RC-P03.3).
6. Aplicar a la fuente académica, por parte de sus autores, DO-2026-10-21-E90-CORPUS: retirar los 16 casos adicionales y el conjunto público, mantener 50 sintéticos (3 adversariales internos), ajuste independiente, 30 preguntas y límites metodológicos. **No atribuir resultados no ejecutados.**
7. Si se usan plantillas privadas de empresas para el corpus sintético, ampliar la frase de 6.3.1 que indica que los contratos se elaboran «a partir de modelos contractuales públicos adaptados».
8. Revisar `docs/tesis/Registro_Diferencias_con_la_Tesis.md`: diferencias de la implementación (modelo de datos, arquitectura, entornos local y AWS, restricciones y pendientes) a evaluar para la tesis, con su decisión de respaldo y una acción sugerida.
