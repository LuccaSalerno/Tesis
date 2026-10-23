# Informe de la revisión candidata v2 del corpus E90 — 22/10/2026

Construida por Claude Code según P0 de DO-2026-10-22-CORPUS-REVISION, con el diseño P0–P16 aprobado por el equipo ([propuesta](Propuesta_Corpus_V2.md)). Datos y código: commit `2082a6e`, rama `codex/corpus-e90`. **Candidata, no congelada, sin revisión de autores.** No se ejecutaron modelos, embeddings, Textract, AWS ni Terraform.

## Qué se resolvió

| Hallazgo | Decisión | Resultado en la v2 |
|---|---|---|
| REV-E90-01, 05 | P14 | Afirmaciones atómicas y limitadas a lo preguntado; ninguna repite el fragmento completo. |
| REV-E90-02, 08 | P5, P6, P7 | Sin ID de inventario en el contenido, los metadatos ni los nombres de archivo; sin glosas de función ni «sintética no fiscal» en títulos; números documentales con formato propio. |
| REV-E90-03, 09 | P10 | Cuatro ambigüedades de contenido con justificación previa en el registro; se interpretan las etiquetas compuestas (COM-08). |
| REV-E90-04, 10 | P11 | Tres vectores distintos y visibles, sin aclaración neutralizante; cada objetivo contradice el oráculo. COM-08 (en T4) y FAC-06 entran en preguntas RAG. |
| REV-E90-06 | P15 | `fuente_contractual` real en los 13 contratos; pie sin «ARCA pendiente»; reporte ARCA en `cuit_candidatos.json`. |
| REV-E90-07 | P2, P4, P5 | Razones sociales verosímiles; en medición, cuatro formatos de fecha (`dd/mm/aaaa`, `dd-mm-aaaa`, `dd/mm/aa` y en letras), importes con y sin símbolo, moneda por código, símbolo o nombre, CUIT con y sin guiones; importes con semilla y sin secuencia. |
| REV-E90-11 | P12, P14 | Sin frase uniforme de plazo y modalidad; condiciones propias por tipo. Cinco preguntas sobre cláusulas contractuales; multidocumento con comparación real; abstenciones en seis contextos. |
| REV-E90-12 | P13 | Cuatro trámites (T1–T4) con mismo proveedor y moneda e importes relacionados; diferencia deliberada y registrada en T3. |
| REV-E90-13 | P9 | 20 de los 40 documentos no contractuales de medición tienen 2 páginas (12 de ellos PDF); 12 campos de medición se ubican en la página 2. |
| REV-E90-14 | P8 | MED_C con detalle de ítems, neto, IVA y total; MED_D en formato carta con los datos en la prosa. |
| REV-E90-15 | P2, P3, P7 | 12 sujetos y CUIT de medición y 6 de ajuste, disjuntos; nombres de archivo neutros. |
| — | P16 | Validador con los controles nuevos y una prueba negativa por cada uno. |

Sin cambios: 65 casos del plan (tipos, grupos, formatos, familias, casos difíciles y adversariales), cinco fuentes contractuales y sus adaptaciones, parámetros de simulación de capturas, reparto 10/8/6/6 y umbrales.

## Verificación ejecutada

| Comando / procedimiento | Resultado |
|---|---|
| `python -m herramientas.corpus_e90.validar` | `errores=0 congelado=no` ([evidencia](Verificacion_V2.json)). |
| `python herramientas/validar_inventario_e90.py --inventario oraculos/e90/inventario_candidato.csv` | Inventario válido: 50 de medición, 15 de ajuste, 3 adversariales, hashes coincidentes. |
| `python -m pytest -q -p no:cacheprovider tests` (entorno del corpus y entorno del backend) | 60 aprobadas, 1 omitida (render local). |
| Ídem con `E90_PRUEBAS_RENDER=1` | 58 aprobadas en `tests/corpus_e90`, sin omisiones. |
| `ruff check` y `ruff format --check` sobre herramientas y pruebas del corpus | Sin hallazgos. |
| Segunda generación en otra raíz limpia con el mismo código | Registros, fragmentos y consultas idénticos byte a byte; los 65 DOCX idénticos; campos e inventario idénticos salvo los hashes de PDF. Los PDF que produce LibreOffice cambian en bytes entre ejecuciones (mismas páginas y localizadores), por lo que los hashes registrados identifican esta generación y no son reproducibles. |
| Inspección visual | Hoja de contactos de las 121 páginas (30 ppp) para detectar superposiciones, recortes y páginas vacías: ninguno, salvo la tercera página de E90-M-CTR-10, que solo contiene el pie. Revisión a 50 ppp de 19 páginas de 10 documentos (ambiguos, adversariales, MED_C, MED_D, BASE_A, BASE_B y la captura fotografiada). La legibilidad del texto no se juzgó visualmente: la cubre el cotejo mecánico de etiqueta y valor del validador. |

El ensayo de CI limpio del backend no se repitió: esta rama no modifica el backend.

## Límites

- Las razones sociales y los 6 CUIT de ajuste son candidatos; su inexistencia no está verificada ([lista](Verificaciones_Pendientes_V2.md)).
- Los títulos comerciales siguen nombrando la clase en los casos no ambiguos (evidencia natural, no pista de construcción). La clasificación sin títulos se ejercita solo en los cuatro casos ambiguos y en las cartas MED_D, cuyo título va en la línea de referencia.
- Las cláusulas adaptadas conservan observaciones del banco aprobado como «documento ficticio» o «predio sintético E90»; no son ID de inventario y no se modificaron porque el banco no estaba en el alcance.
- El renderer cambió respecto de la v1 (LibreOffice 24.2.7.2): la paginación y los hashes dependen de él.
- Las degradaciones siguen siendo simulaciones digitales (DIF-E90-02).

## Cierre

- **Tarea:** revisión candidata v2 del corpus E90 (Etapa 4).
- **Requisitos cubiertos:** §6.3.1; IA-D01–IA-D08; preparación de IA-M02–IA-M07 e IA-M12; RC-P06.2. No se declaran métricas alcanzadas.
- **Decisiones delegadas tomadas:** ninguna.
- **Diferencias con la tesis:** DIF-E90-09 y DIF-E90-10 (provisionales); actualización de DIF-E90-06 y DIF-E90-07.
- **Pendientes:** verificaciones manuales, revisión de contraste de la v2 (P0), revisión de autores y congelación; campañas RC-P07.
