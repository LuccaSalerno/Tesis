> **Documento histórico.** Instrucciones de arranque de octubre de 2026, conservadas como registro; ya no describen el estado del repositorio. El estado vigente está en [`README.md`](../../../README.md) y [`docs/plan/Estado_Implementacion.md`](../../plan/Estado_Implementacion.md).

> **Actualización documental 22/10/2026:** el PDF y el Markdown 6.0–6.3 están sincronizados; ver [informe de sincronización](../../../docs/operacion/Informe_Sincronizacion_Tesis_2026-10-22.md). La implementación, el corpus real y los resultados siguen pendientes.

# ATLAS — Preparación de la reconstrucción (21/10/2026)

**Actualización de este paquete para el inicio de implementación:** ver [informe de cambios](../../../docs/operacion/Informe_Preparacion_Implementacion_2026-10-21.md), [equivalencia EVD-01/BDD](../../../docs/aceptacion/Correspondencia_EVD01_BDD_Tesis.md), [plan del corpus](../../../docs/evaluacion/Plan_Diseno_Corpus_E90.md) y [evidencias necesarias para el capítulo 6](../../../docs/evaluacion/Mapa_Evidencias_Pendientes_Capitulo_6.md). El PDF de `docs/tesis/main.pdf` fue actualizado con la versión más reciente adjuntada por los autores (50 documentos en §6.3.1); la redacción consolidada de 6.0–6.3 ya está incorporada al PDF del 22/10/2026. El plan de 15 ajustes es **propuesta operativa**, no corpus construido.


Este repositorio contiene documentación y corpus candidatos. **No hay aplicación, Terraform ni workflows de CI implementados**, ni ciclo de despliegue/apagado verificado. El equipo comunicó comprobaciones de acceso y privacidad AWS; sus capturas formales siguen pendientes.

## Contenido y política vigente

- `AGENTS.md` fija las reglas del agente; `docs/tesis/main.pdf` está presente como tesis contractual para esta revisión.
- `docs/` contiene decisiones, aceptación, diseño, plan y registros operativos.
- `corpus/` y `oraculos/` contienen documentos y oráculo candidatos de PD-07 para demo/EVD; **no son aún** el conjunto de medición de 50. CUIT pendiente de consulta oficial ARCA.
- `docs/evaluacion/` fija el **protocolo vigente E90**: 50 sintéticos (3 adversariales dentro), 10–15 de ajuste, 30 preguntas RAG y validación operativa como procedimiento separado. El PDF incorporado en esta actualización expresa el corpus de 50; la versión académica consolidada de 6.0–6.3 se encuentra en el PDF adjunto y en el Markdown sincronizado.
- `operaciones/aws/` contiene runbooks manuales y un script de auditoría de solo lectura para ejecución humana. La plantilla de confianza OIDC de GitHub fue retirada por DO-2026-10-21; el antecedente se conserva en las decisiones.
- `herramientas/generar_corpus.py` es la fuente local de generación; no se modifica el corpus en esta tarea.

**DO-2026-10-21-E90A:** para el 90 %, cada sesión AWS es **descartable**: crear `persistent → runtime → demo`, migrar, poblar corpus ficticio mediante seed autorizado y eliminar manualmente **todos los recursos propios de la sesión, incluida RDS**. No se detiene RDS, no se preservan datos entre sesiones. `bootstrap` y los controles de cuenta permanecen. Procedimiento propuesto, no implementado ni probado. [Runbook](../../../operaciones/aws/README_OPERACION_MANUAL.md) · [Especificación del seed](../../../docs/operacion/Seed_Demo_E90_Especificacion.md).

**DO-2026-10-21:** ninguna operación de infraestructura AWS se ejecuta por agentes, GitHub Actions, push, merge o automatizaciones. Solo un operador del equipo ejecuta manualmente planes revisados, con aprobación expresa de impacto y costos. Sin proveedor OIDC de GitHub, roles para Actions ni credenciales AWS en GitHub. CI sin AWS sigue permitido. Se preserva la arquitectura funcional de la tesis.

## Auditoría y estimación económica de este ZIP

- [Auditoría de estado y hallazgos](../../../docs/operacion/Informe_Auditoria_ZIP_2026-10-21.md): qué está bien, defectos concretos, verificaciones locales y límites de la revisión.
- [Cotización preliminar RC-P10-13](../../../docs/operacion/RC-P10-13_Cotizacion_Preliminar_2026-10-21.md) y [planilla reproducible](../../../docs/operacion/RC-P10-13_Modelo_Costos_2026-10-21.xlsx). **No son una cotización guardada en AWS Pricing Calculator ni una autorización de gasto.**

## Inicio del desarrollo local

Leer [INICIO_CODEx_E90.md](../../../INICIO_CODEx_E90.md). El agente puede comenzar localmente sin esperar la cotización AWS o la consulta ARCA; estas bloquean respectivamente el primer despliegue y la congelación del corpus, **no** el trabajo de código local. No inventar resultados de validación operativa ni publicar documentación auténtica.

## Antes del primer despliegue

1. Consolidar las evidencias comunicadas de Organizations, logging Bedrock, acceso a modelos y Budgets; revisar el [registro de destinos](../../../docs/operacion/Registro_Destinos_y_Retencion.md) y congelar la huella de la versión contractual de la tesis y conservar la trazabilidad con su fuente LaTeX.
2. Completar cotización RC-P10-13 por hora, sesión y mes con inactividad/residuales, y registrar presupuesto aceptado. Los budgets USD 1 y USD 20 son alertas, no autorizaciones ni límites de gasto.
3. Implementar y verificar los prerrequisitos 1.0/1.1 del [plan](../../../docs/plan/Plan_Implementacion_por_Etapas.md): el mantenimiento, apagado manual y recuperación se adelantan antes de habilitar demo.
4. Completar inventario, responsables y autorización humana del plan exacto, según [runbook manual](../../../operaciones/aws/README_OPERACION_MANUAL.md) y [política de costos](../../../docs/operacion/Politica_Costos_AWS.md).
5. Consultar CUIT en ARCA y congelar corpus/oráculo. Ejecutar pruebas y conservar evidencia; todavía no hay resultados EVD-01 ni conformidad integral.

ATLAS se usa en sesiones controladas, sin permanecer funcionando en AWS durante el desarrollo. No se incorpora código del prototipo anterior ni se reducen requisitos por costo.

**Advertencia:** los totales del Excel anterior fueron calculados para la modalidad previa con RDS detenido; no son la cotización de E90A y no habilitan gasto.
