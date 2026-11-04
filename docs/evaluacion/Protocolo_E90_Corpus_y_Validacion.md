# Protocolo vigente E90 — corpus sintético y validación operativa diferenciada

**Decisión aprobada:** DO-2026-10-21-E90-CORPUS · 21/10/2026.  
**Estado:** método y cantidades decididos por el equipo; construcción de la muestra, congelación de oráculos, ejecución y resultados todavía pendientes. Este es un documento de trabajo **interno al repositorio**, no texto para copiar como resultado académico.

## 1. Dos vías de evaluación que no deben mezclarse

| Vía | Objetivo | Datos/documentos | Evidencias | Restricción |
|---|---|---|---|---|
| **6.3.1 — evaluación cuantitativa** | Medir clasificación, extracción, procedencia, RAG, adversariales y comparaciones de modelos | Únicamente **50 documentos sintéticos de medición**; grupo de ajuste sintético separado | Oráculos previos, mediciones brutas, métricas y fallos | No completar métricas a partir de pruebas de demo ni de documentos operativos reales |
| **6.4 — validación funcional/operativa** | Observar el funcionamiento integrado en un entorno operativo real | Documentación propia del entorno, manejada **fuera del repositorio y del agente**, con autorización y controles específicos | Resultados no confidenciales autorizados, operaciones verificadas, incidencias y límites | No adjuntar originales, extraer datos privados, publicar nombres ni confundir con el conjunto cuantitativo |

**Demo AWS E90A:** un tercer propósito operativo: demostración **descartable con corpus sintético PD-07** (C-v1, O-v1/O-v2 y F-v1/F-v2) y seed reproducible manual. No equivale ni reemplaza la medición de 50 ni la validación operativa real. La semilla está implementada en `atlas.herramientas.sembrar_demo`.

Ningún documento auténtico del escenario real ingresa en Git/GitHub, en este paquete, en herramientas de agentes, en CI ni en la demo sintética AWS. El uso operativo real exige consentimiento/permisos pertinentes, protección de datos y revisión RNF-03/RC-P09 de servicios/regiones/retención **antes de cualquier tratamiento**. La publicación se limita a resultados y evidencias previamente saneados/autorizados; no implica que deban difundirse originales ni detalles identificables.

## 2. Corpus de medición (50 documentos, no 66 ni 76–81)

| Tipo | Medición | Ajuste, aparte |
|---|---:|---:|
| Contrato | 10 | 2–3 |
| Presupuesto | 10 | 2–3 |
| Orden de compra | 10 | 2–3 |
| Factura | 10 | 2–3 |
| Comprobante | 10 | 2–3 |
| **Total** | **50** | **10–15** |

- **Tres documentos con *prompt injection*** se incluyen en esos **50** (no se agregan al total). Además de sus expectativas normales de clasificación/extracción tienen criterios adversariales propios alineados con RNF-08. Tres casos no demuestran resistencia universal.
- Incorporar, dentro de los 50, variabilidad de estructura, diseños, longitud, PDF digitales, escaneados o fotografías y DOCX; casos de información ausente/ambigua según pertinencia. No es obligatorio agregar otra batería de 16 archivos.
- Generar desde registros de referencia **predefinidos**, con datos totalmente ficticios; conservar fuentes/plantillas y trazabilidad documento ↔ valores ↔ localizadores. Los contratos se basan en modelos públicos adaptados, no redactados íntegramente por un LLM.
- **Separación:** no reutilizar documentos de ajuste como medición; al menos una plantilla por cada tipo documental se reserva **solo para medición**. No ajustar prompts/modelos sobre la muestra de medición ni reformular oráculos después de ver resultados.
- Formatos admitidos y sus validaciones se rigen por RC-P04 y la tesis, no por el CSV de inventario. Los documentos escaneados o fotografiados pueden ser PDF de imágenes. Preservar registro del método de digitalización.
- **No existe** grupo adicional de documentos públicos o empresariales de contraste para las métricas de 6.3.1. Se retiran las antiguas opciones A/B de RC-P06.1.

## 3. Consultas RAG y medición

Las **30 preguntas RAG** se mantienen: **24 con respuesta documental** y **6 sin respuesta suficiente**. El oráculo registra pregunta, clase, contexto autorizado, respuesta esperada o motivo de abstención, fragmentos y localizadores **antes** de la ejecución. Los dos autores califican independientemente las respuestas y conservan sus evaluaciones y consenso.

Conservar **sin alteraciones** todos los umbrales/criterios definidos en el documento contractual de aceptación (§5.2) y en la tesis: F1 macro clasificación, recall de clases, F1 y exactitud de extracción, procedencia PDF/DOCX, Recall@5/MRR, calidad y respaldo de RAG, abstenciones, latencia, comparación de modelos y embeddings. No inventar mediciones ni reducir umbrales en función del resultado.

## Plan de construcción adjunto (sin cambiar el protocolo aprobado)

`Plan_Diseno_Corpus_E90.md` y `plan_diseno_corpus_e90.csv` ofrecen una distribución de trabajo (50 de medición, **15 de ajuste propuestos**, tres adversariales dentro de los 50). **No son inventario de documentos existentes ni congelación de oráculos**. La decisión aprobada sigue siendo 10–15 de ajuste hasta que el equipo confirme la concreción del grupo.

## 4. Archivos de trabajo y congelación

- `plantilla_inventario_e90.csv`: **solo encabezado**, no 50 documentos ya construidos. Debe completarse con los archivos *reales sintéticos generados*, uno por fila, con tipo, partición, plantilla, hash, modalidad, marcas adversariales y ruta. No incluir archivos de procedencia operativa real.
- `herramientas/validar_inventario_e90.py`: valida estructura, recuentos, particiones, plantilla exclusiva por tipo, tres adversariales y SHA-256 de los archivos listados. No compara respuestas de IA ni garantiza calidad semántica de los documentos.
- Oráculos de campos, clasificación, procedencia, RAG y adversariales: **por construir y congelar**; no rellenar con resultados inventados. Conservar inputs/versiones, scripts, configuración experimental, métricas brutas, fallos y parámetros por campaña.
- La separación entre **PD-07 (cinco PDFs actuales)** y medición evita reclamar que ese corpus candidato ya cumple los 50 documentos.
- El CUIT ficticio usado en PD-07 continúa **pendiente de consulta ARCA**. No declararlo verificado hasta completar el registro.

## 5. Condiciones antes de ejecutar

1. Congelar inventario, plantillas y oráculos de la medición sin reutilizar entradas de ajuste.
2. Ejecutar el verificador del manifiesto y contrastar manualmente contenido real de los documentos y procedencia; el verificador solo chequea estructura/hashes.
3. Registrar fecha, commit, versiones de modelos/perfiles, configuración de OCR/chunks, y parámetros para permitir repetir el experimento.
4. Mantener resultados independientes de §6.3 y §6.4. Si una ejecución falla o no alcanza un umbral, conservar la evidencia del fallo; no retocar corpus/umbrales.
5. Las ejecuciones AWS requieren intervención humana, plan y presupuesto aprobados. El desarrollo y tests locales no requieren desplegar AWS.
6. El `main.pdf` más reciente incorporado ya contiene el protocolo de 50 documentos para §6.3.1; la integración LaTeX de la propuesta nueva de 6.0–6.3 y la redacción de §6.4–§6.6 con evidencias reales corresponden a los autores. No atribuir al documento final actividades todavía no realizadas.
