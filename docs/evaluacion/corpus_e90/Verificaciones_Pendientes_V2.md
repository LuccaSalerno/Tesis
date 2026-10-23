# Verificaciones manuales pendientes de la v2

P2 y P3 de DO-2026-10-22-CORPUS-REVISION: las razones sociales y los CUIT son ficticios, pero un dígito verificador válido o un nombre inventado no acreditan que no existan. Antes de congelar, el equipo verifica a mano cada razón social (por ejemplo, en buscadores públicos de sociedades) y los seis CUIT nuevos de ajuste en ARCA, y registra fecha y resultado. El agente no hizo ni simula estas consultas.

Si un nombre o un CUIT coincide con uno real, se reemplaza en `herramientas/corpus_e90/preparar.py` y se regenera la revisión candidata completa (hashes, localizadores y preguntas).

| Razón social | Partición | CUIT asignado | Consulta CUIT (ARCA) | Verificación de la razón social |
|---|---|---|---|---|
| Mantenimiento Integral Pampa Alta S.R.L. | medicion | 30-98641006-2 | Informado «No existe» el 22/10/2026 | Pendiente |
| Servicios Técnicos Arroyo Seco S.A. | medicion | 30-98641003-8 | Informado «No existe» el 22/10/2026 | Pendiente |
| Laboratorios Ensayar Tandil S.A. | medicion | 30-98641007-0 | Informado «No existe» el 22/10/2026 | Pendiente |
| Soluciones Instrumentales Río Dulce S.R.L. | medicion | 30-98641008-9 | Informado «No existe» el 22/10/2026 | Pendiente |
| Técnica Andina de Equipos S.A. | medicion | 30-98641009-7 | Informado «No existe» el 22/10/2026 | Pendiente |
| Control y Medición Bahía Norte S.R.L. | medicion | 30-98641010-0 | Informado «No existe» el 22/10/2026 | Pendiente |
| Asistencia Técnica Sierra Chica S.A. | medicion | 30-98641011-9 | Informado «No existe» el 22/10/2026 | Pendiente |
| Equipamiento Científico Delta Paraná S.R.L. | medicion | 30-98641012-7 | Informado «No existe» el 22/10/2026 | Pendiente |
| Servicios de Laboratorio Cerro Azul S.A. | medicion | 30-98641013-5 | Informado «No existe» el 22/10/2026 | Pendiente |
| Calibraciones del Litoral Norte S.R.L. | medicion | 30-98641001-1 | Informado «No existe» el 22/10/2026 | Pendiente |
| Calibra Mesopotamia S.R.L. | ajuste | 30-98641014-3 | **Pendiente** | Pendiente |
| Talleres de Precisión Valle Medio S.A. | ajuste | 30-98641015-1 | **Pendiente** | Pendiente |
| Instrumentos Puna Austral S.R.L. | ajuste | 30-98641017-8 | **Pendiente** | Pendiente |
| Metrolab Patagonia Sur S.R.L. | medicion | 30-98641004-6 | Informado «No existe» el 22/10/2026 | Pendiente |
| Ingeniería Cuenca del Salado S.A. | medicion | 30-98641005-4 | Informado «No existe» el 22/10/2026 | Pendiente |
| Técnicos Asociados Laguna Brava S.A. | ajuste | 30-98641018-6 | **Pendiente** | Pendiente |
| Metrología Integral Tres Arroyos S.R.L. | ajuste | 30-98641019-4 | **Pendiente** | Pendiente |
| Servicios Analíticos Monte Grande Sur S.A. | ajuste | 30-98641020-8 | **Pendiente** | Pendiente |

Comprador ficticio común a todos los documentos: «Laboratorio de Ensayos ATLAS (organización ficticia)», sin CUIT impreso. El CUIT de la instrucción adversarial de E90-M-FAC-06 (`30-11111111-1`) tiene dígito verificador inválido a propósito.
