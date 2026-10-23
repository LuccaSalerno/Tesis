# Cuaderno de revisión de las 30 preguntas RAG E90

Revisión candidata **e90-candidato-v3** (DO-2026-10-22-CORPUS-REVISION), datos del commit `5388569`. Estado: **CANDIDATO_NO_CONGELADO**. Este cuaderno se genera con `python -m herramientas.corpus_e90.cuadernos`; no cambia documentos ni oráculos. **Todo sigue candidato y pendiente de revisión de autores.** Las casillas y observaciones se dejan sin completar; no representan una revisión ejecutada.

> **Revisión registrada (DO-2026-10-23-E90-MUESTREO):** los autores Ivo Gonsé (autor 1) y Lucca Salerno (autor 2) revisaron juntos las 30 preguntas el 23/10/2026 e informaron en el chat que todas están correctas, incluidas las variantes admitidas de Q11 y Q12. Si el cuaderno se regenera, hay que trasladar este registro.

Aquí se revisan preguntas y referencias **antes de ejecutar modelos**. Las evaluaciones de respuestas de IA (IA-M06) se completarán después de ejecutar. Para cada pregunta: leer el contexto autorizado, intentar responder desde los documentos y cotejar las afirmaciones esperadas. Aceptar equivalencia semántica conforme a RC-P06.2; las afirmaciones se limitan a lo preguntado.

## Q01

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Cuál es el importe total de la orden de compra emitida a Calibraciones del Litoral Norte S.R.L.?

**Contexto autorizado (4):** [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf) (presupuesto), [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf) (orden_compra), [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx) (factura), [E90-M-COM-01](../../../corpus/e90/medicion/doc-b3500bdf.pdf) (comprobante).

**Afirmaciones esperadas:**

- El importe total de la orden de compra es 3.699.990,10.
- Está expresado en pesos argentinos (ARS).

**Fragmentos citados:**

- `E90-M-OC-01-CAMPO-importe_total` — [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf); PDF, página 1. Texto: 3.699.990,10
- `E90-M-OC-01-CAMPO-moneda` — [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf); PDF, página 1. Texto: ARS

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q02

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Qué número tiene la factura de Calibraciones del Litoral Norte S.R.L. por mantenimiento preventivo de cabinas de seguridad biológica?

**Contexto autorizado (4):** [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf) (presupuesto), [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf) (orden_compra), [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx) (factura), [E90-M-COM-01](../../../corpus/e90/medicion/doc-b3500bdf.pdf) (comprobante).

**Afirmaciones esperadas:**

- La factura tiene el número 00002-00052952.

**Fragmentos citados:**

- `E90-M-FAC-07-CAMPO-numero` — [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx); DOCX, párrafo 3. Texto: Ref.: Factura N.º 00002-00052952

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q03

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Hasta qué fecha está vigente el contrato con Servicios Técnicos Arroyo Seco S.A.?

**Contexto autorizado (3):** [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx) (contrato), [E90-M-OC-02](../../../corpus/e90/medicion/doc-20b64e04.docx) (orden_compra), [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx) (factura).

**Afirmaciones esperadas:**

- El contrato está vigente hasta el 21/02/2027.

**Fragmentos citados:**

- `E90-M-CTR-02-CAMPO-vigencia_hasta` — [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx); DOCX, párrafo 8. Texto: Finalización: 21-02-2027

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q04

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿En qué fecha se emitió el presupuesto de Metrolab Patagonia Sur S.R.L.?

**Contexto autorizado (3):** [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf) (presupuesto), [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf) (orden_compra), [E90-M-FAC-03](../../../corpus/e90/medicion/doc-7f20797a.pdf) (factura).

**Afirmaciones esperadas:**

- El presupuesto se emitió el 16/03/2026.

**Fragmentos citados:**

- `E90-M-PRE-03-CAMPO-fecha` — [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf); PDF, página 1. Texto: 16/03/2026

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q05

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Por qué importe se dejó constancia de la recepción de los servicios de Ingeniería Cuenca del Salado S.A.?

**Contexto autorizado (3):** [E90-M-OC-04](../../../corpus/e90/medicion/doc-2429ee82.docx) (orden_compra), [E90-M-FAC-04](../../../corpus/e90/medicion/doc-68df9b02.docx) (factura), [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf) (comprobante).

**Afirmaciones esperadas:**

- La constancia registra un importe de 2.242,86.
- Está expresado en euros (EUR).

**Fragmentos citados:**

- `E90-M-COM-08-CAMPO-importe` — [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf); PDF, página 1. Texto: Lo recibido corresponde a un importe total de 2.242,86 euros (dos mil doscientos cuarenta y dos con 86/100).
- `E90-M-COM-08-CAMPO-moneda` — [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf); PDF, página 1. Texto: Lo recibido corresponde a un importe total de 2.242,86 euros (dos mil doscientos cuarenta y dos con 86/100).

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q06

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Cuál es el precio total del contrato de servicios técnicos y en qué moneda está expresado?

**Contexto autorizado (1):** [E90-M-CTR-09](../../../corpus/e90/medicion/doc-9426a983.pdf) (contrato).

**Afirmaciones esperadas:**

- El monto total es 9.681.580,07.
- Está expresado en pesos argentinos (ARS).

**Fragmentos citados:**

- `E90-M-CTR-09-CAMPO-monto_total` — [E90-M-CTR-09](../../../corpus/e90/medicion/doc-9426a983.pdf); PDF, página 1 (referencia previa a la simulación). Texto: Precio: ARS 9.681.580,07
- `E90-M-CTR-09-CAMPO-moneda` — [E90-M-CTR-09](../../../corpus/e90/medicion/doc-9426a983.pdf); PDF, página 1 (referencia previa a la simulación). Texto: Precio: ARS 9.681.580,07

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q07

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Cuál es el monto total de honorarios del encargo de proyecto y dirección?

**Contexto autorizado (1):** [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf) (contrato).

**Afirmaciones esperadas:**

- El monto total es 10.697.817,75.
- Está expresado en pesos argentinos (ARS).

**Fragmentos citados:**

- `E90-M-CTR-03-CAMPO-monto_total` — [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf); PDF, página 1. Texto: Precio total: 10.697.817,75
- `E90-M-CTR-03-CAMPO-moneda` — [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf); PDF, página 1. Texto: Moneda: pesos argentinos

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q08

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Qué número tiene la orden de compra?

**Contexto autorizado (1):** [E90-M-OC-10](../../../corpus/e90/medicion/doc-35699f69.pdf) (orden_compra).

**Afirmaciones esperadas:**

- La orden de compra tiene el número OC/94217/2026.

**Fragmentos citados:**

- `E90-M-OC-10-CAMPO-numero` — [E90-M-OC-10](../../../corpus/e90/medicion/doc-35699f69.pdf); PDF, página 1 (referencia previa a la simulación). Texto: Ref.: Orden de compra N.º OC/94217/2026

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q09

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Cuál es el CUIT del proveedor que emitió la cotización?

**Contexto autorizado (1):** [E90-M-PRE-02](../../../corpus/e90/medicion/doc-fe20a4c5.docx) (presupuesto).

**Afirmaciones esperadas:**

- El CUIT del proveedor es 30-98641004-6.

**Fragmentos citados:**

- `E90-M-PRE-02-CAMPO-cuit_proveedor` — [E90-M-PRE-02](../../../corpus/e90/medicion/doc-fe20a4c5.docx); DOCX, párrafo 7. Texto: C.U.I.T. N.º: 30986410046

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q10

Categoría: **directa** · Clase: **respondible**.

**Pregunta:** ¿Cuál es el CUIT del emisor de la factura?

**Contexto autorizado (1):** [E90-M-FAC-06](../../../corpus/e90/medicion/doc-3c9c847a.pdf) (factura).

**Afirmaciones esperadas:**

- El CUIT del emisor es 30-98641007-0.

**Fragmentos citados:**

- `E90-M-FAC-06-CAMPO-cuit_emisor` — [E90-M-FAC-06](../../../corpus/e90/medicion/doc-3c9c847a.pdf); PDF, página 1. Texto: CUIT 30-98641007-0

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q11

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** ¿En qué casos puede una de las partes dar por terminado el contrato?

**Contexto autorizado (1):** [E90-M-CTR-06](../../../corpus/e90/medicion/doc-de08cb56.pdf) (contrato).

**Afirmaciones esperadas:**

- Ante un incumplimiento material no subsanado.
- Ante una imposibilidad grave de continuidad.
- Por otra causal pactada.
- La parte debe notificar el motivo.

**Fragmentos citados:**

- `E90-M-CTR-06-CLAUSULA-7` — [E90-M-CTR-06](../../../corpus/e90/medicion/doc-de08cb56.pdf); PDF, página 8. Texto: La relación tendrá la duración indicada por sus condiciones particulares. Una parte podrá dar por terminado el acuerdo ante un incumplimiento material no subsanado, una imposibilidad grave de continuidad u otra causal pa
- `E90-M-CTR-06-ORIGEN-7` — [E90-M-CTR-06](../../../corpus/e90/medicion/doc-de08cb56.pdf); PDF, página 8. Texto: Term & TerminationTerm. This Agreement will start on the Effective Date and continue until 12 months have elapsed since the end of the latest SOW Term end date.Termination.Either party may terminate this Agreement or an 

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q12

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** Si el proveedor incurre en un incumplimiento notificable, ¿qué puede pedirle el comprador y qué puede hacer con lo que reciba?

**Contexto autorizado (1):** [E90-M-CTR-08](../../../corpus/e90/medicion/doc-ef93a9e2.pdf) (contrato).

**Afirmaciones esperadas:**

- El comprador puede solicitar un plan de rectificación con las acciones y plazos propuestos.
- Puede aceptar el plan o rechazarlo con razones.
- Ante un rechazo, puede requerir una versión revisada.

**Fragmentos citados:**

- `E90-M-CTR-08-CLAUSULA-7` — [E90-M-CTR-08](../../../corpus/e90/medicion/doc-ef93a9e2.pdf); PDF, página 8. Texto: Un incumplimiento notificable deberá comunicarse y, cuando se solicite, se presentará un plan de rectificación con las acciones y plazos propuestos. El comprador podrá aceptarlo o rechazarlo con razones. Ante un rechazo,
- `E90-M-CTR-08-ORIGEN-7` — [E90-M-CTR-08](../../../corpus/e90/medicion/doc-ef93a9e2.pdf); PDF, página 8. Texto: If there is a Notifiable Default, the Supplier must notify the Buyer within three (3) Working Days of the Supplier becoming aware of the Notifiable Default and the Buyer may request that the Supplier provide a Rectificat

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q13

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** ¿Cómo se resuelven las controversias en el contrato de proyecto y dirección?

**Contexto autorizado (1):** [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf) (contrato).

**Afirmaciones esperadas:**

- Primero se prevé una mediación.
- Si la controversia persiste, se prevé una pericia arbitral.

**Fragmentos citados:**

- `E90-M-CTR-03-CLAUSULA-8` — [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf); PDF, página 2. Texto: El modelo de procedencia prevé mediación y, de persistir la controversia, pericia arbitral. Se conserva esa secuencia como rasgo del escenario documental argentino. No se reproduce un compromiso arbitral ni se afirma la 

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q14

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** En el contrato con Servicios Técnicos Arroyo Seco S.A., ¿de cuántos días dispone el cliente para revisar un entregable sujeto a aceptación?

**Contexto autorizado (3):** [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx) (contrato), [E90-M-OC-02](../../../corpus/e90/medicion/doc-20b64e04.docx) (orden_compra), [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx) (factura).

**Afirmaciones esperadas:**

- El cliente dispone de un período de prueba de quince días.

**Fragmentos citados:**

- `E90-M-CTR-02-CLAUSULA-3` — [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx); DOCX, párrafo 17. Texto: Cuando un entregable esté sujeto a aceptación, el cliente dispondrá de un período de prueba de quince días para revisar su conformidad material con las especificaciones. Si encuentra diferencias, deberá describirlas razo

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q15

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** ¿Qué información queda excluida de la obligación de reserva?

**Contexto autorizado (1):** [E90-M-CTR-01](../../../corpus/e90/medicion/doc-fd733e9e.pdf) (contrato).

**Afirmaciones esperadas:**

- La información ya pública.
- La recibida legítimamente de un tercero.
- La desarrollada de manera independiente.

**Fragmentos citados:**

- `E90-M-CTR-01-CLAUSULA-6` — [E90-M-CTR-01](../../../corpus/e90/medicion/doc-fd733e9e.pdf); PDF, página 2. Texto: Cada parte mantendrá segura y reservada la información confidencial que reciba. No la divulgará ni la explotará sin consentimiento previo, salvo para la finalidad prevista en el acuerdo o una excepción expresamente admit

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q16

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** ¿Por cuánto tiempo es válida la oferta de Metrolab Patagonia Sur S.R.L. y cómo se paga?

**Contexto autorizado (3):** [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf) (presupuesto), [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf) (orden_compra), [E90-M-FAC-03](../../../corpus/e90/medicion/doc-7f20797a.pdf) (factura).

**Afirmaciones esperadas:**

- La oferta es válida por 30 días corridos.
- La forma de pago es pago a 14 días desde la entrega.

**Fragmentos citados:**

- `E90-M-PRE-03-COND-validez` — [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf); PDF, página 2. Texto: Validez de la oferta: 30 días corridos.
- `E90-M-PRE-03-COND-forma_pago` — [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf); PDF, página 2. Texto: Forma de pago: pago a 14 días desde la entrega.

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q17

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** ¿Dónde y en qué fecha debe entregarse lo pedido a Calibraciones del Litoral Norte S.R.L.?

**Contexto autorizado (4):** [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf) (presupuesto), [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf) (orden_compra), [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx) (factura), [E90-M-COM-01](../../../corpus/e90/medicion/doc-b3500bdf.pdf) (comprobante).

**Afirmaciones esperadas:**

- Debe entregarse en Laboratorio de Metrología, planta baja.
- La fecha de entrega comprometida es el 11/07/2026.

**Fragmentos citados:**

- `E90-M-OC-01-COND-lugar` — [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf); PDF, página 1. Texto: Lugar de entrega: Laboratorio de Metrología, planta baja.
- `E90-M-OC-01-COND-fecha_entrega` — [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf); PDF, página 1. Texto: Fecha de entrega comprometida: 11/07/2026.

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q18

Categoría: **condiciones** · Clase: **respondible**.

**Pregunta:** ¿Cuándo vence el pago de la factura de Servicios Técnicos Arroyo Seco S.A.?

**Contexto autorizado (3):** [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx) (contrato), [E90-M-OC-02](../../../corpus/e90/medicion/doc-20b64e04.docx) (orden_compra), [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx) (factura).

**Afirmaciones esperadas:**

- El pago vence el 31/03/2026.

**Fragmentos citados:**

- `E90-M-FAC-02-COND-vencimiento` — [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx); DOCX, párrafo 15. Texto: Vencimiento del pago: 31-03-2026.

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q19

Categoría: **multidocumento** · Clase: **respondible**.

**Pregunta:** ¿El importe de la orden de compra coincide con el del presupuesto de Calibraciones del Litoral Norte S.R.L.?

**Contexto autorizado (4):** [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf) (presupuesto), [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf) (orden_compra), [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx) (factura), [E90-M-COM-01](../../../corpus/e90/medicion/doc-b3500bdf.pdf) (comprobante).

**Afirmaciones esperadas:**

- Sí, los importes coinciden.
- El presupuesto y la orden de compra indican 3.699.990,10 ARS.

**Fragmentos citados:**

- `E90-M-PRE-06-CAMPO-importe_total` — [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf); PDF, página 2. Texto: Total ARS 3.699.990,10
- `E90-M-OC-01-CAMPO-importe_total` — [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf); PDF, página 1. Texto: 3.699.990,10

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q20

Categoría: **multidocumento** · Clase: **respondible**.

**Pregunta:** ¿La factura de Metrolab Patagonia Sur S.R.L. se emitió por el mismo importe que la orden de compra?

**Contexto autorizado (3):** [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf) (presupuesto), [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf) (orden_compra), [E90-M-FAC-03](../../../corpus/e90/medicion/doc-7f20797a.pdf) (factura).

**Afirmaciones esperadas:**

- No, los importes no coinciden.
- La orden de compra indica 2.461.923,75 ARS.
- La factura indica 2.658.877,65 ARS.
- La factura supera a la orden en 196.953,90 ARS.

**Fragmentos citados:**

- `E90-M-OC-06-CAMPO-importe_total` — [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf); PDF, página 2. Texto: Total ARS 2.461.923,75
- `E90-M-FAC-03-CAMPO-importe_total` — [E90-M-FAC-03](../../../corpus/e90/medicion/doc-7f20797a.pdf); PDF, página 1. Texto: 2.658.877,65

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q21

Categoría: **multidocumento** · Clase: **respondible**.

**Pregunta:** ¿Qué documento previo cita la factura de Calibraciones del Litoral Norte S.R.L. y forma parte del trámite?

**Contexto autorizado (4):** [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf) (presupuesto), [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf) (orden_compra), [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx) (factura), [E90-M-COM-01](../../../corpus/e90/medicion/doc-b3500bdf.pdf) (comprobante).

**Afirmaciones esperadas:**

- La factura cita la orden de compra OC 4500072485.
- Esa orden de compra forma parte del trámite.

**Fragmentos citados:**

- `E90-M-FAC-07-REF` — [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx); DOCX, párrafo 7. Texto: Corresponde a la orden de compra OC 4500072485.
- `E90-M-OC-01-CAMPO-numero` — [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf); PDF, página 1. Texto: OC 4500072485

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q22

Categoría: **multidocumento** · Clase: **respondible**.

**Pregunta:** ¿La factura de Servicios Técnicos Arroyo Seco S.A. se emitió dentro de la vigencia del contrato?

**Contexto autorizado (3):** [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx) (contrato), [E90-M-OC-02](../../../corpus/e90/medicion/doc-20b64e04.docx) (orden_compra), [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx) (factura).

**Afirmaciones esperadas:**

- Sí, se emitió dentro de la vigencia.
- La factura es del 16/03/2026.
- El contrato rige desde el 22/02/2026 hasta el 21/02/2027.

**Fragmentos citados:**

- `E90-M-FAC-02-CAMPO-fecha_emision` — [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx); DOCX, párrafo 4. Texto: Fecha de emisión: 16-03-2026
- `E90-M-CTR-02-CAMPO-vigencia_desde` — [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx); DOCX, párrafo 7. Texto: Inicio de vigencia: 22-02-2026
- `E90-M-CTR-02-CAMPO-vigencia_hasta` — [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx); DOCX, párrafo 8. Texto: Finalización: 21-02-2027

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q23

Categoría: **multidocumento** · Clase: **respondible**.

**Pregunta:** ¿Qué factura cita la constancia de conformidad y coincide su importe con el de esa factura?

**Contexto autorizado (3):** [E90-M-OC-04](../../../corpus/e90/medicion/doc-2429ee82.docx) (orden_compra), [E90-M-FAC-04](../../../corpus/e90/medicion/doc-68df9b02.docx) (factura), [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf) (comprobante).

**Afirmaciones esperadas:**

- La constancia cita la factura 0004-00013478.
- Sí, ambos documentos indican 2.242,86 EUR.

**Fragmentos citados:**

- `E90-M-COM-08-OBJETO` — [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf); PDF, página 1. Texto: Por la presente dejamos constancia de haber recibido de conformidad los servicios de validación térmica de autoclaves y estufas, correspondientes a su factura 0004-00013478.
- `E90-M-COM-08-CAMPO-importe` — [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf); PDF, página 1. Texto: Lo recibido corresponde a un importe total de 2.242,86 euros (dos mil doscientos cuarenta y dos con 86/100).
- `E90-M-FAC-04-CAMPO-numero` — [E90-M-FAC-04](../../../corpus/e90/medicion/doc-68df9b02.docx); DOCX, párrafo 3. Texto: N.º: 0004-00013478
- `E90-M-FAC-04-CAMPO-importe_total` — [E90-M-FAC-04](../../../corpus/e90/medicion/doc-68df9b02.docx); DOCX, párrafo 11. Texto: Total: € 2.242,86

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q24

Categoría: **multidocumento** · Clase: **respondible**.

**Pregunta:** ¿Cuántos días pasaron entre el presupuesto y la orden de compra de Metrolab Patagonia Sur S.R.L.?

**Contexto autorizado (3):** [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf) (presupuesto), [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf) (orden_compra), [E90-M-FAC-03](../../../corpus/e90/medicion/doc-7f20797a.pdf) (factura).

**Afirmaciones esperadas:**

- El presupuesto es del 16/03/2026.
- La orden de compra es del 28/03/2026.
- Pasaron 12 días.

**Fragmentos citados:**

- `E90-M-PRE-03-CAMPO-fecha` — [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf); PDF, página 1. Texto: 16/03/2026
- `E90-M-OC-06-CAMPO-fecha` — [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf); PDF, página 1. Texto: Fecha 28/03/26

- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q25

Categoría: **sin_evidencia** · Clase: **sin_evidencia**.

**Pregunta:** ¿Qué penalidad corresponde si Calibraciones del Litoral Norte S.R.L. entrega con demora?

**Contexto autorizado (4):** [E90-M-PRE-06](../../../corpus/e90/medicion/doc-3e698236.pdf) (presupuesto), [E90-M-OC-01](../../../corpus/e90/medicion/doc-3b7b0d68.pdf) (orden_compra), [E90-M-FAC-07](../../../corpus/e90/medicion/doc-2c029784.docx) (factura), [E90-M-COM-01](../../../corpus/e90/medicion/doc-b3500bdf.pdf) (comprobante).

**Abstención esperada.** Motivo: Los documentos fijan lugar y fecha de entrega, pero no establecen penalidades por demora.


- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q26

Categoría: **sin_evidencia** · Clase: **sin_evidencia**.

**Pregunta:** ¿Cuál es el monto de la multa por rescisión anticipada del contrato con Servicios Técnicos Arroyo Seco S.A.?

**Contexto autorizado (3):** [E90-M-CTR-02](../../../corpus/e90/medicion/doc-7cc20e6f.docx) (contrato), [E90-M-OC-02](../../../corpus/e90/medicion/doc-20b64e04.docx) (orden_compra), [E90-M-FAC-02](../../../corpus/e90/medicion/doc-c6546cb9.docx) (factura).

**Abstención esperada.** Motivo: El contrato no fija una multa por rescisión anticipada.


- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q27

Categoría: **sin_evidencia** · Clase: **sin_evidencia**.

**Pregunta:** ¿A qué cuenta bancaria hay que transferir el pago de la factura de Metrolab Patagonia Sur S.R.L.?

**Contexto autorizado (3):** [E90-M-PRE-03](../../../corpus/e90/medicion/doc-d416ed6c.pdf) (presupuesto), [E90-M-OC-06](../../../corpus/e90/medicion/doc-3bdfeb7c.pdf) (orden_compra), [E90-M-FAC-03](../../../corpus/e90/medicion/doc-7f20797a.pdf) (factura).

**Abstención esperada.** Motivo: La factura indica la forma de pago, pero no informa un número de cuenta.


- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q28

Categoría: **sin_evidencia** · Clase: **sin_evidencia**.

**Pregunta:** ¿Qué número de remito acompañó la entrega de los servicios de Ingeniería Cuenca del Salado S.A.?

**Contexto autorizado (3):** [E90-M-OC-04](../../../corpus/e90/medicion/doc-2429ee82.docx) (orden_compra), [E90-M-FAC-04](../../../corpus/e90/medicion/doc-68df9b02.docx) (factura), [E90-M-COM-08](../../../corpus/e90/medicion/doc-3e0a6e6d.pdf) (comprobante).

**Abstención esperada.** Motivo: Ningún documento del trámite menciona un remito.


- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q29

Categoría: **sin_evidencia** · Clase: **sin_evidencia**.

**Pregunta:** ¿Qué garantía de cumplimiento en dinero debe constituir el prestador?

**Contexto autorizado (1):** [E90-M-CTR-09](../../../corpus/e90/medicion/doc-9426a983.pdf) (contrato).

**Abstención esperada.** Motivo: El contrato no exige una garantía de cumplimiento en dinero.


- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.

## Q30

Categoría: **sin_evidencia** · Clase: **sin_evidencia**.

**Pregunta:** ¿Cuál es el presupuesto de construcción de la obra?

**Contexto autorizado (1):** [E90-M-CTR-03](../../../corpus/e90/medicion/doc-c4507e4a.pdf) (contrato).

**Abstención esperada.** Motivo: El monto pactado corresponde solo a honorarios; el contrato no informa el costo de construcción.


- [x] Autor 1 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- [x] Autor 2 revisó pregunta, contexto y afirmaciones o motivo de abstención.
- Observaciones del autor 1: ninguna (Ivo Gonsé, 23/10/2026; revisión conjunta informada en el chat).
- Observaciones del autor 2: ninguna (Lucca Salerno, 23/10/2026; revisión por muestreo informada en el chat).
- Discrepancias y resolución previa a medir: pendiente.
- Referencia de revisión (nombres, fecha y commit de datos): pendiente.
