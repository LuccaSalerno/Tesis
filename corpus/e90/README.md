# Corpus sintético E90 (v3, congelado el 23/10/2026)

50 documentos de medición y 15 de ajuste. Versión **e90-candidato-v3** (DO-2026-10-22-CORPUS-REVISION, con las correcciones de REV-E90-16 a 19 de DO-2026-10-23-CIERRE D5). Estado: **CANDIDATO_NO_CONGELADO**; referencias y preguntas sin revisión de autores.

Los únicos archivos de entrada están en `medicion/` y `ajuste/`, con nombres neutros (`doc-<8 hex>`). La correspondencia con el ID de inventario (E90-M-CTR-01, etc.) figura solo en `oraculos/e90/inventario_candidato.csv` y en los cuadernos de revisión: ni el contenido, ni los metadatos, ni el nombre del archivo la revelan. Los DOCX de `fuentes_docx/` y los PDF de `pdf_referencia/` son auxiliares reproducibles y no aumentan el N. Los PDF escaneados y fotografiados son simulaciones digitales declaradas, con parámetros y semilla por documento.

Contenido de la v3 (misma estructura que la v2):

- Razones sociales ficticias verosímiles, 12 en medición y 6 en ajuste, sin repetirse entre particiones; un comprador ficticio común. Los 12 CUIT de medición son los del reporte ARCA del equipo del 22/10/2026; los 6 de ajuste y las razones sociales se verificaron a mano: ver `docs/evaluacion/corpus_e90/Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md`.
- Formatos por familia de plantilla: fechas `dd/mm/aaaa`, `dd-mm-aaaa`, `dd/mm/aa` o en letras; importes con o sin símbolo; moneda por código, símbolo o nombre; CUIT con o sin guiones; numeración documental propia de cada tipo.
- Estructuras distintas por familia: tabla (BASE_A), lista (BASE_B), detalle de ítems con neto, IVA y total (MED_C) y carta con los datos en la prosa (MED_D). 20 documentos no contractuales de medición tienen más de una página.
- Cuatro trámites coherentes (mismo proveedor y moneda, importes relacionados, referencias por número); T3 tiene una diferencia deliberada entre orden y factura.
- Cuatro casos de ambigüedad de contenido con justificación previa y tres adversariales con objetivos que contradicen el oráculo.

Registros previos: `registros_fuente.json`. Herramientas y comandos: `herramientas/corpus_e90/README.md`. La v1 queda en Git (`f68da7c`) y su manifiesto en `docs/evaluacion/corpus_e90/v1/`. No usar esta muestra como inventario de PD-07 ni como evidencia de validación operativa real.

ARG_A (E90-M-CTR-03) y sus extractos se distribuyen bajo CC BY-NC-SA 4.0 para uso no comercial: ver `ATRIBUCIONES.md`.
