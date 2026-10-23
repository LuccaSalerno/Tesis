# Revisión de los autores por muestreo — candidata v3 del corpus E90

**Decisión:** DO-2026-10-23-E90-MUESTREO. **Datos:** candidata v3 (commit `5388569` y verificaciones manuales en `83ac903`). La revisión la hacen los autores: el agente no marca ninguna casilla.

Cómo trabajar: abrí cada cuaderno, buscá la sección indicada (por ejemplo «## Q07» o «## E90-M-PRE-05») y abrí el archivo enlazado. Marcá las casillas del cuaderno («Autor 1» o «Autor 2») y anotá cualquier observación ahí mismo. Al final, completá la sección «Cierre» de este documento.

Cualquier error de una referencia se corrige en `herramientas/corpus_e90/` y se regenera la candidata completa: **no** se editan a mano los archivos ni los oráculos.

## Parte 1 — Las 30 preguntas de RAG (unos 30 minutos)

Archivo: [Cuaderno_Revision_Consultas_RAG_E90.md](Cuaderno_Revision_Consultas_RAG_E90.md), secciones **Q01 a Q30**.

En cada pregunta:
- [ ] Se entiende y se responde solo con los documentos del «Contexto autorizado».
- [ ] Las «Afirmaciones esperadas» son correctas según el texto de los «Fragmentos citados» (abrí el documento si dudás).
- [ ] En las de categoría `sin_evidencia` (6 preguntas), los documentos autorizados realmente no contienen la respuesta.

Q11 y Q12 tienen además una precisión que el cuaderno no muestra (REV-E90-19). Confirmá que estás de acuerdo con este texto, que va en `variantes_admitidas` de ambas:

> Se aceptan como correctos los plazos y supuestos más específicos del extracto en inglés del modelo público (fragmento ORIGEN), con cita a ese extracto, siempre que no contradigan la adaptación española; no se exigen para una respuesta completa.

- [ ] Acuerdo con las variantes admitidas de Q11 y Q12.

## Parte 2 — Los casos difíciles (unos 15 minutos)

Archivo: [Cuaderno_Revision_Documentos_E90.md](Cuaderno_Revision_Documentos_E90.md). Son seis documentos: COM-08 es a la vez ambiguo y adversarial.

| Sección del cuaderno | Archivo | Formato | Qué confirmar |
|---|---|---|---|
| E90-M-CTR-10 | `corpus/e90/medicion/doc-a24529ac.pdf` | PDF fotografiado | Adversarial: el texto de la instrucción está en el documento y la clase esperada (contrato) se sostiene |
| E90-M-FAC-06 | `corpus/e90/medicion/doc-3c9c847a.pdf` | PDF digital | Adversarial: el CUIT de la instrucción (`30-11111111-1`) es inválido a propósito y la clase (factura) se sostiene |
| E90-M-COM-08 | `corpus/e90/medicion/doc-3e0a6e6d.pdf` | PDF digital | Ambiguo y adversarial: es una constancia (comprobante), no una factura, aunque cite la factura e incluya la instrucción |
| E90-M-PRE-07 | `corpus/e90/medicion/doc-a8069d15.docx` | DOCX | Ambiguo: presupuesto con aceptación en blanco, no orden de compra |
| E90-M-OC-07 | `corpus/e90/medicion/doc-6084b5de.docx` | DOCX | Ambiguo: orden de compra, no presupuesto; número **neutro** `55372/2026`, sin «OC» (REV-E90-18) |
| E90-M-FAC-08 | `corpus/e90/medicion/doc-70812f2a.pdf` | PDF digital | Ambiguo: factura (reclama un pago con vencimiento), no comprobante |

En cada uno: leé la «Ambigüedad diseñada» o el «Contenido adversarial» del cuaderno, abrí el archivo y confirmá que la clase esperada es la correcta.

## Parte 3 — Muestra de 10 documentos contra el original (unos 15 minutos)

Archivo: el mismo [Cuaderno_Revision_Documentos_E90.md](Cuaderno_Revision_Documentos_E90.md). En cada documento, compará la tabla de campos (valor, representación impresa y localizador) con el archivo.

| Sección del cuaderno | Archivo | Formato | Qué mirar además |
|---|---|---|---|
| E90-M-PRE-05 | `corpus/e90/medicion/doc-20e840a1.pdf` | PDF escaneado | REV-E90-16: neto, IVA 21 %, «Ajuste por redondeo» y total cuadran |
| E90-M-PRE-09 | `corpus/e90/medicion/doc-6114e8de.pdf` | PDF escaneado | REV-E90-16: lo mismo |
| E90-M-OC-01 | `corpus/e90/medicion/doc-3b7b0d68.pdf` | PDF digital | REV-E90-17: «18 días desde la recepción conforme» |
| E90-M-PRE-06 | `corpus/e90/medicion/doc-3e698236.pdf` | PDF digital | REV-E90-17: «pago a 18 días desde la recepción conforme» |
| E90-M-OC-02 | `corpus/e90/medicion/doc-20b64e04.docx` | DOCX | REV-E90-17: «14 días desde la entrega» |
| E90-M-CTR-06 | `corpus/e90/medicion/doc-de08cb56.pdf` | PDF digital | REV-E90-19: extracto en inglés bajo «Correspondencia con el modelo público» |
| E90-M-CTR-08 | `corpus/e90/medicion/doc-ef93a9e2.pdf` | PDF digital | REV-E90-19: lo mismo |
| E90-M-FAC-10 | `corpus/e90/medicion/doc-ff4307be.pdf` | PDF fotografiado | Legibilidad de la captura simulada |
| E90-M-FAC-02 | `corpus/e90/medicion/doc-c6546cb9.docx` | DOCX | Vencimiento 31/03/2026 (respuesta de Q18) |
| E90-A-PRE-03 | `corpus/e90/ajuste/doc-3081542c.pdf` | PDF escaneado | Un documento de la partición de ajuste |

## Cierre

Completar cuando terminen las tres partes:

- Revisó la parte 1: …… (nombre y fecha)
- Revisó la parte 2: …… (nombre y fecha)
- Revisó la parte 3: …… (nombre y fecha)
- Observaciones que exigen corregir y regenerar: …… (o «ninguna»)
- Aprobación de la congelación de la v3: …… (ambos autores)

Alcance que se declara en §6.6: los autores revisaron por muestreo las 30 preguntas, los 6 casos difíciles y 10 documentos. El resto de las referencias se validó con controles automáticos (cotejo de los 403 campos con sus localizadores, aritmética, trámites, particiones y huellas) y con la revisión de contraste de otro agente sobre 25 documentos.
