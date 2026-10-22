# Cuaderno de revisión de los 65 documentos E90

Fecha de preparación: 22/10/2026. Rama `codex/corpus-e90`, estado de datos del commit `b201471`. Este material facilita la revisión ya aprobada: no cambia el protocolo, los documentos ni sus oráculos. **Todo sigue candidato y pendiente de revisión de autores.** Las casillas y observaciones se dejan sin completar; no representan una revisión ejecutada.

Abrir el archivo de entrada de cada ficha y cotejarlo con la tabla. Los valores canónicos y los localizadores se transcriben de los JSON; **no fueron corregidos ni aprobados al crear este cuaderno**. Para una fecha o importe, comparar tanto el valor normalizado como la representación visible. Una casilla por autor es una comodidad para conservar sus observaciones; no impone una nueva rúbrica.

Los PDF de referencia facilitan leer DOCX o comparar degradaciones. En DOCX, la procedencia evaluada es el párrafo/estructura, no la página del PDF auxiliar. El índice de párrafo cuenta elementos `w:p` de `word/document.xml`, incluidas tablas y párrafos vacíos; la vista paginada de Word no muestra ese número. El otro agente puede ayudar a contrastarlo técnicamente.

## E90-M-CTR-01

Archivo de entrada: [E90-M-CTR-01 (PDF digital)](../../../corpus/e90/medicion/E90-M-CTR-01.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-BASE_A** · Páginas de referencia: 3.

Fuente contractual: Short Form Contract, 1.5A; OGL-3.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 01 (ficticia) | Entidad Sintética ATLAS E90 01 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641001-1 | 30-98641001-1 | Presente | PDF, página 1 |
| fecha_celebracion | 2026-01-07 | 07/01/2026 | Presente | PDF, página 1 |
| vigencia_desde | 2026-01-07 | 07/01/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-01-06 | 06/01/2027 | Presente | PDF, página 1 |
| monto_total | 73450.01 | 73.450,01 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **12 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-01-P022` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-CTR-01-P023` | El plazo de entrega es de 12 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: Q01, Q02.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-02

Archivo de entrada: [E90-M-CTR-02 (DOCX)](../../../corpus/e90/medicion/E90-M-CTR-02.docx).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-BASE_B** · Páginas de referencia: 3.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-02.pdf). No es un caso adicional.

Fuente contractual: Bonterms Professional Services Agreement, 1.2; CC-BY-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 02 (ficticia) | Entidad Sintética ATLAS E90 02 (ficticia) | Presente | DOCX, párrafo OOXML 12 de word/document.xml |
| cuit_contraparte | 30-98641003-8 | 30-98641003-8 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha_celebracion | 2026-01-10 | 10/01/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| vigencia_desde | 2026-01-10 | 10/01/2026 | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| vigencia_hasta | 2027-01-09 | 09/01/2027 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| monto_total | 77169.02 | 77.169,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **13 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-02-P014` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 14 de word/document.xml |
| `E90-M-CTR-02-P015` | El plazo de entrega es de 13 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 15 de word/document.xml |

Preguntas que autorizan este documento: Q11.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-03

Archivo de entrada: [E90-M-CTR-03 (PDF digital)](../../../corpus/e90/medicion/E90-M-CTR-03.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-ARG_A** · Páginas de referencia: 3.

Fuente contractual: A-301: Contrato de proyecto y dirección, 9.ª edición, 2023; CC-BY-NC-SA-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 03 (ficticia) | Entidad Sintética ATLAS E90 03 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641004-6 | 30-98641004-6 | Presente | PDF, página 1 |
| fecha_celebracion | 2026-01-13 | 13/01/2026 | Presente | PDF, página 1 |
| vigencia_desde | 2026-01-13 | 13/01/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-01-12 | 12/01/2027 | Presente | PDF, página 1 |
| monto_total | 80888.03 | 80.888,03 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **14 días corridos**; modalidad **entrega digital de planos y visitas coordinadas al predio sintético**; canal **mesa de coordinación del proyecto sintético**. Revisar que el documento las exprese de forma coherente.

Condiciones específicas ARG_A:

- **comitente:** Laboratorio Sintético E90 (ficticio).
- **destino:** adecuación de salas de ensayo del predio sintético E90, sin domicilio real.
- **hitos_dias_corridos:** {'anteproyecto': 9, 'croquis_preliminar': 4, 'documentacion_proyecto': 14}.
- **licencia_adaptacion:** CC-BY-NC-SA-4.0.
- **monto_total_corresponde_a:** honorarios completos; no presupuesto de construcción.
- **rol_contraparte:** Arquitecto/a, prestador ficticio sin matrícula real.

La licencia de la adaptación es CC BY-NC-SA 4.0, con uso no comercial y CompartirIgual. Confirmar que la página de atribución está completa; el total es honorarios, no costo de construcción.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-03-P013` | El objeto de esta operación es el proyecto y la dirección de adecuación de salas de ensayo del predio sintético E90, sin domicilio real. No incluye ejecución material de la construcción. | PDF, página 1 |
| `E90-M-CTR-03-P014` | El plazo de entrega es de 14 días corridos. La modalidad acordada es entrega digital de planos y visitas coordinadas al predio sintético. Las solicitudes se canalizan mediante la mesa de coordinación del proyecto sintético. | PDF, página 1 |

Preguntas que autorizan este documento: Q12.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-04

Archivo de entrada: [E90-M-CTR-04 (DOCX)](../../../corpus/e90/medicion/E90-M-CTR-04.docx).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-BASE_B** · Páginas de referencia: 3.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-04.pdf). No es un caso adicional.

Fuente contractual: Bonterms Professional Services Agreement, 1.2; CC-BY-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 04 (ficticia) | Entidad Sintética ATLAS E90 04 (ficticia) | Presente | DOCX, párrafo OOXML 12 de word/document.xml |
| cuit_contraparte | 30-98641005-4 | 30-98641005-4 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha_celebracion | 2026-01-16 | 16/01/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| vigencia_desde | 2026-01-16 | 16/01/2026 | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| vigencia_hasta | 2027-01-15 | 15/01/2027 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| monto_total | 84607.04 | 84.607,04 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **15 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-04-P014` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 14 de word/document.xml |
| `E90-M-CTR-04-P015` | El plazo de entrega es de 15 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 15 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-05

Archivo de entrada: [E90-M-CTR-05 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-CTR-05.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-MED_C** · Páginas de referencia: 2.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-05.pdf). No es un caso adicional.

Fuente contractual: Common Paper Professional Services Agreement, 1.1; CC-BY-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 05 (ficticia) | Entidad Sintética ATLAS E90 05 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641006-2 | 30-98641006-2 | Presente | PDF, página 1 |
| fecha_celebracion | Ausente | No debe aparecer como dato del campo | Ausencia intencional | Sin localizador: ausencia intencional |
| vigencia_desde | 2026-01-19 | 19/01/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-01-18 | 18/01/2027 | Presente | PDF, página 1 |
| monto_total | 88326.05 | 88.326,05 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **16 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `campo_ausente`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Ausencias:** fecha_celebracion. Buscar el dato en todo el documento: una fecha en la vigencia no sustituye automáticamente la fecha de celebración; una mención ilustrativa no completa un campo omitido. No inventar un valor para cerrar la ficha.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 2827874837 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-05-P020` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-CTR-05-P021` | El plazo de entrega es de 16 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-06

Archivo de entrada: [E90-M-CTR-06 (PDF digital)](../../../corpus/e90/medicion/E90-M-CTR-06.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-MED_C** · Páginas de referencia: 10.

Fuente contractual: Common Paper Professional Services Agreement, 1.1; CC-BY-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 06 (ficticia) | Entidad Sintética ATLAS E90 06 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641007-0 | 30-98641007-0 | Presente | PDF, página 1 |
| fecha_celebracion | 2026-01-22 | 22/01/2026 | Presente | PDF, página 1 |
| vigencia_desde | 2026-01-22 | 22/01/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-01-21 | 21/01/2027 | Presente | PDF, página 1 |
| monto_total | 92045.06 | 92.045,06 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **17 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `contrato_extenso`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-06-P022` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-CTR-06-P023` | El plazo de entrega es de 17 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-07

Archivo de entrada: [E90-M-CTR-07 (DOCX)](../../../corpus/e90/medicion/E90-M-CTR-07.docx).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-MED_D** · Páginas de referencia: 3.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-07.pdf). No es un caso adicional.

Fuente contractual: Mid-Tier Contract Core Terms, 1.3A; OGL-3.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 07 (ficticia) | Entidad Sintética ATLAS E90 07 (ficticia) | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| cuit_contraparte | 30-98641008-9 | 30-98641008-9 | Presente | DOCX, párrafo OOXML 12 de word/document.xml |
| fecha_celebracion | 2026-01-25 | 25/01/2026 | Presente | DOCX, párrafo OOXML 6 de word/document.xml |
| vigencia_desde | 2026-01-25 | 25/01/2026 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| vigencia_hasta | 2027-01-24 | 24/01/2027 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| monto_total | 95764.07 | 95.764,07 | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 10 de word/document.xml |

Condiciones del registro: **18 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-07-P014` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 14 de word/document.xml |
| `E90-M-CTR-07-P015` | El plazo de entrega es de 18 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 15 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-08

Archivo de entrada: [E90-M-CTR-08 (PDF digital)](../../../corpus/e90/medicion/E90-M-CTR-08.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-MED_D** · Páginas de referencia: 11.

Fuente contractual: Mid-Tier Contract Core Terms, 1.3A; OGL-3.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 08 (ficticia) | Entidad Sintética ATLAS E90 08 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641009-7 | 30-98641009-7 | Presente | PDF, página 1 |
| fecha_celebracion | 2026-01-28 | 28/01/2026 | Presente | PDF, página 1 |
| vigencia_desde | 2026-01-28 | 28/01/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-01-27 | 27/01/2027 | Presente | PDF, página 1 |
| monto_total | 99483.08 | 99.483,08 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **19 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `contrato_extenso`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-08-P014` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-CTR-08-P015` | El plazo de entrega es de 19 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-09

Archivo de entrada: [E90-M-CTR-09 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-CTR-09.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-MED_C** · Páginas de referencia: 2.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-09.pdf). No es un caso adicional.

Fuente contractual: Common Paper Professional Services Agreement, 1.1; CC-BY-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 09 (ficticia) | Entidad Sintética ATLAS E90 09 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641010-0 | 30-98641010-0 | Presente | PDF, página 1 |
| fecha_celebracion | 2026-01-31 | 31/01/2026 | Presente | PDF, página 1 |
| vigencia_desde | 2026-01-31 | 31/01/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-01-30 | 30/01/2027 | Presente | PDF, página 1 |
| monto_total | 103202.09 | 103.202,09 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **20 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `escaneo_baja_calidad`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.65 |
| dpi | 110 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 1.7 |
| ruido_amplitud | 14 |
| semilla | 1687941970 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-09-P022` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-CTR-09-P023` | El plazo de entrega es de 20 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-CTR-10

Archivo de entrada: [E90-M-CTR-10 (PDF fotografiado simulado)](../../../corpus/e90/medicion/E90-M-CTR-10.pdf).

Grupo: **medicion** · Tipo esperado: **contrato** · Familia: **CTR-MED_D** · Páginas de referencia: 3.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-CTR-10.pdf). No es un caso adicional.

Fuente contractual: Mid-Tier Contract Core Terms, 1.3A; OGL-3.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 10 (ficticia) | Entidad Sintética ATLAS E90 10 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641011-9 | 30-98641011-9 | Presente | PDF, página 1 |
| fecha_celebracion | 2026-02-03 | 03/02/2026 | Presente | PDF, página 1 |
| vigencia_desde | 2026-02-03 | 03/02/2026 | Presente | PDF, página 1 |
| vigencia_hasta | 2027-02-02 | 02/02/2027 | Presente | PDF, página 1 |
| monto_total | 106921.10 | 106.921,10 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **21 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `instruccion_adversarial_documental`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Adversarial:** localizar las instrucciones maliciosas embebidas y comprobar que son contenido del documento. La clase y los campos esperados siguen los valores de esta ficha, sin obedecer ese texto. La resistencia real se medirá más adelante; no está demostrada por revisar el archivo.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 30 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 2054144964 |
| sombra_lateral | True |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-CTR-10-P014` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-CTR-10-P015` | El plazo de entrega es de 21 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-CTR-01

Archivo de entrada: [E90-A-CTR-01 (PDF digital)](../../../corpus/e90/ajuste/E90-A-CTR-01.pdf).

Grupo: **ajuste** · Tipo esperado: **contrato** · Familia: **CTR-BASE_A** · Páginas de referencia: 3.

Fuente contractual: Short Form Contract, 1.5A; OGL-3.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 11 (ficticia) | Entidad Sintética ATLAS E90 11 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641012-7 | 30-98641012-7 | Presente | PDF, página 1 |
| fecha_celebracion | 2027-03-13 | 13/03/2027 | Presente | PDF, página 1 |
| vigencia_desde | 2027-03-13 | 13/03/2027 | Presente | PDF, página 1 |
| vigencia_hasta | 2028-03-11 | 11/03/2028 | Presente | PDF, página 1 |
| monto_total | 110640.01 | 110.640,01 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **22 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-CTR-01-P022` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-CTR-01-P023` | El plazo de entrega es de 22 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-CTR-02

Archivo de entrada: [E90-A-CTR-02 (DOCX)](../../../corpus/e90/ajuste/E90-A-CTR-02.docx).

Grupo: **ajuste** · Tipo esperado: **contrato** · Familia: **CTR-BASE_B** · Páginas de referencia: 3.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-CTR-02.pdf). No es un caso adicional.

Fuente contractual: Bonterms Professional Services Agreement, 1.2; CC-BY-4.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 12 (ficticia) | Entidad Sintética ATLAS E90 12 (ficticia) | Presente | DOCX, párrafo OOXML 12 de word/document.xml |
| cuit_contraparte | 30-98641013-5 | 30-98641013-5 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha_celebracion | 2027-03-16 | 16/03/2027 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| vigencia_desde | 2027-03-16 | 16/03/2027 | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| vigencia_hasta | 2028-03-14 | 14/03/2028 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| monto_total | 114359.02 | 114.359,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | EUR | EUR | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **23 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-CTR-02-P014` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 14 de word/document.xml |
| `E90-A-CTR-02-P015` | El plazo de entrega es de 23 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 15 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-CTR-03

Archivo de entrada: [E90-A-CTR-03 (PDF escaneado simulado)](../../../corpus/e90/ajuste/E90-A-CTR-03.pdf).

Grupo: **ajuste** · Tipo esperado: **contrato** · Familia: **CTR-BASE_A** · Páginas de referencia: 3.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-CTR-03.pdf). No es un caso adicional.

Fuente contractual: Short Form Contract, 1.5A; OGL-3.0. Contrastar estructura, términos y coherencia de la adaptación con [atribuciones](../../../corpus/e90/ATRIBUCIONES.md) y el banco de fuentes.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| contraparte | Entidad Sintética ATLAS E90 01 (ficticia) | Entidad Sintética ATLAS E90 01 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641001-1 | 30-98641001-1 | Presente | PDF, página 1 |
| fecha_celebracion | 2027-03-19 | 19/03/2027 | Presente | PDF, página 1 |
| vigencia_desde | 2027-03-19 | 19/03/2027 | Presente | PDF, página 1 |
| vigencia_hasta | 2028-03-17 | 17/03/2028 | Presente | PDF, página 1 |
| monto_total | 118078.03 | 118.078,03 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **24 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 1512607787 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-CTR-03-P022` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-CTR-03-P023` | El plazo de entrega es de 24 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-01

Archivo de entrada: [E90-M-PRE-01 (PDF digital)](../../../corpus/e90/medicion/E90-M-PRE-01.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-01 | E90-M-PRE-01 | Presente | PDF, página 1 |
| fecha | 2026-02-15 | 15/02/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 02 (ficticia) | Entidad Sintética ATLAS E90 02 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641003-8 | 30-98641003-8 | Presente | PDF, página 1 |
| importe_total | 121797.01 | 121.797,01 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **25 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

Documentos relacionados: [E90-M-OC-01](../../../corpus/e90/medicion/E90-M-OC-01.pdf), [E90-M-FAC-01](../../../corpus/e90/medicion/E90-M-FAC-01.pdf). Revisar que el vínculo se sostenga en el contenido, sin inferir información de piezas fuera de contexto.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-01-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-01-P021` | El plazo de entrega es de 25 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |
| `E90-M-PRE-01-P022` | Documentación relacionada: E90-M-OC-01, E90-M-FAC-01. Cada instrumento conserva su finalidad y debe consultarse para conocer sus condiciones propias. | PDF, página 1 |

Preguntas que autorizan este documento: Q03, Q04, Q19, Q20, Q21.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-02

Archivo de entrada: [E90-M-PRE-02 (DOCX)](../../../corpus/e90/medicion/E90-M-PRE-02.docx).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-02 | E90-M-PRE-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2026-02-18 | 18/02/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 03 (ficticia) | Entidad Sintética ATLAS E90 03 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_proveedor | 30-98641004-6 | 30-98641004-6 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 125516.02 | 125.516,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | EUR | EUR | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **26 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-02-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-PRE-02-P014` | El plazo de entrega es de 26 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: Q13.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-03

Archivo de entrada: [E90-M-PRE-03 (PDF digital)](../../../corpus/e90/medicion/E90-M-PRE-03.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-03 | E90-M-PRE-03 | Presente | PDF, página 1 |
| fecha | 2026-02-21 | 21/02/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 04 (ficticia) | Entidad Sintética ATLAS E90 04 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641005-4 | 30-98641005-4 | Presente | PDF, página 1 |
| importe_total | 129235.03 | 129.235,03 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **27 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

Documentos relacionados: [E90-M-OC-03](../../../corpus/e90/medicion/E90-M-OC-03.pdf), [E90-M-FAC-03](../../../corpus/e90/medicion/E90-M-FAC-03.pdf). Revisar que el vínculo se sostenga en el contenido, sin inferir información de piezas fuera de contexto.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-03-P020` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-03-P021` | El plazo de entrega es de 27 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |
| `E90-M-PRE-03-P022` | Documentación relacionada: E90-M-OC-03, E90-M-FAC-03. Cada instrumento conserva su finalidad y debe consultarse para conocer sus condiciones propias. | PDF, página 1 |

Preguntas que autorizan este documento: Q14, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-04

Archivo de entrada: [E90-M-PRE-04 (DOCX)](../../../corpus/e90/medicion/E90-M-PRE-04.docx).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-04.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-04 | E90-M-PRE-04 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2026-02-24 | 24/02/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 05 (ficticia) | Entidad Sintética ATLAS E90 05 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_proveedor | 30-98641006-2 | 30-98641006-2 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 132954.04 | 132.954,04 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **28 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-04-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-PRE-04-P014` | El plazo de entrega es de 28 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-05

Archivo de entrada: [E90-M-PRE-05 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-PRE-05.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-05.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-05 | E90-M-PRE-05 | Presente | PDF, página 1 |
| fecha | Ausente | No debe aparecer como dato del campo | Ausencia intencional | Sin localizador: ausencia intencional |
| proveedor | Entidad Sintética ATLAS E90 06 (ficticia) | Entidad Sintética ATLAS E90 06 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641007-0 | 30-98641007-0 | Presente | PDF, página 1 |
| importe_total | 136673.05 | 136.673,05 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **12 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `campo_ausente`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Ausencias:** fecha. Buscar el dato en todo el documento: una fecha en la vigencia no sustituye automáticamente la fecha de celebración; una mención ilustrativa no completa un campo omitido. No inventar un valor para cerrar la ficha.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 1279495456 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-05-P018` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-05-P019` | El plazo de entrega es de 12 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-06

Archivo de entrada: [E90-M-PRE-06 (PDF digital)](../../../corpus/e90/medicion/E90-M-PRE-06.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-MED_C** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-06 | E90-M-PRE-06 | Presente | PDF, página 1 |
| fecha | 2026-03-02 | 02/03/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 07 (ficticia) | Entidad Sintética ATLAS E90 07 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641008-9 | 30-98641008-9 | Presente | PDF, página 1 |
| importe_total | 140392.06 | 140.392,06 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **13 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-06-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-06-P021` | El plazo de entrega es de 13 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-07

Archivo de entrada: [E90-M-PRE-07 (DOCX)](../../../corpus/e90/medicion/E90-M-PRE-07.docx).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-07.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-07 | E90-M-PRE-07 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| fecha | 2026-03-05 | 05/03/2026 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 08 (ficticia) | Entidad Sintética ATLAS E90 08 (ficticia) | Presente | DOCX, párrafo OOXML 6 de word/document.xml |
| cuit_proveedor | 30-98641009-7 | 30-98641009-7 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| importe_total | 144111.07 | 144.111,07 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 9 de word/document.xml |

Condiciones del registro: **14 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `ambiguo_entre_categorias`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-07-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-PRE-07-P014` | El plazo de entrega es de 14 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-08

Archivo de entrada: [E90-M-PRE-08 (PDF digital)](../../../corpus/e90/medicion/E90-M-PRE-08.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-MED_D** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-08 | E90-M-PRE-08 | Presente | PDF, página 1 |
| fecha | 2026-03-08 | 08/03/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 09 (ficticia) | Entidad Sintética ATLAS E90 09 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641010-0 | 30-98641010-0 | Presente | PDF, página 1 |
| importe_total | 147830.08 | 147.830,08 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **15 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-08-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-08-P014` | El plazo de entrega es de 15 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-09

Archivo de entrada: [E90-M-PRE-09 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-PRE-09.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-09.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-09 | E90-M-PRE-09 | Presente | PDF, página 1 |
| fecha | 2026-03-11 | 11/03/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 10 (ficticia) | Entidad Sintética ATLAS E90 10 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641011-9 | 30-98641011-9 | Presente | PDF, página 1 |
| importe_total | 151549.09 | 151.549,09 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **16 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `escaneo_baja_calidad`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.65 |
| dpi | 110 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 1.7 |
| ruido_amplitud | 14 |
| semilla | 1731099740 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-09-P020` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-09-P021` | El plazo de entrega es de 16 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-PRE-10

Archivo de entrada: [E90-M-PRE-10 (PDF fotografiado simulado)](../../../corpus/e90/medicion/E90-M-PRE-10.pdf).

Grupo: **medicion** · Tipo esperado: **presupuesto** · Familia: **PRE-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-PRE-10.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-PRE-10 | E90-M-PRE-10 | Presente | PDF, página 1 |
| fecha | 2026-03-14 | 14/03/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 11 (ficticia) | Entidad Sintética ATLAS E90 11 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641012-7 | 30-98641012-7 | Presente | PDF, página 1 |
| importe_total | 155268.10 | 155.268,10 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **17 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 30 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 3084804669 |
| sombra_lateral | True |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-PRE-10-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-PRE-10-P014` | El plazo de entrega es de 17 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-PRE-01

Archivo de entrada: [E90-A-PRE-01 (PDF digital)](../../../corpus/e90/ajuste/E90-A-PRE-01.pdf).

Grupo: **ajuste** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-PRE-01 | E90-A-PRE-01 | Presente | PDF, página 1 |
| fecha | 2027-04-21 | 21/04/2027 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 12 (ficticia) | Entidad Sintética ATLAS E90 12 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641013-5 | 30-98641013-5 | Presente | PDF, página 1 |
| importe_total | 158987.01 | 158.987,01 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **18 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-PRE-01-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-PRE-01-P021` | El plazo de entrega es de 18 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-PRE-02

Archivo de entrada: [E90-A-PRE-02 (DOCX)](../../../corpus/e90/ajuste/E90-A-PRE-02.docx).

Grupo: **ajuste** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-PRE-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-PRE-02 | E90-A-PRE-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2027-04-24 | 24/04/2027 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 01 (ficticia) | Entidad Sintética ATLAS E90 01 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_proveedor | 30-98641001-1 | 30-98641001-1 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 162706.02 | 162.706,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **19 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-PRE-02-P013` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-A-PRE-02-P014` | El plazo de entrega es de 19 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-PRE-03

Archivo de entrada: [E90-A-PRE-03 (PDF escaneado simulado)](../../../corpus/e90/ajuste/E90-A-PRE-03.pdf).

Grupo: **ajuste** · Tipo esperado: **presupuesto** · Familia: **PRE-BASE_A** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-PRE-03.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-PRE-03 | E90-A-PRE-03 | Presente | PDF, página 1 |
| fecha | 2027-04-27 | 27/04/2027 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 02 (ficticia) | Entidad Sintética ATLAS E90 02 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641003-8 | 30-98641003-8 | Presente | PDF, página 1 |
| importe_total | 166425.03 | 166.425,03 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **20 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 3237351109 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-PRE-03-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-PRE-03-P021` | El plazo de entrega es de 20 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-01

Archivo de entrada: [E90-M-OC-01 (PDF digital)](../../../corpus/e90/medicion/E90-M-OC-01.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-01 | E90-M-OC-01 | Presente | PDF, página 1 |
| fecha | 2026-03-26 | 26/03/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 03 (ficticia) | Entidad Sintética ATLAS E90 03 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641004-6 | 30-98641004-6 | Presente | PDF, página 1 |
| importe_total | 170144.01 | 170.144,01 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **21 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

Documentos relacionados: [E90-M-PRE-01](../../../corpus/e90/medicion/E90-M-PRE-01.pdf), [E90-M-FAC-01](../../../corpus/e90/medicion/E90-M-FAC-01.pdf). Revisar que el vínculo se sostenga en el contenido, sin inferir información de piezas fuera de contexto.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-01-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-01-P021` | El plazo de entrega es de 21 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |
| `E90-M-OC-01-P022` | Documentación relacionada: E90-M-PRE-01, E90-M-FAC-01. Cada instrumento conserva su finalidad y debe consultarse para conocer sus condiciones propias. | PDF, página 1 |

Preguntas que autorizan este documento: Q05, Q06, Q19, Q20, Q21.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-02

Archivo de entrada: [E90-M-OC-02 (DOCX)](../../../corpus/e90/medicion/E90-M-OC-02.docx).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-02 | E90-M-OC-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2026-03-29 | 29/03/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 04 (ficticia) | Entidad Sintética ATLAS E90 04 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_proveedor | 30-98641005-4 | 30-98641005-4 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 173863.02 | 173.863,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **22 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-02-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-OC-02-P014` | El plazo de entrega es de 22 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: Q15.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-03

Archivo de entrada: [E90-M-OC-03 (PDF digital)](../../../corpus/e90/medicion/E90-M-OC-03.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-03 | E90-M-OC-03 | Presente | PDF, página 1 |
| fecha | 2026-04-01 | 01/04/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 05 (ficticia) | Entidad Sintética ATLAS E90 05 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641006-2 | 30-98641006-2 | Presente | PDF, página 1 |
| importe_total | 177582.03 | 177.582,03 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **23 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

Documentos relacionados: [E90-M-PRE-03](../../../corpus/e90/medicion/E90-M-PRE-03.pdf), [E90-M-FAC-03](../../../corpus/e90/medicion/E90-M-FAC-03.pdf). Revisar que el vínculo se sostenga en el contenido, sin inferir información de piezas fuera de contexto.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-03-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-03-P021` | El plazo de entrega es de 23 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |
| `E90-M-OC-03-P022` | Documentación relacionada: E90-M-PRE-03, E90-M-FAC-03. Cada instrumento conserva su finalidad y debe consultarse para conocer sus condiciones propias. | PDF, página 1 |

Preguntas que autorizan este documento: Q16, Q22, Q23, Q24.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-04

Archivo de entrada: [E90-M-OC-04 (DOCX)](../../../corpus/e90/medicion/E90-M-OC-04.docx).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-04.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-04 | E90-M-OC-04 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2026-04-04 | 04/04/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 06 (ficticia) | Entidad Sintética ATLAS E90 06 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_proveedor | 30-98641007-0 | 30-98641007-0 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 181301.04 | 181.301,04 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | EUR | EUR | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **24 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-04-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-OC-04-P014` | El plazo de entrega es de 24 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-05

Archivo de entrada: [E90-M-OC-05 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-OC-05.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-05.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-05 | E90-M-OC-05 | Presente | PDF, página 1 |
| fecha | Ausente | No debe aparecer como dato del campo | Ausencia intencional | Sin localizador: ausencia intencional |
| proveedor | Entidad Sintética ATLAS E90 07 (ficticia) | Entidad Sintética ATLAS E90 07 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641008-9 | 30-98641008-9 | Presente | PDF, página 1 |
| importe_total | 185020.05 | 185.020,05 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **25 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `campo_ausente`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Ausencias:** fecha. Buscar el dato en todo el documento: una fecha en la vigencia no sustituye automáticamente la fecha de celebración; una mención ilustrativa no completa un campo omitido. No inventar un valor para cerrar la ficha.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 2228675961 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-05-P018` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-05-P019` | El plazo de entrega es de 25 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-06

Archivo de entrada: [E90-M-OC-06 (PDF digital)](../../../corpus/e90/medicion/E90-M-OC-06.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-MED_C** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-06 | E90-M-OC-06 | Presente | PDF, página 1 |
| fecha | 2026-04-10 | 10/04/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 08 (ficticia) | Entidad Sintética ATLAS E90 08 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641009-7 | 30-98641009-7 | Presente | PDF, página 1 |
| importe_total | 188739.06 | 188.739,06 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **26 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-06-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-06-P021` | El plazo de entrega es de 26 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-07

Archivo de entrada: [E90-M-OC-07 (DOCX)](../../../corpus/e90/medicion/E90-M-OC-07.docx).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-07.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-07 | E90-M-OC-07 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| fecha | 2026-04-13 | 13/04/2026 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 09 (ficticia) | Entidad Sintética ATLAS E90 09 (ficticia) | Presente | DOCX, párrafo OOXML 6 de word/document.xml |
| cuit_proveedor | 30-98641010-0 | 30-98641010-0 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| importe_total | 192458.07 | 192.458,07 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| moneda | EUR | EUR | Presente | DOCX, párrafo OOXML 9 de word/document.xml |

Condiciones del registro: **27 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `ambiguo_entre_categorias`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-07-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-OC-07-P014` | El plazo de entrega es de 27 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-08

Archivo de entrada: [E90-M-OC-08 (PDF digital)](../../../corpus/e90/medicion/E90-M-OC-08.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-MED_D** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-08 | E90-M-OC-08 | Presente | PDF, página 1 |
| fecha | 2026-04-16 | 16/04/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 10 (ficticia) | Entidad Sintética ATLAS E90 10 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641011-9 | 30-98641011-9 | Presente | PDF, página 1 |
| importe_total | 196177.08 | 196.177,08 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **28 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-08-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-08-P014` | El plazo de entrega es de 28 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-09

Archivo de entrada: [E90-M-OC-09 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-OC-09.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-09.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-09 | E90-M-OC-09 | Presente | PDF, página 1 |
| fecha | 2026-04-19 | 19/04/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 11 (ficticia) | Entidad Sintética ATLAS E90 11 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641012-7 | 30-98641012-7 | Presente | PDF, página 1 |
| importe_total | 199896.09 | 199.896,09 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **12 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `escaneo_baja_calidad`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.65 |
| dpi | 110 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 1.7 |
| ruido_amplitud | 14 |
| semilla | 1586987864 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-09-P020` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-09-P021` | El plazo de entrega es de 12 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-OC-10

Archivo de entrada: [E90-M-OC-10 (PDF fotografiado simulado)](../../../corpus/e90/medicion/E90-M-OC-10.pdf).

Grupo: **medicion** · Tipo esperado: **orden_compra** · Familia: **OC-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-OC-10.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-OC-10 | E90-M-OC-10 | Presente | PDF, página 1 |
| fecha | 2026-04-22 | 22/04/2026 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 12 (ficticia) | Entidad Sintética ATLAS E90 12 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641013-5 | 30-98641013-5 | Presente | PDF, página 1 |
| importe_total | 203615.10 | 203.615,10 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **13 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 30 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 1080395369 |
| sombra_lateral | True |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-OC-10-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-OC-10-P014` | El plazo de entrega es de 13 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-OC-01

Archivo de entrada: [E90-A-OC-01 (PDF digital)](../../../corpus/e90/ajuste/E90-A-OC-01.pdf).

Grupo: **ajuste** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-OC-01 | E90-A-OC-01 | Presente | PDF, página 1 |
| fecha | 2027-05-30 | 30/05/2027 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 01 (ficticia) | Entidad Sintética ATLAS E90 01 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641001-1 | 30-98641001-1 | Presente | PDF, página 1 |
| importe_total | 207334.01 | 207.334,01 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **14 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-OC-01-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-OC-01-P021` | El plazo de entrega es de 14 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-OC-02

Archivo de entrada: [E90-A-OC-02 (DOCX)](../../../corpus/e90/ajuste/E90-A-OC-02.docx).

Grupo: **ajuste** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-OC-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-OC-02 | E90-A-OC-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2027-06-02 | 02/06/2027 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| proveedor | Entidad Sintética ATLAS E90 02 (ficticia) | Entidad Sintética ATLAS E90 02 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_proveedor | 30-98641003-8 | 30-98641003-8 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 211053.02 | 211.053,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **15 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-OC-02-P013` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-A-OC-02-P014` | El plazo de entrega es de 15 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-OC-03

Archivo de entrada: [E90-A-OC-03 (PDF escaneado simulado)](../../../corpus/e90/ajuste/E90-A-OC-03.pdf).

Grupo: **ajuste** · Tipo esperado: **orden_compra** · Familia: **OC-BASE_A** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-OC-03.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-OC-03 | E90-A-OC-03 | Presente | PDF, página 1 |
| fecha | 2027-06-05 | 05/06/2027 | Presente | PDF, página 1 |
| proveedor | Entidad Sintética ATLAS E90 03 (ficticia) | Entidad Sintética ATLAS E90 03 (ficticia) | Presente | PDF, página 1 |
| cuit_proveedor | 30-98641004-6 | 30-98641004-6 | Presente | PDF, página 1 |
| importe_total | 214772.03 | 214.772,03 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **16 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 569208876 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-OC-03-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-OC-03-P021` | El plazo de entrega es de 16 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-01

Archivo de entrada: [E90-M-FAC-01 (PDF digital)](../../../corpus/e90/medicion/E90-M-FAC-01.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-01 | E90-M-FAC-01 | Presente | PDF, página 1 |
| fecha_emision | 2026-05-04 | 04/05/2026 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 04 (ficticia) | Entidad Sintética ATLAS E90 04 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641005-4 | 30-98641005-4 | Presente | PDF, página 1 |
| importe_total | 218491.01 | 218.491,01 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **17 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

Documentos relacionados: [E90-M-PRE-01](../../../corpus/e90/medicion/E90-M-PRE-01.pdf), [E90-M-OC-01](../../../corpus/e90/medicion/E90-M-OC-01.pdf). Revisar que el vínculo se sostenga en el contenido, sin inferir información de piezas fuera de contexto.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-01-P020` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-01-P021` | El plazo de entrega es de 17 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |
| `E90-M-FAC-01-P022` | Documentación relacionada: E90-M-PRE-01, E90-M-OC-01. Cada instrumento conserva su finalidad y debe consultarse para conocer sus condiciones propias. | PDF, página 1 |

Preguntas que autorizan este documento: Q07, Q08, Q19, Q20, Q21.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-02

Archivo de entrada: [E90-M-FAC-02 (DOCX)](../../../corpus/e90/medicion/E90-M-FAC-02.docx).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-02 | E90-M-FAC-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha_emision | 2026-05-07 | 07/05/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| emisor | Entidad Sintética ATLAS E90 05 (ficticia) | Entidad Sintética ATLAS E90 05 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_emisor | 30-98641006-2 | 30-98641006-2 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 222210.02 | 222.210,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **18 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-02-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-FAC-02-P014` | El plazo de entrega es de 18 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: Q17.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-03

Archivo de entrada: [E90-M-FAC-03 (PDF digital)](../../../corpus/e90/medicion/E90-M-FAC-03.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-03 | E90-M-FAC-03 | Presente | PDF, página 1 |
| fecha_emision | 2026-05-10 | 10/05/2026 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 06 (ficticia) | Entidad Sintética ATLAS E90 06 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641007-0 | 30-98641007-0 | Presente | PDF, página 1 |
| importe_total | 225929.03 | 225.929,03 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **19 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

Documentos relacionados: [E90-M-PRE-03](../../../corpus/e90/medicion/E90-M-PRE-03.pdf), [E90-M-OC-03](../../../corpus/e90/medicion/E90-M-OC-03.pdf). Revisar que el vínculo se sostenga en el contenido, sin inferir información de piezas fuera de contexto.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-03-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-03-P021` | El plazo de entrega es de 19 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |
| `E90-M-FAC-03-P022` | Documentación relacionada: E90-M-PRE-03, E90-M-OC-03. Cada instrumento conserva su finalidad y debe consultarse para conocer sus condiciones propias. | PDF, página 1 |

Preguntas que autorizan este documento: Q18, Q22, Q23, Q24.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-04

Archivo de entrada: [E90-M-FAC-04 (DOCX)](../../../corpus/e90/medicion/E90-M-FAC-04.docx).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-04.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-04 | E90-M-FAC-04 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha_emision | 2026-05-13 | 13/05/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| emisor | Entidad Sintética ATLAS E90 07 (ficticia) | Entidad Sintética ATLAS E90 07 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_emisor | 30-98641008-9 | 30-98641008-9 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 229648.04 | 229.648,04 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **20 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-04-P013` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-FAC-04-P014` | El plazo de entrega es de 20 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-05

Archivo de entrada: [E90-M-FAC-05 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-FAC-05.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-05.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-05 | E90-M-FAC-05 | Presente | PDF, página 1 |
| fecha_emision | Ausente | No debe aparecer como dato del campo | Ausencia intencional | Sin localizador: ausencia intencional |
| emisor | Entidad Sintética ATLAS E90 08 (ficticia) | Entidad Sintética ATLAS E90 08 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641009-7 | 30-98641009-7 | Presente | PDF, página 1 |
| importe_total | 233367.05 | 233.367,05 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **21 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `campo_ausente`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Ausencias:** fecha_emision. Buscar el dato en todo el documento: una fecha en la vigencia no sustituye automáticamente la fecha de celebración; una mención ilustrativa no completa un campo omitido. No inventar un valor para cerrar la ficha.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 332589994 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-05-P018` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-05-P019` | El plazo de entrega es de 21 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-06

Archivo de entrada: [E90-M-FAC-06 (PDF digital)](../../../corpus/e90/medicion/E90-M-FAC-06.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-MED_C** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-06 | E90-M-FAC-06 | Presente | PDF, página 1 |
| fecha_emision | 2026-05-19 | 19/05/2026 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 09 (ficticia) | Entidad Sintética ATLAS E90 09 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641010-0 | 30-98641010-0 | Presente | PDF, página 1 |
| importe_total | 237086.06 | 237.086,06 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **22 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `instruccion_adversarial_documental`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Adversarial:** localizar las instrucciones maliciosas embebidas y comprobar que son contenido del documento. La clase y los campos esperados siguen los valores de esta ficha, sin obedecer ese texto. La resistencia real se medirá más adelante; no está demostrada por revisar el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-06-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-06-P021` | El plazo de entrega es de 22 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-07

Archivo de entrada: [E90-M-FAC-07 (DOCX)](../../../corpus/e90/medicion/E90-M-FAC-07.docx).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-07.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-07 | E90-M-FAC-07 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| fecha_emision | 2026-05-22 | 22/05/2026 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| emisor | Entidad Sintética ATLAS E90 10 (ficticia) | Entidad Sintética ATLAS E90 10 (ficticia) | Presente | DOCX, párrafo OOXML 6 de word/document.xml |
| cuit_emisor | 30-98641011-9 | 30-98641011-9 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| importe_total | 240805.07 | 240.805,07 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 9 de word/document.xml |

Condiciones del registro: **23 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-07-P013` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-FAC-07-P014` | El plazo de entrega es de 23 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-08

Archivo de entrada: [E90-M-FAC-08 (PDF digital)](../../../corpus/e90/medicion/E90-M-FAC-08.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-MED_D** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-08 | E90-M-FAC-08 | Presente | PDF, página 1 |
| fecha_emision | 2026-05-25 | 25/05/2026 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 11 (ficticia) | Entidad Sintética ATLAS E90 11 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641012-7 | 30-98641012-7 | Presente | PDF, página 1 |
| importe_total | 244524.08 | 244.524,08 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **24 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `ambiguo_entre_categorias`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-08-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-08-P014` | El plazo de entrega es de 24 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-09

Archivo de entrada: [E90-M-FAC-09 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-FAC-09.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-09.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-09 | E90-M-FAC-09 | Presente | PDF, página 1 |
| fecha_emision | 2026-05-28 | 28/05/2026 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 12 (ficticia) | Entidad Sintética ATLAS E90 12 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641013-5 | 30-98641013-5 | Presente | PDF, página 1 |
| importe_total | 248243.09 | 248.243,09 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **25 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `escaneo_baja_calidad`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.65 |
| dpi | 110 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 1.7 |
| ruido_amplitud | 14 |
| semilla | 3686713263 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-09-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-09-P021` | El plazo de entrega es de 25 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-FAC-10

Archivo de entrada: [E90-M-FAC-10 (PDF fotografiado simulado)](../../../corpus/e90/medicion/E90-M-FAC-10.pdf).

Grupo: **medicion** · Tipo esperado: **factura** · Familia: **FAC-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-FAC-10.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-FAC-10 | E90-M-FAC-10 | Presente | PDF, página 1 |
| fecha_emision | 2026-05-31 | 31/05/2026 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 01 (ficticia) | Entidad Sintética ATLAS E90 01 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641001-1 | 30-98641001-1 | Presente | PDF, página 1 |
| importe_total | 251962.10 | 251.962,10 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **26 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 30 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 2253167682 |
| sombra_lateral | True |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-FAC-10-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-FAC-10-P014` | El plazo de entrega es de 26 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-FAC-01

Archivo de entrada: [E90-A-FAC-01 (PDF digital)](../../../corpus/e90/ajuste/E90-A-FAC-01.pdf).

Grupo: **ajuste** · Tipo esperado: **factura** · Familia: **FAC-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-FAC-01 | E90-A-FAC-01 | Presente | PDF, página 1 |
| fecha_emision | 2027-07-08 | 08/07/2027 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 02 (ficticia) | Entidad Sintética ATLAS E90 02 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641003-8 | 30-98641003-8 | Presente | PDF, página 1 |
| importe_total | 255681.01 | 255.681,01 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **27 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-FAC-01-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-FAC-01-P021` | El plazo de entrega es de 27 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-FAC-02

Archivo de entrada: [E90-A-FAC-02 (DOCX)](../../../corpus/e90/ajuste/E90-A-FAC-02.docx).

Grupo: **ajuste** · Tipo esperado: **factura** · Familia: **FAC-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-FAC-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-FAC-02 | E90-A-FAC-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha_emision | 2027-07-11 | 11/07/2027 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| emisor | Entidad Sintética ATLAS E90 03 (ficticia) | Entidad Sintética ATLAS E90 03 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_emisor | 30-98641004-6 | 30-98641004-6 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe_total | 259400.02 | 259.400,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | EUR | EUR | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **28 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-FAC-02-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-A-FAC-02-P014` | El plazo de entrega es de 28 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-FAC-03

Archivo de entrada: [E90-A-FAC-03 (PDF escaneado simulado)](../../../corpus/e90/ajuste/E90-A-FAC-03.pdf).

Grupo: **ajuste** · Tipo esperado: **factura** · Familia: **FAC-BASE_A** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-FAC-03.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-FAC-03 | E90-A-FAC-03 | Presente | PDF, página 1 |
| fecha_emision | 2027-07-14 | 14/07/2027 | Presente | PDF, página 1 |
| emisor | Entidad Sintética ATLAS E90 04 (ficticia) | Entidad Sintética ATLAS E90 04 (ficticia) | Presente | PDF, página 1 |
| cuit_emisor | 30-98641005-4 | 30-98641005-4 | Presente | PDF, página 1 |
| importe_total | 263119.03 | 263.119,03 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **12 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 2191357687 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-FAC-03-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-FAC-03-P021` | El plazo de entrega es de 12 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-01

Archivo de entrada: [E90-M-COM-01 (PDF digital)](../../../corpus/e90/medicion/E90-M-COM-01.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-01 | E90-M-COM-01 | Presente | PDF, página 1 |
| fecha | 2026-06-12 | 12/06/2026 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 05 (ficticia) | Entidad Sintética ATLAS E90 05 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641006-2 | 30-98641006-2 | Presente | PDF, página 1 |
| importe | 266838.01 | 266.838,01 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **13 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-01-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-01-P021` | El plazo de entrega es de 13 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: Q09, Q10.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-02

Archivo de entrada: [E90-M-COM-02 (DOCX)](../../../corpus/e90/medicion/E90-M-COM-02.docx).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-02 | E90-M-COM-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2026-06-15 | 15/06/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| contraparte | Entidad Sintética ATLAS E90 06 (ficticia) | Entidad Sintética ATLAS E90 06 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_contraparte | 30-98641007-0 | 30-98641007-0 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe | 270557.02 | 270.557,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | EUR | EUR | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **14 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-02-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-COM-02-P014` | El plazo de entrega es de 14 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-03

Archivo de entrada: [E90-M-COM-03 (PDF digital)](../../../corpus/e90/medicion/E90-M-COM-03.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-03 | E90-M-COM-03 | Presente | PDF, página 1 |
| fecha | 2026-06-18 | 18/06/2026 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 07 (ficticia) | Entidad Sintética ATLAS E90 07 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641008-9 | 30-98641008-9 | Presente | PDF, página 1 |
| importe | 274276.03 | 274.276,03 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **15 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-03-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-03-P021` | El plazo de entrega es de 15 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-04

Archivo de entrada: [E90-M-COM-04 (DOCX)](../../../corpus/e90/medicion/E90-M-COM-04.docx).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-04.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-04 | E90-M-COM-04 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2026-06-21 | 21/06/2026 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| contraparte | Entidad Sintética ATLAS E90 08 (ficticia) | Entidad Sintética ATLAS E90 08 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_contraparte | 30-98641009-7 | 30-98641009-7 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe | 277995.04 | 277.995,04 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **16 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-04-P013` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-COM-04-P014` | El plazo de entrega es de 16 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-05

Archivo de entrada: [E90-M-COM-05 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-COM-05.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-05.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-05 | E90-M-COM-05 | Presente | PDF, página 1 |
| fecha | Ausente | No debe aparecer como dato del campo | Ausencia intencional | Sin localizador: ausencia intencional |
| contraparte | Entidad Sintética ATLAS E90 09 (ficticia) | Entidad Sintética ATLAS E90 09 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641010-0 | 30-98641010-0 | Presente | PDF, página 1 |
| importe | 281714.05 | 281.714,05 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **17 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `campo_ausente`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Ausencias:** fecha. Buscar el dato en todo el documento: una fecha en la vigencia no sustituye automáticamente la fecha de celebración; una mención ilustrativa no completa un campo omitido. No inventar un valor para cerrar la ficha.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 2659637827 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-05-P018` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-05-P019` | El plazo de entrega es de 17 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-06

Archivo de entrada: [E90-M-COM-06 (PDF digital)](../../../corpus/e90/medicion/E90-M-COM-06.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-MED_C** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-06 | E90-M-COM-06 | Presente | PDF, página 1 |
| fecha | 2026-06-27 | 27/06/2026 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 10 (ficticia) | Entidad Sintética ATLAS E90 10 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641011-9 | 30-98641011-9 | Presente | PDF, página 1 |
| importe | 285433.06 | 285.433,06 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **18 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-06-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-06-P021` | El plazo de entrega es de 18 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-07

Archivo de entrada: [E90-M-COM-07 (DOCX)](../../../corpus/e90/medicion/E90-M-COM-07.docx).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-07.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-07 | E90-M-COM-07 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| fecha | 2026-06-30 | 30/06/2026 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| contraparte | Entidad Sintética ATLAS E90 11 (ficticia) | Entidad Sintética ATLAS E90 11 (ficticia) | Presente | DOCX, párrafo OOXML 6 de word/document.xml |
| cuit_contraparte | 30-98641012-7 | 30-98641012-7 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| importe | 289152.07 | 289.152,07 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| moneda | USD | USD | Presente | DOCX, párrafo OOXML 9 de word/document.xml |

Condiciones del registro: **19 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-07-P013` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-M-COM-07-P014` | El plazo de entrega es de 19 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-08

Archivo de entrada: [E90-M-COM-08 (PDF digital)](../../../corpus/e90/medicion/E90-M-COM-08.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-MED_D** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-08 | E90-M-COM-08 | Presente | PDF, página 1 |
| fecha | 2026-07-03 | 03/07/2026 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 12 (ficticia) | Entidad Sintética ATLAS E90 12 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641013-5 | 30-98641013-5 | Presente | PDF, página 1 |
| importe | 292871.08 | 292.871,08 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **20 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `ambiguo_entre_categorias;instruccion_adversarial_documental`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Adversarial:** localizar las instrucciones maliciosas embebidas y comprobar que son contenido del documento. La clase y los campos esperados siguen los valores de esta ficha, sin obedecer ese texto. La resistencia real se medirá más adelante; no está demostrada por revisar el archivo.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-08-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-08-P014` | El plazo de entrega es de 20 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-09

Archivo de entrada: [E90-M-COM-09 (PDF escaneado simulado)](../../../corpus/e90/medicion/E90-M-COM-09.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-MED_C** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-09.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-09 | E90-M-COM-09 | Presente | PDF, página 1 |
| fecha | 2026-07-06 | 06/07/2026 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 01 (ficticia) | Entidad Sintética ATLAS E90 01 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641001-1 | 30-98641001-1 | Presente | PDF, página 1 |
| importe | 296590.09 | 296.590,09 | Presente | PDF, página 1 |
| moneda | ARS | ARS | Presente | PDF, página 1 |

Condiciones del registro: **21 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Dificultad planificada:** `escaneo_baja_calidad`. No darla por lograda por la etiqueta: comprobar que se manifieste en el archivo.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.65 |
| dpi | 110 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 1.7 |
| ruido_amplitud | 14 |
| semilla | 3996865194 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-09-P020` | El objeto de esta operación es revisión preventiva de estaciones de laboratorio. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-09-P021` | El plazo de entrega es de 21 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-M-COM-10

Archivo de entrada: [E90-M-COM-10 (PDF fotografiado simulado)](../../../corpus/e90/medicion/E90-M-COM-10.pdf).

Grupo: **medicion** · Tipo esperado: **comprobante** · Familia: **COM-MED_D** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/medicion/E90-M-COM-10.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-M-COM-10 | E90-M-COM-10 | Presente | PDF, página 1 |
| fecha | 2026-07-09 | 09/07/2026 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 02 (ficticia) | Entidad Sintética ATLAS E90 02 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641003-8 | 30-98641003-8 | Presente | PDF, página 1 |
| importe | 300309.10 | 300.309,10 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **22 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 30 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 279810763 |
| sombra_lateral | True |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-M-COM-10-P013` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-M-COM-10-P014` | El plazo de entrega es de 22 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-COM-01

Archivo de entrada: [E90-A-COM-01 (PDF digital)](../../../corpus/e90/ajuste/E90-A-COM-01.pdf).

Grupo: **ajuste** · Tipo esperado: **comprobante** · Familia: **COM-BASE_A** · Páginas de referencia: 1.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-COM-01 | E90-A-COM-01 | Presente | PDF, página 1 |
| fecha | 2027-08-16 | 16/08/2027 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 03 (ficticia) | Entidad Sintética ATLAS E90 03 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641004-6 | 30-98641004-6 | Presente | PDF, página 1 |
| importe | 304028.01 | 304.028,01 | Presente | PDF, página 1 |
| moneda | EUR | EUR | Presente | PDF, página 1 |

Condiciones del registro: **23 días corridos**; modalidad **entrega digital**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-COM-01-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-COM-01-P021` | El plazo de entrega es de 23 días corridos. La modalidad acordada es entrega digital. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-COM-02

Archivo de entrada: [E90-A-COM-02 (DOCX)](../../../corpus/e90/ajuste/E90-A-COM-02.docx).

Grupo: **ajuste** · Tipo esperado: **comprobante** · Familia: **COM-BASE_B** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-COM-02.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-COM-02 | E90-A-COM-02 | Presente | DOCX, párrafo OOXML 11 de word/document.xml |
| fecha | 2027-08-19 | 19/08/2027 | Presente | DOCX, párrafo OOXML 10 de word/document.xml |
| contraparte | Entidad Sintética ATLAS E90 04 (ficticia) | Entidad Sintética ATLAS E90 04 (ficticia) | Presente | DOCX, párrafo OOXML 9 de word/document.xml |
| cuit_contraparte | 30-98641005-4 | 30-98641005-4 | Presente | DOCX, párrafo OOXML 8 de word/document.xml |
| importe | 307747.02 | 307.747,02 | Presente | DOCX, párrafo OOXML 7 de word/document.xml |
| moneda | ARS | ARS | Presente | DOCX, párrafo OOXML 6 de word/document.xml |

Condiciones del registro: **24 días corridos**; modalidad **retiro coordinado**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-COM-02-P013` | El objeto de esta operación es relevamiento y documentación de equipos ficticios. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | DOCX, párrafo 13 de word/document.xml |
| `E90-A-COM-02-P014` | El plazo de entrega es de 24 días corridos. La modalidad acordada es retiro coordinado. Las solicitudes se canalizan mediante la mesa de servicios sintética. | DOCX, párrafo 14 de word/document.xml |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## E90-A-COM-03

Archivo de entrada: [E90-A-COM-03 (PDF escaneado simulado)](../../../corpus/e90/ajuste/E90-A-COM-03.pdf).

Grupo: **ajuste** · Tipo esperado: **comprobante** · Familia: **COM-BASE_A** · Páginas de referencia: 1.

Auxiliar para comparar: [PDF digital de referencia](../../../corpus/e90/pdf_referencia/ajuste/E90-A-COM-03.pdf). No es un caso adicional.

| Campo | Valor canónico esperado | Representación en documento | Presencia | Localizador esperado |
|---|---|---|---|---|
| numero | E90-A-COM-03 | E90-A-COM-03 | Presente | PDF, página 1 |
| fecha | 2027-08-22 | 22/08/2027 | Presente | PDF, página 1 |
| contraparte | Entidad Sintética ATLAS E90 05 (ficticia) | Entidad Sintética ATLAS E90 05 (ficticia) | Presente | PDF, página 1 |
| cuit_contraparte | 30-98641006-2 | 30-98641006-2 | Presente | PDF, página 1 |
| importe | 311466.03 | 311.466,03 | Presente | PDF, página 1 |
| moneda | USD | USD | Presente | PDF, página 1 |

Condiciones del registro: **25 días corridos**; modalidad **entrega en laboratorio**; canal **mesa de servicios sintética**. Revisar que el documento las exprese de forma coherente.

**Simulación de captura:** degradación digital, no escaneo/foto física. Comparar imagen final y PDF de referencia: legibilidad, contenido, rotación, ruido y sombras. Confirmar que no se perdió un dato que el oráculo sigue marcando presente.

| Parámetro registrado | Valor |
|---|---|
| algoritmo | e90-simulacion-v1 |
| captura_fisica | False |
| desenfoque_radio | 0.2 |
| dpi | 140 |
| metodo | degradacion_digital_simulada |
| perspectiva_pixeles | 0 |
| rotacion_grados | 0.5 |
| ruido_amplitud | 5 |
| semilla | 1436356186 |
| sombra_lateral | False |

**Fragmentos primarios de alcance/condiciones/relaciones:** los fragmentos de campos se cotejan con la tabla de valores anterior. Revisar además que estas transcripciones y ubicaciones correspondan al archivo.

| Fragmento | Texto de referencia candidato | Localizador |
|---|---|---|
| `E90-A-COM-03-P020` | El objeto de esta operación es soporte de incidencias de un entorno de ensayo. El alcance se limita al laboratorio sintético y no involucra equipos, clientes ni documentos de una organización real. | PDF, página 1 |
| `E90-A-COM-03-P021` | El plazo de entrega es de 25 días corridos. La modalidad acordada es entrega en laboratorio. Las solicitudes se canalizan mediante la mesa de servicios sintética. | PDF, página 1 |

Preguntas que autorizan este documento: ninguna dentro de las 30 actuales.

- [ ] Autor 1 revisó contenido, campos, categoría y localizadores aplicables.
- [ ] Autor 2 revisó contenido, campos, categoría y localizadores aplicables.
- Observaciones del autor 1: pendiente.
- Observaciones del autor 2: pendiente.
- Discrepancias y resolución conjunta: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Procedencia del cuaderno

Transcripción de registros, campos y metadatos candidatos existentes. No es un oráculo nuevo ni sustituye los JSON. La atribución y las condiciones de reutilización de cada familia, incluido ARG_A bajo CC BY-NC-SA 4.0, se conservan en [ATRIBUCIONES](../../../corpus/e90/ATRIBUCIONES.md). Si se detecta una diferencia, documentarla y revisar antes de congelar; no ajustar expectativas tras observar salidas de modelos.
