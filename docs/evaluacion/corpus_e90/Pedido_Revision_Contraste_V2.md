# Pedido de revisión técnica de contraste — corpus E90 v2

Pedido del equipo según P0 de DO-2026-10-22-CORPUS-REVISION: la v2 la construyó Claude Code; la revisión de contraste la hace el otro agente.

---

Revisá la revisión candidata **v2** del corpus E90 en la rama `codex/corpus-e90`. Los datos y el código están en `2082a6e` y la documentación en `d5f20ba`. La construyó Claude Code según el diseño aprobado P0–P16 (`docs/evaluacion/corpus_e90/Propuesta_Corpus_V2.md`). Esta es la revisión técnica de contraste que exige P0: no la construiste vos, así que revisala como revisor independiente, no como autor.

**Leé primero:** `AGENTS.md`; DO-2026-10-22-CORPUS-REVISION y su adenda en `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md`; `docs/evaluacion/corpus_e90/Informe_Revision_V2.md`; `Revision_Tecnica_Contraste_2026-10-22.md` (hallazgos REV-E90-01 a 15); `Guia_Revision_Autores_E90.md`.

**Alcance y restricciones:**
- Solo lectura sobre `corpus/e90/`, `oraculos/e90/` y `herramientas/corpus_e90/`. No regeneres, no corrijas archivos ni oráculos y no cambies hashes. Si encontrás un defecto, documentalo con una corrección propuesta.
- No ejecutes modelos, Textract, Bedrock, AWS ni Terraform. No congeles nada ni marques revisiones de autores.
- No consultes ARCA ni registros de sociedades: esas verificaciones son manuales del equipo (`Verificaciones_Pendientes_V2.md`).
- No ajustes umbrales, oráculos ni pruebas para que algo pase. Si una prueba falla, informalo con su salida.

**1. Reproducir las verificaciones**
- `python -m herramientas.corpus_e90.validar`
- `python herramientas/validar_inventario_e90.py --inventario oraculos/e90/inventario_candidato.csv`
- `python -m pytest -q -p no:cacheprovider tests`
- Si tenés python-docx, Pillow y LibreOffice: `E90_PRUEBAS_RENDER=1 python -m pytest -q tests/corpus_e90`.
- Opcional: generar en una raíz limpia (`herramientas/corpus_e90/README.md`) y comparar con lo instalado. Lo esperado: registros, fragmentos, consultas y DOCX idénticos; PDF distintos en bytes.

**2. Comprobar que cada REV-E90-01 a 15 quedó resuelto en los archivos, no solo en el informe**
- Ningún ID E90 en el contenido, los metadatos, los nombres de archivo ni las preguntas. Sin glosas de función ni aclaraciones de construcción.
- Sujetos y CUIT disjuntos entre ajuste y medición. Variedad real de formatos de fecha, importe, moneda, CUIT y número documental.
- MED_C y MED_D estructuralmente distintos de BASE_A y BASE_B en los cuatro tipos no contractuales.
- Al menos 15 documentos no contractuales de medición con 2 o más páginas, y campos fuera de la página 1.
- Trámites T1–T4: mismo proveedor y moneda, importes relacionados y referencias por número; la diferencia de T3 está registrada.

**3. Revisión semántica (lo que los validadores no cubren)**
- **Ambigüedad:** abrí PRE-07, OC-07, FAC-08 y COM-08 (rutas en el índice de `Cuaderno_Revision_Documentos_E90.md`). ¿Son ambiguos de verdad? ¿La clase esperada se sostiene con la justificación registrada? ¿Queda alguna pista que la delate (número documental, verbos, título)?
- **Adversariales:** CTR-10, FAC-06 y COM-08. ¿El texto es visible tras la simulación de captura? ¿Cada objetivo contradice el oráculo? ¿Algún fragmento del documento le avisa al modelo que lo ignore?
- **Preguntas:** abrí cada contexto y respondé Q01–Q30 vos mismo. Verificá que las afirmaciones sean correctas, completas, limitadas a lo preguntado y sostenidas por los fragmentos citados. Verificá que las seis abstenciones no tengan respuesta en el contexto y juzgá si la redacción es natural (RC-P06.2.11).
- **Campos:** en una muestra de al menos 15 documentos de todas las familias y formatos (incluidas capturas y DOCX), cotejá valor normalizado, representación impresa, etiqueta y página o párrafo contra el archivo final. En capturas, mirá la imagen, no solo el PDF de referencia.
- **Distractores:** neto, IVA y total en MED_C; fecha de emisión frente a fecha de entrega o vencimiento; las dos fechas en una sola oración de las cartas MED_D.

**4. Riesgos que el constructor ya señaló y conviene juzgar**
- En los casos no ambiguos, los títulos comerciales nombran la clase («Factura», «Orden de compra»). Esto se trata como evidencia natural, no como pista. ¿Lo compartís?
- Las cláusulas adaptadas del banco aprobado conservan observaciones como «documento ficticio» o «predio sintético E90».
- El comprador ficticio es común a los 65 documentos.
- Los hashes de PDF no se pueden reproducir entre ejecuciones de LibreOffice.
- La inspección visual del constructor fue de baja resolución.

**5. Entregable**
- Escribí `docs/evaluacion/corpus_e90/Revision_Contraste_V2_<fecha>.md` con:
  - dictamen (apto o no apto para la revisión de autores);
  - comandos ejecutados y sus resultados;
  - hallazgos nuevos numerados desde REV-E90-16, cada uno con severidad, evidencia (ID de documento o pregunta y ubicación) y corrección propuesta.
- Si conviene, agregá un JSON de evidencia.
- Actualizá `docs/plan/Estado_Implementacion.md` y `Archivos_Incremento.txt`, y commiteá en la misma rama sin push.
- Informá con el formato de `AGENTS.md` §6.8.
