# Auditoría estructural de PD-07 para preparar el corpus E90

Fecha: 22/10/2026. Base: `1e2a6c6`. Estado: **auditoría estática parcial, sin modificar originales ni cerrar criterios de aceptación**.

## Resultado comprobado

Se inspeccionaron los cinco PDF y sus cinco fuentes DOCX, el generador reproducible y el oráculo preliminar. Los cinco hashes PDF coinciden y las páginas coinciden con el oráculo: 10 del contrato y una de cada orden/factura, 14 en total. Todos contienen texto extraíble y la marca de documento ficticio en cada página PDF y en las fuentes DOCX; los tamaños y cantidades de páginas se encuentran dentro de los límites comprobados de RC-P04.

En los campos presentes en el oráculo se comprobó presencia de la representación esperada tanto en el PDF como en el XML del DOCX. Esto es un cotejo de presencia textual normalizada, no una prueba de exactitud semántica ni de que un sistema extraiga el campo correcto. Los siete localizadores del contrato apuntan a páginas que contienen la representación esperada. Los tres conjuntos de R1–R4 del JSON coinciden con el recálculo estático sobre sus valores; no se ejecutó la API ni se verificaron reglas del sistema desplegado.

## Hallazgos para resolver

| ID provisional | Hallazgo | Acción pendiente |
|---|---|---|
| CORPUS-E90-PROP-01 | Faltan ocho referencias de RC-P04 en el oráculo: número y proveedor de O-v1/O-v2, y número y emisor de F-v1/F-v2 | Proponer su incorporación, cotejar identificadores contra documentos y acordar el esquema. DIF-84 permanece abierta |
| CORPUS-E90-PROP-02 | Solo el contrato tiene localizadores PDF por campo; los cuatro auxiliares no los tienen. No hay localizadores estructurales DOCX en el oráculo | Preparar referencias de página y estructura, con revisión antes de congelar |
| CORPUS-E90-PROP-03 | El CUIT sigue candidato con consulta ARCA pendiente | Documentar consulta según PD-07; no sustituir por validación del dígito |
| CORPUS-E90-PROP-04 | El oráculo identifica la factura con una etiqueta específica de pieza sintética, distinta del identificador de clase `factura` de RC-P04 | Documentar correspondencia para el evaluador; no contar una etiqueta editorial como nueva categoría del dominio |
| CORPUS-E90-PROP-05 | No se verificó una fuente contractual pública atribuida para el contrato actual | Revisar procedencia; no transferir este documento a medición ni usarlo como modelo público autorizado |

El plan E90 existente tiene 65 filas de diseño, 50 previstas para medición y 15 para ajuste; 13 por tipo, con BASE_A/BASE_B compartidas y MED_C/MED_D exclusivas por tipo, y tres marcas adversariales. Este recuento no acredita que existan esos archivos.

## Método y evidencia

Se usaron biblioteca estándar para SHA-256, JSON, CSV, XML y ZIP, y pypdf 6.10.0 del runtime de Codex para páginas/texto PDF. El DOCX se leyó como contenedor OOXML, sin ejecutar el generador. El registro `Auditoria_PD07_Evidencia_Estructural.json` conserva verificaciones por documento, campos faltantes, localizadores, recuentos y hashes de entrada. No contiene texto extraído ni respuestas de IA. El script temporal de auditoría está en `/tmp/auditar_pd07_corpus_e90.py`; su hash está en la evidencia. Los archivos temporales no son artefactos permanentes del repositorio.

No se regeneraron DOCX ni PDF. La revisión visual completa y la equivalencia de render DOCX/PDF no se ejecutaron. No se consultó ARCA, no se llamó a AWS y no se midió IA. No se marca `Cumple`, no se congela el corpus y no se modifica el registro global de diferencias. Una revisión técnica de otro agente puede contrastar estos hallazgos; no sustituye las revisiones humanas exigidas.
