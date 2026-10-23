# Verificaciones manuales de la v2 (completadas)

**Actualización del 23/10/2026:** el equipo informó «No existe» para los seis CUIT de ajuste y «Sin coincidencia observada» para las 18 razones sociales ([registro](Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md)). No hubo que reemplazar ninguna. Siguen vigentes para la v3, que no cambió sujetos ni CUIT.

P2 y P3 de DO-2026-10-22-CORPUS-REVISION: las razones sociales y los CUIT son ficticios, pero un dígito verificador válido o un nombre inventado no acreditan que no existan. Antes de congelar, el equipo verifica a mano cada razón social (por ejemplo, en buscadores públicos de sociedades) y los seis CUIT nuevos de ajuste en ARCA, y registra fecha y resultado. El agente no hizo ni simula estas consultas.

Si un nombre o un CUIT coincide con uno real, se reemplaza en `herramientas/corpus_e90/preparar.py` y se regenera la revisión candidata completa (hashes, localizadores y preguntas).

| Razón social | Partición | CUIT asignado | Consulta CUIT (ARCA) | Verificación de la razón social |
|---|---|---|---|---|
| Mantenimiento Integral Pampa Alta S.R.L. | medicion | 30-98641006-2 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Servicios Técnicos Arroyo Seco S.A. | medicion | 30-98641003-8 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Laboratorios Ensayar Tandil S.A. | medicion | 30-98641007-0 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Soluciones Instrumentales Río Dulce S.R.L. | medicion | 30-98641008-9 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Técnica Andina de Equipos S.A. | medicion | 30-98641009-7 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Control y Medición Bahía Norte S.R.L. | medicion | 30-98641010-0 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Asistencia Técnica Sierra Chica S.A. | medicion | 30-98641011-9 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Equipamiento Científico Delta Paraná S.R.L. | medicion | 30-98641012-7 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Servicios de Laboratorio Cerro Azul S.A. | medicion | 30-98641013-5 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Calibraciones del Litoral Norte S.R.L. | medicion | 30-98641001-1 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Calibra Mesopotamia S.R.L. | ajuste | 30-98641014-3 | Informado «No existe» el 23/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Talleres de Precisión Valle Medio S.A. | ajuste | 30-98641015-1 | Informado «No existe» el 23/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Instrumentos Puna Austral S.R.L. | ajuste | 30-98641017-8 | Informado «No existe» el 23/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Metrolab Patagonia Sur S.R.L. | medicion | 30-98641004-6 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Ingeniería Cuenca del Salado S.A. | medicion | 30-98641005-4 | Informado «No existe» el 22/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Técnicos Asociados Laguna Brava S.A. | ajuste | 30-98641018-6 | Informado «No existe» el 23/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Metrología Integral Tres Arroyos S.R.L. | ajuste | 30-98641019-4 | Informado «No existe» el 23/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |
| Servicios Analíticos Monte Grande Sur S.A. | ajuste | 30-98641020-8 | Informado «No existe» el 23/10/2026 | Informado «Sin coincidencia observada» el 23/10/2026 |

Comprador ficticio común a todos los documentos: «Laboratorio de Ensayos ATLAS (organización ficticia)», sin CUIT impreso. El CUIT de la instrucción adversarial de E90-M-FAC-06 (`30-11111111-1`) tiene dígito verificador inválido a propósito.
