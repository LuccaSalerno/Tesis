# ATLAS — PFI UADE 2026

Reconstrucción desde cero. Leer [AGENTS.md](AGENTS.md) y [estado de preparación](README_PRIMERO.md) antes de trabajar.

La decisión del equipo del 21/10/2026 exige operaciones AWS exclusivamente manuales por un integrante autorizado, con impacto y costos aprobados. GitHub Actions solo admite CI sin AWS; no se configura OIDC de GitHub. Terraform y la arquitectura de la tesis se preservan. Ver [operación manual](operaciones/aws/README_OPERACION_MANUAL.md) y [política de costos](docs/operacion/Politica_Costos_AWS.md).

Todavía no hay infraestructura ni aplicación implementadas o verificadas en este repositorio. ATLAS no funcionará permanentemente en AWS durante el desarrollo.


## Operación E90: demo descartable

[Decisión E90A](docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md) · [runbook manual](operaciones/aws/README_OPERACION_MANUAL.md) · [especificación de seed](docs/operacion/Seed_Demo_E90_Especificacion.md). No hay despliegues automáticos GitHub ni AWS seed funcional implementado aún.

## Evaluación E90: decisión final del corpus

[Protocolo vigente de evaluación](docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md) · [Decisión DO-2026-10-21-E90-CORPUS](docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md) · [Guía de inicio para el agente](INICIO_CODEx_E90.md).

Medición: 50 **sintéticos** (10 por tipo), con 3 pruebas de *prompt injection* dentro de esos 50; 10–15 archivos separados de ajuste y 30 preguntas RAG. No se crean los 16 casos extra ni un conjunto público. La demo descartable y EVD-01 tienen su escenario sintético PD-07; la validación operativa real constituye un procedimiento distinto, sin ingreso de documentos auténticos al repositorio/CI/agente ni a la demo. Los resultados no confidenciales de esa validación se registran únicamente cuando existan y estén autorizados.

**La fuente académica `docs/tesis/main.pdf` todavía tiene el recuento anterior; sus autores realizan la modificación.** Esto no bloquea la fundación local del backend, frontend y base, pero el protocolo de 50 es el vigente para producir el corpus de evaluación.
