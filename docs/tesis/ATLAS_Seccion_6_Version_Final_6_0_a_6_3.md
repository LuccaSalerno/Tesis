# 6 Validación y resultados

La validación de ATLAS examina el cumplimiento de los requerimientos y el comportamiento del prototipo en el circuito documental, el procesamiento inteligente y las operaciones del sistema. Integra pruebas funcionales, evaluaciones técnicas y un escenario de uso representativo. Los resultados se contrastan con criterios de aceptación previamente definidos y se analizan junto con las limitaciones de la evaluación.

## 6.1 Estrategia de validación

La estrategia distingue la verificación funcional, la medición de cobertura de código, la evaluación cuantitativa del procesamiento inteligente y las pruebas de confiabilidad, seguridad y rendimiento. La validación en un escenario representativo complementa estos ensayos mediante la observación del recorrido integrado del trámite, sin reemplazar las mediciones específicas.

Los casos funcionales se vinculan con los requerimientos y las reglas del dominio. Las evaluaciones técnicas utilizan datos de referencia, condiciones de ejecución identificables y criterios de aceptación establecidos antes de las mediciones. La interpretación considera la versión del software, el entorno, las configuraciones y los conjuntos de datos empleados. La evidencia comprende resultados de pruebas, métricas, registros técnicos y observaciones del escenario representativo. Los resultados y su discusión se presentan en la Sección 6.5.

## 6.2 Pruebas funcionales y automatizadas

La verificación funcional comprende pruebas unitarias, de integración y de aceptación sobre los comportamientos definidos en la Sección 3.3. Las pruebas de aceptación se estructuran mediante escenarios de desarrollo guiado por comportamiento (*Behavior-Driven Development*, BDD), expresados en Gherkin con la secuencia Dado–Cuando–Entonces. Cada escenario establece precondiciones, acciones y resultados esperados, incluidos los rechazos ante operaciones no autorizadas o incompatibles con el estado del trámite.

La siguiente tabla relaciona los grupos funcionales con los requerimientos y los comportamientos evaluados.

| Grupo funcional | Requerimientos relacionados | Comportamiento evaluado |
|---|---|---|
| Acceso y administración | RF-01, RF-02, RF-24 y RF-25 | Autenticación, permisos por trámite, administración de cuentas y acceso restringido a información documental. |
| Trámites y versiones documentales | RF-03 a RF-07 y RF-26 | Creación y cancelación de trámites, carga pendiente de confirmación, detección de posibles versiones, incorporación, descarte e inmutabilidad del historial. |
| Clasificación, extracción y validación | RF-08 a RF-12 | Sugerencias automáticas, correcciones humanas, procedencia de los valores y conservación de las versiones de origen. |
| Consulta y consistencia | RF-13 a RF-16 | Consultas acotadas por autorización, vínculos propuestos y confirmados, y reglas aplicadas sobre información validada. |
| Revisión, auditoría y cierre | RF-17 a RF-23 | Propuesta y ejecución del flujo, asignaciones, decisiones, trazabilidad, reconstrucción del historial y firma digital simulada. |

Las pruebas sobre la interfaz complementan las verificaciones realizadas mediante la interfaz de programación de aplicaciones (API). En particular, se inspeccionan los recorridos de carga, validación, aprobación, corrección y cierre para comprobar que el estado actual, las acciones disponibles y las alternativas de recuperación ante errores resulten identificables dentro del propio recorrido, conforme a RNF-07.

### Verificación de la cadena de evidencia documental

Esta verificación se centra en la posibilidad de reconstruir la relación entre los documentos y sus versiones, los valores sugeridos y validados con su procedencia, las ejecuciones de reglas de consistencia, las tareas, los ciclos de revisión y las decisiones humanas. Cada decisión se vincula con el ciclo y el conjunto de versiones que considera; las validaciones, en cambio, permanecen asociadas con versiones documentales concretas. También se comprueba que puedan recuperarse los controles efectivamente considerados al decidir, sin sustituirlos por ejecuciones posteriores de las mismas reglas.

La verificación comprende cuatro recorridos independientes, vinculados con RN-09, RN-12 y RN-13: una aprobación seguida de la incorporación confirmada de una nueva versión antes del cierre; una observación que da lugar a una corrección documental y a una nueva revisión; la subsanación de una observación sin modificar el archivo; y el intento de resolver una tarea que permanece abierta en un ciclo anterior. Los escenarios comprueban la conservación de decisiones e intervenciones previas, la ausencia de transferencia automática de aprobaciones y el rechazo de acciones desactualizadas. Incluyen la revalidación de las versiones modificadas, la preservación de validaciones sobre versiones que no cambian y la actualización de los controles pertinentes. Las advertencias automáticas no reemplazan la decisión de una persona.

El cumplimiento de estos recorridos se comprueba, mediante la API autenticada y autorizada, tanto sobre el resultado de las operaciones como sobre las relaciones y los estados recuperables después de cada intervención. Se verifican asimismo los permisos de consulta de la evidencia, la integridad del historial y las restricciones del cierre mediante firma simulada. Una respuesta HTTP satisfactoria o la mera existencia de entidades en la base de datos no constituyen, por sí solas, evidencia suficiente de cumplimiento. La documentación de los escenarios identifica los documentos sintéticos, las condiciones iniciales y los resultados esperados, de modo que las comprobaciones sean repetibles.

### Cobertura de las pruebas automatizadas

La cobertura de código se mide mediante las pruebas automatizadas, identificando los componentes incluidos y las exclusiones justificadas. El criterio de aceptación establece una cobertura mínima del 85 %. Este indicador se distingue de la cobertura de requerimientos y de las métricas de calidad del procesamiento inteligente: un porcentaje elevado de código ejercitado no demuestra por sí solo la corrección de los comportamientos evaluados. Los resultados de las pruebas y la cobertura obtenida se presentan en la Sección 6.5.

## 6.3 Pruebas técnicas y no funcionales

La evaluación técnica complementa las pruebas funcionales mediante mediciones de calidad del procesamiento inteligente y ensayos de confiabilidad, seguridad y rendimiento. Los procedimientos verifican los requerimientos no funcionales aplicables de la Sección 3.3.5 y establecen, además, criterios de aceptación propios para el procesamiento inteligente.

### 6.3.1 Evaluación de los componentes de procesamiento inteligente

La evaluación comprende la clasificación documental, la extracción de información, la procedencia de los valores, la recuperación semántica y las respuestas de la consulta asistida. Las mediciones utilizan referencias conocidas, definidas antes de observar las salidas de los modelos.

**Conjunto documental de evaluación.** El corpus de medición comprende 50 documentos sintéticos, diez de cada tipo admitido: contrato, presupuesto, orden de compra, factura y comprobante. Se construyen a partir de registros ficticios con valores y localizadores de referencia, utilizando distintas plantillas, estructuras y formatos. Los contratos se basan en modelos públicos adaptados con datos ficticios, sin generar íntegramente su contenido mediante un modelo de lenguaje. Se incluyen archivos PDF digitales, PDF escaneados o fotografiados y DOCX, con variaciones en diseño, longitud y calidad de captura.

Dentro de esos 50 documentos se incluyen casos ambiguos entre categorías, campos intencionalmente ausentes, contratos extensos, escaneos de baja calidad y tres documentos con instrucciones maliciosas embebidas. Las categorías esperadas de los casos ambiguos y las ausencias de campos se fijan en las referencias antes de medir. No se agregan documentos por estas condiciones.

Se utiliza por separado un grupo de ajuste de 10 a 15 documentos sintéticos, con dos o tres ejemplares por tipo, para configurar instrucciones y esquemas de procesamiento. Ningún documento de ajuste se incorpora a la medición y al menos una plantilla de cada categoría se reserva exclusivamente para esta última. La evaluación de consulta comprende 30 preguntas sobre el conjunto autorizado: 24 con respuesta documental y seis sin evidencia suficiente. Sus respuestas y fragmentos de referencia se establecen previamente. Ambos autores califican las respuestas de manera independiente y resuelven las discrepancias mediante revisión conjunta.

**Métricas y criterios de aceptación.** La siguiente tabla reúne los indicadores y los criterios de aceptación.

| Capacidad | Indicador | Criterio de aceptación |
|---|---|---|
| Clasificación documental | Exactitud global, precisión, exhaustividad y F1 por categoría; F1 macro | F1 macro ≥ 0,90 y exhaustividad ≥ 0,80 en cada categoría |
| Extracción de información | Precisión, exhaustividad y F1 por campo y tipo documental | F1 ≥ 0,85 en cada tipo documental |
| Campos críticos | Exactitud de importe total, fecha, número documental y CUIT de la contraparte | Exactitud ≥ 0,90 sobre valores esperados presentes |
| Valores inventados | Proporción de valores extraídos sin respaldo documental | ≤ 5 % del total de valores extraídos |
| Procedencia en PDF | Proporción de valores con referencia a la página correcta | ≥ 90 % de los valores evaluados |
| Procedencia en DOCX | Corrección de localizadores estructurales | Evaluación diferenciada, sin umbral de paginación |
| Recuperación semántica | Recall@5 y rango recíproco medio (MRR) | Recall@5 ≥ 0,80; MRR como indicador complementario |
| Respuestas asistidas | Corrección y respaldo documental de las respuestas | ≥ 80 % de respuestas correctas y ≥ 90 % de afirmaciones sustantivas respaldadas |
| Abstención | Abstenciones correctas ante consultas sin información suficiente | ≥ 80 % |
| Contenido adversarial | Alteraciones indebidas causadas por instrucciones documentales | Ninguna en los tres documentos evaluados |
| Latencia de consulta | Mediana y percentil 95 del tiempo de respuesta | Mediana ≤ 5 s y percentil 95 ≤ 10 s |

Para la clasificación se construye una matriz de confusión y se calculan las métricas por categoría, además del F1 macro como promedio no ponderado de los cinco valores de F1. La extracción compara los valores obtenidos con las referencias, después de normalizar fechas, importes e identificadores fiscales. Un valor correcto constituye un verdadero positivo; uno incorrecto se contabiliza simultáneamente como falso positivo y falso negativo, porque informa un dato erróneo y no recupera el esperado. Un valor omitido cuenta como falso negativo y uno inventado, sin respaldo documental, como falso positivo. Los campos definidos como no aplicables no generan un falso negativo por su ausencia, aunque sí se registra un falso positivo cuando el sistema les atribuye indebidamente un valor. A partir de estos recuentos se calculan precisión, exhaustividad y F1 por campo y tipo documental. Para los campos críticos, la exactitud se calcula respecto de los valores esperados presentes; una omisión o un valor incorrecto no constituye un acierto.

La procedencia se comprueba comparando los localizadores obtenidos con las ubicaciones de referencia. En los PDF se exige la página correcta y se consideran fallos las referencias ausentes o incorrectas. En los DOCX se evalúan por separado los localizadores estructurales disponibles —sección, párrafo o fragmento—, sin aplicar el umbral de páginas de PDF. Los resultados de archivos digitales y escaneados se diferencian para observar el efecto conjunto del reconocimiento óptico y la extracción; no se calcula una tasa directa de errores de caracteres o palabras ni se atribuyen todos los fallos exclusivamente al reconocimiento óptico.

La recuperación semántica se evalúa sobre las preguntas con fragmentos relevantes preidentificados. Recall@5 representa la proporción de fragmentos relevantes recuperados entre los cinco primeros resultados, mientras que MRR considera la posición del primer fragmento relevante. Las seis preguntas sin respuesta documental se excluyen de ambos cálculos y se utilizan para medir la abstención. Las respuestas generadas se clasifican como correctas, parciales o incorrectas, admitiendo equivalencia de significado sin exigir coincidencia literal. Solo las correctas cuentan para el umbral del 80 %; las parciales no se computan como aciertos. De manera independiente se verifica si cada afirmación sustantiva está respaldada por los fragmentos citados. Una abstención se considera correcta cuando reconoce la insuficiencia de evidencia sin inventar información ni recurrir a fuentes no autorizadas.

Los tres documentos adversariales permiten examinar si las instrucciones incorporadas al contenido alteran la clasificación, la extracción o las respuestas, o inducen cambios funcionales no autorizados. Este ensayo no constituye una demostración de resistencia ante cualquier instrucción maliciosa. La evaluación de instrucciones adversariales incluidas en consultas y de salidas estructuradas inválidas se complementa en la Sección 6.3.3. Las reglas de consistencia documental quedan fuera de las métricas de los modelos: se verifican funcionalmente sobre datos confirmados por una persona, conforme a la Sección 6.2.

**Comparación de modelos.** Se comparan Claude Haiku 4.5 y Claude Sonnet 4.6 utilizando los mismos documentos, contenido extraído, instrucciones, esquemas y criterios; para la generación de respuestas ambos reciben idénticos fragmentos recuperados. Clasificación, extracción y consulta asistida se miden en tres repeticiones por modelo, con parámetros de generación fijos y comparables y alternancia del orden de ejecución. Cada métrica se calcula sobre el conjunto completo en cada repetición, conservando sus resultados individuales, promedio y dispersión. Las decisiones de sustitución utilizan los promedios, no la mejor ejecución.

El criterio de sustitución, fijado antes de las mediciones, establece que Sonnet 4.6 reemplaza a Haiku 4.5 cuando alcanza un criterio de aceptación incumplido por este sin introducir nuevos incumplimientos, o cuando mejora en al menos cinco puntos porcentuales absolutos el F1 macro de extracción —promedio no ponderado de los cinco tipos documentales— y mantiene los límites de calidad y latencia. En los demás casos se conserva Haiku 4.5.

La comparación de Cohere Embed Multilingual v3 y Amazon Titan Text Embeddings V2 mantiene los mismos documentos, fragmentos, consultas, filtros de autorización y cinco resultados recuperados. Cada modelo dispone de una indexación propia y congelada, con vectores de 1024 dimensiones y búsqueda exacta por similitud coseno. El criterio equivalente para la recuperación establece que Titan reemplaza a Cohere únicamente si mejora Recall@5 en al menos cinco puntos porcentuales absolutos sin incumplir el mínimo establecido.

La latencia de consulta se mide mediante las 30 preguntas, repetidas tres veces por cada modelo generativo, para un total de 90 solicitudes por modelo. Se registra el tiempo completo entre la recepción de la solicitud y la respuesta, incluidos los arranques en frío. La mediana y el percentil 95 se calculan sobre las respuestas completadas, sin excluir selectivamente observaciones lentas; los errores y los reintentos se informan por separado. Las configuraciones experimentales, los datos de referencia y los criterios de sustitución se fijan antes de las mediciones y se mantienen sin cambios durante la evaluación.

La comparación y la selección de los modelos utilizan el mismo conjunto documental. Por ese motivo, sus resultados no constituyen una evaluación independiente del desempeño de la alternativa elegida.

### 6.3.2 Confiabilidad y recuperación del procesamiento asíncrono

La confiabilidad del procesamiento asíncrono se examina mediante fallos e interrupciones controlados, en relación con RNF-05 y RNF-06. Los escenarios contemplan trabajos demorados, fallos transitorios de servicios externos, errores definitivos, repeticiones de una misma operación y recuperación de inicios no confirmados.

Ante un procesamiento demorado se comprueba que el trabajo conserve un estado técnico consultable —pendiente, en proceso, completado o fallido, según corresponda— y que el usuario pueda abandonar la pantalla y regresar sin perder su seguimiento. En los fallos transitorios se observa el mecanismo de reintento y se verifica que las ejecuciones repetidas no dupliquen documentos, versiones ni resultados. Para los errores definitivos se verifica la identificación de la causa y de una alternativa de recuperación, así como la ausencia de reintentos indefinidos y de alteraciones indebidas del estado funcional del trámite. Las entradas inválidas, como formatos no admitidos o metadatos ausentes, se rechazan con indicación de la causa y de la acción de recuperación, sin crear documentos ni versiones.

Se comprueba asimismo la ausencia de entidades huérfanas y la recuperación de inicios fallidos o no confirmados mediante el mecanismo de reconciliación de trabajos. La evidencia comprende estados y relaciones consultables, registros de cada intento, errores y referencias de correlación. Se distingue en todo momento el estado técnico del procesamiento del estado funcional del trámite: un fallo del primero no constituye por sí mismo una transición válida del segundo.

### 6.3.3 Seguridad, privacidad y trazabilidad técnica

La evaluación de seguridad comprende las verificaciones de autorización, cifrado y gestión de secretos, destinos de procesamiento, integridad de la auditoría y protección de la información sensible, conforme a RNF-01 a RNF-04 y RNF-08 a RNF-09.

La verificación comprende las operaciones de la matriz de la Tabla 3.II con roles permitidos y denegados, con y sin acceso al trámite, y con cuentas habilitadas y deshabilitadas. Las solicitudes incluyen además intentos de acceder directamente a documentos y versiones mediante sus identificadores y consultas asistidas que buscan recuperar información de trámites ajenos. El criterio de aceptación exige obtener el resultado esperado en todos los casos: las operaciones autorizadas se completan y las no autorizadas se rechazan, sin exposición documental ni modificaciones funcionales indebidas.

Se inspecciona la configuración del entorno para comprobar el cifrado de las comunicaciones, la provisión de credenciales fuera del código y la correspondencia entre los destinos y las condiciones de retención realmente utilizados y los registrados para el tratamiento de documentos. La integridad de la auditoría se verifica mediante intentos de modificar o eliminar eventos desde las operaciones funcionales ordinarias, seguidos de la comprobación de que sus atributos permanecen intactos.

El tratamiento del contenido no confiable se evalúa con instrucciones adversariales incorporadas en documentos y consultas. Se comprueba que no habiliten acciones privilegiadas sobre permisos, versiones, tareas o estados del trámite, y que las salidas estructuradas inválidas se rechacen o identifiquen para revisión. Las consultas adversariales no amplían el corpus de 50 documentos definido para la evaluación cuantitativa.

Para comprobar la protección de los registros técnicos se emplean marcadores identificables en datos sintéticos. Se examinan registros de aplicación, trazas, errores e historiales de procesamiento, incluidos los casos de fallo y reintento. El criterio de aceptación exige que no aparezcan contenido documental ni entradas o salidas sensibles de los servicios de inteligencia artificial, sin perder los identificadores operativos necesarios para reconstruir la secuencia técnica.

### 6.3.4 Rendimiento y comportamiento operativo

El rendimiento de ATLAS se examina mediante los tiempos de respuesta de las operaciones interactivas y la duración de los trabajos de procesamiento documental. Ambas mediciones se consideran por separado debido a las diferencias entre la respuesta inmediata de la API y la ejecución asíncrona.

Se utilizan escenarios de una, cinco y diez solicitudes concurrentes sobre operaciones representativas de consulta y procesamiento. En cada ejecución se identifican las condiciones de infraestructura y los datos utilizados, junto con las operaciones completadas, los errores, las latencias y la duración de los trabajos.

Para el procesamiento documental se mide el intervalo entre la aceptación del trabajo y la disponibilidad de su resultado técnico. Esta medición permite caracterizar los efectos de la concurrencia sobre los tiempos de procesamiento y la continuidad de los estados observables.

La consulta asistida utiliza los criterios de latencia establecidos en la Sección 6.3.1, considerando el tiempo completo desde la recepción de la solicitud hasta la entrega de la respuesta. Las mediciones incluyen los tiempos de inicialización que afectan la operación, sin excluir selectivamente observaciones desfavorables.

Los resultados caracterizan el comportamiento del prototipo bajo las condiciones ensayadas y se interpretan en relación con la configuración utilizada, sin extrapolar su desempeño a niveles de carga o condiciones productivas no evaluadas.
