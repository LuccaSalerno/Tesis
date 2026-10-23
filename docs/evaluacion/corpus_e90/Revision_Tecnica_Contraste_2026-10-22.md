# Revisión técnica de contraste del corpus E90 — 22/10/2026

**Dictamen:** coincido en **no congelar ni medir**. Los hallazgos REV-E90-01 a REV-E90-06 se confirman, pero el problema de fondo es más amplio: el candidato es tan uniforme que varias métricas de §6.3 podrían cumplirse sin demostrar la capacidad que pretenden medir. La integridad estructural (hashes, particiones, plantillas, procedencia, licencias, CUIT, CI sin AWS) está bien resuelta y no se cuestiona.

Revisión solicitada por el equipo, sobre `e871a59`, rama `codex/corpus-e90`. La realizó un agente (Claude Code) que **no participó en la construcción** del incremento, a partir de los archivos, oráculos y código de la rama. No es revisión de autores, validación jurídica ni experimento de IA. Si cuenta como la revisión técnica independiente de P6 (DO-2026-10-22-CORPUS-CONSTRUCCION) lo decide el equipo. No se modificaron documentos del corpus, oráculos, código ni hashes.

## Verificación ejecutada

| Comando / procedimiento | Resultado observado |
|---|---|
| `python -m pytest -q -p no:cacheprovider tests` (entorno del backend) | 46 aprobadas, una omitida explícitamente (render local optativo). |
| `python -m herramientas.corpus_e90.validar` | `errores=0 congelado=no`. |
| `pdftotext` sobre PDF finales y de referencia | Lectura de E90-M-FAC-01, FAC-06, FAC-08, PRE-03, PRE-07, OC-07, COM-08 y CTR-10. |
| Análisis de `campos_candidatos.json`, `consultas_candidatas.json`, `registros_fuente.json` y `artefactos_candidatos.json` | Recuentos y patrones citados abajo. |
| `git merge-tree` contra `fundacion/local-backend` (`93d4367`) | Sin conflictos. |

No se ejecutaron modelos, embeddings, Textract, AWS ni Terraform.

## Confirmación de REV-E90-01 a REV-E90-06

- **REV-E90-01:** confirmado. `consultas.py` usa el fragmento completo como única afirmación esperada; Q11–Q18 exigen el canal de solicitudes.
- **REV-E90-02:** confirmado y ampliado en REV-E90-07 y REV-E90-08. Además de la glosa, el título nombra la clase («Factura sintética no fiscal»).
- **REV-E90-03:** confirmado y **más grave que lo informado** (REV-E90-09).
- **REV-E90-04:** confirmado y **más grave que lo informado** (REV-E90-10).
- **REV-E90-05:** confirmado y ampliado en REV-E90-11.
- **REV-E90-06:** confirmado; sincronización editorial, sin otra observación.

## Hallazgos adicionales

### REV-E90-07 — P1: valores sin variación de formato ni de contenido

En los 403 registros de campos, al reemplazar dígitos por un comodín, **cada campo tiene un único formato** (salvo `monto_total`, que solo varía en cantidad de dígitos):

- Todas las fechas son `DD/MM/AAAA`; todos los importes `999.999,99`; todos los CUIT `30-XXXXXXXX-X`; las monedas son siempre los códigos `ARS`, `USD` o `EUR`.
- Las 12 entidades se llaman «Entidad Sintética ATLAS E90 NN (ficticia)».
- Los importes son una secuencia determinística: +3.719,01 por caso dentro de cada tipo, +48.347 entre tipos, y los centavos coinciden con el número de caso (CTR-01 73.450,01; CTR-02 77.169,02; COM-01 266.838,01…).
- En los 52 documentos no contractuales, `numero` es el propio ID E90 (52 de 52).
- Las etiquetas impresas coinciden literalmente con los nombres de campo de `comun.ETIQUETAS` («Importe total», «CUIT del emisor»).

Consecuencia: IA-M02 mide principalmente localizar una etiqueta fija y copiar el valor contiguo; la normalización de fechas, importes e identificadores que exige IA-M02 casi no se ejercita. IA-D01/IA-D04 piden registros con proveedores, fechas, importes e identificadores ficticios y «variedad de diseño, formato…»; los nombres y valores actuales no la aportan.

**Corrección propuesta:** razones sociales ficticias verosímiles (verificadas como inexistentes del mismo modo que los CUIT); formatos variados por plantilla (fecha numérica y en letras, `$`, `U$S`, `USD`, «pesos», separadores distintos, CUIT con y sin guiones); importes y números documentales sin relación con el ID; sinónimos de etiquetas por familia. El oráculo conserva el valor normalizado.

### REV-E90-08 — P1: el ID del benchmark como pista transversal

El ID E90 aparece en el subtítulo, como número documental, en «Documentación relacionada» y en **24 de las 30 preguntas** (Q01–Q24). Esto extiende REV-E90-02 a extracción y RAG: la recuperación puede resolverse por coincidencia léxica del ID y la formulación no es natural (RC-P06.2.11).

**Dependencia:** aplicar REV-E90-02 (IDs neutros en el contenido) sin regenerar las preguntas y el campo `numero` rompe Q01–Q24 y 52 referencias. Las correcciones deben aplicarse juntas, en una sola revisión candidata.

### REV-E90-09 — P1: ninguno de los cuatro casos ambiguos es ambiguo

| Caso | Observación |
|---|---|
| E90-M-PRE-07 | Título «Propuesta comercial y presupuesto definitivo»: nombra su propia clase. Glosa «Presenta una oferta económica». |
| E90-M-OC-07 | Título «…orden de compra confirmada»: nombra su propia clase. Glosa: «las referencias a una oferta no cambian su carácter de orden», que resuelve explícitamente la ambigüedad. |
| E90-M-FAC-08 | Título orientado a orden de compra, pero la glosa «Representa un cargo por servicios» delata la clase. |
| E90-M-COM-08 | Sin transformación por la etiqueta compuesta (REV-E90-03). |

El generador (`generar.py`, rama `ambiguo_entre_categorias`) solo cambia el título a «Propuesta comercial y …». **Corrección propuesta:** retirar la glosa y diseñar por tipo una ambigüedad de contenido (por ejemplo, presupuesto con lenguaje de aceptación, factura que referencia una orden), con la justificación previa de la clase esperada que pide REV-E90-03.

### REV-E90-10 — P1: la aclaración embebida neutraliza los adversariales

Los tres casos (CTR-10, FAC-06, COM-08) cierran la instrucción maliciosa con «Este texto pertenece al contenido recibido, no a una instrucción autorizada del operador». La propia pieza le indica al modelo que la ignore, así que el resultado de IA-M07 («ninguna alteración») no permitiría distinguir resistencia del sistema de obediencia a esa aclaración. Junto con el objetivo no contrastable de COM-08 (REV-E90-04), la evidencia adversarial sería débil en los tres casos.

**Corrección propuesta:** retirar la aclaración del contenido (la condición sintética y adversarial ya consta en inventario, oráculo y marca de agua); variar redacción, ubicación y vector (texto de cuerpo, nota al pie, campo de observaciones); en cada caso, apuntar a un valor que contradiga el oráculo (otra clase, otro importe, otro estado).

### REV-E90-11 — P2: las preguntas RAG no ejercitan recuperación ni cláusulas

- 24 preguntas tienen un único documento autorizado; con documentos de una a tres páginas, Recall@5 (IA-M05) queda prácticamente asegurado.
- Las ocho de «condiciones» responden con la misma frase de plantilla («El plazo de entrega es de N días corridos…»), presente incluso en facturas y comprobantes. **Ninguna** pregunta usa las 43 cláusulas adaptadas de las cinco fuentes contractuales.
- Las seis multidocumento piden dos importes de documentos nombrados: son dos preguntas directas yuxtapuestas, sin comparación ni síntesis.
- Q30 anticipa la abstención en la pregunta («…que no está incluido aquí»).

**Corrección propuesta, sin cambiar el reparto 10/8/6/6:** contextos por trámite de varios documentos; condiciones redactadas sobre cláusulas contractuales (rescisión, penalidades, confidencialidad, garantía) de contratos extensos y capturas; multidocumento con comparación real (diferencias de importe, coherencia de plazos); abstenciones distribuidas en contextos distintos y formuladas sin pistas.

### REV-E90-12 — P2: tríadas incoherentes como un mismo trámite

En E90-CONTEXTO-01, presupuesto, orden y factura tienen tres proveedores distintos (E90 02, 03, 04) y tres monedas (USD, EUR, ARS); lo mismo ocurre en E90-CONTEXTO-03. Una secuencia presupuesto → orden → factura de un mismo trámite con tres proveedores y tres monedas no es verosímil, y los documentos se vinculan solo por la lista de IDs impresa. Lo considero defecto de construcción, no solo una justificación pendiente. **Corrección propuesta:** mismo proveedor y moneda por tríada, con importes relacionados (o una discrepancia deliberada y documentada).

### REV-E90-13 — P2: procedencia PDF casi trivial

40 de los 50 documentos de medición tienen una sola página (6 de tres, 2 de dos, uno de 10 y uno de 11). Para esos 40, acertar la página en IA-M03 (≥90 %) está garantizado. **Corrección propuesta:** documentos no contractuales de dos o más páginas en parte de la muestra (detalle de ítems, condiciones en hoja aparte), manteniendo los 50 y los formatos.

### REV-E90-14 — P1 (adenda): plantillas exclusivas de medición casi idénticas a las compartidas

Hallazgo agregado al preparar el diseño v2. En los tipos no contractuales, `generar.py` arma MED_C con la misma tabla de dos columnas que BASE_A y MED_D con la misma lista «Etiqueta: valor» que BASE_B; solo cambian la tipografía, el orden de los campos, un encabezado y el párrafo final. IA-D03 exige al menos una plantilla exclusiva por tipo en medición: formalmente se cumple, pero en la práctica la medición casi no contiene diseños que no estén en ajuste. **Corrección propuesta:** que MED_C y MED_D tengan estructuras propias (por ejemplo, detalle de ítems con subtotal, impuestos y total; formato carta con los datos en prosa).

### REV-E90-15 — P2 (adenda): sujetos compartidos entre particiones e ID en archivos

- Las 12 entidades y los 12 CUIT se asignan con `index % 12` a los 65 registros, así que los mismos sujetos aparecen en ajuste y en medición (por ejemplo, «E90 01» en E90-M-CTR-01 y en E90-A-PRE-02). No es reutilizar ejemplos, pero permite memorizar sujetos durante el ajuste.
- Los nombres de archivo de las entradas, el título en los metadatos del PDF y las propiedades del DOCX son el ID E90. El backend no parece enviar el nombre de archivo al modelo, pero sí lo muestra a quienes evalúan.

**Corrección propuesta:** sujetos disjuntos por partición; nombres de archivo y metadatos neutros, con la correspondencia en el inventario.

## Respuestas del equipo

El 22/10/2026 el equipo respondió que sí a las dos preguntas (DO-2026-10-22-CORPUS-REVISION): esta revisión cuenta como la revisión técnica independiente de P6 y se aprueba en principio la regeneración v2. El diseño está en [Propuesta_Corpus_V2.md](Propuesta_Corpus_V2.md), pendiente de aprobación.

## Alcance de las correcciones

Ninguna de las propuestas cambia cantidades, particiones, tipos, formatos, adversariales, reparto de preguntas ni umbrales: entran en «las variaciones relevantes se incorporan dentro de los 50» (IA-D05). Igualmente requieren regenerar documentos, hashes, localizadores y referencias, por lo que conviene aprobarlas como decisión del equipo y aplicarlas en **una sola revisión candidata v2**. No se cambia ninguna clasificación esperada por conveniencia.

## Cierre de la tarea

- **Tarea:** revisión técnica de contraste del candidato E90 (Etapa 4), solicitada por el equipo.
- **Requisitos cubiertos por la revisión:** §6.3.1; IA-D01, IA-D04, IA-D05, IA-D08; preparación de IA-M02, IA-M03, IA-M05, IA-M06, IA-M07; RC-P06.2. No se declaran métricas alcanzadas.
- **Archivos modificados:** este informe; enlace en la guía de autores; estado de implementación; lista acumulativa de archivos del incremento.
- **Decisiones delegadas tomadas:** ninguna.
- **Diferencias con la tesis registradas:** ninguna. REV-E90-07 a REV-E90-13 son IDs provisionales de hallazgos del candidato.
- **Pruebas:** 46 aprobadas, una omitida explícitamente; validador sin errores.
- **Pendientes o bloqueos:** decidir y aplicar la revisión candidata v2 (REV-E90-01 a 13); luego revisión de ambos autores, congelación y campañas RC-P07.
- **Preguntas para el equipo:** ¿esta revisión cuenta como la revisión técnica independiente de P6? ¿Se aprueba la regeneración v2 con el alcance descrito?
