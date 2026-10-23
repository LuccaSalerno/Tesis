# Resumen del registro de diferencias para los autores

**Fecha:** 23/10/2026. **Decisión:** DO-2026-10-23-CIERRE (D7). **Fuente:** [Registro_Diferencias_con_la_Tesis.md](Registro_Diferencias_con_la_Tesis.md) (121 entradas). Este documento **no modifica la tesis**: agrupa las diferencias por sección y propone borradores de texto para que los autores decidan y los copien a la fuente. Ningún borrador afirma resultados experimentales: las mediciones de §6.3 todavía no se ejecutaron.

## Cómo leerlo

| Grupo | Entradas | Qué hacer |
|---|---|---|
| Con acción sugerida en el registro | 62: 55 de texto (abajo, por sección) y 7 ya decididas por el equipo (DO-2026-10-23-DIF) | Revisar el borrador y adaptarlo |
| Acción «opcional» | 26 | Solo si se quiere detallar la implementación |
| Sin acción | 17 | Ninguna |
| Listas de pendientes y de corpus (formato corto) | 16 | Ver su estado en el registro; DIF-47, 48 y 49 ya están resueltas |
| Locales o de la CI (incluidas arriba) | DIF-40 a 44, DIF-95 a 98 | Mencionar en §6 solo si se describe el entorno de pruebas |

Prioridad sugerida: **§5.2 y Figura 5.4**, porque el modelo de datos es lo que más cambió, y después **§5.3.5** y la **Tabla 3.VI**.

## Borradores por sección

### §3.2 (requisitos funcionales)

- **RF-03 (DIF-01):** «El sistema deberá permitir al responsable crear un trámite con un título obligatorio y una descripción opcional, y registrar su identificador, responsable, estado y fechas.»
- **RF-12 y RF-09 (DIF-31):** agregar al final de RF-12: «La validación se registra sobre la versión vigente del documento; las versiones anteriores conservan sus validaciones como historial.»
- **RF-14 (DIF-55):** «Eliminar un vínculo es una baja lógica: el vínculo, su justificación y las ejecuciones de reglas asociadas permanecen en el historial.»
- **RF-15 (DIF-56):** «El sistema sugiere vínculos entre documentos cuyos CUIT validados coinciden (factura–orden de compra y orden de compra–contrato); la sugerencia requiere la confirmación del responsable.»
- **RF-25 (DIF-15, DIF-120):** «El primer administrador operativo se registra mediante una operación de inicialización del operador, fuera de la API. La supresión de una cuenta es irreversible, no puede aplicarse sobre la propia cuenta y elimina la identidad en el proveedor de autenticación antes de desvincular los datos identificatorios del registro interno.»

### Tablas 3.II y 3.VI (permisos y estados)

- **Validación y vínculos (DIF-32, DIF-60):** «Los datos se validan y los vínculos se administran con el trámite en Borrador o Pendiente de validación. En Observado, el responsable primero subsana el trámite y después corrige.»
- **Subsanación (DIF-70, DIF-71):** «La subsanación es una acción explícita del responsable que lleva el trámite a Pendiente de validación; después de corregir, se confirma un ciclo de revisión nuevo. Las decisiones del ciclo observado permanecen en el historial y no se trasladan.»
- **Datos requeridos (DIF-67, DIF-91):** «Antes de confirmar el flujo, cada dato del esquema del tipo documental debe estar resuelto por una persona: con un valor validado o declarado ausente porque no consta o no aplica.»
- **Cancelación (DIF-118):** agregar a la fila de cancelación: «Si existe un ciclo en curso, el ciclo pasa a Cancelado y sus tareas abiertas quedan anuladas.»
- **Revisor (DIF-39, DIF-62, DIF-73):** «El revisor/aprobador accede en modo lectura a las versiones de los ciclos en los que tiene una tarea asignada; si la tarea se reasigna, pierde ese acceso.»

### §3.4.1 (interfaz)

- **Áreas del trámite (DIF-87):** reemplazar las ocho pestañas por seis: Resumen, Documentos y datos, Vínculos y controles, Consulta, Revisión e Historial, más la vista «Evidencia de la decisión».
- **Mockups pendientes (DIF-74):** agregar el de «Evidencia de la decisión» (ítem 1 de los impactos de las decisiones técnicas).

### §5.2 y Figura 5.4 (modelo de datos)

- **Entidades con columnas agregadas (DIF-01, 02, 05, 06, 07):** TRAMITE con título y descripción; USUARIO con la autorización de cierre; ARCHIVO con nombre, formato, tamaño, autor e instante de carga, y el estado `vencido`; VERSION_DOCUMENTAL con autor e instante; EVENTO_AUDITORIA con tipo de actor (usuario o sistema), instante y solicitud.
- **Tipo del documento (DIF-04, DIF-115):** «El tipo de un documento refleja la clasificación validada de su versión vigente; una versión nueva no la hereda.»
- **Fragmento (DIF-10):** «Cada fragmento se asocia con el archivo procesado; el documento y la versión se obtienen por la versión que referencia ese archivo.»
- **Ejecución de reglas (DIF-53, DIF-54):** mostrar la relación entre EJECUCION_REGLA y las versiones consideradas, y nombrar los valores de `tipo` (referencia, campos), `origen` (manual, automático) y `estado` (pendiente, confirmado, rechazado, eliminado) del vínculo.
- **Estados de ciclo y tarea (DIF-68, DIF-69, DIF-118):** ciclo: en curso, aprobado, observado, desplazado y cancelado; tarea: en espera, pendiente, aprobada, observada, anulada y descartada.
- **Estructuras operativas (DIF-64, DIF-65):** plantillas de flujo versionadas por alcance (contrato o general), de uno a tres pasos, y el registro de asignaciones de tareas.
- **Firma simulada (DIF-116):** «FIRMA_SIMULADA referencia la versión dentro del ciclo aprobado y es inmutable; hay una por trámite.»

### §5.3.1 y §5.3.2 (carga y procesamiento)

- **Clave del original (DIF-13):** sustituir «el archivo original se conserva sin modificaciones, identificado mediante su clave» por «el contenido del original no se modifica; al confirmar la incorporación se traslada al prefijo definitivo y su huella SHA-256 garantiza la integridad».
- **Vencimiento de cargas (DIF-06, DIF-22):** «La URL de carga vence a los cinco minutos y una carga tiene 24 horas para incorporarse; después vence, no puede incorporarse y sus objetos se eliminan.»
- **Estados del trabajo (DIF-29, DIF-113):** usar «pendiente, en espera, en ejecución, completado y fallido»; mencionar el reconciliador periódico y el reintento manual del responsable.
- **Orden y formatos de validación (DIF-33, DIF-34):** «Primero se valida la clasificación y después los campos, en formato canónico; un dígito verificador de CUIT inválido genera una advertencia.»
- **Lectura del original (DIF-89):** «El navegador lee el original mediante una URL de lectura temporal, con las mismas reglas de acceso.»

### §5.3.3 (sugerencias, procedencia y versiones)

- **Procedencia (DIF-26):** «La página y la sección se aceptan solo si la cita textual del modelo aparece en esa página; si no, la sugerencia se conserva sin localizador y con el motivo.»
- **Versión nueva (DIF-115):** «Al procesar un archivo, el sistema sugiere que es una versión nueva de un documento del trámite cuando coincide el tipo validado y el número documental o, en su defecto, el CUIT de la contraparte, el proveedor o el emisor; la relación es una sugerencia hasta que el responsable la confirma, la rechaza o descarta el archivo.»

### §5.3.4 (consulta asistida)

- **Alcance (DIF-35, DIF-39):** «La consulta usa solo las versiones vigentes; para el revisor, las de sus ciclos.»
- **Conservación (DIF-36):** «Se conservan todas las consultas: pregunta, respuesta o abstención, fragmentos recuperados y citados, modelo y versiones.»
- **Abstención (DIF-37):** «Se descartan las afirmaciones sin cita a los fragmentos recuperados; si no queda ninguna, la respuesta es una abstención.»

### §5.3.5 (reglas)

- **Cuándo se ejecutan (DIF-57):** sustituir «Cuando se incorpora un nuevo documento o una nueva versión, se vuelven a ejecutar las reglas» por «Las reglas se vuelven a ejecutar cuando cambian los valores validados o los vínculos; una versión nueva las vuelve a ejecutar al validarse, porque solo se usan valores validados».
- **No aplicable (DIF-58):** «Una regla sin vínculo pertinente se presenta como no aplicable sin registrar una ejecución; las monedas distintas en R4 sí registran una ejecución no aplicable.»

### §5.4 (arquitectura, seguridad y operación)

- **Verificación de tokens (DIF-14):** «Además del autorizador de API Gateway, el backend verifica cada token con el JWKS del grupo de usuarios.»
- **Bedrock en la API (DIF-20):** mencionar que la API invoca Bedrock para la consulta asistida.
- **Modo mantenimiento (DIF-77):** «La operación admite los modos active, draining y offline; fuera de active no se aceptan cambios.»
- **Cifrado (DIF-79):** sustituir la mención de claves KMS por entorno por «cifrado administrado por AWS (SSE-S3 y claves de servicio)».
- **Figura 5.2 (DIF-78, DIF-93, DIF-114, DIF-120):** todos los componentes están implementados; describirlos como desplegados solo después de la sesión AWS de la sección 6.

### Sección 6 (evaluación)

- **Estrategia de pruebas (DIF-43, DIF-45):** la CI usa respuestas fijas para Textract y Bedrock y exige al menos un 90 % de cobertura en cada módulo; la calidad de los servicios se mide en §6.3 con los servicios reales.
- **§6.3.1 (DIF-110):** la recuperación se mide fuera de la API, con coseno exacto y un índice congelado por modelo; un *chunk* cubre un fragmento si contiene al menos el 80 % de sus palabras (tolerancia confirmada en D6).
- **§6.3.3 (DIF-112):** describir los dos niveles (CI y AWS) y qué casos permitidos cubre la CI.
- **§6.3.4 (DIF-111):** describir el punto de medición en el cliente y la línea de base de red.

## Decisiones del equipo (DO-2026-10-23-DIF)

Tomadas el 23/10/2026 sobre las recomendaciones del agente:

| DIF | Tema | Decisión |
|---|---|---|
| DIF-24 | PDF con contraseña solo de propietario | Se mantiene el rechazo de todo PDF cifrado |
| DIF-28 | Límite de 400.000 caracteres | Resguardo interno; los límites visibles son los de RC-P04 |
| DIF-30 | Corrección del tipo | No se vuelve a extraer; la persona registra los campos del nuevo esquema |
| DIF-86 | Dimensionamiento | `db.t4g.medium` como hipótesis; confirmado solo si la carga de §6.3.4 lo respalda |
| DIF-114 | TLS mínimo en CloudFront | Sin dominio propio; se declara la limitación |
| DIF-119 | Título en la lista de tareas sin asignar | Se omite también ahí (implementado) |
| DIF-84 | Oráculo PD-07 v2 | Congelado; ARCA sin inscripción para el CUIT `30-96472518-3` |
