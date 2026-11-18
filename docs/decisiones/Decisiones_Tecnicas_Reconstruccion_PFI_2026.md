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

### DO-2026-10-22-TAR — Tareas, decisiones y evidencia de la decisión (hito 1.8)

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** RF-17 a RF-22, RN-07, RN-08, RN-09, RN-12, RN-13, Tabla 3.VI, Figura 5.4, PD-02, PD-03, PD-05, RC-P03.

1. **P1 — Plantillas de flujo:** las da de alta el administrador operativo por API. Son inmutables y versionadas, tienen de uno a tres pasos con revisor por defecto y se aplican a `contrato` o `general`, con a lo sumo una activa por alcance. Se desactivan, nunca se borran. El revisor por defecto del último paso debe tener autorización de cierre (RC-P03.2.5).
2. **P2 — Sugerencia (RF-17):** se calcula al consultarla y no se guarda. Plantilla de contratos si algún documento vigente tiene la clasificación validada como contrato; si no, la general. Hasta la confirmación no existe ninguna tarea. La confirmación envía la plantilla y su versión; si ya no es la sugerida, 409.
3. **P3 — Enviar a validación:** Borrador → Pendiente de validación por el responsable, con al menos un documento incorporado (Tabla 3.VI). Sin otras condiciones.
4. **P4 — Confirmar datos y flujo:** Pendiente de validación → Pendiente de aprobación. Exige la clasificación y todos los campos del esquema del tipo (RC-P04) validados en cada documento vigente. En una transacción crea el ciclo n+1 con las versiones vigentes y todas sus tareas, ya asignadas al revisor por defecto: la primera `pendiente` y las demás `en_espera`. Si el revisor por defecto es el responsable, la tarea queda sin asignar y señalada al administrador (RC-P03.3).
5. **P5 — Decisión (RF-20, RN-08):** solo el asignado, con rol de revisor/aprobador y cuenta habilitada; el administrador nunca. Tarea `pendiente`, ciclo `en_curso`, trámite en Pendiente de aprobación y bloqueado (PD-05.2). La observación exige motivo; en la aprobación es opcional. Aprobar una tarea intermedia habilita la siguiente; aprobar la última deja ciclo y trámite en Aprobado; observar deja ciclo y trámite en Observado y las tareas en espera, `descartada`. Sobre una tarea anulada responde el mensaje de PD-05.3 y no registra nada.
6. **P6 — `DECISION_CONTROL` (PD-02):** guarda los identificadores de las ejecuciones vigentes cuyas versiones pertenecen todas al ciclo, que son las que muestra la vista de la tarea (una sola función alimenta ambas). En Pendiente de aprobación no se valida ni se vincula, por lo que los controles no cambian durante el ciclo.
7. **P7 — Asignación (RF-19):** un endpoint del administrador asigna o reasigna; exige el rol requerido habilitado y que la persona no sea el responsable. Cada cambio se guarda en la tabla técnica `asignacion_tarea` (anterior, nueva, quién y cuándo) y como evento de auditoría. El administrador lista las tareas sin asignar con metadatos solamente (RF-24).
8. **P8 — Acceso del revisor:** se deriva de tener una tarea asignada en el trámite. Es de solo lectura y se limita a las versiones de los ciclos de esas tareas: documentos, validaciones, vínculos, controles y consulta asistida (versiones vigentes ∩ versiones de sus ciclos). Si se reasigna la tarea, el acceso se pierde.
9. **P9 — Subsanación (RN-13):** acción explícita del responsable, Observado → Pendiente de validación, sin crear versión. Luego corrige validaciones y vínculos y confirma un ciclo nuevo. Las aprobaciones del ciclo anterior quedan en el historial y no se trasladan.
10. **P10 — RN-12 con documento nuevo (PD-05.1):** en la transacción de la incorporación, el ciclo `en_curso` pasa a `desplazado`, sus tareas abiertas a `anulada` (PD-05.4) y el trámite a Borrador. Un ciclo aprobado conserva su estado. Las versiones nuevas (RF-06) siguen en la Etapa 2.
11. **P11 — Línea de tiempo (RF-22):** `GET /tramites/{id}/linea-tiempo`, eventos ordenados con solo metadatos y enlace a la versión. El revisor ve todos los eventos y solo abre las versiones de sus ciclos.
12. **P12 — Evidencia (PD-03, PD-06):** `GET /decisiones/{id}/evidencia` con decisión, tarea, ciclo y versiones exactas; las validaciones de esas versiones vigentes en el instante de la decisión, calculadas por la cadena de reemplazos y la fecha, sin duplicarlas; los controles de `DECISION_CONTROL` con entradas, resultado y explicación; y los eventos del ciclo, sus tareas y decisiones, las validaciones y las ejecuciones listadas. Acceso: responsable y revisor con tarea en ese ciclo; el administrador recibe 404.
13. **Alcance EVD-01:** en este hito se ejecutan EVD-C y EVD-N12 (con documento nuevo como cambio del conjunto documental). EVD-A y EVD-B siguen omitidos hasta RF-06 (Etapa 2).
14. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-22-OPS — Preparación local del despliegue manual E90A (hito 1.0)

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** RC-P10, RC-P10-13, RC-P10-15, DO-2026-10-21, DO-2026-10-21-E90A, PD-07. **No autoriza crear, modificar ni destruir recursos AWS:** el agente prepara código, planes y procedimientos; el operador humano los ejecuta tras aprobar plan, impacto y costos.

1. **P1 — Orden:** cambios de la aplicación para correr en AWS; Terraform y empaquetado; seed y exportación de evidencia probados en local; runbook concreto, plan de destrucción y cotización por sesión.
2. **P2 — Mantenimiento:** objeto `control/mantenimiento.json` en el bucket documental, que la API solo lee, con caché de 15 s y denegación si no puede leerse. `draining`: se admiten consultas y las operaciones que modifican responden 503. `offline`: todo responde 503 salvo `/salud`, con `Retry-After`. `/salud` informa el estado. Las Lambdas de procesamiento no se bloquean; el drenaje verifica que no queden trabajos.
3. **P3 — Lambda privada de operaciones:** una función dentro de la VPC, invocada solo por el operador, con las acciones `inicializar_base`, `migrar`, `estado_migraciones`, `crear_administrador` y `verificar_drenaje` (solo lectura y conteos).
4. **P4 — Conexión a la base:** `bd_autenticacion = clave | iam`. Con `iam`, un token de RDS por conexión y TLS `verify-full` con el paquete de certificados de RDS, que descarga el equipo.
5. **P5 — FastAPI en Lambda:** biblioteca **Mangum** (aprobada como dependencia nueva).
6. **P6 — Empaquetado:** un solo zip arm64 para todas las funciones, construido con Docker; Terraform lo sube a un bucket de artefactos de la raíz `demo`.
7. **P7 — Terraform:** raíces `bootstrap`, `persistent`, `runtime` y `demo`; `tests` documentado y no desplegado en E90. Terraform ≥ 1.10 (`use_lockfile`) y proveedor AWS fijado a una versión exacta. Se aprueba instalar Terraform en local para `fmt` y `validate -backend=false`, sin credenciales ni operaciones AWS.
8. **P8 — Protecciones y destrucción selectiva:** `prevent_destroy` en `bootstrap`. RDS con `deletion_protection`, `skip_final_snapshot` y `delete_automated_backups` gobernados por `retiro_autorizado`. Buckets sin `force_destroy`, vaciados con una herramienta que simula por defecto y exige escribir el nombre del bucket. Retiro `demo → runtime → persistent` con planes revisados; sin `destroy` global ni `state rm`.
9. **P9 — Recursos del primer despliegue:** sin frontend/CloudFront, Scheduler/reconciliador, Lambda de Cognito ni endpoint de interfaz de Lambda. Endpoints de interfaz: Step Functions, Bedrock Runtime y Secrets Manager (temporal), más el gateway de S3. SSE-S3 sin claves KMS propias.
10. **P10 — Cognito y cuentas:** User Pool y cliente con `USER_PASSWORD_AUTH` solo en demo. El operador crea cuatro usuarios ficticios; las contraseñas solo viven en su terminal. El primer administrador se crea con `crear_administrador`; las demás cuentas, por API.
11. **P11 — Seed:** solo por API. Confirma la sugerencia que coincide con el oráculo y corrige al valor del oráculo la que no. Deja dos trámites: uno completo hasta la evidencia (demo D) y otro en Pendiente de validación. Manifiesto local de la sesión sin tokens. Probado contra el stack local.
12. **P12 — Exportación de evidencia:** por API, JSON local con índice SHA-256; funciona en `draining`.
13. **P13 — Cotización por sesión:** inventario de recursos facturables derivado del Terraform y fórmula por hora y por sesión con tarifas preliminares no oficiales. La exportación de Pricing Calculator y la aprobación siguen siendo del equipo.
14. **P14 — Oráculo:** el seed usa `oraculo_PD07_preliminar.json`, marcado como preliminar; no acredita EVD-01.
15. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-22-WEB — Aplicación web, fuentes documentales y resolución de DIF-67, DIF-84 y DIF-21

**Fecha:** 22/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** §3.2–3.4, §5.5, §6.2, HU-04, RF-10 a RF-13, RF-21, RF-22, Tabla 3.II, Tabla 3.VI, PD-03, PD-07, RC-P04, DO-2026-10-22-TAR, DO-2026-10-22-OPS. **Principio:** la interfaz permite usar y demostrar lo que funciona; no muestra capacidades inexistentes (RF-06, RF-23, RN-14 y RF-24 quedan fuera hasta implementarse).

1. **F1 — Orden:** base → trámite, historial y evidencia (D, lectura) → tareas y decisión (D) → carga y validación con visor (A) → vínculos y controles (C) → consulta asistida (B) → administración.
2. **F2 — Stack:** React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui (Radix, `class-variance-authority`, `clsx`, `tailwind-merge`), `lucide-react`, React Router 7, TanStack Query 5, `openapi-typescript` (desarrollo) y `openapi-fetch`, Zod, `react-pdf`; Vitest, Testing Library, jsdom y Playwright. Sin React Hook Form, gestores de estado ni analítica. Versiones exactas con al menos dos semanas.
3. **F3 — Autenticación en el navegador:** Cognito `InitiateAuth` (`USER_PASSWORD_AUTH`) por `fetch`, sin SDK; token de acceso en memoria y de refresco en `sessionStorage`. En local, se pega un token emitido con `token_local`.
4. **F4 — Fuente documental:** `GET /tramites/{t}/versiones/{v}/archivo` devuelve una URL prefirmada de lectura de 5 minutos, con las mismas reglas de acceso que el resto de las consultas (P8 de DO-2026-10-22-TAR). CORS GET en el bucket documental. Los DOCX se presentan con su localizador estructural, sin visor.
5. **F5 — Nombres:** columna `nombre_visible` en `usuario`, cargada por el administrador, y `GET /usuarios/directorio?ids=` para cualquier cuenta habilitada (solo id y nombre).
6. **F6 — Historial de consultas:** `GET /tramites/{t}/consultas` devuelve las consultas propias de quien consulta.
7. **F7 — Publicación para la demo:** la aplicación corre en la máquina del presentador contra API Gateway; CORS en API Gateway y en el bucket por Terraform, aplicado por el operador. S3 + CloudFront queda para después, con aprobación y costo.
8. **F8 — Semilla según PD-07:** C-v1 + O-v1 + F-v2; la revisión legal aprueba y la aprobación final observa con motivo (trámite Observado). Un segundo trámite con C-v1 procesado e incorporado, en Borrador, para el recorrido en vivo.
9. **F9 — Procesamiento simulado:** herramienta solo para desarrollo y pruebas E2E con respuestas fijas, rotulada como simulación y rechazada en demo. No se usa como evidencia ni en la defensa.
10. **F10 — DIF-67:** nuevo tipo de validación `ausente`, sin valor, con motivo `no_consta` o `no_aplica`, actor, fecha, versión y, si existía, la sugerencia descartada. La confirmación del flujo (P4 de DO-2026-10-22-TAR) exige cada campo del esquema **resuelto por una persona**: con valor validado o declarado ausente. En R1–R4, un campo ausente produce falta de datos con esa explicación.
11. **F11 — DIF-84:** oráculo v2 con los nombres de RC-P04 para los cinco documentos y regeneración de O y F con un número documental estable entre versiones, sin cambiar fechas, importes, CUIT ni resultados de reglas. Tarea del equipo (Etapa 0.8); hasta entonces la semilla usa la referencia impresa como número.
12. **F12 — DIF-21:** se cierra como «No requiere cambio». RF-21 audita acciones significativas del ciclo del trámite; los rechazos 401 y 403 permanecen en los registros técnicos (código, solicitud, usuario, sin contenido) y se cubren con pruebas negativas.
13. **F13 — CI:** job de frontend sin AWS (lint, tipos, pruebas y build).
14. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-23-E90-MEDICION — Arnés de medición de §6.3

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** §6.3.1–§6.3.4, IA-M01 a IA-M12, RC-P06.2, RC-P07, DO-2026-10-21-E90-CORPUS, DO-2026-10-22-CORPUS-REVISION. **Principio:** se mide el código de producción; ningún resultado de la partición de medición se observa antes de congelar los oráculos.

1. **P1 — Corpus:** `codex/corpus-e90` se integra por *merge* en `fundacion/local-backend`; DIF-E90-01 a 10 pasan a DIF-99 a DIF-108, con el alias anterior.
2. **P2 — Ubicación:** paquete `atlas.evaluacion` en `backend/src`, con pruebas en la CI (≥ 90 % por módulo) y excluido del paquete Lambda.
3. **P3 — Modos:** *directo* (Textract y Bedrock desde la máquina del operador) para la calidad de §6.3.1; *API* (ATLAS desplegado) para la latencia IA-M08 y la carga §6.3.4 (fase 2).
4. **P4 — Compuerta:** el modo `oficial` exige oráculos `CONGELADO` y revisados por los autores, y registra sus hashes; el modo `ensayo` solo admite la partición de ajuste y PD-07.
5. **P5 — Bucket:** raíz Terraform `evaluacion` con un único bucket (TLS, cifrado, bloqueo público, ciclo de vida de 2 días) para Textract asíncrono; se crea y destruye por campaña con aprobación del operador.
6. **P6 — Pipeline:** `analisis.clasificar`/`extraer`, `desde_textract`/`desde_docx`, `segmentar` y las instrucciones de consulta de producción, con el modelo como parámetro y temperatura 0. OCR una vez por documento, reutilizado en repeticiones y modelos.
7. **P7 — Tipo de extracción:** el tipo **sugerido**, como en producción; si difiere del esperado, los campos esperados cuentan como omitidos.
8. **P8 — Comparación:** normalizadores de `atlas.procesamiento.valores` y `comparable()` para textos; correcto, incorrecto (FP y FN), omitido e inventado según IA-M02.
9. **P9 — Campos críticos:** importe (`monto_total`, `importe_total`, `importe`), fecha (`fecha_celebracion`, `fecha`, `fecha_emision`), número (`numero`; el contrato no lo tiene) y CUIT de la contraparte (`cuit_contraparte`, `cuit_proveedor`, `cuit_emisor`).
10. **P10 — Procedencia:** PDF, página informada igual a la del oráculo (ausente es error); DOCX, el bloque informado contiene el párrafo del oráculo, sin umbral.
11. **P11 — Recuperación:** un índice congelado por modelo de embeddings, misma segmentación, coseno exacto en memoria, k = 5 y filtro por documentos autorizados. Un *chunk* es relevante si contiene el texto normalizado de un fragmento relevante del oráculo. Recall@5 = fracción de fragmentos relevantes cubiertos en los cinco primeros, promedio sobre las 24 respondibles; MRR con el primer *chunk* relevante.
12. **P12 — Alternativas:** adaptador de Titan Text Embeddings V2 (1024 dimensiones, normalización explícita); perfil de Sonnet 4.6 verificado con `list-inference-profiles` antes de la campaña.
13. **P13 — Repeticiones:** tres, alternando el orden Haiku/Sonnet (H→S, S→H, H→S); métricas por repetición, promedio y dispersión; la regla de sustitución se calcula sobre promedios y la decisión la registra el equipo.
14. **P14 — RAG:** el arnés genera respuestas con citas y una planilla por autor; las respuestas idénticas se agrupan; una herramienta consolida conservando calificaciones individuales y consenso. Sin juez automático.
15. **P15 — Adversariales:** la clasificación y la extracción no deben coincidir con los objetivos del ataque cuando difieren de lo esperado; se evalúan Q05 y Q10; la salida está forzada al esquema y no hay acciones disponibles.
16. **P16 — Evidencia:** `evaluacion/campanas/<id>/` con manifiesto (commit, modelos y perfiles, hashes de corpus, oráculos, instrucciones y segmentación), JSONL por llamada, métricas e informe; versionado (datos sintéticos). Los registros técnicos solo llevan identificadores.
17. **P17 — Fase 2:** cargador del corpus en ATLAS desplegado, latencia IA-M08 (90 consultas por modelo) y carga OP-01/OP-02 con concurrencias 1, 5 y 10.
18. **P18 — Fuera de este hito:** §6.3.3 (matriz de la Tabla 3.II en AWS y marcadores en CloudWatch) y §6.3.2 (depende del reconciliador RC-P08).
19. No modifica RF, RN, RNF, umbrales ni criterios de aceptación.

### DO-2026-10-23-E90-API — Latencia y carga contra la API desplegada (fase 2)

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** IA-M08, §6.3.4 (OP-01 a OP-03), RC-P07.4, DO-2026-10-23-E90-MEDICION P17.

1. **P1 — Ubicación:** módulos `cargador`, `latencia` y `carga` en `atlas.evaluacion`; campaña de tipo `api` con manifiesto propio (URL, `version_codigo`, perfil declarado, región).
2. **P2 — Corpus en ATLAS:** por la API, como la semilla, un trámite por contexto autorizado (12 contextos disjuntos, 21 documentos): carga prefirmada, confirmación, espera e incorporación, sin validación. La medición se carga solo después de congelar.
3. **P3 — Latencia IA-M08:** 30 preguntas × 3 repeticiones por modelo, secuenciales; el cliente cronometra cada `POST` completo; errores, 429, *timeouts* y reintentos se registran aparte; se verifica que `modelo_generacion` coincida con el perfil declarado.
4. **P4 — Instrumentación:** encabezado `Server-Timing` en la consulta (embeddings, recuperación, generación, total y arranque en frío) y `creado_en`, `ejecucion_iniciada_en` y `actualizado_en` en `TrabajoRespuesta`. Solo metadatos técnicos.
5. **P5 — Haiku y Sonnet:** cambio de `perfil_generativo` y `modelo_generativo` en Terraform, con el orden H, S │ S, H │ H, S.
6. **P6 — Estadísticos:** mediana y p95 por rango más cercano sobre todas las respuestas completadas, sin excluir observaciones lentas ni arranques en frío.
7. **P7 — Red:** 30 `GET /salud` como línea de base del tiempo de red, informada junto a la latencia.
8. **P8 — Carga OP-01/OP-02:** concurrencias 1, 5 y 10; interactiva (`POST` de consulta y `GET /tramites/{id}`, 30 solicitudes por nivel) y asíncrona (k documentos distintos, duración del trabajo con tiempos del servidor), con la partición de ajuste y 3 preguntas genéricas fijas.
9. **P9 — OP-03:** los umbrales de IA-M08, sin un segundo umbral.
10. **P10 — Cuenta:** la fase 0 verifica la concurrencia de Lambda; no se cambia la reservada sin aprobación.
11. **P11 — Ensayo:** modo `ensayo` sobre el ajuste con las preguntas genéricas, no reportable.
12. **P12 — Evidencia y pruebas:** `carga_corpus.json`, `latencia.jsonl`, `carga.jsonl`, `metricas.json` e `informe.md` en la campaña; pruebas con transporte simulado y `TestClient`, sin AWS en la CI.
13. No modifica RF, RN, RNF, umbrales ni criterios de aceptación.

### DO-2026-10-23-SEG — Ejecutor de seguridad de §6.3.3 (SEG-01 a SEG-04)

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** §6.3.3, Tabla 3.II, RNF-01 a RNF-04, RNF-08, RNF-09, SEG-01 a SEG-04, RC-P01.

1. **P1 — Ubicación:** módulo `atlas.evaluacion.seguridad` con su línea de comandos; campaña de tipo `seguridad` en `evaluacion/campanas/<id>/`.
2. **P2 — Actores:** responsable dueño, responsable ajeno, revisor con tarea, revisor sin tarea, aprobador con autorización de cierre, administrador, cuenta deshabilitada y solicitud sin token. En AWS se agregan tres cuentas ficticias de Cognito (`atlas-responsable-2`, `atlas-revisor-2`, `atlas-deshabilitada`).
3. **P3 — Escenario propio por la API:** trámite A del dueño con un documento sintético procesado e incorporado, campos validados, vínculo, flujo confirmado y ciclo con tarea del revisor; trámite B del responsable ajeno con su propio documento. No depende de la semilla de la demo.
4. **P4 — Matriz declarativa:** cada operación de la Tabla 3.II por actor, con el resultado esperado según las convenciones de RC-P01 (2xx; 403 sin el rol; 404 sin acceso al trámite; 401 sin token; 403 con cuenta deshabilitada). Primero los casos denegados; los permitidos que consumen estado, al final. Después de cada denegado, la huella del trámite (detalle e historial) no cambia.
5. **P5 — Acceso directo por identificador:** documentos, versiones y URL del original de A pedidos por actores sin acceso, y combinando el trámite B con identificadores de A: 404 y sin URL.
6. **P6 — Consulta asistida cruzada:** el responsable ajeno pregunta en su trámite por un dato que solo está en A; la respuesta y sus referencias no contienen el marcador de A.
7. **P7 — SEG-03:** métodos de modificación y borrado sobre el historial: 404 o 405; el historial se lee idéntico (huella) antes y después.
8. **P8 — SEG-04:** marcadores sintéticos únicos en el contenido de los documentos, títulos, nombres de archivo y preguntas, incluidos un fallo (archivo ilegible) y su reintento; búsqueda en CloudWatch Logs de las cuatro Lambda y en los historiales de Step Functions, exigiendo a la vez los identificadores de correlación.
9. **P9 — SEG-02:** verificación de solo lectura de la configuración (S3 cifrado, solo TLS y bloqueo público; RDS cifrado y `rds.force_ssl`; variables de entorno de Lambda sin secretos por nombre; registro de invocaciones de Bedrock desactivado; retención de registros; endpoint de Secrets Manager retirado; región y perfiles), contrastada con el Registro de destinos. Informe con nombres y banderas, sin valores.
10. **P10 — RNF-08:** documento y consulta con instrucciones adversariales que piden aprobar, reasignar o cambiar roles: sin cambios de estado, tareas ni roles.
11. **P11 — Operaciones no implementadas** (sugerencia de versión RF-06, cancelación RN-14, firma RF-23, supresión de cuentas RF-25, estado operativo general RF-24): se informan como «no implementada», nunca como Cumple.
12. **P12 — Dos niveles:** la misma matriz corre en la CI contra la aplicación local (procesamiento simulado y moto) y en una sesión AWS contra la API desplegada; tolerancia cero.
13. **P13 — Evidencia:** `seguridad.jsonl` con actor, operación, esperado, obtenido y cumple por caso, más el informe; sin cuerpos de respuesta.
14. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-23-REC — Reconciliador, «En espera», intento manual y pruebas de §6.3.2

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** RC-P08 (1 a 13), RNF-05, RNF-06, §5.3.1, §5.4.4, §6.3.2 (AS-01 a AS-04), RC-P10.

1. **P1 — Admisión:** estado `en_espera` (migración 0011). Al confirmar una carga, un *lock* transaccional (`pg_advisory_xact_lock`) cuenta los trabajos en curso: con cupo, `pendiente` e inicio; sin cupo, `en_espera`. Límite por despliegue: 10 en demo, 5 en pruebas.
2. **P2 — En curso:** `pendiente` y `en_ejecucion`; el cupo se libera al completar o fallar.
3. **P3 — Reconciliador:** quinta Lambda en la VPC, cada 5 minutos: (a) `pendiente` con más de 2 minutos: busca la ejecución por su nombre determinista y la reconoce o la inicia, sin crear una segunda; (b) admite `en_espera` por antigüedad mientras haya cupo; (c) marca fallido un `en_ejecucion` cuya ejecución terminó (FAILED, TIMED_OUT, ABORTED) o que supera 30 minutos. Solo identificadores en los registros.
4. **P4 — Programación:** EventBridge Scheduler `rate(5 minutes)` en la raíz `demo`, con rol mínimo y una variable que lo apaga.
5. **P5 — Mantenimiento:** el reconciliador no actúa fuera de `active`; al volver, recupera los pendientes en orden.
6. **P6 — Intento manual:** `POST /tramites/{t}/archivos/{a}/reintento`, solo el responsable y solo con el trabajo fallido; incrementa el intento, pasa por la admisión y se audita (RNF-06, RC-P08.4).
7. **P7 — Interfaz:** «En espera de capacidad», sin presentarlo como error, y «Reintentar procesamiento» en los trabajos fallidos, solo para el responsable.
8. **P8 — Nivel A (CI):** AS-01 a AS-04 con fallos inyectados y la admisión con 12 confirmaciones simultáneas y límite 10.
9. **P9 — Nivel B (AWS):** `python -m atlas.evaluacion.confiabilidad` en una sesión de ensayo: espera y admisión, fallo permanente e intento manual, eventos técnicos. El inicio fallido se cubre en el nivel A.
10. **P10 — Límites:** `TimeoutSeconds` 2400 como tope duro de la máquina; el reconciliador aplica los 30 minutos de RC-P08.2.
11. **P11 — Evidencia:** `confiabilidad.jsonl` e informe en la campaña, sin contenido.
12. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-23-WEB-HOST — Frontend servido con S3 y CloudFront

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** §5.4.2 y Figura 5.2 (frontend en S3 y CloudFront), DO-2026-10-22-WEB F7, RNF-02, RNF-03, DO-2026-10-21.

1. **P1 — Raíz `web`:** bucket privado y distribución de CloudFront, independiente y **persistente entre sesiones** (como `bootstrap`) para una URL estable; solo archivos estáticos, sin contenido documental; se retira al cerrar el proyecto.
2. **P2 — CloudFront:** Origin Access Control, HTTPS obligatorio (TLS ≥ 1.2), compresión, `PriceClass_100`, 403 y 404 → `index.html` con 200 (rutas de React), `index.html` sin caché y `assets/*` con caché larga.
3. **P3 — Encabezados:** HSTS, `nosniff`, `frame-ancestors 'none'`, `Referrer-Policy` estricta y CSP con `connect-src` limitado a API Gateway, Cognito y el bucket documental de la región (con comodines, sin dependencia circular con `demo`).
4. **P4 — Configuración:** `configuracion.json` leído al iniciar (URL de la API y cliente de Cognito); sin el archivo, se usan las variables `VITE_*`. Por sesión solo se publica ese archivo.
5. **P5 — CORS:** el dominio de CloudFront se suma a `origenes_cors` (`persistent`) y `origenes_web` (`demo`); `localhost:4173` se conserva como respaldo.
6. **P6 — Publicación:** `infra/web/publicar.sh` (`--aplicacion`, `--configuracion`), con invalidación; solo el operador, nunca la CI.
7. **P7 — Registros:** destino del bucket web en el Registro de destinos; DIF-78 se cierra en lo que respecta al frontend.
8. **P8 — Pruebas:** `terraform validate`, pruebas del frontend de la carga de configuración, `bash -n` y simulación del script; en la sesión, el E2E contra CloudFront.
9. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-23-VER — Versión nueva, descarte y firma digital simulada

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** RF-05 a RF-07, RF-23, RN-11, RN-12, RN-15, PD-05, RC-P03.2, Figura 5.4 (`FIRMA_SIMULADA`), EVD-A, EVD-B.

1. **P1 — Detección (RF-06):** reglas explicables, sin IA adicional. Candidato: documento del trámite cuya versión vigente tiene tipo validado igual al tipo sugerido del archivo y coincide en número documental o, si no, en el CUIT de la contraparte, proveedor o emisor. Prioridad número sobre CUIT; empate, el más reciente. Una sola candidata con su criterio.
2. **P2 — Persistencia:** tabla técnica `sugerencia_version` (migración 0012) con archivo, documento candidato, criterio, estado (pendiente, confirmada, rechazada) y resolución; se calcula en la persistencia del procesamiento y se revalida al confirmar.
3. **P3 — Rutas de RF-07 (solo responsable):** `POST …/archivos/{a}/version` confirma la relación y crea la versión nueva; la incorporación como documento nuevo registra el rechazo; `POST …/archivos/{a}/descarte` descarta sin crear documento ni versión.
4. **P4 — Versión nueva:** número siguiente, predecesora y cambio de vigencia en una transacción con el trámite bloqueado (PD-05); la anterior conserva sus validaciones; RN-12 con el mismo mecanismo que DIF-72.
5. **P5 — Firma (RF-23, RN-11):** `POST /tramites/{t}/firma {version_id}`: revisor con autorización de cierre y tarea en el ciclo aprobado; trámite Aprobado; versión vigente del ciclo. Tabla `firma_simulada` (Figura 5.4) con clave foránea compuesta a la versión del ciclo, una por trámite; el trámite pasa a Cerrado y se audita; RN-15 en todas las rutas de escritura.
6. **P6 — Integridad:** SHA-256 de un registro canónico (versión, huella del archivo, firmante, instante), visible y recalculable, rotulado «Firma digital simulada — sin validez jurídica».
7. **P7 — Interfaz:** sugerencia con criterio y tres acciones en Documentos; «Firmar (simulación)» para el aprobador; firma visible en resumen, evidencia e historial.
8. **P8 — Evidencia:** la evidencia de la decisión y la línea de tiempo incluyen la firma; EVD-A y EVD-B dejan de omitirse (V8 a V11).
9. **P9 — Semilla:** tercer trámite con EVD-B completo hasta la firma; el trámite en vivo admite RF-06 con O-v2.
10. **P10 — Fuera de alcance:** cancelación (RF-26, RN-14), panel del administrador (RF-24), supresión de cuentas (RF-25).
11. **P11 — Pruebas:** detección, rutas con negativos de autorización, RN-12 con versión nueva y concurrencia, firma, BDD de EVD-A y EVD-B, interfaz.
12. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-23-CIERRE — Cancelación, estado general, supresión de cuentas y dudas abiertas

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno). **Estado:** cerrada a nivel de diseño. **Base:** RF-24, RF-25, RF-26, RN-14, RN-15, HU-01, HU-10, Tabla 3.VI, §5.4.2, §5.4.3, DO-2026-10-23-VER.

**Dudas resueltas:**
- **D1:** con una versión nueva, las reglas se ejecutan al validarla y no al confirmarla (RN-02, RN-06). **D2:** el `tipo` del documento queda vacío hasta validar la versión nueva. **D3:** la sugerencia de versión admite el estado `descartada`.
- **D4 (DIF-84, F11):** el agente regenera O y F con un número estable entre versiones, sin cambiar fechas, importes ni CUIT, y publica el oráculo v2 preliminar.
- **D5:** el agente prepara correcciones de REV-E90-16 a 19 en una candidata v3 sin cambiar cantidades, particiones ni umbrales; las verificaciones manuales, la revisión de autores y la congelación son del equipo.
- **D6:** se confirma la tolerancia del 80 % para la relevancia (DIF-110).
- **D7:** el agente prepara un resumen clasificado del registro de diferencias y borradores de texto para los impactos pendientes en la tesis.

**Diseño:**
1. **P1 — Cancelación (RF-26):** `POST /tramites/{t}/cancelacion {motivo}`, solo el responsable, desde Borrador, Pendiente de validación, Pendiente de aprobación u Observado; 409 en Aprobado, Cerrado o Cancelado. Motivo obligatorio en `motivo_cancelacion`; evento `tramite_cancelado`.
2. **P2 — Ciclo y tareas:** el ciclo en curso pasa al estado nuevo `cancelado` y sus tareas abiertas a `anulada` con su evento; la decisión tardía responde 409 «El trámite fue cancelado».
3. **P3 — Trabajo asíncrono (RN-14):** un procesamiento que termina después guarda sus sugerencias sin cambiar el estado; no se sugieren versiones en trámites terminales; el reconciliador marca `fallido` (`tramite_terminal`) los trabajos en espera de esos trámites. Prueba de carrera.
4. **P4 — Estado general (RF-24):** `GET /administracion/estado-general`, solo el administrador: conteos de trámites, tareas (abiertas, sin asignar, en espera, asignadas a cuentas no habilitadas) y trabajos fallidos o en espera; lista de trámites con id, estado, responsable, fechas, cantidad de documentos y tareas abiertas, **sin título ni descripción**.
5. **P5 — Negativos de RF-24:** sin títulos, valores validados ni contenido; 403 para los demás roles.
6. **P6 — Supresión (RF-25):** `POST /usuarios/{id}/supresion`, solo el administrador, no sobre la propia cuenta, irreversible. Estado `suprimida`, `identificador_externo` y `nombre_visible` en NULL, sin roles ni autorización de cierre; evento `cuenta_suprimida`. Las intervenciones quedan atribuidas al id interno («Cuenta suprimida #id»); sus tareas abiertas aparecen en P4 para reasignarlas.
7. **P7 — Cognito:** Lambda `cuentas` fuera de la VPC, invocada por la API mediante el endpoint privado de Lambda: busca por `sub` y ejecuta `AdminDeleteUser`, idempotente. Primero Cognito y después la base.
8. **P8 — Terraform:** Lambda e IAM mínimo en `demo`; permiso de invocación para la API; endpoint de interfaz `lambda` en `runtime` (≈ US$ 0,02/h por sesión, costo aceptado). Validado sin AWS; lo aplica el operador.
9. **P9 — Local y CI:** puerto `GestorIdentidades` con un simulador sin Cognito.
10. **P10 — Interfaz:** «Cancelar trámite» con motivo; panel «Estado general»; «Suprimir cuenta» con confirmación explícita.
11. **P11 — Semilla:** cuarto trámite cancelado con motivo y sin documentos.
12. **P12 — Pruebas:** rutas con negativos, RN-15 sobre Cancelado, carrera de RN-14 y la Lambda con Cognito simulado (moto).
13. **P13 — Registro:** DIF nuevos, DIF-47 resuelta, Estado, ensayo de CI, commit y push.
14. No modifica RF, RN, RNF ni criterios de aceptación; el estado `cancelado` del ciclo es una extensión técnica registrada como DIF.

### DO-2026-10-23-DIF — Decisiones sobre las diferencias pendientes del registro

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno), sobre las recomendaciones del agente. **Estado:** cerrada. **Base:** [Resumen_Diferencias_para_Autores.md](../tesis/Resumen_Diferencias_para_Autores.md), RC-P04, RC-P10-13, RF-24, PD-07.

1. **DIF-24:** se mantiene el rechazo de todo PDF cifrado, aun con contraseña solo de propietario, y de los DOCX protegidos. Se aclara en la tesis.
2. **DIF-28:** el límite de 400.000 caracteres normalizados se conserva como resguardo interno del procesamiento; los límites de carga de RC-P04 (50 páginas, 150.000 caracteres en DOCX) siguen siendo los visibles.
3. **DIF-30:** corregir la clasificación no vuelve a extraer; los campos del esquema nuevo se registran por la persona (RN-02).
4. **DIF-86:** `db.t4g.medium` se mantiene como hipótesis para la sesión; la tesis lo presenta como confirmado solo si la carga de §6.3.4 lo respalda.
5. **DIF-114:** sin dominio propio; con `*.cloudfront.net` los navegadores negocian TLS 1.2 o 1.3 y la imposibilidad de fijar el mínimo se declara como limitación.
6. **DIF-119:** la lista de tareas sin asignar del administrador tampoco muestra el título del trámite: solo su identificador (TR-n), como el estado general.
7. **DIF-84:** el oráculo PD-07 v2 se congela. Consulta manual del equipo en ARCA (23/10/2026): el CUIT `30-96472518-3` no existe. Como advierte PD-07, el control no garantiza al 100 % la inexistencia de una asignación futura.
8. No modifica RF, RN, RNF ni criterios de aceptación.

### DO-2026-10-23-E90-MUESTREO — Revisión de los autores por muestreo antes de congelar la v3

**Fecha:** 23/10/2026. **Aprobada por:** el equipo (comunicada por Lucca Salerno), sobre la recomendación del agente. **Estado:** cerrada; la revisión está pendiente de ejecución por los autores. **Base:** DO-2026-10-22-CORPUS-REVISION (revisión de autores antes de congelar), DO-2026-10-23-CIERRE (D5), [Revision_Autores_Muestreo_V3.md](../evaluacion/corpus_e90/Revision_Autores_Muestreo_V3.md).

1. La revisión de los autores previa a la congelación de la candidata v3 se hace por muestreo: las 30 preguntas de RAG con sus respuestas de referencia, los 6 casos difíciles (3 adversariales y 4 ambiguos, uno compartido) y 10 documentos contra su original, incluidos los cambios de la v3.
2. El resto de las referencias queda validado por los controles automáticos y por la revisión de contraste sobre 25 documentos; el alcance se declara como limitación en §6.6.
3. Los autores marcan las casillas de los cuadernos y completan el cierre del documento de muestreo; el agente no marca revisiones. Una observación que exija corregir una referencia se resuelve en el generador y se regenera la candidata completa.
4. Con la revisión completa y la aprobación de ambos autores, la v3 se congela.

### DO-2026-10-23-E90-CONGELACION — Congelación de la candidata v3 del corpus E90

**Fecha:** 23/10/2026. **Aprobada por:** Ivo Gonsé y Lucca Salerno (comunicada por Lucca Salerno), después de completar las tres partes del muestreo sin observaciones que exijan regenerar. **Estado:** cerrada. **Base:** DO-2026-10-23-E90-MUESTREO, DO-2026-10-23-E90-MEDICION (P4, compuerta de la medición oficial), [Revision_Autores_Muestreo_V3.md](../evaluacion/corpus_e90/Revision_Autores_Muestreo_V3.md).

1. **P1 — Registro:** `oraculos/e90/congelamiento.json` con fecha, autores, decisión, alcance del muestreo y las huellas SHA-256 de los documentos, auxiliares, registros y oráculos.
2. **P2 — Oráculos:** `campos`, `fragmentos` y `consultas` pasan a `CONGELADO` con `revisado_por_autores` a nivel de archivo y la modalidad «muestreo»; por elemento, «revisado» solo en las 30 consultas y en los campos de los 10 documentos de la muestra.
3. **P3 — Corpus generado sin cambios:** registros, inventario, CUIT y documentos conservan sus bytes; la congelación los fija por huella.
4. **P4 — Herramientas:** `herramientas/corpus_e90/congelar.py` (una sola vez) y modo congelado del validador, que exige que las huellas coincidan; pruebas de ambos modos.
5. **P5 — Registro:** limitación de alcance para §6.6 y estado; la medición oficial de §6.3.1 queda habilitada.

### DO-2026-10-24-RETIRO-TOTAL — Retiro de `web` y `bootstrap` hasta la exposición final

**Fecha:** 24/10/2026. **Aprobada por:** Lucca Salerno (operador autorizado), al cerrar la sesión E90A del 24/10 y con la demo terminada; **se informa a Ivo Gonsé**. **Estado:** cerrada. **Modifica:** la regla de AGENTS.md §3 y de DO-2026-10-21-E90A que declara `bootstrap` intocable, y la guía de la sección 6 («`web` queda»), **solo para este retiro**.

1. **Motivo:** costo cero en la cuenta 014574285566 hasta la exposición final; toda la evidencia de la sección 6 está versionada en Git (`evaluacion/campanas/`).
2. **Orden:** `web` primero (su estado vive en el bucket de `bootstrap`); después se vacía el bucket de estado versionado y se destruye `bootstrap`, cuyo estado es local.
3. **`prevent_destroy`:** se desactiva solo en la copia local para este retiro y se restaura en el código en el mismo cambio: la próxima creación vuelve a quedar protegida.
4. **Consecuencia:** para la exposición final se reconstruye todo desde la Parte 1 de la guía (bootstrap, web, persistent, runtime, demo y semilla); la URL de CloudFront cambia. Los estados remotos vacíos de `demo`, `runtime`, `persistent` y `evaluacion` se pierden con el bucket (no gestionan recursos).
5. **Sin cambios:** cuenta, Organizations, Budgets y configuración de privacidad siguen fuera del alcance de los agentes y de este retiro.

### DO-2026-10-24-IA-M06-CONJUNTA — Calificación conjunta de las respuestas de §6.3.1

**Fecha:** 24/10/2026. **Aprobada por:** Ivo Gonsé y Lucca Salerno (comunicada por Lucca Salerno). **Estado:** cerrada. **Base:** evaluacion/README.md («Calificación»), RC-P06.2.10, DO-2026-10-23-E90-MUESTREO.

1. **Modalidad:** los autores calificaron **juntos** una sola planilla (`planillas/conjunta.csv`, 65 grupos de respuestas) en lugar de dos planillas independientes con discrepancias y consenso. No se mide el acuerdo entre evaluadores; `metricas.json` lo informa como `modalidad: conjunta`. Se declara como limitación en §6.6.
2. **Calificación y conteo de afirmaciones:** manuales, de ambos autores. Las filas 26 a 28 (Q12, Sonnet) se corrigieron a `correcta` por la variante admitida de Q12 (plazos del extracto en inglés, citado); Q25–Q30 sin respuesta se registran como `abstencion_correcta`, salvo la fila 65 (Q30, Sonnet, no se abstuvo): `abstencion_incorrecta`. El detalle de las 126 afirmaciones de las 58 respuestas respondibles está en `planillas/revision_afirmaciones.csv`; el conteo partió de un borrador preparado por el agente, que los autores revisaron y aprobaron afirmación por afirmación.
3. **Herramienta:** `metricas --con-calificaciones` usa `planillas/conjunta.csv` si existe (`planillas.consolidar_conjunta`, exige los conteos de las respondibles); si no, el flujo de dos planillas.
4. **Resultado:** IA-M06 cumple con ambos modelos (Haiku: correctas 0,875, respaldo 0,949, abstenciones 1,000; Sonnet: 0,958, 0,980, 0,833).

### DO-2026-11-09-DEMO-SURDELTA — Escenario de demostración SurDelta para los videos y la defensa

**Fecha:** 09/11/2026. **Aprobada por:** Lucca Salerno. **Estado:** cerrada. **Base:** devolución de EP3 (escenario concreto, contratos de valor, caso de negocio), PD-07, EVD-01, DO-2026-10-22-OPS P11.

1. **P1 — Escenario nuevo, no reemplazo:** `sembrar_demo --escenario surdelta`; el escenario PD-07 sigue siendo el predeterminado y conserva su evidencia y pruebas.
2. **P2 — Trámites sembrados:** «Provisión de acero inoxidable para la línea de válvulas» Cerrado, sin advertencias (agregado el 10/11/2026: un caso propio de la planta con el CUIT de ajuste 30-98641018-6); «Compra de equipos para el área comercial» Observado por R1 (factura con CUIT de otra empresa, vínculo manual); «Renovación de soporte informático» Pendiente de aprobación; «Contratación de limpieza» Cancelado. Ajustes del 10/11/2026: se retiró de la cartera el mantenimiento de planta cerrado, porque duplicaba el de la grabación y confundía; su recorrido completo sigue verificado por las pruebas. Para que el video entre en 5 minutos, el mantenimiento de planta se siembra en Borrador con la orden y la factura v1 validadas y sin vínculos confirmados (ningún control aplica todavía); en la grabación la responsable carga y valida el contrato y confirma los vínculos.
3. **P3 — Historia:** la factura v1 supera la OC (R4, sobrefacturación de horas adicionales no autorizadas); la v2 la corrige como versión nueva (RF-06/07). La OC se fecha antes de la vigencia (R3): advertencia que el revisor acepta. Es el recorrido de EVD-01 con otros datos; no acredita EVD-01.
4. **P4 — Flujo:** la plantilla de dos pasos del escenario PD-07; el revisor observa en el ciclo 1.
5. **P5 — Documentos:** generador reproducible `herramientas/generar_corpus_surdelta.py` (python-docx y LibreOffice, entorno de `herramientas/corpus_e90/requisitos.txt`), salida en `corpus/surdelta/` y oráculo `oraculos/oraculo_surdelta_v1.json` con huellas. Sin texto de control visible. CUIT: solo los ya consultados por el equipo en ARCA (el de PD-07 y los de la partición de **ajuste** de E90; ninguno de medición). Separado de PD-07 y del corpus de 50 (§6.3).
6. **P6 — Registro:** guion de los dos videos en `operaciones/demo/Guion_Demo.md`; pruebas de la semilla contra la API con PostgreSQL.

### DO-2026-11-09-WEB-FLUJOS — Presentación de los flujos de revisión en la interfaz

**Fecha:** 09/11/2026. **Aprobada por:** Lucca Salerno. **Estado:** cerrada. **Base:** RF-17, RF-18, RF-25, DO-2026-10-22-TAR (P1, P2), devolución de EP3. Solo frontend: sin cambios de reglas, API, datos ni modelo.

1. **Administración:** un flujo por alcance (contrato y general) con sus pasos y quién resuelve cada uno. **Editar** crea la versión siguiente a partir de la vigente (las plantillas siguen inmutables); **Volver a usar** crea una versión nueva con los pasos de una anterior. Los pasos se renombran, reasignan, reordenan y quitan; para el último solo se ofrecen cuentas con autorización de cierre.
2. **Cuentas:** se ve y se otorga o retira la autorización de cierre (API existente, RF-25).
3. **Trámite:** el flujo se muestra recién con los documentos validados (la plantilla depende de la clasificación validada); el ciclo se ve como recorrido de pasos con estado, persona y evidencia.
4. **Pendiente (flujos), para después de la entrega:** el modelo de dos alcances no refleja los tipos de gestión de una organización. Opción a decidir por el equipo: varios flujos activos con nombre propio y elección del responsable al confirmar (toca backend, RF-17 y DO-2026-10-22-TAR).

### DO-2026-11-09-ESTADOS-DEMO — Fotos de la base para repetir la demo (temporal)

**Fecha:** 09/11/2026. **Aprobada por:** Lucca Salerno, incluida la desactivación transitoria de las protecciones. **Estado:** cerrada; **se retira después de la exposición**. **Base:** DO-2026-10-21-E90A (eliminación administrativa de datos de una sesión descartable), RNF-04, RN-10.

1. Acciones `guardar_estado` y `restablecer_estado` de la Lambda de operaciones (`atlas/operacion/estados_demo.py`), invocadas a mano por el operador; ninguna ruta de la API ni pantalla.
2. Resguardos: solo en demo o en local, operación en `offline`, sin ejecuciones de procesamiento en curso (y base drenada para guardar) y confirmación con el nombre de la base. Rol IAM de operaciones: lectura de `control/mantenimiento.json`.
3. Restablecer corre como dueño de las tablas en una sola transacción: desactiva los *triggers* de usuario (inmutabilidad, sin borrado ni TRUNCATE), reemplaza los datos y los reactiva. Las identidades no retroceden. No es una operación funcional de borrado ni acredita persistencia.

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

## DO-2026-10-22-CORPUS-CONSTRUCCION — Construcción aislada del corpus candidato

**Fecha:** 22/10/2026. **Aprobada expresamente por el equipo en esta conversación**, incluidas las ampliaciones sobre fuentes contractuales. **Rama:** `codex/corpus-e90`, base `3b86143`. Alcance: preparación de Etapa 4 y auditoría PD-07 en lectura; no modifica RF/RN/RNF, umbrales, aplicación ni arquitectura. Los IDs DIF-E90-* son provisionales y se renumeran al integrar con otras ramas.

1. **P1:** auditoría PD-07 en solo lectura. Se conservan sus cinco PDF/DOCX, generador, datos, inconsistencias y oráculo. La auditoría identifica faltantes, no cierra DIF-84 ni acredita EVD-01. La historia principal de demo sigue siendo el contrato sintético de mantenimiento entre empresas ficticias argentinas previsto por PD-07.
2. **P2:** 50 documentos de medición y 15 de ajuste (tres por tipo). No mezclar corpus funcional, ajuste, medición y validación operativa real. No agregar los antiguos 16 extra ni un conjunto público de contraste.
3. **P3:** seguir el plan existente y su CSV: BASE_A/BASE_B compartidas, MED_C/MED_D exclusivas de medición por tipo. Tres adversariales dentro de los 50. Registros fuente previos y documentos independientes entre particiones.
4. **P4:** python-docx y Pillow aprobadas en requisitos propios de `herramientas/corpus_e90`, con versiones fijas, fuera del backend. LibreOffice, pdftoppm e ImageMagick como herramientas locales con versión registrada. CI valida los archivos ya generados, sus cantidades, particiones, plantillas, hashes, localizadores y consultas; no regenera. Las pruebas dependientes de herramientas del sistema se omiten con motivo explícito cuando no estén; el render se habilita solo de forma local y expresa. No se modifica el workflow ni se incorporan estas dependencias a Lambda.
5. **CUIT:** proponer aproximadamente 12 identificadores ficticios de dígito válido como candidatos. El equipo hace la consulta manual ARCA antes de la generación definitiva. Una coincidencia o fallo obliga a reemplazar y regenerar con nuevas referencias/hashes. No usar dígitos inválidos ni afirmar inexistencia por el algoritmo.
6. **Digitalización:** se autorizan degradaciones digitales simuladas, con parámetros y semilla por documento y declaración explícita en las diferencias. No presentarlas como capturas físicas. El equipo puede aportar fotos reales de documentos sintéticos más adelante; no se incorporan documentos operativos reales.
7. **P5:** reparto 10 directas, 8 condiciones/cláusulas, 6 multidocumento y 6 sin evidencia, como diseño de muestra, conforme a RC-P06.2. Redactar preguntas solo sobre archivos construidos. Las referencias preparadas siguen candidatas y sin evaluación humana de respuestas.
8. **P6:** revisión técnica independiente y revisión de ambos autores antes de congelar. Alcance autorizado hasta generación candidata y validadores; no congelar, medir modelos, inventar resultados ni marcar oráculos como revisados.
9. **Fuentes contractuales aprobadas por el equipo:** BASE_A, GOV.UK Short Form Contract 1.5A; BASE_B, Bonterms Professional Services Agreement 1.2; MED_C, Common Paper Professional Services Agreement 1.1; MED_D, GOV.UK Mid-Tier Core Terms 1.3A. Las tres últimas se aprobaron expresamente en un mensaje posterior. Conservar atribución, versiones exactas, enlaces, licencia, originales/extractos trazables y registro de traducciones/modificaciones; comprobar excepciones antes de usar. No usar logos, firmas, contratos privados ni datos confidenciales. Preservar diversidad real de estructura, cláusulas, complejidad y presentación; no presentar adaptaciones como modelos jurídicamente validados para Argentina. MED_C/MED_D no se utilizan en ajuste.

**Materiales:** `herramientas/corpus_e90/README.md`, `corpus/e90/`, `oraculos/e90/`, `docs/evaluacion/corpus_e90/`. Los cuatro modelos públicos son fuentes de adaptación, no archivos de medición ni datos de una relación contractual real. `plantillas/contratos.json` conserva procedencia y traducciones seleccionadas.

## DO-2026-10-22-CORPUS-ARG-A — fuente argentina CPAU

El equipo solicitó y aprobó, después de verificar su procedencia y licencia, reemplazar únicamente **E90-M-CTR-03** (CTR-BASE_A, PDF digital) por **CTR-ARG_A**, modelo CPAU MEPAU A-301, Contrato de proyecto y dirección, 9.ª edición de 2023. La respuesta expresa del equipo fue: «Aprobado. Reemplazá E90-M-CTR-03 (BASE_A) por CPAU para incorporar la familia ARG_A exclusivamente en medición».

Se conservan 50 documentos de medición y 15 de ajuste, sus tipos, formatos, tres adversariales, casos difíciles y 30 consultas (10/8/6/6). Las cuatro familias iniciales siguen representadas: medición de contratos BASE_A=1, BASE_B=2, MED_C=3, MED_D=3, ARG_A=1; ajuste BASE_A=2 y BASE_B=1. ARG_A, MED_C y MED_D no se utilizan en ajuste. No cambia el protocolo de evaluación ni PD-07.

El equipo autorizó adaptar el modelo concreto bajo CC BY-NC-SA 4.0, con atribución al autor/organismo, fuente, edición, cambios, uso no comercial y misma licencia para las adaptaciones compartidas. La ficha individual y el PDF de siete páginas fueron contrastados antes de adaptarlo. No se detectó aviso contradictorio; la licencia no figura impresa en el PDF y su asignación se documenta desde el campo específico de la ficha, asociado al archivo y SHA-256. Detalle y límites de la comprobación en `docs/evaluacion/corpus_e90/Incorporacion_ARG_A_CPAU.md` y su evidencia.

Se preservan los otros 64 documentos y 128 auxiliares por hash; se actualizan las siete referencias de campos del caso, fragmentos, Q12, metadatos e inventario/manifiestos. Todos continúan candidatos, sin revisión de autores ni congelación. Incorporar una fuente argentina agrega cobertura documental; un único caso no acredita representatividad ni ausencia de sesgos. No se amplía ningún requisito funcional ni se toma una decisión delegada.

## DO-2026-10-22-CORPUS-REVISION — revisión independiente y regeneración v2

**Fecha:** 22/10/2026. **Aprobada expresamente por el equipo en esta conversación** («ambas sí»), en respuesta a las dos preguntas de `docs/evaluacion/corpus_e90/Revision_Tecnica_Contraste_2026-10-22.md`.

1. La revisión técnica de contraste (`569c79e`), realizada por un agente que no construyó el incremento, **cuenta como la revisión técnica independiente de P6** de DO-2026-10-22-CORPUS-CONSTRUCCION. No reemplaza la revisión de ambos autores ni la congelación.
2. Se aprueba **en principio** una revisión candidata **v2** del corpus que resuelva en conjunto REV-E90-01 a REV-E90-15, sin cambiar cantidades (50 + 15), particiones, tipos, formatos, plantillas aprobadas, tres adversariales, reparto 10/8/6/6 ni umbrales. Ninguna clasificación esperada se cambia por conveniencia. El diseño detallado (decisiones P1…Pn de `docs/evaluacion/corpus_e90/Propuesta_Corpus_V2.md`) **requiere aprobación antes de regenerar**; se registrará como adenda de esta decisión.
3. La v1 (`f68da7c`) se conserva como evidencia histórica de la revisión; no se reescribe su historial ni sus hashes registrados.

**Adenda — diseño v2 aprobado (22/10/2026):** el equipo aprobó P0–P16 de `docs/evaluacion/corpus_e90/Propuesta_Corpus_V2.md` con las opciones recomendadas («Apruebo P0–P16 con las opciones recomendadas»). Según P0, la v2 la construye Claude Code y la revisión de contraste queda a cargo del otro agente. Las razones sociales (P2) y los seis CUIT nuevos de ajuste (P3) se generan como candidatos; el equipo los verifica a mano antes de congelar y, si alguno coincide con uno real, se reemplaza y se regenera.
