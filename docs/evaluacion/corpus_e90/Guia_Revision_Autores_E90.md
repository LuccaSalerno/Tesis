# Guía completa de revisión por los autores — corpus E90 (v2)

Revisión candidata **e90-candidato-v2**, datos del commit `2082a6e` en `codex/corpus-e90` (DO-2026-10-22-CORPUS-REVISION). Esta guía facilita la revisión: no cambia el protocolo, los documentos ni sus oráculos. **Todo sigue candidato y pendiente de revisión de autores.** Las casillas y observaciones se dejan sin completar; no representan una revisión ejecutada.

**Qué revisar:** los 65 archivos de entrada (50 de medición + 15 de ajuste, 13 por tipo), sus 403 referencias de campos (398 presentes y cinco ausencias intencionales), clases esperadas, casos difíciles, cuatro trámites multidocumento y 30 preguntas RAG. Son 45 PDF y 20 DOCX; los PDF de referencia suman 121 páginas. Hay 20 PDF de capturas simuladas. Los 130 auxiliares no aumentan la muestra.

La v2 resuelve los hallazgos REV-E90-01 a 15 de las revisiones técnicas ([constructor v1](Revision_Tecnica_Agente_2026-10-22.md), [contraste](Revision_Tecnica_Contraste_2026-10-22.md)) según el [diseño aprobado](Propuesta_Corpus_V2.md). Detalle de lo hecho y verificado: [informe de la v2](Informe_Revision_V2.md). La v1 queda como antecedente en [v1/](v1/README.md).

La revisión de documentos y oráculos antes de congelar está prevista en el plan (paso 5), IA-D y RC-P06.2. La **calificación de respuestas de IA** corresponde a IA-M06 y se hará después de ejecutar; no confundirla con esta revisión previa.

## Orden recomendado

| Paso | Documento | Qué revisar |
|---|---|---|
| 1 | [Plan de diseño](../Plan_Diseno_Corpus_E90.md); [protocolo E90](../Protocolo_E90_Corpus_y_Validacion.md) | 50 + 15, separación ajuste/medición y alcance sintético. |
| 2 | [Decisiones técnicas](../../decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md) (DO-CORPUS, ARG-A, REVISION); [aceptación 5.1 y 5.2](../../aceptacion/Contrato_Aceptacion_Integral_Reconstruccion_PFI_2026-10-20_v1_1.md) | Campos por tipo, preguntas, rúbrica y umbrales. No redefinirlos al revisar. |
| 3 | [Cuaderno de los 65 documentos](Cuaderno_Revision_Documentos_E90.md) | Índice con el archivo neutro de cada ID; por ficha, clase, campos, etiqueta impresa, localizador, ambigüedad, adversarial y trámite. |
| 4 | [Cuaderno de las 30 preguntas](Cuaderno_Revision_Consultas_RAG_E90.md) | Pregunta, contexto, afirmaciones esperadas y fragmentos; seis abstenciones. |
| 5 | [Cuaderno de las cinco fuentes](Cuaderno_Revision_Fuentes_Contractuales_E90.md); [fuentes públicas](Modelos_Publicos_Candidatos.md); [atribuciones](../../../corpus/e90/ATRIBUCIONES.md); [incorporación CPAU](Incorporacion_ARG_A_CPAU.md) | Adaptaciones y traducciones (sin cambios en la v2). |
| 6 | [Reporte manual ARCA](Verificacion_Manual_CUIT_ARCA_2026-10-22.md); [razones sociales y CUIT a verificar](Verificaciones_Pendientes_V2.md) | Los 12 CUIT de medición ya informados; verificar las 18 razones sociales y los 6 CUIT nuevos de ajuste. |

## Checklist para cada documento

1. **Clase sin pistas:** el contenido permite sostener la clase esperada por su finalidad (quién emite, qué pide, qué registra). No debe haber ID de inventario, explicación de la función ni aclaraciones de construcción. Los títulos comerciales naturales son evidencia legítima.
2. **Campos:** cada valor está en el documento, en la representación impresa de la ficha (formato de la familia) y junto a la etiqueta indicada. Comprobar que el valor normalizado corresponde a lo impreso (fechas en letras, importes con símbolo, CUIT sin guiones, moneda por nombre o símbolo).
3. **Ausencias:** en los cinco casos, el dato falta realmente; otra fecha (por ejemplo, de entrega o vencimiento) no completa el campo omitido.
4. **Procedencia:** el PDF muestra el dato en la página indicada (en 12 campos, la página 2). En DOCX, cotejar el párrafo con apoyo técnico si hace falta.
5. **Distractores:** en las facturas y pedidos con detalle, distinguir neto, IVA y total; en las órdenes, fecha de emisión y fecha de entrega.
6. **Trámites:** en T1–T4, mismo proveedor y moneda, importes relacionados y referencias por número documental. T3 tiene una diferencia deliberada entre orden y factura.
7. **Ambigüedad y adversariales:** revisar la justificación previa y que el texto adversarial pida algo que contradiga el oráculo. La IA no debe seguirlo; eso se mide después.
8. **Evidencia:** conservar observaciones, discrepancias y decisión de ambos autores. Tests verdes no equivalen a aprobación.

## Casos para mirar con atención particular

| Fenómeno | Casos | Qué comprobar |
|---|---|---|
| Ausencia intencional | [E90-M-CTR-05](../../../corpus/e90/medicion/doc-61715899.pdf), [E90-M-PRE-05](../../../corpus/e90/medicion/doc-20e840a1.pdf), [E90-M-OC-05](../../../corpus/e90/medicion/doc-670e723d.pdf), [E90-M-FAC-05](../../../corpus/e90/medicion/doc-2267774a.pdf), [E90-M-COM-05](../../../corpus/e90/medicion/doc-ba200f04.pdf) | Cinco fechas ausentes; no convertir ausencia en dato. |
| Extensión | [E90-M-CTR-06](../../../corpus/e90/medicion/doc-de08cb56.pdf), [E90-M-CTR-08](../../../corpus/e90/medicion/doc-ef93a9e2.pdf) | Contratos de 10 y 11 páginas con anexos bilingües. |
| Calidad baja | [E90-M-CTR-09](../../../corpus/e90/medicion/doc-9426a983.pdf), [E90-M-PRE-09](../../../corpus/e90/medicion/doc-6114e8de.pdf), [E90-M-OC-09](../../../corpus/e90/medicion/doc-105a92b9.pdf), [E90-M-FAC-09](../../../corpus/e90/medicion/doc-af3efe12.pdf), [E90-M-COM-09](../../../corpus/e90/medicion/doc-6ae702f2.pdf) | Degradación visible que aún permita cotejar el oráculo. |
| Ambigüedad | [E90-M-PRE-07](../../../corpus/e90/medicion/doc-a8069d15.docx), [E90-M-OC-07](../../../corpus/e90/medicion/doc-6084b5de.docx), [E90-M-FAC-08](../../../corpus/e90/medicion/doc-70812f2a.pdf), [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf) | Propuesta con aceptación en blanco; pedido que reproduce la cotización; liquidación con mención de recepción; constancia que cita factura e importe. |
| Adversariales | [E90-M-CTR-10](../../../corpus/e90/medicion/doc-a24529ac.pdf), [E90-M-FAC-06](../../../corpus/e90/medicion/doc-3c9c847a.pdf), [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf) | Nota dentro de una cláusula, nota al pie en letra chica y campo de observaciones; objetivos: otra clase, monto 0, CUIT inválido, trámite aprobado, importe y moneda falsos, omitir citas. |
| Fuente argentina | [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf) | Honorarios en pesos argentinos, no costo de obra; licencia CC BY-NC-SA 4.0. |

## Preguntas

| Preguntas | Qué revisar |
|---|---|
| [Q01](Cuaderno_Revision_Consultas_RAG_E90.md#q01), [Q02](Cuaderno_Revision_Consultas_RAG_E90.md#q02), [Q03](Cuaderno_Revision_Consultas_RAG_E90.md#q03), [Q04](Cuaderno_Revision_Consultas_RAG_E90.md#q04), [Q05](Cuaderno_Revision_Consultas_RAG_E90.md#q05), [Q06](Cuaderno_Revision_Consultas_RAG_E90.md#q06), [Q07](Cuaderno_Revision_Consultas_RAG_E90.md#q07), [Q08](Cuaderno_Revision_Consultas_RAG_E90.md#q08), [Q09](Cuaderno_Revision_Consultas_RAG_E90.md#q09), [Q10](Cuaderno_Revision_Consultas_RAG_E90.md#q10) | Directas: dato correcto en trámites, contratos sueltos, una captura escaneada, una fotografiada, un DOCX y dos adversariales (Q05 en el contexto de la constancia, Q10 sobre el CUIT inyectado). |
| [Q11](Cuaderno_Revision_Consultas_RAG_E90.md#q11), [Q12](Cuaderno_Revision_Consultas_RAG_E90.md#q12), [Q13](Cuaderno_Revision_Consultas_RAG_E90.md#q13), [Q14](Cuaderno_Revision_Consultas_RAG_E90.md#q14), [Q15](Cuaderno_Revision_Consultas_RAG_E90.md#q15), [Q16](Cuaderno_Revision_Consultas_RAG_E90.md#q16), [Q17](Cuaderno_Revision_Consultas_RAG_E90.md#q17), [Q18](Cuaderno_Revision_Consultas_RAG_E90.md#q18) | Condiciones: cinco sobre cláusulas contractuales (terminación, rectificación, controversias, aceptación, reserva) y tres comerciales (validez y pago, lugar y fecha de entrega, vencimiento). |
| [Q19](Cuaderno_Revision_Consultas_RAG_E90.md#q19), [Q20](Cuaderno_Revision_Consultas_RAG_E90.md#q20), [Q21](Cuaderno_Revision_Consultas_RAG_E90.md#q21), [Q22](Cuaderno_Revision_Consultas_RAG_E90.md#q22), [Q23](Cuaderno_Revision_Consultas_RAG_E90.md#q23), [Q24](Cuaderno_Revision_Consultas_RAG_E90.md#q24) | Multidocumento: coincidencia de importes, diferencia deliberada, documento citado, vigencia, factura citada por la constancia y días entre documentos. |
| [Q25](Cuaderno_Revision_Consultas_RAG_E90.md#q25), [Q26](Cuaderno_Revision_Consultas_RAG_E90.md#q26), [Q27](Cuaderno_Revision_Consultas_RAG_E90.md#q27), [Q28](Cuaderno_Revision_Consultas_RAG_E90.md#q28), [Q29](Cuaderno_Revision_Consultas_RAG_E90.md#q29), [Q30](Cuaderno_Revision_Consultas_RAG_E90.md#q30) | Abstenciones en seis contextos distintos, varias con información cercana pero ausente (fecha de entrega sin penalidad, forma de pago sin cuenta, honorarios sin costo de obra). |

RC-P06.2 pide además naturalidad y ausencia de pistas artificiales. Las preguntas nombran a la empresa del trámite, no el ID. No cambiar preguntas después de observar resultados de modelos.

## Archivos canónicos

| Archivo | Contenido |
|---|---|
| [corpus/e90/registros_fuente.json](../../../corpus/e90/registros_fuente.json) | Valores previos a generar, contextos, ambigüedades, adversariales, condiciones y referencias. |
| [oraculos/e90/campos_candidatos.json](../../../oraculos/e90/campos_candidatos.json) | 403 campos con valor normalizado, representación, etiqueta impresa y localizador. |
| [oraculos/e90/fragmentos_candidatos.json](../../../oraculos/e90/fragmentos_candidatos.json) | 727 fragmentos: 398 de campos y 329 de condiciones, cláusulas, objeto, referencias y adversariales. |
| [oraculos/e90/consultas_candidatas.json](../../../oraculos/e90/consultas_candidatas.json) | 30 preguntas con contexto, afirmaciones atómicas o motivo de abstención. |
| [oraculos/e90/inventario_candidato.csv](../../../oraculos/e90/inventario_candidato.csv) | 65 rutas neutras con ID, tipo, grupo, formato, familia, hash y marca adversarial. |
| [oraculos/e90/artefactos_candidatos.json](../../../oraculos/e90/artefactos_candidatos.json) | Huellas, herramientas, páginas y parámetros de simulación. |
| [oraculos/e90/cuit_candidatos.json](../../../oraculos/e90/cuit_candidatos.json) | 18 CUIT: 12 de medición con el reporte ARCA del equipo y 6 de ajuste pendientes. |
| [herramientas/corpus_e90/plantillas/contratos.json](../../../herramientas/corpus_e90/plantillas/contratos.json) | Cinco fuentes contractuales (sin cambios en la v2). |

## Antes de congelar

- Verificar a mano las 18 razones sociales y los 6 CUIT nuevos de ajuste ([lista](Verificaciones_Pendientes_V2.md)). Si alguno coincide con uno real, reemplazarlo y regenerar.
- Revisión de contraste de la v2 por el agente que no la construyó (P0).
- Revisión de ambos autores con los cuadernos; luego, congelación.

## PD-07, en una revisión aparte

La historia principal de mantenimiento y sus cinco PDF no forman parte de los 65 E90; ver [auditoría PD-07](Auditoria_PD07.md). Esta guía no resuelve sus campos faltantes ni DIF-84.

## Huellas de los archivos canónicos al preparar esta guía

| Archivo | SHA-256 |
|---|---|
| [corpus/e90/registros_fuente.json](../../../corpus/e90/registros_fuente.json) | `9bb8326de60f566bed8ccdabd249a6761560ca70a4196187b151bff02575e970` |
| [oraculos/e90/artefactos_candidatos.json](../../../oraculos/e90/artefactos_candidatos.json) | `aaf3be33bbe58da7e55d2460b80c03aa9a3455ab18153a948bd05d72288979c3` |
| [oraculos/e90/inventario_candidato.csv](../../../oraculos/e90/inventario_candidato.csv) | `89ad1df144718ee874b37829bac8c3c1d662aa490085c1ee391b201b888eaa98` |
| [oraculos/e90/campos_candidatos.json](../../../oraculos/e90/campos_candidatos.json) | `9c28b90c6e1a912bfdb467f95f3d21d7749207b02c440dc00d1449a2eb86e800` |
| [oraculos/e90/fragmentos_candidatos.json](../../../oraculos/e90/fragmentos_candidatos.json) | `32f62a662a3008fbebc68bbb9d824b0942361938570209b56e8f9cbf9e6ef529` |
| [oraculos/e90/consultas_candidatas.json](../../../oraculos/e90/consultas_candidatas.json) | `b692bb65b6760629d8a79b192c5576e5ff896b24d305889831d019fd1e6a9acb` |
| [oraculos/e90/cuit_candidatos.json](../../../oraculos/e90/cuit_candidatos.json) | `f707a69e9f2c4a0212645acdef3e2af78183d8c9f1c4d81690a236727cf5c8eb` |
| [herramientas/corpus_e90/plantillas/contratos.json](../../../herramientas/corpus_e90/plantillas/contratos.json) | `f25d0bb1c95996206e7d23e4467bcd5b9b950c138150f58962b1f16e4e7463fc` |
