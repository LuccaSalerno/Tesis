# Plan de implementación por etapas — ATLAS (PFI UADE 2026)

**Fecha:** 21/10/2026
**Cambio operativo del 21/10/2026:** DO-2026-10-21. Toda operación de infraestructura AWS es manual, ejecutada por un integrante autorizado tras aprobar impacto y costos. GitHub Actions conserva solo CI sin AWS; los agentes preparan los cambios locales. E90 adopta DO-2026-10-21-E90A: demo AWS descartable, seed sintético por sesión y eliminación manual controlada de sus recursos; no RDS detenido. DO-2026-10-21-E90-CORPUS ajusta el protocolo cuantitativo a 50 documentos sintéticos, con 3 adversariales internos y ajuste separado, sin alterar métricas o umbrales; la validación operativa es independiente. La preparación de la retirada segura se adelanta como prerrequisito de habilitación.

**Base:** tesis vigente, `Decisiones_Tecnicas_Reconstruccion_PFI_2026.md`, contrato de aceptación integral v1.1 y EVD-01.

Cada etapa produce algo **funcionando de punta a punta**. Lo que se posterga se **difiere**, no se simplifica en contra de la tesis: si un requisito todavía no está, simplemente no está; no se implementa una versión que lo contradiga.

---

**Cotización de referencia:** [informe preliminar](../operacion/RC-P10-13_Cotizacion_Preliminar_2026-10-21.md) y [modelo reproducible](../operacion/RC-P10-13_Modelo_Costos_2026-10-21.xlsx), todavía sin exportación de AWS Pricing Calculator ni autorización de gasto. Las compuertas 1.0 y 1.1 no se consideran verificadas por la existencia de estos documentos.

## Etapa 0 — Prerrequisitos (los hace el equipo, no el agente)

| # | Tarea | Referencia |
|---|---|---|
| 0.1 | Repositorio o rama nuevos, **sin el código del prototipo anterior** | Regla general 2 |
| 0.2 | Copiar al repositorio los documentos de `docs/` (tesis, decisiones, aceptación, diseño y este plan) | AGENTS.md §1 |
| 0.3 | Cuenta AWS dentro de una organización de AWS Organizations, con la **política de exclusión de servicios de IA** aplicada | RC-P09.1 |
| 0.4 | Acceso habilitado en Bedrock a Claude Haiku 4.5, Claude Sonnet 4.6, Cohere Embed Multilingual v3 y Titan Text Embeddings V2 (incluido el formulario de primer uso de Anthropic), verificando perfiles con `GetInferenceProfile` | RC-P09.5 |
| 0.5 | Registro de invocaciones de Bedrock **desactivado** y verificado | RC-P09.2 |
| 0.6 | Revisar los presupuestos existentes y consolidar evidencia; completar cotización oficial por hora/sesión/mes con inactividad y presupuesto aceptado antes del primer recurso facturable. Las alertas no limitan gasto ni autorizan despliegues | RC-P10-13, DO-2026-10-21 |
| 0.7 | Preparación documentada del despliegue manual: operador autorizado, revisión de planes/costos, identidad humana de mínimo privilegio, estado remoto, inventario previsto, apagado y recuperación preparados. Sin OIDC de GitHub ni roles/credenciales AWS para Actions | RC-P02, RC-P10, DO-2026-10-21 |
| 0.8 | **Contrato sintético C-v1** de PD-07 (de 8 a 12 páginas, PDF digital), con CUIT ficticio consultado en ARCA y marca «DOCUMENTO FICTICIO — SIN VALIDEZ COMERCIAL NI FISCAL». Si se llega al hito 1.6: también O-v1, O-v2, F-v1 y F-v2 | PD-07 |

---

## Etapa 1 — Demo del sábado 24/10 (recorte vertical)

**Objetivo:** llegar a la defensa con un recorrido real centrado en el **contrato**, aunque sea parcial.

Los hitos se construyen **en orden**. Cada uno marcado como «punto de demo» deja algo mostrable si el tiempo se termina ahí.

| Hito | Contenido | Requisitos | Punto de demo |
|---|---|---|---|
| **1.0** | Antes del primer despliegue: definir y ensayar localmente mantenimiento `active/draining/offline`, drenaje de URLs/trabajos, control manual de Scheduler, **plan de eliminación selectiva de demo (incluida RDS) sin tocar `bootstrap`**, seed sintético por API, exportación de evidencia y conciliación de costos. Cotización completa por sesión y aprobación previa | RC-P10-08, 09, 13; RC-P08; RNF-06, RNF-09 | — |
| **1.1** | El operador prepara una sola vez `bootstrap` y para cada sesión nueva aplica manualmente `persistent → runtime → demo`, en `offline`. Crear RDS **nuevo**, inicializar usuarios y pgvector, migrar y **sembrar** datos sintéticos por API. Verificar ciclo completo de creación, evaluación y **destrucción manual selectiva**, incluida RDS sin snapshot final ni retención de backups, conservando solo `bootstrap`; identidad IAM, proxy, TLS, aislamiento y residuales. No abrir la demo sin verificar la retirada segura y persistencia dentro de la sesión | RC-P10-01 a 09, 13, 15; B, C, E, V-RP, V-DB, V-MT, V-TF, V-CO, IAM (alcance inicial) | — |
| **1.2** | Autenticación con Cognito, tres usuarios ficticios (responsable, revisor/aprobador con autorización de cierre, administrador operativo), autorización por rol y por trámite para las operaciones implementadas, eventos de auditoría | RF-01, RF-02, RF-21, RNF-01, RNF-04 | — |
| **1.3** | Crear trámite; carga con URL prefirmada; confirmación de la carga con validación de formato y límites; trabajo técnico y estados de procesamiento; confirmación de la incorporación del archivo como documento nuevo, que crea su versión inicial | RF-03, RF-04, RF-05, RF-07, RC-P04, RC-P08 (básico) | — |
| **1.4** | Procesamiento con Step Functions: Textract y Claude Haiku 4.5 para clasificar el contrato y extraer sus siete campos, con la **página de origen** de cada valor | RF-08, RF-10, RF-11, RC-P04 | — |
| **1.5** | Validación humana: confirmar o corregir la clasificación y cada campo, conservando valor sugerido, valor validado, actor, fecha, versión y fuente | RF-09, RF-12, RN-02, RN-03 | **A** · carga y validación del contrato con evidencia de página |
| **1.6** | Consulta asistida sobre el contrato: embeddings con Cohere, búsqueda en pgvector, respuesta con cita al fragmento y abstención cuando no hay evidencia | RF-13 | **B** · «¿hasta cuándo está vigente?» con cita |
| **1.7** | Orden de compra y factura, vínculos entre documentos, reglas R1 a R4 con sus cuatro resultados posibles | RF-14 a RF-16, PD-01 | **C** · advertencia de orden fuera de vigencia |
| **1.8** | Flujo de tareas desde plantilla, decisión del revisor, registro automático en `DECISION_CONTROL` y vista «Evidencia de la decisión» | RF-17 a RF-20, RF-22, PD-02, PD-03, RC-P03.1 | **D** · recorrido completo del diferencial |

**Compuerta de habilitación:** 1.0 es previo a crear recursos facturables. En 1.1 se verifica el cierre seguro sin carga documental; con 1.2–1.4 disponibles se ejecuta una prueba técnica cerrada con datos sintéticos, persistencia y trazabilidad **dentro de la sesión**, más drenaje y destrucción controlada. **No** se acredita con esto la persistencia del mismo trámite entre despliegues (criterio B original). Ningún punto de demo se habilita antes de superar estas verificaciones. Si faltan controles o presupuesto, se posterga AWS; no se relaja la arquitectura ni se afirma que la demo dispone de apagado seguro.

**Diferido explícitamente para después del sábado:** despliegue `tests`, reconciliador completo (antes de usarlo deben verificarse sus controles de drenaje y recuperación), firma simulada, sugerencia de nueva versión (RF-06), versionado con cambio de ciclo (RN-12), reasignación de tareas, panel del administrador, cobertura de pruebas del 85 % y campañas EVD-01.

**Automatización operativa:** fuera de alcance por DO-2026-10-21. La modalidad A (DO-2026-10-21-E90A) **elimina RDS**, no lo deja detenido durante semanas; toda creación, seed, drenaje y destrucción se ejecuta manualmente por el operador.

**Pruebas en la Etapa 1:** pruebas unitarias y de API para lo implementado en cada hito, incluidas las negativas de autorización. No se reclama el cumplimiento de ningún criterio de los contratos de aceptación.

**Punto de decisión:** el **viernes 23/10 a las 18 h** (ajustable por el equipo), si el punto de demo **A** no funciona de forma estable, el equipo conserva la alternativa previamente prevista de usar la demo del prototipo anterior en la defensa, separada de esta reconstrucción, y la Etapa 1 continúa sin presión después de la entrega. Esa alternativa no autoriza reutilizar código previo ni operar AWS fuera de la política manual y de costos. Si falla la compuerta económica u operativa, tampoco se habilita la reconstrucción en AWS aunque el punto A funcione.

**Datos de la demo:** solo el corpus sintético de PD-07. Ningún documento real.

---

**Trazabilidad editorial EVD-01:** el título de la tesis pasó a «Verificación de la cadena de evidencia documental» en la propuesta Markdown de §6.2, pero EVD-01/V1–V11 y los cuatro casos de la reconstrucción se mantienen como IDs internos. BDD/Gherkin está aprobado para describir aceptación; las pruebas API deben implementarse y ejecutarse. Véase `docs/aceptacion/Correspondencia_EVD01_BDD_Tesis.md`.

## Etapa 2 — Cadena de evidencia completa (diferencial)

- Completar V1, V2, V3, V4, V7 y V9: versionado, cambio de ciclo (RN-12) con operación atómica y rechazo de decisiones tardías (PD-05), separación de funciones (RC-P03.3).
- Despliegue manual autorizado de `tests`, con cotización incremental, aislamiento completo (RC-P10-03, 05, 06) y pruebas negativas reales antes de habilitarlo. Si se aprueba desplegar `tests`, demostrar aislamiento de pruebas y su retirada sin afectar una sesión demo; evitar compartir recursos efímeros con ciclo de vida diferente.
- Corpus completo de PD-07 y oráculo versionado.
- Pruebas automatizadas EVD-A, EVD-B, EVD-C y EVD-N12 contra la API, incluidas las dos pruebas de orden forzado y las diez carreras (PD-08).
- Integración continua con GitHub Actions sin acceso a AWS (RC-P02). Las campañas EVD-01 desplegadas y toda migración remota se inician manualmente y se supervisan fuera del runner, con costos autorizados; se conservan las aserciones automatizadas y la evidencia.

## Etapa 3 — Cobertura integral

- RF, RN y RNF restantes según el contrato de aceptación integral: firma simulada y autorización de cierre (RC-P03.2), cancelación, reasignación, panel del administrador, baja de usuarios.
- Ampliar las verificaciones de mantenimiento, drenaje, creación y eliminación descartable E90A ya exigidas en 1.0/1.1; reconciliador completo y estado «En espera» (RC-P08), con pruebas de recuperación antes de su activación. No se posterga a esta etapa la protección económica de la primera demo.
- Recuperación ante fallos y verificaciones A a F, V-RP, V-DB, V-MT, V-TF, V-CO e IAM de RC-P10.
- Cobertura de pruebas ≥ 85 %.

## Etapa 4 — Evaluación experimental (Sección 6.3)

- Diseñar y congelar **50 documentos sintéticos de medición** (10 por tipo; 3 con *prompt injection* incluidos), más **10–15 documentos de ajuste separados** (2–3 por tipo); al menos una plantilla exclusiva de medición por tipo, inventario de hashes y registros de referencia. No generar los antiguos 16 extra ni un conjunto público/empresarial de contraste.
- Implementar el oráculo de **30 preguntas RAG**, seis sin respuesta, y los oráculos de clasificación, extracción, procedencia y tres pruebas adversariales (RC-P05, RC-P06.2, DO-2026-10-21-E90-CORPUS).
- Comparación de modelos y embeddings (RC-P07), pruebas técnicas y de rendimiento, actualización de la cotización previa y registro de costos reales (RC-P10-13). Cada campaña AWS tiene autorización manual y presupuesto; la cotización inicial no se difiere a esta etapa.

**Evidencias de evaluación a recolectar:** `docs/evaluacion/Mapa_Evidencias_Pendientes_Capitulo_6.md` (instrumentos, resultados esperados, evidencias saneadas para 6.2–6.6). Los escenarios BDD declarados y el CSV de plan del corpus no constituyen ejecución.

## Etapa 5 — Resultados y tesis

- Campañas finales de EVD-01 y de 6.3 con oráculos congelados, conservando todas las ejecuciones y los resultados fallidos.
- **Línea separada de validación operativa real (§6.4):** su ejecución requiere autorizaciones y controles RNF-03/RC-P09; ni documentos operativos ni datos confidenciales entran en el repositorio, la CI, el agente o la demo descartable. Documentar solo resultados no sensibles autorizados, sin atribuirles los umbrales del corpus sintético.
- Los autores elaboran los resultados reales de 6.2, 6.4 y 6.5 y actualizan la tesis (incluyendo integrar en LaTeX el capítulo 6 actualizado y conservar el diseño de 50 documentos ya presente en el PDF más reciente). **El agente no redacta resultados inexistentes ni modifica `main.pdf`.**
