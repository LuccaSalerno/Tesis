# Contexto para redactar los resultados del capítulo 6 (ATLAS, PFI UADE 2026)

**Para:** el agente que redacte los resultados en la tesis. **Preparado:** 24/10/2026, al cerrar las mediciones de la sesión E90A del 23–24/10. **Fuente de verdad:** los archivos de evidencia citados acá (repositorio `Tesis`, rama `fundacion/local-backend`, commit `7ad65e5` o posterior). Todo número de este documento sale de esos archivos; si encontrás una diferencia, prevalece el archivo.

## 1. Qué hay que escribir y dónde

Archivo: `~/development/Documento Tesis/chapters/validation_results.tex` (LaTeX, otro repositorio). Estructura actual:

| Sección | Etiqueta | Estado | Qué hacer |
|---|---|---|---|
| 6.1 Estrategia de validación | `sec:estrategia-validacion` | Escrita (método) | No tocar |
| 6.2 Pruebas funcionales y automatizadas | `sec:pruebas-funcionales` | Escrita (método); tiene «Verificación de la cadena de evidencia documental» y «Cobertura de las pruebas automatizadas» | Agregar los números reales (§4.1) sin cambiar el método |
| 6.3.1 a 6.3.4 | `sec:evaluacion-procesamiento-inteligente`, `sec:confiabilidad-recuperacion-procesamiento-asincrono`, `sec:seguridad-privacidad-trazabilidad-tecnica`, `sec:rendimiento-comportamiento-operativo` | Escritas (método, criterios y tabla de umbrales `tab:indicadores-criterios-procesamiento-inteligente`) | No cambiar criterios ni umbrales. Solo ajustar lo que el procedimiento real cambió (§5) si los autores lo piden |
| 6.4 Validación en un escenario representativo | `sec:validacion-escenario-representativo` | Escrita por los autores (Automac S.A.) | **No tocar.** Es la validación operativa del equipo, separada de §6.3 (ver §2) |
| 6.5 Resultados y discusión | `sec:resultados-discusion` | **Vacía** (`% TODO EP3`) | Redactar completa (§4 y §6) |
| 6.6 Limitaciones de la validación | `sec:limitaciones-validacion` | Escrita parcialmente (`% TODO EP3`) | Corregir una frase y agregar limitaciones observadas (§7) |

Estilo de los capítulos existentes (respetarlo):

- Español formal, impersonal o tercera persona («se midió», «los resultados muestran»); sin primera persona ni tono promocional.
- Coma decimal (`0{,}875`), porcentajes como `90\,\%`, símbolos matemáticos en modo matemático (`$\geq$`).
- Tablas con `longtable` dentro de `\begingroup\footnotesize ... \endgroup`, columnas `p{...\textwidth}`, `\caption{...}\label{tab:...}`, encabezado repetido con `\endhead`, y debajo `\noindent\textit{Fuente: elaboración propia.}\par`.
- Referencias cruzadas con `Sección~\ref{...}` y `Tabla~\ref{...}`.
- Nombres de modelos como en 6.3: «Claude Haiku 4.5», «Claude Sonnet 4.6», «Cohere Embed Multilingual v3», «Amazon Titan Text Embeddings V2».
- La verificación de EVD-01 se llama en la tesis «cadena de evidencia documental» (no renombrar).

## 2. Reglas que no se pueden romper

1. **No inventar ni redondear a favor.** Cada cifra sale de la evidencia. Un incumplimiento se informa como tal (hay uno: exactitud crítica de fechas).
2. **No cambiar umbrales ni criterios** de la Tabla `tab:indicadores-criterios-procesamiento-inteligente` ni de las secciones 6.3.x.
3. **§6.3 y §6.4 son evaluaciones distintas.** §6.3 es cuantitativa y sintética (corpus E90 de 50 documentos); §6.4 es la experiencia operativa del equipo. No mezclar muestras, métricas ni conclusiones entre ambas; el corpus de la demo (PD-07) tampoco sustituye al de 50.
4. **EVD-01 no está acreditado.** Los cuatro recorridos de la cadena de evidencia se ejecutan como escenarios en la CI y el recorrido completo se ejecutó en AWS, pero no se aplicó el procedimiento formal de acreditación de EVD-01 con su oráculo. Decirlo así.
5. **Interpretación proporcional:** los resultados valen para el corpus sintético, la configuración y la carga ensayadas; no extrapolar a producción ni a cargas mayores.
6. **Nada de contenido documental real:** todo lo medido es sintético.

## 3. Condiciones de ejecución (para describir el entorno)

| Aspecto | Valor |
|---|---|
| Sesión | E90A `e90-2026-10-24`, 23/10/2026 22:30 a 24/10/2026 ~16:30 (hora de Argentina), infraestructura descartable creada y destruida por el operador |
| Cuenta y región | Una cuenta AWS del equipo; `us-east-1` |
| Código desplegado | `6232839` (el mismo para todas las mediciones de §6.3.2 a §6.3.4; §6.3.1 corrió con el harness local en el commit `b872e0c`, sin cambios de código de procesamiento) |
| Arquitectura | API Gateway HTTP + Lambda (FastAPI), Step Functions Standard, Textract (TABLES + LAYOUT), Bedrock, RDS PostgreSQL 16 Multi-AZ con pgvector vía RDS Proxy con IAM, Cognito, S3, EventBridge Scheduler (reconciliador cada 5 min), frontend en S3 + CloudFront |
| Modelos | Generativo de producción: Claude Haiku 4.5 (perfil `us.`); comparado con Claude Sonnet 4.6. Embeddings: Cohere Embed Multilingual v3; comparado con Amazon Titan Text Embeddings V2 |
| Límite de procesamiento | **3 trabajos concurrentes** (`limite_concurrencia = 3`), porque la cuota de ejecuciones concurrentes de Lambda de la cuenta es 10 (la cuenta no tenía el aumento solicitado). Los trabajos excedentes quedan «En espera» y los admite el reconciliador |
| Corpus de medición | E90 v3 **congelado** (DO-2026-10-23-E90-CONGELACION): 50 documentos sintéticos (10 por tipo: contrato, presupuesto, orden de compra, factura, comprobante); formatos: 20 PDF digitales, 15 DOCX, 10 PDF escaneados, 5 PDF fotografiados; 3 adversariales incluidos (E90-M-CTR-10, E90-M-FAC-06, E90-M-COM-08); 15 de ajuste separados; 30 preguntas RAG (24 respondibles, 6 sin evidencia). Revisión de los autores por muestreo (30 preguntas, 6 casos difíciles, 10 documentos) |
| Repeticiones | 3 por modelo generativo |

## 4. Resultados por sección

### 4.1 Pruebas funcionales y automatizadas (§6.2)

Evidencia: ensayo de CI limpio del 24/10 (`backend/herramientas_ci/ensayo_ci_limpio.sh`), CI de GitHub, `evaluacion/campanas/semilla-e90-2026-10-24/`.

- **Pruebas automatizadas:** 835 aprobadas, 2 omitidas, 0 fallidas; cobertura total 98 %, y **cada uno de los 110 módulos ≥ 90 %** (el criterio de la tesis es ≥ 85 %; el equipo exigió 90 % por módulo, DIF-45). Pruebas del corpus: 71 aprobadas, 1 omitida. PostgreSQL con pgvector real en la CI.
- **Escenarios de aceptación (BDD, pytest-bdd):** 6 características Gherkin con 20 escenarios: incorporación documental, validación humana, consulta asistida, vínculos y reglas de consistencia, flujo de revisión y evidencia de la decisión, y reconstrucción de la cadena de evidencia documental (recorridos EVD-A, EVD-B, EVD-C y EVD-N12). Se ejecutan en cada CI contra la API.
- **Recorrido completo en AWS:** la semilla sintética (PD-07) recorrió por la API el trámite completo: validación de C-v1, O-v1 y F-v2, vínculos, controles (R3 advierte por fecha fuera de vigencia), revisión legal aprobada, aprobación final observada, O-v2 sugerida como **versión nueva por su número** (RF-06) y confirmada, R3 pasa a cumplimiento, ciclo 2 aprobado y **firma simulada** aplicada (RF-23). Además, **las personas completaron el mismo recorrido desde la interfaz** en el trámite «en vivo» (id 2), que quedó Cerrado con firma. La evidencia exportada por la API (71 archivos: trámites, archivos, sugerencias, validaciones, vínculos y controles con historial, ciclos, línea de tiempo, evidencia de cada decisión y firma) está en `evaluacion/campanas/semilla-e90-2026-10-24/evidencia/`, con índice SHA-256.
- **Nivel B (servicios reales, verificación puntual, no es métrica de §6.3):** `evaluacion/campanas/nivel-b/`. C-v1 (10 páginas): tipo correcto y 7 de 7 campos correctos con la página esperada, 25,7 s; la consulta de vigencia responde citando la página 6 y la consulta sin evidencia se abstiene sin citar.

### 4.2 Procesamiento inteligente (§6.3.1)

Evidencia: `evaluacion/campanas/e90-oficial-1/` (`informe.md`, `metricas.json`, `planillas/conjunta.csv`, `planillas/revision_afirmaciones.csv`). Serie de 3 repeticiones; errores técnicos 0 en cada una.

| Criterio | Indicador | Umbral | Haiku 4.5 | Sonnet 4.6 |
|---|---|---|---|---|
| IA-M01 | F1 macro de clasificación | ≥ 0,90 | 1,000 — cumple | 1,000 — cumple |
| IA-M01 | Exhaustividad mínima por categoría | ≥ 0,80 | 1,000 — cumple | 1,000 — cumple |
| IA-M02 | F1 de extracción, tipo más bajo | ≥ 0,85 | 0,884 (contrato) — cumple | 0,852 (0,847/0,861/0,847) — cumple |
| IA-M02 | F1 macro de extracción | — (sustitución) | 0,950 | 0,936 |
| IA-M02 | Exactitud crítica, campo más bajo | ≥ 0,90 | **0,778 (fecha) — no cumple** | **0,778 (fecha) — no cumple** |
| IA-M02 | Valores inventados | ≤ 5 % | 0 % — cumple | 0 % — cumple |
| IA-M03 | Procedencia PDF, página correcta | ≥ 0,90 | 1,000 (212/212) — cumple | 1,000 (212/212) — cumple |
| IA-M03 | Procedencia DOCX (sin umbral) | — | 0,785 (73/93) | 0,989 (91/92) |
| IA-M05 | Recall@5 (MRR) | ≥ 0,80 | Cohere 0,976 (0,678) — cumple | Titan 0,969 (0,678) — cumple |
| IA-M06 | Respuestas correctas | ≥ 0,80 | 0,875 — cumple | 0,958 — cumple |
| IA-M06 | Afirmaciones respaldadas | ≥ 0,90 | 0,949 — cumple | 0,980 — cumple |
| IA-M06 | Abstenciones correctas | ≥ 0,80 | 1,000 — cumple | 0,833 — cumple |
| IA-M07 | Adversariales con alteraciones | 0 de 3 | 0 — cumple | 0 — cumple |

Detalle para la discusión:

- **Clasificación:** matriz de confusión diagonal (10/10 en cada tipo), en las tres repeticiones y con ambos modelos.
- **Extracción por tipo (Haiku):** contrato 0,884; presupuesto, orden, factura y comprobante 0,966 cada uno. Sonnet: contrato 0,847, presupuesto 0,932, el resto 0,966.
- **Por formato (ambos modelos salvo DOCX):** DOCX 1,000 (Haiku) / 0,951 (Sonnet); PDF digital 0,944; **PDF escaneado 0,842** (el formato más bajo; efecto conjunto de OCR y extracción, sin atribuirlo solo al OCR); PDF fotografiado 1,000.
- **Campos críticos (Haiku):** importe 50/50, número 40/40, CUIT de la contraparte 50/50, **fecha 35/45**. Sonnet: importe 50/50, número 38/40, CUIT 49/50, fecha 35/45.
- **Causa del incumplimiento de fecha (verificada en el detalle de `metricas.json`):** las 10 fechas marcadas como incorrectas son las mismas con ambos modelos y en los cinco tipos (COM-06, COM-09, CTR-06, CTR-09, FAC-06, FAC-09, OC-06, OC-09, PRE-06, PRE-09). En todas, el documento imprime la fecha con **año de dos dígitos** (por ejemplo, `22/07/26`) y el modelo la **extrajo correctamente** (`22/07/26`), pero el normalizador de fechas del prototipo (`backend/src/atlas/procesamiento/valores.py`, función `_fecha`) solo reconoce años de cuatro dígitos y deja el valor sin convertir a ISO; la comparación con la referencia (`2026-07-22`) falla. Es un **defecto de normalización del prototipo**, no un error de lectura de los modelos. El resultado medido se informa tal cual (0,778, no cumple). **El normalizador se corrigió el 24/10/2026, después de la medición** (DIF-124: años de dos dígitos como siglo XXI), verificado con pruebas unitarias y normalizando los 10 valores ya extraídos; **no se volvió a medir**, así que la tesis no puede afirmar que el criterio ahora se cumple. Puede decir que la causa fue identificada y corregida en el prototipo y que su efecto sobre la métrica queda pendiente de una nueva medición.
- **Procedencia DOCX de Haiku:** los 20 localizadores faltantes se concentran en un contrato (E90-M-CTR-02, campos sin localizador de párrafo); Sonnet falla uno (E90-M-CTR-04).
- **Respuestas (IA-M06):** calificadas por **ambos autores en conjunto** sobre una planilla de 65 respuestas distintas (agrupadas por contenido idéntico; DO-2026-10-24-IA-M06-CONJUNTA). Haiku: 3 parciales (Q12 con Haiku, que omite que el rechazo debe expresar razones; Q21, que atribuye a la factura una cita al presupuesto; Q22, que infiere la fecha de emisión del período facturado). Sonnet: 1 parcial (Q22). Abstención: Haiku se abstuvo en las 6 sin evidencia; Sonnet respondió Q30 (dijo correctamente que el monto es de honorarios y no el presupuesto de obra, pero no se abstuvo) y se contó como abstención incorrecta. Afirmaciones: 126 en las 58 respuestas respondibles agrupadas; 3 sin respaldo en las citas (Q21 Haiku, Q22 Haiku, Q22 Sonnet).
- **Adversariales:** ninguno de los tres documentos con instrucciones embebidas alteró clasificación, extracción, citas ni el estado del trámite.
- **Sustitución (reglas fijadas antes de medir, sobre promedios):** Sonnet no recupera ningún criterio incumplido por Haiku (ambos fallan fecha) y no mejora el F1 macro de extracción (−1,3 puntos), así que **se conserva Haiku 4.5**. Titan no mejora Recall@5 en 5 puntos (−0,7), así que **se conserva Cohere**. La selección se hizo sobre el mismo corpus de medición (ya declarado en 6.3.1).

### 4.3 Confiabilidad y recuperación (§6.3.2)

Evidencia: `evaluacion/campanas/e90-confiabilidad-1/` y `e90-confiabilidad-2/` (cada una con `resultado.json`, `confiabilidad.jsonl`); análisis en `e90-confiabilidad-1/analisis_sobreasignacion.md` y `ejecuciones_step_functions.txt`.

- **Escenario «espera»:** 6 documentos subidos a la vez con límite 3. Quedaron 2 «En espera» al confirmar; el reconciliador los admitió en su ciclo siguiente (unos 4 minutos después); los 6 terminaron completados.
- **Escenario «fallo»:** un DOCX vacío falla de forma definitiva; el intento nuevo manual (intento 2) vuelve a fallar sin reintentos indefinidos y **sin cambiar el estado del trámite**.
- **Campaña 1: 5 de 6 criterios.** El criterio «espera sin sobreasignación» dio un pico de 4 > 3, pero el ejecutor sumaba estados devueltos al confirmar cada carga, tomados en instantes distintos. Los tiempos reales de Step Functions muestran un máximo de **3** ejecuciones simultáneas (el trabajo 75 empezó después de que terminara el 71). Se conservó el resultado y se agregó el análisis.
- **Campaña 2 (ejecutor corregido para medir el pico con los tiempos del servidor): 6 de 6.** Pico 3 por tiempos del servidor y por sondeos; se repite el patrón de 4 admitidos y 2 en espera.
- **Incidente de la sesión (corregido antes de las mediciones de §6.3.2 a §6.3.4):** Textract rechazó trabajos con `IdempotentParameterMismatchException` porque el token de idempotencia dependía solo del trabajo y del intento y la base nueva repetía identificadores de una sesión anterior en la misma cuenta. El token incluye ahora la huella del objeto (DIF-122). Es una evidencia de por qué la idempotencia debe ser única por objeto y no solo por identificador interno.

### 4.4 Seguridad, privacidad y trazabilidad (§6.3.3)

Evidencia: `evaluacion/campanas/e90-seguridad-1/` (`informe.md`, `seguridad.json`, `configuracion.json`, `marcadores.json`, `analisis_rds_force_ssl.md`) y `e90-seguridad-2/` (solo configuración).

- **Matriz de autorización (SEG-01, SEG-03, RNF-08): 237 de 237** casos con el resultado esperado: permisos por rol (Tabla 3.II), acceso directo por identificador a trámites ajenos, consulta asistida cruzada sin exposición de otro trámite, auditoría inmutable, consulta adversarial que pide acciones privilegiadas sin cambios de roles, tareas ni estados. Los rechazos que modifican se verificaron con una «huella» de estado antes y después (unas 4.650 solicitudes en total).
- **Registros sin contenido documental (SEG-04): 28 de 28.** Ningún marcador sintético apareció en CloudWatch (API, procesamiento, persistencia, operaciones) ni en el historial de Step Functions; la correlación por solicitud y el identificador de trabajo sí están; el camino de error se ejercitó.
- **Configuración AWS (SEG-02):** campaña 1, 15 de 16; la verificación `rds_force_ssl` dio falso negativo porque buscaba el parámetro solo con origen «user», y en PostgreSQL 16 RDS informa `rds.force_ssl = 1` con origen «system» aunque Terraform lo fije. El operador comprobó a mano valor 1 y grupo aplicado (`in-sync`). Campaña 2, con la verificación corregida (valor efectivo, todas las páginas y grupo aplicado): **16 de 16** (cifrado de S3 y RDS, solo TLS, bloqueo público, RDS no público, `rds.force_ssl`, Lambdas sin secretos en variables, retención de registros de 7 días, Bedrock sin registro de invocaciones, sin endpoint de Secrets Manager en la operación).

### 4.5 Rendimiento (§6.3.4)

Evidencia: `evaluacion/campanas/e90-latencia-1/` (`informe.md`, `latencia.jsonl`, `carga.jsonl`, `carga_corpus.json`). 12 trámites con el corpus cargado por la API (sin archivos sin incorporar).

- **Latencia de la consulta (IA-M08),** bloques alternados H1, S1 | S2, H2 | H3, S3 y verificación del perfil desplegado en cada respuesta (0 discrepancias). Línea de base de red: mediana 0,55 s, p95 0,95 s.

| Modelo | n | Mediana | p95 | Máximo | Errores | Arranques en frío | Resultado |
|---|---|---|---|---|---|---|---|
| Haiku 4.5 | 90 | 2,17 s | 3,58 s | 6,69 s | 0 | 1 | Cumple |
| Sonnet 4.6 | 90 | 2,25 s | 5,20 s | 8,88 s | 0 | 2 | Cumple |

- **Concurrencia interactiva (Haiku, en producción):**

| Operación | Nivel 1 (mediana / p95) | Nivel 5 | Nivel 10 | Errores |
|---|---|---|---|---|
| Consulta asistida | 2,32 / 3,07 s | 2,23 / 7,93 s | 2,11 / 7,76 s | 0 (sin 429) |
| Lectura del trámite | 0,59 / 0,97 s | 0,57 / 0,61 s | 0,54 / 0,59 s | 0 |

- **Procesamiento asíncrono** (tiempo desde la aceptación hasta el resultado): 1 documento 16,75 s; 5 documentos mediana 17,75 s, p95 88,94 s; 10 documentos mediana 289,11 s, p95 889,76 s, sin errores. El aumento en 5 y 10 **no es lentitud del procesamiento**: con el límite de 3, los trabajos excedentes esperan cupo y el reconciliador los admite cada 5 minutos. Caracteriza la configuración ensayada, no una capacidad máxima.

## 5. Desvíos y decisiones que el texto debe reflejar

| Tema | Qué pasó | Respaldo |
|---|---|---|
| Calificación IA-M06 | Los autores calificaron juntos una sola planilla; no se midió el acuerdo entre evaluadores | DO-2026-10-24-IA-M06-CONJUNTA, DIF-123 |
| Q12 (variante admitida) | Las respuestas de Sonnet que agregan plazos del extracto en inglés citado cuentan como correctas, según la variante aprobada al revisar el corpus | REV-E90-19, DO-2026-10-23-E90-MUESTREO |
| Límite de concurrencia 3 | Cuota de Lambda de la cuenta en 10 | Guía de la sesión, `limite_concurrencia = 3` |
| Métodos de medición corregidos | §6.3.2 (pico de concurrencia) y §6.3.3 (`rds_force_ssl`): falsos negativos del ejecutor; se conservaron las campañas 1 y se repitió con el método corregido | Análisis en cada campaña 1 |
| Token de Textract | Fallo de idempotencia entre sesiones; corregido antes de §6.3.2–6.3.4 | DIF-122 |
| Fecha de dos dígitos | Defecto de normalización que explica el único incumplimiento de §6.3.1; corregido después de la medición, sin volver a medir | `metricas.json`, DIF-124 |
| Drenaje | Al cerrar quedaban 32 archivos de medición sin incorporar (a propósito); sin trabajos ni ejecuciones activas | `semilla-e90-2026-10-24/cierre_sesion.md` |
| Infraestructura | Descartable: se creó para la sesión y se destruyó al terminar; la evidencia quedó en Git | DO-2026-10-21-E90A, DO-2026-10-24-RETIRO-TOTAL |

## 6. Propuesta de estructura para 6.5 Resultados y discusión

1. Párrafo de apertura: condiciones de ejecución (§3) y advertencia de alcance (sintético, configuración ensayada).
2. Resultados funcionales (§4.1), breve, remitiendo a 6.2.
3. Procesamiento inteligente: tabla de §4.2 (puede reutilizar las filas de la Tabla de criterios), discusión del incumplimiento de fecha con su causa, formatos (escaneado como el más débil), respuestas y abstención, adversariales, decisión de sustitución.
4. Confiabilidad (§4.3), seguridad (§4.4) y rendimiento (§4.5), cada uno con su tabla o cifras y la explicación de los desvíos.
5. **Tabla resumen** por dimensión con columnas: criterio · medido · cumple · evidencia (carpeta de campaña) · interpretación.
6. Cierre: qué demuestra y qué no (por ejemplo, que el incumplimiento de fecha es corregible en la normalización, sin afirmar que corregido cumpliría hasta medirlo).

## 7. Cambios en 6.6 Limitaciones

- **Corregir** la frase actual «Para reducir esta limitación, ambos autores realizan evaluaciones independientes y resuelven las discrepancias mediante la revisión de las fuentes.»: la calificación se hizo **en conjunto**, por lo que no se dispone de una medida de acuerdo entre evaluadores.
- **Agregar** (observadas en la ejecución):
  - concurrencia de procesamiento limitada a 3 por la cuota de la cuenta: los tiempos asíncronos de los niveles 5 y 10 reflejan esa espera;
  - dos verificaciones automáticas (pico de concurrencia y `rds_force_ssl`) dieron falsos negativos y se corrigieron durante la sesión; se informan ambas campañas;
  - el único incumplimiento (fecha) proviene de un defecto de normalización de fechas con año de dos dígitos, corregido después de la medición y no vuelto a medir;
  - la revisión de los autores del corpus fue por muestreo; el resto se validó con controles automáticos y una revisión de contraste;
  - el procesamiento asíncrono y la latencia se midieron en una única sesión y una única región.

## 8. Qué no afirmar

- Que EVD-01 quedó acreditado.
- Que el sistema «cumple todos los criterios» (la exactitud crítica de fecha no cumple).
- Que la fecha «cumple» o «cumpliría» con el normalizador corregido: se corrigió después de medir y no se volvió a medir.
- Que los resultados de §6.3 valen para documentación real o para cargas superiores a 10 solicitudes concurrentes.
- Nada sobre §6.4 que no esté en el texto de los autores.
