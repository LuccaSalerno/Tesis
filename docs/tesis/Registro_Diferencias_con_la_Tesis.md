# Registro de diferencias entre la implementación y la tesis

**Propósito:** reunir en un solo lugar todo lo que la implementación agrega, precisa, restringe o resuelve de otra forma respecto de `docs/tesis/main.pdf`, para que los autores decidan si hay que actualizar la tesis. **No modifica requisitos:** cada entrada indica qué decisión la respalda. Lo que contradiga RF, RN o RNF no se implementa sin consultar (AGENTS.md §2.3).

**Actualización:** 22/10/2026, después del hito 1.6 (rama `fundacion/local-backend`).

**Cómo se usa:**
- Toda diferencia nueva se agrega en el mismo cambio que la introduce (AGENTS.md §6 y §7).
- El **estado** de cada entrada es uno de estos:
  - `Pendiente` (sin revisar);
  - `Aplicar en la tesis`;
  - `No requiere cambio` (es un detalle de implementación);
  - `Aplicada` (indicar la versión del PDF).
- **Tipos:**
  - **Agregado:** algo que la tesis no menciona.
  - **Precisión:** concreta algo que la tesis deja abierto.
  - **Restricción:** acota algo que la tesis permite.
  - **Diferencia:** se hizo de otra forma que la descrita.
  - **Pendiente:** la tesis lo da por existente y todavía no está implementado.

---

## A. Modelo de datos (Sección 5.2, Figura 5.4)

Las entidades y relaciones de la Figura 5.4 existen con sus nombres. La tesis aclara que el diagrama es simplificado; estas son las columnas y tablas que se agregaron.

| ID | Entidad / sección | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-01 | TRAMITE (RF-03) | Se agregan `titulo` (obligatorio) y `descripcion` (opcional). RF-03 enumera identificador, responsable, estado y fechas, sin título | Agregado. Decisión del equipo P2 (PD-04) | Agregar título y descripción a RF-03 y a la Figura 5.4 | Pendiente |
| DIF-02 | USUARIO (RC-P03.2) | `autorizacion_cierre` como columna booleana de la cuenta, auditada | Precisión. P1 (PD-04) | Mostrar en la Figura 5.4 cómo se registra la autorización de cierre | Pendiente |
| DIF-03 | USUARIO (RF-25) | Estados `habilitada`, `deshabilitada` y `suprimida`. Al suprimir, `identificador_externo` queda nulo | Precisión. PD-04-001 | Opcional: nombrar los estados de la cuenta | Pendiente |
| DIF-04 | DOCUMENTO (§3.2.1, RN-02) | `tipo` queda vacío hasta validar la clasificación; luego toma el valor validado | Precisión. P3 (PD-04) | Aclarar en §5.2 que el tipo surge de la clasificación validada | Pendiente |
| DIF-05 | ARCHIVO (RF-04, §3.3.3) | Se agregan `nombre`, `formato`, `tamano_bytes`, `cargado_por_id` y `cargado_en` (metadatos de carga) | Agregado. PD-04-004 | Incluirlos en la Figura 5.4 si se quiere mostrar los metadatos de carga | Pendiente |
| DIF-06 | ARCHIVO (§5.2) | `estado_incorporacion` admite `pendiente`, `incorporado`, `descartado` y **`vencido`** (carga no incorporada en 24 h) | Agregado. DO-2026-10-22-CARGAS | Mencionar el vencimiento de cargas pendientes (ver DIF-22) | Pendiente |
| DIF-07 | VERSION_DOCUMENTAL, EVENTO_AUDITORIA | Versión: se agregan `creado_en` y `creado_por_id`. Evento: se agregan `actor_tipo` (usuario o **sistema**), `ocurrido_en` y `solicitud_id`; `actor_id` es nulo en acciones del sistema | Agregado. PD-04-004 | Aclarar que hay eventos atribuidos al sistema (vencimiento de cargas, alta del primer administrador) | Pendiente |
| DIF-08 | VALOR_SUGERIDO, REFERENCIA_FUENTE (§5.3.3) | Sugerencias con `valor_original`, `motivo_sin_fuente`, trabajo, intento, modelo y versiones. Fuentes con `fragmento`; el trabajo y el intento quedan nulos si la fuente la indica una persona. Un dato no extraído no genera sugerencia | Precisión. PD-04-007, PD-04-008 | Opcional: mencionar el motivo de ausencia de localizador (RF-11) | Pendiente |
| DIF-09 | VALIDACION_HUMANA (§5.3.3) | Se agregan `clase`, `tipo` (`confirmacion`, `correccion` o `sin_sugerencia`) y `validado_en`. La base garantiza una sola cadena de reemplazos por dato | Precisión. PD-04-008 | Opcional | Pendiente |
| DIF-10 | FRAGMENTO (§5.3.4) | Se asocia con el archivo; el documento y la versión se obtienen a través de la versión que referencia ese archivo, no con columnas propias. Se agregan trabajo, intento, orden, modelo de embeddings y versión de segmentación | Precisión. PD-04-009 | Verificar que «se asocia con el documento y la versión» admita la asociación indirecta | Pendiente |
| DIF-11 | Estructuras operativas (§5.2) | Tablas que el diagrama omite: `autorizacion_carga` (URL prefirmada emitida), `trabajo_procesamiento`, `consulta_asistida` y `consulta_fragmento` | Agregado (previsto por §5.2). PD-04-005, PD-04-009 | Opcional: listarlas en el texto de §5.2 | Pendiente |
| DIF-12 | Integridad en la base (RNF-04, RN-10) | Más allá de «operaciones ordinarias de la interfaz»: el usuario de aplicación de PostgreSQL no tiene `DELETE` ni `TRUNCATE`, y versiones, eventos, sugerencias, validaciones, fragmentos y consultas son inmutables por *trigger*, incluso para el propietario. Única excepción: `usuario_rol` admite `DELETE` porque guarda los roles actuales; el historial queda en la auditoría | Precisión, más estricta. PD-04-002 | Opcional: mencionar el refuerzo en la base | Pendiente |
| DIF-13 | ARCHIVO (§5.3.2: «el archivo original se conserva sin modificaciones, identificado mediante su clave») | El contenido no cambia, pero **la clave del objeto cambia una vez**: al incorporarse, el original se copia de `cargas-temporales/` a `documentos/` y se verifica su huella | Diferencia. DO-2026-10-22-CARGAS | Ajustar la frase de §5.3.2: la clave puede cambiar al confirmar la incorporación; la huella garantiza la integridad | Pendiente |

## B. Arquitectura, seguridad y despliegue (Secciones 5.1 y 5.4)

| ID | Sección | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-14 | §5.4.2 («API Gateway verifica los tokens… antes de invocar la API») | Además del autorizador de API Gateway, **el backend verifica cada token** (firma, emisor, cliente, `token_use` y vencimiento) con el JWKS del User Pool, que recibe por configuración porque la Lambda no tiene salida a Internet | Agregado. DT-AUT-01 | Mencionar la verificación en profundidad en §5.4.2 y §5.4.3 | Pendiente |
| DIF-15 | RF-25 (alta de cuentas) | Las cuentas se dan de alta por su `sub` de Cognito. **El primer administrador** se crea con una operación manual del operador, fuera de la API | Precisión. DT-AUT-02 | Mencionar cómo se inicializa el primer administrador | Pendiente |
| DIF-16 | §5.4.2 (Lambdas de procesamiento) | Dos funciones: procesamiento (fuera de la VPC: S3, Textract y Bedrock) y persistencia (dentro de la VPC: PostgreSQL). La etapa Preparar devuelve al flujo la clave S3 del archivo (una referencia técnica) | Precisión. DT-PROC-01 | Opcional: detallar las funciones de §5.4.2 | Pendiente |
| DIF-17 | §5.3.1 (orquestación) | Resultados intermedios en S3 bajo `resultados/{trabajo}/{intento}/`; reintentos de 3 intentos (2, 4 y 8 s) solo ante errores transitorios; límite de 150 consultas a Textract cada 12 s; Textract con `TABLES` y `LAYOUT` | Precisión. DO-2026-10-22-PROC, RC-P08 | Opcional | Pendiente |
| DIF-18 | §5.4 (API) | Un trámite inexistente o sin acceso responde **404 en ambos casos** (no revela existencia). Errores con forma `{"detalle"}`, cabecera `X-Solicitud-Id`, 503 ante fallas de servicios externos | Precisión. RC-P01-002, RC-P01-004 | No requiere cambio | Pendiente |
| DIF-19 | RNF-09 y regla 5 de AGENTS.md (registros) | Registros JSON con lista cerrada de metadatos. No se registran mensajes de excepción ni el registro de acceso de uvicorn (que incluye la consulta). Cada registro se escribe de inmediato | Precisión. RC-P01-002 | Opcional | Pendiente |
| DIF-20 | §5.4.2 (Bedrock en la API) | La API usa Bedrock para la consulta asistida (embeddings de la pregunta y generación), por el endpoint de interfaz previsto en RC-P10 | Precisión | Verificar que §5.4.2 lo mencione | Pendiente |
| DIF-21 | Tabla 3.II (registro de rechazos) | Los rechazos de autenticación y autorización (401 y 403) quedan **solo en los registros técnicos**, con el código del motivo, no como eventos de auditoría | Precisión, **pregunta abierta** al equipo | Definir si RF-21 exige auditar los intentos denegados | Pendiente |

## C. Cargas y almacenamiento

| ID | Sección | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-22 | §5.3.1, §5.3.2 (carga) | **La URL prefirmada vence a los 5 minutos.** Una carga tiene 24 h para confirmarse e incorporarse; después vence y no puede incorporarse. Limpieza idempotente de objetos vencidos (todas sus versiones y multipartes) y regla S3 Lifecycle de respaldo de 2 días sobre `cargas-temporales/`. Los resultados intermedios de una carga vencida también se eliminan | Agregado. DO-2026-10-22-CARGAS, DO-2026-10-22-PROC (P3) | Incorporar el vencimiento de cargas pendientes en §5.3.2 y la retención en §5.4.3 / RNF-03 | Pendiente |
| DIF-23 | RF-04, RC-P04 (metadatos requeridos) | Para autorizar la carga se piden `nombre`, `formato` y `tamano_bytes` declarado. Al confirmar, el tamaño y el tipo real se verifican contra lo autorizado | Precisión. RC-P01-004 | Opcional | Pendiente |
| DIF-24 | RC-P04 (protección) | Se rechaza **todo** PDF cifrado, incluso si solo tiene contraseña de propietario, y los DOCX protegidos (contenedor OLE) | Precisión | Confirmar con el equipo y, si se mantiene, aclararlo | Pendiente |

## D. Procesamiento inteligente (Sección 5.3)

| ID | Sección | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-25 | §5.3, §5.4.3 (salida estructurada) | Bedrock **Converse** con uso de herramienta forzado y `temperature` 0. Las instrucciones son archivos versionados con huella fija | Precisión. DO-2026-10-22-PROC (P2) | Opcional: mencionar el mecanismo de salida estructurada | Pendiente |
| DIF-26 | RF-11, §5.3.3 (localizador) | La página y la sección se aceptan **solo si la cita textual del modelo aparece en esa página**. Si no, la sugerencia se conserva sin localizador y con el motivo (`no_verificada` o `no_informada`). En DOCX no hay páginas: el localizador es sección y párrafo o tabla | Precisión. DT-PROC-02 | Describir la verificación de procedencia en §5.3.3 | Pendiente |
| DIF-27 | §5.3.2 (normalización) | Fechas ISO, importes con dos decimales, CUIT `##-########-#` (con verificación del dígito) y moneda ISO 4217; se conserva el valor original | Precisión. DT-PROC-02 | Opcional | Pendiente |
| DIF-28 | §5.3 (límites) | Un documento de más de 400.000 caracteres normalizados es fallo técnico: no se trunca | Agregado, parámetro configurable. DT-PROC-02 | Verificar compatibilidad con RC-P04 (50 páginas o 150.000 caracteres) | Pendiente |
| DIF-29 | RNF-05 («pendiente, en proceso, completado o fallido») | Estados técnicos `pendiente`, **`en_ejecucion`**, `completado` y `fallido`. «En espera» (RC-P08) todavía no está | Diferencia de nombre, pendiente. PD-04-005 | Unificar el nombre («en proceso» o «en ejecución») | Pendiente |
| DIF-30 | RF-10 (corrección del tipo) | Si se corrige el tipo, se presentan los campos del nuevo esquema **sin sugerencias** (se extrajeron con el esquema anterior). Volver a extraer queda pendiente de decisión | Restricción temporal. DO-2026-10-22-VAL (P3) | Decidir si la tesis exige volver a extraer con el tipo confirmado | Pendiente |

## E. Validación humana (RF-09, RF-12, Tabla 3.VI)

| ID | Sección | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-31 | RF-09, RF-12 | Se valida **solo la versión vigente** | Restricción. DO-2026-10-22-VAL (P1) | Aclarar en RF-12 o §5.3.3 | Pendiente |
| DIF-32 | Tabla 3.VI | Se admite validar en **Borrador** y **Pendiente de validación**. En **Observado**, recién con la transición de subsanación (RN-13, hito 1.8). En los demás estados se rechaza | Precisión. DO-2026-10-22-VAL (P2) | Aclarar en qué estados se puede validar | Pendiente |
| DIF-33 | RF-10, §5.3.2 | Los campos se validan **después** de validar la clasificación | Precisión. DO-2026-10-22-VAL (P3) | Aclarar el orden | Pendiente |
| DIF-34 | §5.3.2 (formatos) | El valor validado se exige en formato canónico. Un dígito verificador de CUIT inválido produce una **advertencia, no un rechazo** | Agregado. DO-2026-10-22-VAL (P4) | Mencionarlo, porque los valores validados alimentan R1 a R4 | Pendiente |

## F. Consulta asistida (RF-13, RN-04, §5.3.4)

| ID | Sección | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-35 | §5.3.4 («Las versiones históricas solo pueden utilizarse cuando el usuario está autorizado») | **Solo versiones vigentes.** No se consultan versiones históricas, ni siquiera para el responsable | Restricción. DO-2026-10-22-RAG (P1) | Ajustar §5.3.4 o definir qué autoriza a consultar versiones históricas | Pendiente |
| DIF-36 | §5.3.4 («respuestas asistidas cuya evidencia se conserva») | Se conservan **todas** las consultas: pregunta, respuesta o abstención, fragmentos recuperados y citados, modelo y versiones. Sin borrado | Precisión. DO-2026-10-22-RAG (P2) | Aclarar que se conservan todas y su retención (RNF-03) | Pendiente |
| DIF-37 | RF-13 (abstención) | Abstiene el modelo; el backend descarta las afirmaciones sin cita a los fragmentos recuperados y, si no queda ninguna, la respuesta es una abstención. **Sin umbral de similitud.** La respuesta es la unión de las afirmaciones citadas | Precisión. DO-2026-10-22-RAG (P3) | Describir el criterio en §5.3.4 | Pendiente |
| DIF-38 | §5.3.4 (segmentación) | `segmentacion-v1`: fragmentos de hasta 1.200 caracteres dentro de una misma página y sección; k = 5 por coseno exacto (RC-P07.3) | Precisión. DT-RAG-01 | Opcional | Pendiente |
| DIF-39 | Tabla 3.II («Realizar una consulta asistida: revisor en tarea asignada») | Por ahora consulta **solo el responsable**: el revisor se habilita con las tareas (hito 1.8) | Pendiente de implementación | Ninguna (temporal) | Pendiente |

## G. Entornos: local, CI y AWS

| ID | Tema | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-40 | Servicios AWS en local y CI | S3 y Step Functions se simulan con **moto** (en Docker y dentro de pytest). El código es el mismo con boto3 y solo cambia `ATLAS_AWS_ENDPOINT_URL`, prohibido en demo | Agregado. DT-AWS-01 | Opcional: mencionarlo en la estrategia de pruebas (§6) | Pendiente |
| DIF-41 | Autenticación en local y CI | Tokens con la forma de Cognito firmados con claves locales; el mismo verificador que en AWS | Agregado. DT-AUT-01 | Opcional | Pendiente |
| DIF-42 | PostgreSQL local (RC-P10-15) | Un script local emula la inicialización privilegiada: bases `atlas_dev` y `atlas_tests`, en lugar de `pfi_demo` y `pfi_tests` | Precisión | No requiere cambio | Pendiente |
| DIF-43 | Textract y Bedrock en pruebas (RC-P02.3: «sin simuladores») | La CI usa **respuestas fijas** para probar solo la lógica propia. La calidad se mide con los servicios reales en sesiones AWS autorizadas (`tests/aws_real`) y en §6.3 | Precisión del alcance. DO-2026-10-22-PROC (P1) | Si §6 describe la estrategia de pruebas, mencionarlo | Pendiente |
| DIF-44 | Migraciones (bajar versiones) | Bajar la migración 0004 convierte `vencido` en `descartado`; bajar la 0006 elimina las fuentes indicadas por personas. Solo para recrear bases locales y de pruebas: en E90A la demo no baja migraciones, se destruye | Precisión | No requiere cambio | Pendiente |

## H. Pruebas y calidad (Sección 6, RC-P02)

| ID | Tema | Implementación | Tipo y respaldo | Acción sugerida | Estado |
|---|---|---|---|---|---|
| DIF-45 | Cobertura (RC-P02.7: ≥ 85 %) | La CI exige **≥ 90 % en cada módulo**, no solo en el total | Más estricto. Pedido del equipo (22/10/2026) | Si la tesis menciona el 85 %, decidir si se actualiza | Pendiente |
| DIF-46 | Aceptación BDD | Escenarios Gherkin ejecutados con `pytest-bdd` contra la API. Los de EVD-01 se omiten con su motivo hasta los hitos 1.7 y 1.8 | Precisión. DO-2026-10-22-BDD | Opcional | Pendiente |

## I. Pendientes que la tesis da por existentes

Para no describir en la tesis como implementado lo que todavía no está:

| ID | Requisito | Estado de la implementación |
|---|---|---|
| DIF-47 | RF-25: supresión de cuentas | Requiere la Lambda de operaciones de Cognito (§5.4.2); no implementada |
| DIF-48 | RN-12 y PD-05: anular tareas abiertas al incorporar | La vuelta a Borrador está implementada; los ciclos y tareas llegan con el hito 1.8 |
| DIF-49 | RF-06 y RF-07: sugerencia y confirmación de nueva versión, descarte de archivos | Solo «documento nuevo»; el resto queda para la Etapa 2 |
| DIF-50 | RC-P08: reconciliador y estado «En espera» | Diseñados; sin implementar (Etapa 3) |
| DIF-51 | Infraestructura (Terraform, despliegue, limpieza programada) | Sin implementar; requiere aprobación (DO-2026-10-21) |
