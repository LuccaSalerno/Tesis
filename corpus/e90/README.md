# Corpus sintético E90 candidato

50 documentos de medición y 15 de ajuste. Estado: **CANDIDATO_NO_CONGELADO**. El equipo informó consulta manual ARCA del 22/10/2026, «No existe» para los doce CUIT; evidencia en `docs/evaluacion/corpus_e90/Verificacion_Manual_CUIT_ARCA_2026-10-22.md`. Referencias y preguntas no revisadas por los autores. Los archivos generados antes de ese reporte conservan su leyenda histórica de consulta pendiente.

Los únicos archivos de entrada de la muestra están en `medicion/` y `ajuste/`, enumerados en `oraculos/e90/inventario_candidato.csv`. Los DOCX fuente y PDF de referencia de las otras carpetas son auxiliares reproducibles y no aumentan el N de medición. Las transformaciones de los PDF de imágenes son simulaciones digitales declaradas, con parámetros y semilla por documento.

Registros previos: `registros_fuente.json`. Herramientas, dependencias, comandos de validación y procedimiento de revisión: `herramientas/corpus_e90/README.md`. No usar esta muestra como inventario de PD-07 ni como evidencia de validación operativa real.

DO-2026-10-22-CORPUS-ARG-A: E90-M-CTR-03 usa la familia argentina CPAU, exclusiva de medición, en reemplazo de una repetición de BASE_A. Los otros 64 documentos conservan sus hashes. ARG_A y sus adaptaciones/extractos se distribuyen bajo CC BY-NC-SA 4.0 para uso no comercial: ver `ATRIBUCIONES.md`. No se modifica la licencia del código ni de las otras fuentes.
