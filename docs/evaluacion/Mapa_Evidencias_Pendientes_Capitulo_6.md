# Evidencias que deberán recolectarse para terminar el capítulo 6

**Estado:** plantilla de planificación, **sin resultados observados**. No sustituye los contratos de aceptación. Se completa con evidencias auténticas y saneadas de las pruebas realizadas; no registrar documentos empresariales o prompts/outputs sensibles en logs, Git, CI, agentes ni demo.

| Sección | Evidencias a solicitar al equipo al ejecutar | Compuerta para poder escribir resultados |
|---|---|---|
| **6.2 Funcional** | Matriz RF-01…RF-26/RN-01…RN-15 → escenarios Gherkin/API/UI → estado por caso; ejecución y logs saneados, esperado/observado, commit y ambiente; cuatro recorridos EVD-01 y V1–V11; decisiones/controles asociados recuperables por API; pruebas negativas, carreras y cambio de versión confirmado | Suite implementada y ejecutada; no confundir código de test con test aprobado |
| **6.2 Cobertura** | Reporte `pytest-cov` u otro instrumento declarado; denominador (líneas/ramas), módulos y exclusiones, versión de código, cobertura realmente alcanzada y pruebas que la generan | Comparación real con **≥85 %**, sin inferir cobertura de RF a partir de líneas |
| **6.2 / RNF-07** | Capturas/registro de tareas con estados visibles, acciones permitidas y recuperación ante fallos en carga, validación, observación, aprobación y cierre; versión UI/rol | Evidencia visual y funcional, no solo API |
| **6.3.1 Corpus** | Inventario real de 50 medición y grupo de ajuste separado (10–15), hashes y plantillas; registro generador, casos difíciles, tres adversariales internos; oráculos precongelados de clasificación/extracción/procedencia | Corpus generado, inspeccionado y congelado, no plan CSV |
| **6.3.1 Clasificación/extracción** | Resultados brutos por documento/campo, errores/ausencias/no aplicables/invenciones, matrices de confusión, F1 y recall por tipo/categoría, exactitud campos críticos, localizadores PDF y DOCX | Métricas calculadas desde oráculos anteriores a la medición; reportar fallos |
| **6.3.1 RAG** | 30 consultas, 24 respondibles y 6 sin evidencia, fragmentos esperados/recuperados, Recall@5 y MRR, calificaciones independientes de ambos autores, discrepancias y consenso, corrección/citas/abstenciones | Rúbrica aplicada, sin contar parciales como correctas |
| **6.3.1 Modelos/latencia** | Series individuales (3 repeticiones de generativos según RC-P07), promedios y dispersión; versión modelo/perfil/temperatura/esquema; comparación embeddings con índices congelados; 30 consultas ×3 por modelo generativo, tiempos brutos, arranques en frío, errores/reintentos | Reglas de sustitución preestablecidas, sin eliminar muestras lentas selectivamente ni alterar umbrales |
| **6.3.2 Recuperación** | Pruebas controladas de trabajos demorados, fallos transitorios/definitivos, duplicaciones, idempotencia, entradas inválidas, huérfanos y reconciliación; estados técnicos/funcionales y registros correlacionados | Cada caso verifica sus efectos persistentes y ausencia de alteración funcional indebida |
| **6.3.3 Seguridad** | Matriz Tabla 3.II autorizados/denegados, por rol/acceso/cuenta; accesos directos por ID, consultas cruzadas, cifrado, secretos/retención autorizada, auditoría inmutable, RNF-08 en documentos/consultas y salidas inválidas, RNF-09 en logs y **historiales técnicos** | Configuración comprobada en entorno real de ensayo y reportes saneados; ningún marcador sensible registrado |
| **6.3.4 Rendimiento** | Carga con concurrencias 1/5/10, detalle de operaciones/entradas, configuración AWS, errores, respuestas, duración asíncrona y criterios de latencia de 6.3.1 | Reportar condiciones, mediana/p95, fallos y restricciones sin extrapolar a producción |
| **6.4 Escenario representativo** | **Autorización de organización/personas y tratamiento** cuando aplique, alcance y contexto agregados, roles, actividades y documentación permitida; observaciones de uso, dificultades, incidencias, capturas saneadas y consentimiento para publicar agregados | Ejecutado **separadamente** del corpus sintético y de la demo; ningún documento operativo original ingresa al ZIP o agentes. No atribuir umbrales sintéticos a datos reales |
| **6.5 Resultados y discusión** | Tabla real por dimensión: criterio / medido / cumple o no / evidencia / interpretación; selección de Haiku/Sonnet y Cohere/Titan con razones; desviaciones y decisiones tomadas; costos reales si se informan | No se completa con casilleros inventados; los casos no ejecutados se indican |
| **6.6 Limitaciones** | Limitaciones de diseño (muestra sintética, OCR indirecto, ataques acotados, acuerdo entre evaluadores, selección en mismo corpus, carga), más restricciones efectivamente observadas | No presentar hipótesis como observaciones ni generalizar fuera del entorno probado |

## Plantillas de registro (se completan luego)

- `plantilla_registro_ejecuciones.csv`: una fila por caso/ejecución. Los campos de resultados están **vacíos** deliberadamente.
- `plan_oraculo_30_consultas_rag_e90.csv`: 30 lugares reservados, sin preguntas ni respuestas inventadas.
- `plantilla_oraculo_campos_e90.csv`: solo el esquema para registrar valores esperados, presencia y procedencia.
- `docs/aceptacion/` y `docs/decisiones/` contienen los criterios y comparaciones autorizados que guían la ejecución.

## Responsabilidades y momentos de cierre

- **Agente de implementación:** implementa código, Gherkin/steps, tests, instrumentación, exportadores y plantillas, sin acceder a datos empresariales ni declarar pruebas que no ejecutó.
- **Equipo autor:** revisa/corrige oráculos antes de medir, observa resultados, revisa configuración de proveedores/regiones/retención, autoriza uso de datos reales para §6.4 fuera del repositorio y redacta conclusiones fieles.
- **Operador AWS autorizado:** revisa plan/costo e inicia manualmente cualquier recurso facturable, registra actividades y desmontaje seguro; nada de AWS desde CI/agentes.
- **Redacción final:** al disponer de evidencia se completa §6.4 y §6.5, y se ajusta §6.6. Antes de eso, sus apartados representan un diseño o están pendientes.
