# Diseño operativo de la muestra E90 — plan, no corpus construido

> **17/11/2026 (DO-2026-11-17-DATASETS):** el corpus se construyó, congeló y midió. Sus documentos, oráculos, generadores y el plan de 65 filas (`generadores/evaluacion/plan.csv`) están en [atlas-tesis-datasets](https://github.com/LuccaSalerno/atlas-tesis-datasets); el corpus congelado, en el historial de Git de este repositorio (último commit que lo tiene: `eab2954`). Las rutas de este documento son históricas.

**Estado 21/10/2026:** diseño de filas y cobertura preparado para generación y revisión. **No hay 50 documentos de medición ni 15 de ajuste generados y validados en este ZIP.** El protocolo vigente de aceptación sigue admitiendo **10–15 documentos de ajuste (2–3 por tipo)**; para la implementación se propone concretarlo en **15 (3 por tipo)**, elección dentro del rango que debe confirmar el equipo antes de congelar el inventario. No cambiar la tesis para decir 15 hasta decidirlo y construirlos.

**Adenda 22/10/2026 — DO-2026-10-22-CORPUS-ARG-A:** el equipo aprobó sustituir únicamente la plantilla de E90-M-CTR-03, de CTR-BASE_A a CTR-ARG_A (CPAU). Los 65 casos, tipos, formatos, particiones, dificultades y adversariales se conservan. Las cuatro familias iniciales siguen representadas; ARG_A es exclusiva de medición. El CSV sigue siendo diseño; los archivos construidos y sus referencias se encuentran en el inventario candidato separado. Esta adenda no modifica el protocolo E90.

## Cantidades y particiones que no se modifican

| Grupo | Contrato | Presupuesto | Orden de compra | Factura | Comprobante | Total |
|---|---:|---:|---:|---:|---:|---:|
| Medición aprobada | 10 | 10 | 10 | 10 | 10 | **50** |
| Ajuste propuesto | 3 | 3 | 3 | 3 | 3 | **15** |

`plan_diseno_corpus_e90.csv` contiene **65 especificaciones de casos**, no archivos existentes; nunca pasarlo al validador como si fuera `plantilla_inventario_e90.csv`. Al generar efectivamente cada documento debe crearse una fila con ruta real, formato comprobado, SHA-256 y referencias en el **inventario real**, que se valida con `herramientas/validar_inventario_e90.py`.

## Diseño de variabilidad

- Cada uno de los cinco tipos incluye PDF digital, DOCX, PDF escaneado y PDF fotografiado dentro de sus diez ejemplos de medición. Estas proporciones son una **propuesta de distribución**, no un nuevo requisito del contrato.
- Se proponen plantillas parcialmente compartidas con ajuste (`BASE_A`, `BASE_B`) y plantillas reservadas exclusivamente a medición (`MED_C`, `MED_D`) por tipo; **no exponer las exclusivas al ajuste**.
- Los casos difíciles están identificados **a nivel de intención** en `casos_dificiles_planificados`: ambigüedad categorial, ausencias de campos, contratos extensos y escaneos degradados. Falta producirlos e inspeccionar que realmente expresen ese fenómeno.
- **Exactamente tres** casos tienen la marca `prompt_injection=si` entre los **50 de medición**, distribuidos entre tipos. No agregar otros tres fuera de la muestra. También se mantienen las pruebas adversariales de consulta por separado, sin generar documentos extra.
- Cada documento parte de un **registro de referencia previo**, con valor esperado y localizador verificable; las ausencias intencionales se fijan antes de consultar modelos. Un campo `no_aplicable` no se convierte en una omisión. Contratos construidos adaptando modelos públicos con datos ficticios, no generados íntegramente por LLM.
- Las categorías ambiguas requieren una etiqueta objetiva previa y revisión de ambos autores. Para escaneos/fotos registrar método y grado real de degradación (no basta la etiqueta del plan).
- No copiar archivos del corpus PD-07 a la partición de medición como si cumplieran estos casos; PD-07 se mantiene separado para demo/EVD.

## Procedimiento que convierte el plan en corpus congelado

1. Confirmar o ajustar el plan de **15 documentos de ajuste** dentro del rango vigente; registrar la decisión. Resolver CUIT ficticios conforme al control ARCA aplicable, sin copiar datos de una entidad real como si fueran ficticios.
2. Diseñar los registros fuente, campos aplicables, ausentes y críticos por tipo; fijar expectativas y localizadores antes de generar cada documento.
3. Construir los documentos en formatos reales y las capturas/escaneos, verificando manualmente su contenido y calidad. Registrar licencia/plantilla para modelos contractuales públicos adaptados.
4. Completar el inventario real con archivos `corpus/…`, hashes, plantillas, partición y las tres marcas adversariales. Nunca llenar el inventario con rutas hipotéticas.
5. Construir los oráculos de campos, clasificación, procedencia y el de **30 consultas RAG** (24 respondibles, 6 para abstención). Ambos autores revisan y resuelven discrepancias antes de congelar.
6. Validar inventario, archivos y oráculos; congelar versión/commit y prohibir el ajuste con elementos de medición. Conservar fallos sin cambiar referencias después de medir.

**Compuerta:** hasta completar 1–6, la sección 6.3.1 dispone de **metodología**, pero no de corpus, resultados ni demostración de cumplimiento. La validación §6.4 se realiza por una vía independiente, sin documentación empresarial real en este repositorio.
