# Guía completa de revisión por los autores — corpus E90

Fecha de preparación: 22/10/2026. Rama `codex/corpus-e90`, estado de datos del commit `b201471`. Este material facilita la revisión ya aprobada: no cambia el protocolo, los documentos ni sus oráculos. **Todo sigue candidato y pendiente de revisión de autores.** Las casillas y observaciones se dejan sin completar; no representan una revisión ejecutada.

**Qué revisar ahora:** los 65 archivos de entrada (50 medición + 15 ajuste, 13 por tipo), sus 403 referencias de campos, clasificación/procedencia, condiciones y 30 preguntas RAG. Son 45 PDF y 20 DOCX; los PDF digitales de referencia suman 104 páginas. Hay 20 PDF de capturas simuladas. Los 130 auxiliares no aumentan la muestra y no necesitan una segunda aprobación como si fueran casos distintos.

La revisión de documentos/oráculos y la resolución de discrepancias antes de congelar están previstas en el procedimiento del plan (paso 5), IA-D y RC-P06.2. IA-M12 fija criterios/oráculos antes de medir. La **calificación independiente de respuestas de IA** corresponde a IA-M06 y se hará después de ejecutar; no confundirla con esta revisión previa.

**Actualización de revisión técnica (22/10/2026):** el agente revisó los 65 documentos, sus 104 páginas, campos, fuentes y consultas. [Informe y hallazgos](Revision_Tecnica_Agente_2026-10-22.md): integridad estructural verificada, **sin visto bueno todavía para congelar/medir** por discrepancias semánticas y riesgos metodológicos pendientes. Es autorrevisión técnica; no completa la revisión de los autores.

## Orden recomendado y archivos que hay que abrir

| Paso | Documento/archivo | Qué revisar |
|---|---|---|
| 1 | [Plan de diseño y adenda ARG_A](../Plan_Diseno_Corpus_E90.md); [protocolo E90](../Protocolo_E90_Corpus_y_Validacion.md) | Entender 50+15, separación ajuste/medición y alcance sintético. El protocolo mantiene antecedentes de cuando el corpus no estaba construido: las decisiones posteriores concretan 15 y ARG_A. |
| 2 | [Decisiones técnicas: RC-P04, RC-P06.2, DO-CORPUS y ARG_A](../../decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md); [aceptación, apartados 5.1 y 5.2](../../aceptacion/Contrato_Aceptacion_Integral_Reconstruccion_PFI_2026-10-20_v1_1.md) | Campos por tipo, preguntas, referencias, rúbrica y umbrales existentes. No redefinirlos al revisar. La tesis vigente sigue en [main.pdf](../../tesis/main.pdf) (§6.3.1). |
| 3 | [Cuaderno de los 65 documentos](Cuaderno_Revision_Documentos_E90.md) | Abrir cada entrada y cotejar los valores/localizadores de su ficha. Dejar observaciones y resolución, con nombres/fecha/commit. |
| 4 | [Cuaderno de las 30 preguntas](Cuaderno_Revision_Consultas_RAG_E90.md) | Revisar Q01–Q30, respuestas, contexto y todos los fragmentos; seis abstenciones. No puntuar respuestas de IA todavía inexistentes. |
| 5 | [Cuaderno comparado de las cinco fuentes](Cuaderno_Revision_Fuentes_Contractuales_E90.md); [Fuentes públicas y versiones](Modelos_Publicos_Candidatos.md); [atribuciones y licencias](../../../corpus/e90/ATRIBUCIONES.md); [incorporación CPAU](Incorporacion_ARG_A_CPAU.md) | Coherencia/diversidad de los 13 contratos, adaptación y traducciones; dos extensos bilingües; uso no comercial y CompartirIgual de ARG_A. |
| 6 | [Revisión técnica independiente](Revision_Independiente.md); [reporte manual ARCA del 22/10/2026](Verificacion_Manual_CUIT_ARCA_2026-10-22.md) | Contrastar comprobaciones técnicas y registrar el reporte de CUIT ya aportado. Las menciones previas de ARCA pendiente son históricas; los archivos existentes conservan esa leyenda anterior. |

## Checklist exacto para cada documento

1. **Identidad y finalidad:** el archivo abre, es sintético y su contenido permite sostener la categoría esperada (contrato, presupuesto, orden, factura o comprobante). Justificar las categorías ambiguas por su finalidad, no por el nombre de archivo.
2. **Campos:** cada valor de la ficha está efectivamente en el documento y corresponde al campo correcto. Comprobar sujetos/CUIT, fechas, vigencia, importes y moneda; no confundir fecha de celebración con vigencia ni monto de honorarios con presupuesto de obra.
3. **Ausencias:** en los cinco casos de ausencia intencional, el dato realmente falta. La presencia de otra fecha o un dato ilustrativo no completa automáticamente el campo omitido.
4. **Procedencia:** el PDF muestra el dato en la página señalada. Para DOCX, cotejar el localizador estructural, con apoyo técnico si hace falta; su PDF auxiliar no sustituye el localizador DOCX. Si el valor se repite, comprobar el contexto/etiqueta del campo, no solo la igualdad textual.
5. **Condiciones y vínculos:** el plazo, la modalidad, el canal y las referencias relacionadas son coherentes. Las tríadas de RAG deben estar relacionadas en su contenido y contexto autorizado.
6. **Variedad y casos difíciles:** comprobar que el diseño y la dificultad realmente existen. En capturas, comparar el PDF final de imágenes con su referencia y decidir si la calidad es adecuada; registrar que son simulaciones, no fotos/escaneos físicos.
7. **Adversariales:** localizar el texto malicioso en los tres casos y mantener las expectativas de categoría/campos establecidas; no seguir sus instrucciones. El comportamiento de la IA se medirá posteriormente.
8. **Evidencia:** conservar observaciones de ambos autores, discrepancias y decisión. Una lista de checks vacíos o tests automáticos no equivale a una aprobación. No completar indicadores de revisión de los JSON sin una revisión real.

Campos del esquema existente:

| Tipo | Campos esperados |
|---|---|
| Contratos | contraparte, cuit_contraparte, fecha_celebracion, vigencia_desde, vigencia_hasta, monto_total, moneda |
| Presupuestos | numero, fecha, proveedor, cuit_proveedor, importe_total, moneda |
| Órdenes de compra | numero, fecha, proveedor, cuit_proveedor, importe_total, moneda |
| Facturas | numero, fecha_emision, emisor, cuit_emisor, importe_total, moneda |
| Comprobantes | numero, fecha, contraparte, cuit_contraparte, importe, moneda |

## Todos los documentos que hay que revisar

Cada fila corresponde a un único archivo de entrada. El enlace a ficha muestra sus valores esperados. Para los DOCX y PDF simulados se ofrece también un PDF auxiliar de consulta. Ninguna casilla está aprobada.

### Contratos: 10 de medición + 3 de ajuste

| Archivo original | Grupo | Formato | Familia | Atención especial | Referencias para revisar |
|---|---|---|---|---|---|
| [E90-M-CTR-01](../../../corpus/e90/medicion/E90-M-CTR-01.pdf) | medicion | PDF digital | CTR-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-01) |
| [E90-M-CTR-02](../../../corpus/e90/medicion/E90-M-CTR-02.docx) | medicion | DOCX | CTR-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-02.pdf) |
| [E90-M-CTR-03](../../../corpus/e90/medicion/E90-M-CTR-03.pdf) | medicion | PDF digital | CTR-ARG_A | CPAU argentino; honorarios; CC BY-NC-SA | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-03) |
| [E90-M-CTR-04](../../../corpus/e90/medicion/E90-M-CTR-04.docx) | medicion | DOCX | CTR-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-04) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-04.pdf) |
| [E90-M-CTR-05](../../../corpus/e90/medicion/E90-M-CTR-05.pdf) | medicion | PDF escaneado simulado | CTR-MED_C | campo_ausente | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-05) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-05.pdf) |
| [E90-M-CTR-06](../../../corpus/e90/medicion/E90-M-CTR-06.pdf) | medicion | PDF digital | CTR-MED_C | contrato_extenso | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-06) |
| [E90-M-CTR-07](../../../corpus/e90/medicion/E90-M-CTR-07.docx) | medicion | DOCX | CTR-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-07) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-07.pdf) |
| [E90-M-CTR-08](../../../corpus/e90/medicion/E90-M-CTR-08.pdf) | medicion | PDF digital | CTR-MED_D | contrato_extenso | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-08) |
| [E90-M-CTR-09](../../../corpus/e90/medicion/E90-M-CTR-09.pdf) | medicion | PDF escaneado simulado | CTR-MED_C | escaneo_baja_calidad | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-09) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-09.pdf) |
| [E90-M-CTR-10](../../../corpus/e90/medicion/E90-M-CTR-10.pdf) | medicion | PDF fotografiado simulado | CTR-MED_D | instruccion_adversarial_documental | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-ctr-10) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-10.pdf) |
| [E90-A-CTR-01](../../../corpus/e90/ajuste/E90-A-CTR-01.pdf) | ajuste | PDF digital | CTR-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-ctr-01) |
| [E90-A-CTR-02](../../../corpus/e90/ajuste/E90-A-CTR-02.docx) | ajuste | DOCX | CTR-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-ctr-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-CTR-02.pdf) |
| [E90-A-CTR-03](../../../corpus/e90/ajuste/E90-A-CTR-03.pdf) | ajuste | PDF escaneado simulado | CTR-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-ctr-03) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-CTR-03.pdf) |

### Presupuestos: 10 de medición + 3 de ajuste

| Archivo original | Grupo | Formato | Familia | Atención especial | Referencias para revisar |
|---|---|---|---|---|---|
| [E90-M-PRE-01](../../../corpus/e90/medicion/E90-M-PRE-01.pdf) | medicion | PDF digital | PRE-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-01) |
| [E90-M-PRE-02](../../../corpus/e90/medicion/E90-M-PRE-02.docx) | medicion | DOCX | PRE-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-02.pdf) |
| [E90-M-PRE-03](../../../corpus/e90/medicion/E90-M-PRE-03.pdf) | medicion | PDF digital | PRE-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-03) |
| [E90-M-PRE-04](../../../corpus/e90/medicion/E90-M-PRE-04.docx) | medicion | DOCX | PRE-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-04) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-04.pdf) |
| [E90-M-PRE-05](../../../corpus/e90/medicion/E90-M-PRE-05.pdf) | medicion | PDF escaneado simulado | PRE-MED_C | campo_ausente | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-05) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-05.pdf) |
| [E90-M-PRE-06](../../../corpus/e90/medicion/E90-M-PRE-06.pdf) | medicion | PDF digital | PRE-MED_C | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-06) |
| [E90-M-PRE-07](../../../corpus/e90/medicion/E90-M-PRE-07.docx) | medicion | DOCX | PRE-MED_D | ambiguo_entre_categorias | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-07) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-07.pdf) |
| [E90-M-PRE-08](../../../corpus/e90/medicion/E90-M-PRE-08.pdf) | medicion | PDF digital | PRE-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-08) |
| [E90-M-PRE-09](../../../corpus/e90/medicion/E90-M-PRE-09.pdf) | medicion | PDF escaneado simulado | PRE-MED_C | escaneo_baja_calidad | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-09) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-09.pdf) |
| [E90-M-PRE-10](../../../corpus/e90/medicion/E90-M-PRE-10.pdf) | medicion | PDF fotografiado simulado | PRE-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-pre-10) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-10.pdf) |
| [E90-A-PRE-01](../../../corpus/e90/ajuste/E90-A-PRE-01.pdf) | ajuste | PDF digital | PRE-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-pre-01) |
| [E90-A-PRE-02](../../../corpus/e90/ajuste/E90-A-PRE-02.docx) | ajuste | DOCX | PRE-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-pre-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-PRE-02.pdf) |
| [E90-A-PRE-03](../../../corpus/e90/ajuste/E90-A-PRE-03.pdf) | ajuste | PDF escaneado simulado | PRE-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-pre-03) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-PRE-03.pdf) |

### Órdenes de compra: 10 de medición + 3 de ajuste

| Archivo original | Grupo | Formato | Familia | Atención especial | Referencias para revisar |
|---|---|---|---|---|---|
| [E90-M-OC-01](../../../corpus/e90/medicion/E90-M-OC-01.pdf) | medicion | PDF digital | OC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-01) |
| [E90-M-OC-02](../../../corpus/e90/medicion/E90-M-OC-02.docx) | medicion | DOCX | OC-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-02.pdf) |
| [E90-M-OC-03](../../../corpus/e90/medicion/E90-M-OC-03.pdf) | medicion | PDF digital | OC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-03) |
| [E90-M-OC-04](../../../corpus/e90/medicion/E90-M-OC-04.docx) | medicion | DOCX | OC-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-04) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-04.pdf) |
| [E90-M-OC-05](../../../corpus/e90/medicion/E90-M-OC-05.pdf) | medicion | PDF escaneado simulado | OC-MED_C | campo_ausente | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-05) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-05.pdf) |
| [E90-M-OC-06](../../../corpus/e90/medicion/E90-M-OC-06.pdf) | medicion | PDF digital | OC-MED_C | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-06) |
| [E90-M-OC-07](../../../corpus/e90/medicion/E90-M-OC-07.docx) | medicion | DOCX | OC-MED_D | ambiguo_entre_categorias | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-07) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-07.pdf) |
| [E90-M-OC-08](../../../corpus/e90/medicion/E90-M-OC-08.pdf) | medicion | PDF digital | OC-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-08) |
| [E90-M-OC-09](../../../corpus/e90/medicion/E90-M-OC-09.pdf) | medicion | PDF escaneado simulado | OC-MED_C | escaneo_baja_calidad | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-09) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-09.pdf) |
| [E90-M-OC-10](../../../corpus/e90/medicion/E90-M-OC-10.pdf) | medicion | PDF fotografiado simulado | OC-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-oc-10) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-10.pdf) |
| [E90-A-OC-01](../../../corpus/e90/ajuste/E90-A-OC-01.pdf) | ajuste | PDF digital | OC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-oc-01) |
| [E90-A-OC-02](../../../corpus/e90/ajuste/E90-A-OC-02.docx) | ajuste | DOCX | OC-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-oc-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-OC-02.pdf) |
| [E90-A-OC-03](../../../corpus/e90/ajuste/E90-A-OC-03.pdf) | ajuste | PDF escaneado simulado | OC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-oc-03) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-OC-03.pdf) |

### Facturas: 10 de medición + 3 de ajuste

| Archivo original | Grupo | Formato | Familia | Atención especial | Referencias para revisar |
|---|---|---|---|---|---|
| [E90-M-FAC-01](../../../corpus/e90/medicion/E90-M-FAC-01.pdf) | medicion | PDF digital | FAC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-01) |
| [E90-M-FAC-02](../../../corpus/e90/medicion/E90-M-FAC-02.docx) | medicion | DOCX | FAC-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-02.pdf) |
| [E90-M-FAC-03](../../../corpus/e90/medicion/E90-M-FAC-03.pdf) | medicion | PDF digital | FAC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-03) |
| [E90-M-FAC-04](../../../corpus/e90/medicion/E90-M-FAC-04.docx) | medicion | DOCX | FAC-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-04) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-04.pdf) |
| [E90-M-FAC-05](../../../corpus/e90/medicion/E90-M-FAC-05.pdf) | medicion | PDF escaneado simulado | FAC-MED_C | campo_ausente | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-05) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-05.pdf) |
| [E90-M-FAC-06](../../../corpus/e90/medicion/E90-M-FAC-06.pdf) | medicion | PDF digital | FAC-MED_C | instruccion_adversarial_documental | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-06) |
| [E90-M-FAC-07](../../../corpus/e90/medicion/E90-M-FAC-07.docx) | medicion | DOCX | FAC-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-07) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-07.pdf) |
| [E90-M-FAC-08](../../../corpus/e90/medicion/E90-M-FAC-08.pdf) | medicion | PDF digital | FAC-MED_D | ambiguo_entre_categorias | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-08) |
| [E90-M-FAC-09](../../../corpus/e90/medicion/E90-M-FAC-09.pdf) | medicion | PDF escaneado simulado | FAC-MED_C | escaneo_baja_calidad | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-09) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-09.pdf) |
| [E90-M-FAC-10](../../../corpus/e90/medicion/E90-M-FAC-10.pdf) | medicion | PDF fotografiado simulado | FAC-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-fac-10) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-10.pdf) |
| [E90-A-FAC-01](../../../corpus/e90/ajuste/E90-A-FAC-01.pdf) | ajuste | PDF digital | FAC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-fac-01) |
| [E90-A-FAC-02](../../../corpus/e90/ajuste/E90-A-FAC-02.docx) | ajuste | DOCX | FAC-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-fac-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-FAC-02.pdf) |
| [E90-A-FAC-03](../../../corpus/e90/ajuste/E90-A-FAC-03.pdf) | ajuste | PDF escaneado simulado | FAC-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-fac-03) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-FAC-03.pdf) |

### Comprobantes: 10 de medición + 3 de ajuste

| Archivo original | Grupo | Formato | Familia | Atención especial | Referencias para revisar |
|---|---|---|---|---|---|
| [E90-M-COM-01](../../../corpus/e90/medicion/E90-M-COM-01.pdf) | medicion | PDF digital | COM-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-01) |
| [E90-M-COM-02](../../../corpus/e90/medicion/E90-M-COM-02.docx) | medicion | DOCX | COM-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-02.pdf) |
| [E90-M-COM-03](../../../corpus/e90/medicion/E90-M-COM-03.pdf) | medicion | PDF digital | COM-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-03) |
| [E90-M-COM-04](../../../corpus/e90/medicion/E90-M-COM-04.docx) | medicion | DOCX | COM-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-04) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-04.pdf) |
| [E90-M-COM-05](../../../corpus/e90/medicion/E90-M-COM-05.pdf) | medicion | PDF escaneado simulado | COM-MED_C | campo_ausente | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-05) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-05.pdf) |
| [E90-M-COM-06](../../../corpus/e90/medicion/E90-M-COM-06.pdf) | medicion | PDF digital | COM-MED_C | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-06) |
| [E90-M-COM-07](../../../corpus/e90/medicion/E90-M-COM-07.docx) | medicion | DOCX | COM-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-07) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-07.pdf) |
| [E90-M-COM-08](../../../corpus/e90/medicion/E90-M-COM-08.pdf) | medicion | PDF digital | COM-MED_D | ambiguo_entre_categorias;instruccion_adversarial_documental | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-08) |
| [E90-M-COM-09](../../../corpus/e90/medicion/E90-M-COM-09.pdf) | medicion | PDF escaneado simulado | COM-MED_C | escaneo_baja_calidad | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-09) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-09.pdf) |
| [E90-M-COM-10](../../../corpus/e90/medicion/E90-M-COM-10.pdf) | medicion | PDF fotografiado simulado | COM-MED_D | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-m-com-10) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-10.pdf) |
| [E90-A-COM-01](../../../corpus/e90/ajuste/E90-A-COM-01.pdf) | ajuste | PDF digital | COM-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-com-01) |
| [E90-A-COM-02](../../../corpus/e90/ajuste/E90-A-COM-02.docx) | ajuste | DOCX | COM-BASE_B | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-com-02) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-COM-02.pdf) |
| [E90-A-COM-03](../../../corpus/e90/ajuste/E90-A-COM-03.pdf) | ajuste | PDF escaneado simulado | COM-BASE_A | Revisión general | [Ficha y campos](Cuaderno_Revision_Documentos_E90.md#e90-a-com-03) · [PDF auxiliar](../../../corpus/e90/pdf_referencia/ajuste/E90-A-COM-03.pdf) |

## Casos para mirar con atención particular

| Fenómeno | Casos concretos | Qué comprobar |
|---|---|---|
| Ausencia intencional | [E90-M-CTR-05](../../../corpus/e90/medicion/E90-M-CTR-05.pdf), [E90-M-PRE-05](../../../corpus/e90/medicion/E90-M-PRE-05.pdf), [E90-M-OC-05](../../../corpus/e90/medicion/E90-M-OC-05.pdf), [E90-M-FAC-05](../../../corpus/e90/medicion/E90-M-FAC-05.pdf), [E90-M-COM-05](../../../corpus/e90/medicion/E90-M-COM-05.pdf) | Son cinco fechas ausentes; no convertir ausencia en dato inventado. |
| Extensión | [E90-M-CTR-06](../../../corpus/e90/medicion/E90-M-CTR-06.pdf), [E90-M-CTR-08](../../../corpus/e90/medicion/E90-M-CTR-08.pdf) | Contratos de 10 y 11 páginas, anexos bilingües y coherencia de traducción/condiciones. |
| Calidad baja | [E90-M-CTR-09](../../../corpus/e90/medicion/E90-M-CTR-09.pdf), [E90-M-PRE-09](../../../corpus/e90/medicion/E90-M-PRE-09.pdf), [E90-M-OC-09](../../../corpus/e90/medicion/E90-M-OC-09.pdf), [E90-M-FAC-09](../../../corpus/e90/medicion/E90-M-FAC-09.pdf), [E90-M-COM-09](../../../corpus/e90/medicion/E90-M-COM-09.pdf) | La degradación debe ser visible y permitir cotejar el oráculo con el final. |
| Ambigüedad | [E90-M-PRE-07](../../../corpus/e90/medicion/E90-M-PRE-07.docx), [E90-M-OC-07](../../../corpus/e90/medicion/E90-M-OC-07.docx), [E90-M-FAC-08](../../../corpus/e90/medicion/E90-M-FAC-08.pdf), [E90-M-COM-08](../../../corpus/e90/medicion/E90-M-COM-08.pdf) | Justificación objetiva de clase; posibles títulos que sugieran otra categoría; no basta la intención del plan. |
| Instrucciones maliciosas | [E90-M-CTR-10](../../../corpus/e90/medicion/E90-M-CTR-10.pdf), [E90-M-FAC-06](../../../corpus/e90/medicion/E90-M-FAC-06.pdf), [E90-M-COM-08](../../../corpus/e90/medicion/E90-M-COM-08.pdf) | Exactamente tres; la instrucción no cambia la verdad documental ni autoriza acciones. |
| Fuente argentina | [E90-M-CTR-03](../../../corpus/e90/medicion/E90-M-CTR-03.pdf) | Roles, fases de proyecto, honorarios en ARS y licencia; la muestra no representa todo el contexto argentino. |

## Todas las preguntas que hay que revisar

| Preguntas | Cantidad | Qué revisar |
|---|---|---|
| [Q01](Cuaderno_Revision_Consultas_RAG_E90.md#q01), [Q02](Cuaderno_Revision_Consultas_RAG_E90.md#q02), [Q03](Cuaderno_Revision_Consultas_RAG_E90.md#q03), [Q04](Cuaderno_Revision_Consultas_RAG_E90.md#q04), [Q05](Cuaderno_Revision_Consultas_RAG_E90.md#q05), [Q06](Cuaderno_Revision_Consultas_RAG_E90.md#q06), [Q07](Cuaderno_Revision_Consultas_RAG_E90.md#q07), [Q08](Cuaderno_Revision_Consultas_RAG_E90.md#q08), [Q09](Cuaderno_Revision_Consultas_RAG_E90.md#q09), [Q10](Cuaderno_Revision_Consultas_RAG_E90.md#q10) | 10 | Dato y moneda/sujeto correctos, sin otra pieza no autorizada. |
| [Q11](Cuaderno_Revision_Consultas_RAG_E90.md#q11), [Q12](Cuaderno_Revision_Consultas_RAG_E90.md#q12), [Q13](Cuaderno_Revision_Consultas_RAG_E90.md#q13), [Q14](Cuaderno_Revision_Consultas_RAG_E90.md#q14), [Q15](Cuaderno_Revision_Consultas_RAG_E90.md#q15), [Q16](Cuaderno_Revision_Consultas_RAG_E90.md#q16), [Q17](Cuaderno_Revision_Consultas_RAG_E90.md#q17), [Q18](Cuaderno_Revision_Consultas_RAG_E90.md#q18) | 8 | Plazo/modalidad/cláusulas con fuente suficiente; pregunta natural. Q12 corresponde al nuevo CPAU. |
| [Q19](Cuaderno_Revision_Consultas_RAG_E90.md#q19), [Q20](Cuaderno_Revision_Consultas_RAG_E90.md#q20), [Q21](Cuaderno_Revision_Consultas_RAG_E90.md#q21), [Q22](Cuaderno_Revision_Consultas_RAG_E90.md#q22), [Q23](Cuaderno_Revision_Consultas_RAG_E90.md#q23), [Q24](Cuaderno_Revision_Consultas_RAG_E90.md#q24) | 6 | Los importes/monedas y relaciones de al menos dos documentos están respaldados dentro del contexto. |
| [Q25](Cuaderno_Revision_Consultas_RAG_E90.md#q25), [Q26](Cuaderno_Revision_Consultas_RAG_E90.md#q26), [Q27](Cuaderno_Revision_Consultas_RAG_E90.md#q27), [Q28](Cuaderno_Revision_Consultas_RAG_E90.md#q28), [Q29](Cuaderno_Revision_Consultas_RAG_E90.md#q29), [Q30](Cuaderno_Revision_Consultas_RAG_E90.md#q30) | 6 | Falta evidencia suficiente dentro del contexto autorizado; no contestar desde otras piezas o conocimiento general. |

Además de la exactitud de la referencia, RC-P06.2 pide naturalidad y revisar pistas/coincidencias textuales artificiales antes de congelar. Las seis negativas actuales comparten PRE-03 como contexto: revisar que ese diseño y los motivos de abstención resulten adecuados para la muestra aprobada; no afirmar diversidad de contextos que no existe. No cambiar preguntas tras observar resultados de modelos.

## Archivos canónicos para contrastar las fichas

| Archivo | Contenido y función |
|---|---|
| [corpus/e90/registros_fuente.json](../../../corpus/e90/registros_fuente.json) | Valores definidos antes de generar, categoría, dificultades, condiciones y relaciones de cada documento. |
| [oraculos/e90/campos_candidatos.json](../../../oraculos/e90/campos_candidatos.json) | 403 campos: 398 presentes y cinco ausentes, normalización, representación y localizador. |
| [oraculos/e90/fragmentos_candidatos.json](../../../oraculos/e90/fragmentos_candidatos.json) | 534 fragmentos primarios con texto y localizador; revisar los citados y su coherencia con el archivo. |
| [oraculos/e90/consultas_candidatas.json](../../../oraculos/e90/consultas_candidatas.json) | 30 preguntas, contexto autorizado, respuesta o abstención, afirmaciones y citas. |
| [oraculos/e90/inventario_candidato.csv](../../../oraculos/e90/inventario_candidato.csv) | 65 rutas de entrada, tipos, grupos, formatos, familias, hashes y marcas adversariales. |
| [oraculos/e90/artefactos_candidatos.json](../../../oraculos/e90/artefactos_candidatos.json) | Huellas, versiones, fuentes DOCX/PDF auxiliares, páginas y parámetros de simulación; revisión parcial ARG_A. |
| [herramientas/corpus_e90/plantillas/contratos.json](../../../herramientas/corpus_e90/plantillas/contratos.json) | Cinco fuentes originales con versiones, licencia, cláusulas y adaptaciones; comprobar especialmente la coherencia de traducciones. |
| [oraculos/e90/cuit_candidatos.json](../../../oraculos/e90/cuit_candidatos.json) | Doce resultados manuales reportados por el equipo, todos «No existe», fecha 22/10/2026; siguen candidatos. |

El cuaderno de documentos transcribe también los 136 fragmentos de alcance/condiciones/relaciones; los 398 fragmentos de campos se cotejan junto con las tablas de valores. Los JSON siguen siendo los oráculos canónicos. Los cuadernos son una vista de revisión de esta versión; si un documento o referencia cambia, deben actualizarse las fichas y repetir las comprobaciones que afecte el cambio.

## Procedencia de los contratos

| Familia | Fuente y versión aprobada | Licencia | Uso |
|---|---|---|---|
| BASE_A | [Short Form Contract, 1.5A](https://www.gov.uk/government/publications/the-short-form-contract) | [OGL-3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) | Ajuste y medición |
| BASE_B | [Bonterms Professional Services Agreement, 1.2](https://bonterms.com/standard/professional-services-agreement-v1.2) | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | Ajuste y medición |
| MED_C | [Common Paper Professional Services Agreement, 1.1](https://commonpaper.com/standards/professional-services-agreement/1.1) | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | Solo medición |
| MED_D | [Mid-Tier Contract Core Terms, 1.3A](https://www.gov.uk/government/publications/the-mid-tier-contract-core-terms) | [OGL-3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) | Solo medición |
| ARG_A | [A-301: Contrato de proyecto y dirección, 9.ª edición, 2023](https://repositorio.cpau.org/items/show/823) | [CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) | Solo medición, E90-M-CTR-03 |

Revisar cada familia una vez frente a su fuente original y luego que sus contratos conserven coherencia y variedad real. El agente comprobó procedencia/licencias; la revisión de autores debe contrastar adaptación, traducciones y adecuación de la muestra. Esto no exige que los autores emitan una validación jurídica profesional para Argentina. Ver [verificación del archivo CPAU](fuentes/ARG_A_CPAU_verificacion.json).

## Puntos concretos para decidir antes de congelar

- **Preguntas de condiciones:** Q11–Q18 siguen un patrón centrado en plazo/modalidad. Revisar si esa muestra satisface la comprensión de condiciones/cláusulas prevista y si su redacción resulta natural. Esta guía registra el diseño actual y no lo da por aprobado.
- **Abstenciones:** Q25–Q30 usan el mismo contexto PRE-03. Confirmar sus seis motivos y la adecuación de ese diseño; no atribuir variedad de contextos inexistente.
- **Metadatos heredados:** doce contratos mantienen `fuente_contractual=pendiente_aprobacion` en los registros iniciales, mientras el banco de cinco fuentes registra su aprobación y el manifiesto identifica las familias usadas. Revisar/armonizar ese estado documental antes de la versión definitiva; no interpretar la etiqueta aislada como una aprobación o un rechazo nuevos.
- **Leyendas ARCA:** los documentos construidos antes del reporte manual del equipo conservan el texto de consulta pendiente. El registro posterior del 22/10/2026 consigna «No existe» para los doce CUIT E90. Dejar coherente la versión definitiva sin fingir que se consultaron antes de construir los candidatos.

## Control técnico y material de apoyo

El otro agente puede repetir los verificadores y revisar hashes, duplicados, particiones, exclusividad de plantillas, localizadores, referencias y versiones. Ustedes revisan el sentido documental y las referencias antes de aprobar; no necesitan calcular a mano cada SHA-256. Las pruebas ya conservadas no sustituyen la revisión semántica.

- [Resultado del ensayo limpio ARG_A](Ensayo_CI_ARG_A.txt).
- [Verificación estructural](Verificacion_Candidatos.json).
- [Revisión visual previa](Revision_Visual_Preliminar.json).
- [Preservación y revisión parcial ARG_A](Revision_ARG_A.json).
- [Diferencias con la tesis, DIF-E90-01 a DIF-E90-08](../../tesis/Registro_Diferencias_con_la_Tesis.md). Revisar simulaciones, bilingüismo, fuentes y límites; los IDs se renumerarán al integrar.

## PD-07, en una revisión aparte

La historia principal de mantenimiento y sus cinco PDF no forman parte de los 65 E90. Para preparar la demo/EVD tienen revisión propia; ver [auditoría PD-07](Auditoria_PD07.md). Esta guía no resuelve sus ocho campos/localizadores faltantes ni DIF-84. La consulta de los doce CUIT E90 no acredita por sí sola el CUIT distinto usado en PD-07.

Documentos de la demo, **solo para una revisión separada de PD-07**:

- [C-v1: contrato de mantenimiento](../../../corpus/C-v1_Contrato_Mantenimiento_ATLAS.pdf).
- [O-v1: orden original](../../../corpus/O-v1_Orden_Compra.pdf).
- [O-v2: orden corregida](../../../corpus/O-v2_Orden_Compra.pdf).
- [F-v1: factura original](../../../corpus/F-v1_Factura.pdf).
- [F-v2: factura corregida](../../../corpus/F-v2_Factura.pdf).
- [Oráculo preliminar PD-07](../../../oraculos/oraculo_PD07_preliminar.json).

Estas piezas no aumentan los 65 E90 y no se solicita aprobarlas como parte de esta revisión de la muestra cuantitativa.

## Qué queda registrado al terminar

Conservar autor/fecha/commit de datos, observaciones de cada revisor, discrepancias y resolución en cada ficha, más aprobación de composición/fuentes y de Q01–Q30. No registrar una prueba de IA, puntuación o consenso experimental que todavía no existe. La aprobación del corpus antecede a la congelación y a la ejecución de las campañas.

## Huellas de las fuentes de estos cuadernos

| Archivo canónico | SHA-256 al preparar esta guía |
|---|---|
| [corpus/e90/registros_fuente.json](../../../corpus/e90/registros_fuente.json) | `744f52b22db381e94ac428d32118e54a2b40fcabc53bba6933d7f94d476e8eac` |
| [oraculos/e90/artefactos_candidatos.json](../../../oraculos/e90/artefactos_candidatos.json) | `3c3cfd34e42a723ef6e73254f8446de58477854b0c4241d50985386936dad58f` |
| [oraculos/e90/inventario_candidato.csv](../../../oraculos/e90/inventario_candidato.csv) | `1c78d9ee9e35173442dd0aac71c2e502d4fac7e5d17c1b339acac675a807f965` |
| [oraculos/e90/campos_candidatos.json](../../../oraculos/e90/campos_candidatos.json) | `5788074a743dccf39336df8c73a16ed8c9cbb73d654ae7864d4ec8c7dabd94ef` |
| [oraculos/e90/fragmentos_candidatos.json](../../../oraculos/e90/fragmentos_candidatos.json) | `35fcab05738cd20f892365f06278fc873f5e2b3946a0f06050b19fb7adbc41a8` |
| [oraculos/e90/consultas_candidatas.json](../../../oraculos/e90/consultas_candidatas.json) | `d42c430beb65981e5512ac410c4c6607f4c7079d7bd6a8b5cab503dbc7dc2d6e` |
| [oraculos/e90/cuit_candidatos.json](../../../oraculos/e90/cuit_candidatos.json) | `937c486ecd759aa7b6ea70a0c944cd06e00c0cb1af6ab70aaf75213161b17015` |
| [herramientas/corpus_e90/plantillas/contratos.json](../../../herramientas/corpus_e90/plantillas/contratos.json) | `f25d0bb1c95996206e7d23e4467bcd5b9b950c138150f58962b1f16e4e7463fc` |

## Informe de esta preparación

Tarea: proporcionar lista completa y fichas legibles para la revisión humana del corpus E90.
Requisitos cubiertos: IA-D01/02/03/04/07/08, RC-P04, RC-P06.2 y congelación previa IA-M12; IA-M06 se distingue como evaluación posterior.
Archivos modificados: esta guía y tres cuadernos de revisión, con enlaces a los 65 archivos reales y las 30 preguntas; estado e índice del incremento actualizados con sus rutas.
Decisiones delegadas tomadas: ninguna. No se agregan criterios o requisitos.
Diferencias con la tesis registradas: ninguna nueva; vistas documentales de referencias ya existentes.
Pruebas: **65 fichas, 403 campos (cinco ausencias), 136 fragmentos de texto, 30 preguntas, cinco fuentes/43 cláusulas, 488 enlaces locales y 95 anclas verificados**. Ocho fuentes canónicas y los 195 artefactos conservan sus hashes. Suite raíz: **46 aprobadas y una omitida** con motivo explícito. La primera ejecución mostró una advertencia por caché de pytest no escribible en el worktree; la comprobación final usa `-p no:cacheprovider`. No se repite el ensayo completo de backend por esta vista documental, sin código ni datos modificados.
Pendientes o bloqueos: todas las revisiones humanas siguen pendientes; no se congela ni se modifica el estado de oráculos.
Preguntas para el equipo: ninguna para preparar este material.
