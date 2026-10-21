# INICIO CODEX — ATLAS E90, desarrollo desde cero

**Estado del paquete:** decisiones de arquitectura/operación y método E90 consolidadas a 21/10/2026. **No incluye backend, frontend, Terraform, infraestructura desplegada, seed API, evaluación terminada ni datos medidos**. No constituye aceptación EVD-01 ni informe final de tesis.

## Lectura obligatoria

Antes de desarrollar: `AGENTS.md` → `docs/tesis/main.pdf` (RF/RN/RNF, modelo y arquitectura) → `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` → `docs/aceptacion/` → `docs/diseno/RC-P10_Diseno_Infraestructura.md` → `docs/plan/Plan_Implementacion_por_Etapas.md` → `docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md`.

**Única discrepancia de fuente deliberada:** la versión PDF de tesis aún describe 16 casos sintéticos extra y 10–15 públicos; el equipo aprobó sustituir exclusivamente ese método de medición por **50 sintéticos**, tres con prompt injection dentro, **10–15 de ajuste por separado**, 30 preguntas. El contrato de aceptación IA-D03..D07 y RC-P05/06 ya están actualizados para que no se implemente el protocolo antiguo. Los autores actualizarán el PDF: **no lo edites** y no alteres requisitos/umbrales.

## Primera tarea del agente

1. Auditar sin destruir ni reescribir nada el estado Git del ZIP y sugerir al equipo cómo consolidar los archivos todavía *untracked*. Trabajar en rama; sin `push` ni `merge` a `main`.
2. Construir **solo la fundación local**: estructura del monorepositorio, backend FastAPI, frontend React/TypeScript, PostgreSQL + pgvector local, Alembic, configuración sin secretos, pytest e inicio de CI sin acceso AWS. Respetar decisiones y RF/RN/RNF del PDF.
3. Implementar el primer incremento de persistencia real del dominio siguiendo la Figura 5.4 y el contrato de aceptación, con migraciones y tests. Registrar decisiones delegadas autorizadas en `docs/decisiones/Decisiones_Delegadas.md`.
4. Hacer incrementos verticales chicos según hitos del plan, con pruebas y trazabilidad. No usar código del prototipo anterior.
5. En paralelo, **preparar** registros/plantillas/oráculos y generar 50 documentos de medición y 10–15 de ajuste. No confundirlos con el corpus PD-07 de cinco documentos ni inventar resultados. Utilizar el inventario/validador de `docs/evaluacion/`.
6. **No ejecutar AWS ni Terraform** como agente. Escribir IaC y runbooks para aprobación manual futura; ningún OIDC ni workflows con credenciales AWS. Antes de desplegar hace falta cotización oficial, costos aceptados y prueba del procedimiento de eliminación selectiva.

## Separación obligatoria

- **Demo descartable E90A:** sintéticos, recreada por sesión; la semilla API está **pendiente**. Destruye RDS bajo autorización manual y pierde datos entre sesiones.
- **Evaluación cuantitativa §6.3:** 50 sintéticos con oráculo precongelado y 30 preguntas RAG.
- **Validación funcional/operativa §6.4:** la realiza el equipo en entorno real bajo autorización; ni originales ni datos sensibles se transfieren a este repositorio, agente, CI o demo. Registrar solo resultados autorizados y no confidenciales.

## Primer criterio de entrega

Proyecto ejecutable **localmente** con tests que pasan, base real pgvector y migraciones reproducibles, sin calls AWS y sin prometer capacidades que no existen. Informar archivos, trazabilidad, pruebas, pendientes y decisiones delegadas según `AGENTS.md`. No marcar criterios contractuales como «Cumple» sin evidencia.
