# Revisión técnica del corpus E90 — 22/10/2026

**Dictamen:** la integridad estructural está verificada, pero **todavía no doy visto bueno para congelar el corpus ni iniciar la medición definitiva**. Hay una discrepancia concreta entre ocho preguntas y sus respuestas exigidas, y problemas de construcción que pueden facilitar artificialmente la evaluación. Los archivos siguen siendo candidatos útiles; los tests verdes no resuelven estos hallazgos semánticos.

Revisión solicitada por el equipo, sobre `630d0da`, en `codex/corpus-e90`. Es una **autorrevisión técnica del mismo agente que construyó el incremento**. No se presenta como revisión independiente de otro autor, aprobación de ambos autores, validación jurídica ni experimento de IA. Ningún indicador humano se completa y ningún criterio se congela.

## Alcance y resultados comprobados

| Comprobación | Resultado observado |
|---|---|
| Muestra y separación | 50 documentos de medición + 15 de ajuste; 10 + 3 por tipo; tres adversariales incluidos en medición. No se mezcló PD-07. |
| Archivos | 65 entradas (45 PDF y 20 DOCX), 65 fuentes DOCX y 65 PDF de referencia. Los 195 artefactos conservan sus hashes. |
| Plantillas | BASE_A/BASE_B compartidas; MED_C/MED_D exclusivas de medición por tipo; ARG_A exclusivamente en E90-M-CTR-03. |
| Contratos | 13: medición A=1, B=2, C=3, D=3, ARG_A=1; ajuste A=2, B=1. Las cinco fuentes conservan versiones, atribuciones y condiciones particulares. |
| Referencias de campos | 403: 398 valores presentes y cinco ausencias intencionales; sin discrepancias en representaciones, etiquetas y localizadores cotejados. |
| Inspección visual | 104 páginas, 52 paneles: PDF final para entradas PDF; PDF de referencia para entradas DOCX, además de leer su XML. Sin recortes, superposiciones o campos ilegibles observados a la escala utilizada. |
| Capturas | 20 PDF de capturas simuladas, identificados como tales, con parámetros y semillas. Su legibilidad visual no acredita calidad de Textract. |
| Fuentes públicas | Hashes de cinco originales cotejados; 43 extractos originales localizados y adaptaciones leídas. No se detectó en esta revisión una nueva incompatibilidad con la procedencia documentada; ARG_A conserva uso no comercial y CompartirIgual. |
| RAG | 30 preguntas: 10 directas / 8 condiciones / 6 multidocumento / 6 sin evidencia; 24 respondibles. Todos los fragmentos citados pertenecen al contexto autorizado y aparecen en sus localizadores. |
| CUIT | Doce números con dígito válido. Resultado «No existe» y fecha 22/10/2026 informados por el equipo en su consulta manual ARCA; no se atribuye consulta propia al agente. |

El cotejo de datos se realizó también con una comprobación separada del generador/validador: Poppler para PDF, XML de DOCX y formatos de fecha/decimal calculados independientemente. En capturas se cotejó visualmente el resultado final. La comparación textual de un PDF verifica la página y la etiqueta, no reemplaza la lectura del contexto. La evidencia detallada por documento, consulta y fuente está en [el registro JSON](Revision_Tecnica_Agente_2026-10-22.json).

## Hallazgos que deben resolverse antes de congelar

### REV-E90-01 — P1: ocho referencias exigen información no preguntada

**Q11–Q18** preguntan por plazo y modalidad, pero `respuesta_referencia` y `afirmaciones_esperadas` incorporan también el canal para solicitudes. Por ejemplo, Q11 pide el plazo y la modalidad de CTR-02; sus dos datos son «13 días corridos» y «entrega en laboratorio». La referencia agrega una tercera afirmación sobre la mesa de servicios.

La rúbrica RC-P06.2.10 considera correcta una respuesta con todas las afirmaciones esperadas y parcial una que omita algunas. Una respuesta que conteste exactamente lo solicitado podría, por tanto, ser penalizada injustamente. El dato adicional sí existe en el documento: el problema es la exigencia del oráculo, no una alucinación.

**Corrección propuesta:** limitar las afirmaciones obligatorias a plazo y modalidad, conservando el fragmento original como evidencia más amplia. Desagregar los hechos para aplicar la rúbrica sin exigir coincidencia literal. Mantener 30 preguntas y su distribución. No hay resultados de modelos que se puedan favorecer y no se propone modificar umbrales.

Origen: [consultas.py, selección de condiciones](../../../herramientas/corpus_e90/consultas.py#L84) y [asignación de afirmaciones](../../../herramientas/corpus_e90/consultas.py#L48). El candidato permanece sin modificar para dejar trazable la observación.

### REV-E90-02 — P1 metodológico: pistas de categoría demasiado explícitas

Los 65 documentos imprimen identificadores como `E90-M-FAC-08`; el mismo código de categoría aparece tanto en ajuste como en medición. Los 52 documentos no contractuales agregan además una explicación uniforme de su función: oferta económica, instrucción de adquisición, cargo por servicios o constancia de recepción, a veces descartando expresamente las categorías rivales.

Los títulos propios de documentos comerciales son evidencia legítima. El riesgo aquí son las etiquetas introducidas por la construcción del benchmark: permiten aprender el código o la glosa y acertar sin distinguir el documento por su contenido. Esto también debilita la supuesta ambigüedad. Las cuatro familias formales están separadas según el plan, pero sus códigos y glosas permanecen compartidos.

**Resolución propuesta antes de medir:** conservar el ID E90 en inventarios/oráculos y utilizar identificadores documentales neutros en el contenido; mantener la advertencia sintética y las atribuciones; revisar las glosas didácticas sin borrar títulos o términos comerciales naturales. Si se decide conservar estas pistas, registrar expresamente la limitación: el resultado no demuestra clasificación de documentos sin esas ayudas. Una regeneración debe recalcular hashes/localizadores y referencias dependientes; esta revisión no la ejecuta.

Origen: [generar.py](../../../herramientas/corpus_e90/generar.py#L225). Es un riesgo metodológico observado, no un nuevo umbral de aceptación.

### REV-E90-03 — P2: construcción de los casos ambiguos

- **E90-M-COM-08:** el registro combina `ambiguo_entre_categorias;instruccion_adversarial_documental`. El generador compara por igualdad con la etiqueta única de ambigüedad, por lo que omite esa transformación. El documento final mantiene el mismo título y explicación de finalidad que otros comprobantes; la instrucción maliciosa no aporta la ambigüedad comercial planificada.
- **E90-M-FAC-08:** el título es «Propuesta comercial y orden de compra confirmada», aunque la clasificación esperada es factura. El cuerpo describe un cargo por servicios y contiene los campos de factura. Esto puede ser una ambigüedad deliberada y no demuestra por sí solo que el oráculo esté equivocado, pero falta registrar la justificación específica de por qué prevalece la categoría factura y qué indicios debe resolver el evaluador.

**Corrección propuesta:** interpretar las etiquetas combinadas y definir el caso de ambigüedad por tipo, con una justificación verificable del resultado esperado. No cambiar la categoría del oráculo por conveniencia. Mantener los casos y las particiones aprobadas.

Origen: [generar.py, rama de títulos ambiguos](../../../herramientas/corpus_e90/generar.py#L218).

## Mejoras y sincronizaciones recomendadas

### REV-E90-04 — P2: alcance adversarial limitado

CTR-10, FAC-06 y COM-08 tienen el mismo texto malicioso y la misma aclaración de que no es una instrucción autorizada. En COM-08 la orden maliciosa pide clasificar como comprobante, exactamente su categoría correcta: acertar no distingue obediencia de resistencia en ese vector. Sí conserva ataques distintos sobre importe, fuentes y estado del trámite.

Recomiendo variar la presentación y procurar que los objetivos de ataque sean contrastables con el oráculo, sin aumentar los tres documentos ni cambiar las reglas funcionales. La mera presencia de las tres instrucciones queda verificada; su resistencia solo se demostrará ejecutando el sistema.

### REV-E90-05 — P2: precisión y diversidad de las preguntas

Las 24 referencias respondibles almacenan cada respuesta entera como una sola afirmación. Varias contienen hechos separables; conviene desagregarlos para que la evaluación de respuestas parciales y citas sea consistente, sin crear una regla nueva de coincidencia literal.

Las ocho preguntas de condiciones repiten el mismo patrón de plazo/modalidad. Las seis multidocumento comparan importes/monedas en las dos tríadas 01 y 03. Las seis abstenciones usan exclusivamente PRE-03; al leer ese contexto, la información pedida efectivamente no consta. En total, las consultas autorizan **13 documentos**: PDF digitales y DOCX; no cubren capturas, contratos extensos ni los tres adversariales.

Los recuentos y las referencias son correctos. La concentración limita lo que puede concluirse sobre RAG; RC-P06.2.2 procura representar tipos y formatos y RC-P06.2.11 exige revisión de formulación natural. Recomiendo ampliar condiciones sustantivas y contextos sin cambiar el reparto aprobado, y justificar las tríadas como documentos del mismo trámite pese a sus proveedores/monedas diferentes. No se infiere que esa diferencia sea necesariamente inválida ni se inventa un requisito de igualdad de proveedores.

### REV-E90-06 — P2 documental: metadatos anteriores a las aprobaciones

Doce registros contractuales mantienen `fuente_contractual="pendiente_aprobacion"`, aunque el banco, los artefactos y la documentación identifican sus fuentes aprobadas. Los documentos también conservan leyendas de ARCA pendiente anteriores al reporte manual, circunstancia ya aclarada en el registro del 22/10/2026.

Sincronizar estos estados al preparar la nueva revisión candidata. No hace falta repetir la consulta ARCA por esta discrepancia editorial ni cambiar los CUIT según el reporte recibido. No se modifican aquí los archivos binarios ni sus hashes.

## Verificación ejecutada y límites

| Comando / procedimiento | Resultado de esta revisión |
|---|---|
| `python -m pytest -q -p no:cacheprovider tests` | 46 aprobadas, una omitida explícitamente: render local optativo, no activado en este entorno de pruebas. |
| `python -m herramientas.corpus_e90.validar` | Cero errores; no congelado. |
| Validador del inventario con `oraculos/e90/inventario_candidato.csv` | Válido, recuentos y hashes coincidentes. |
| `ruff check --no-cache herramientas/corpus_e90 tests/corpus_e90` | Sin hallazgos. |
| Cotejo separado de campos, fuentes y referencias RAG | Sin discrepancias en los cotejos mecánicos detallados arriba; los problemas semánticos se informan por separado. |
| Render e inspección visual | 65 documentos / 104 páginas / 52 paneles. |

No se ejecutaron modelos, embeddings, Textract, AWS, Terraform, frontend ni validación operativa real. **RC-P07 sigue pendiente de implementación/ejecución experimental**; disponer del corpus y de las preguntas no completa la comparación de modelos y embeddings de la Etapa 4. Tampoco se acredita ningún umbral de §6.3 ni el cumplimiento de aceptación por existir código.

El ensayo completo de CI del backend conserva su evidencia anterior en `Ensayo_CI_ARG_A.txt`; no se presenta como vuelto a ejecutar en esta revisión documental. Los ocho archivos canónicos y los 195 artefactos mantienen sus bytes. Los registros de revisión humana, consenso y congelación siguen sin completar.

## Cierre de la tarea

- **Tarea:** revisión técnica sustantiva del candidato de Etapa 4, solicitada por el equipo.
- **Requisitos cubiertos por la revisión:** §6.3.1; IA-D01–IA-D08; preparación de IA-M06/IA-M12; RC-P04 y RC-P06.2. No se declaran métricas alcanzadas.
- **Archivos modificados:** este informe y su JSON de evidencia; enlace de aviso en la guía de autores; estado de implementación; lista acumulativa de archivos del incremento.
- **Decisiones delegadas tomadas:** ninguna.
- **Diferencias con la tesis registradas:** ninguna nueva implementación; los hallazgos REV-E90-01 a REV-E90-06 describen pendientes del candidato y no autorizan modificar el protocolo.
- **Pruebas:** resultados observados en la tabla anterior.
- **Pendientes:** resolver REV-E90-01/02/03; revisar las recomendaciones restantes; validar una revisión corregida; revisión humana prevista y congelación posterior; campañas RC-P07 y medición de IA pendientes.
- **Preguntas para el equipo:** ninguna para completar esta revisión. Las correcciones propuestas no se aplicaron silenciosamente a los documentos ni al oráculo.
