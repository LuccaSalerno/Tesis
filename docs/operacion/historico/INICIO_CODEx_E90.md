> **Documento histórico.** Instrucciones de arranque de octubre de 2026, conservadas como registro; ya no describen el estado del repositorio. El estado vigente está en [`README.md`](../../../README.md) y [`docs/plan/Estado_Implementacion.md`](../../plan/Estado_Implementacion.md).

# INICIO CODEX — ATLAS E90, desarrollo desde cero

**Estado del paquete:** decisiones de arquitectura/operación y método E90 consolidadas a 21/10/2026. **No incluye backend, frontend, Terraform, infraestructura desplegada, seed API, evaluación terminada ni datos medidos**. No constituye aceptación EVD-01 ni informe final de tesis.

## Lectura obligatoria

Antes de desarrollar: `AGENTS.md` → `docs/tesis/main.pdf` (RF/RN/RNF, modelo y arquitectura) → `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` → `docs/aceptacion/` → `docs/diseno/RC-P10_Diseno_Infraestructura.md` → `docs/plan/Plan_Implementacion_por_Etapas.md` → `docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md`.

**Estado de las fuentes:** el `docs/tesis/main.pdf` incluido fue reemplazado por el PDF más reciente entregado por los autores, con 50 documentos sintéticos en §6.3.1. La redacción consolidada 6.0–6.3 ya está incorporada al PDF vigente y se conserva en `docs/tesis/ATLAS_Seccion_6_Version_Final_6_0_a_6_3.md` como copia Markdown sincronizada; esto no acredita ejecuciones. El protocolo E90 y las decisiones de aceptación fijan el corpus, sin 16 extras ni contraste público. La etiqueta académica «Verificación de la cadena de evidencia documental» corresponde al contrato interno **EVD-01** y conserva V1–V11. **BDD/Gherkin Dado–Cuando–Entonces está confirmado** para aceptación; consultar `docs/aceptacion/Correspondencia_EVD01_BDD_Tesis.md`. No suponer que los escenarios declarados ya se ejecutaron.

## Primera tarea del agente

1. Auditar sin destruir ni reescribir nada el estado Git del ZIP y sugerir al equipo cómo consolidar los archivos todavía *untracked*. Trabajar en rama; sin `push` ni `merge` a `main`.
2. Construir **solo la fundación local**: estructura del monorepositorio, backend FastAPI, frontend React/TypeScript, PostgreSQL + pgvector local, Alembic, configuración sin secretos, pytest e inicio de CI sin acceso AWS. Respetar decisiones y RF/RN/RNF del PDF.
3. Implementar el primer incremento de persistencia real del dominio siguiendo la Figura 5.4 y el contrato de aceptación, con migraciones y tests. Registrar decisiones delegadas autorizadas en `docs/decisiones/Decisiones_Delegadas.md`.
4. Hacer incrementos verticales chicos según hitos del plan, con pruebas y trazabilidad. No usar código del prototipo anterior.
5. En paralelo, **preparar** registros/plantillas/oráculos a partir de `docs/evaluacion/Plan_Diseno_Corpus_E90.md` y generar 50 documentos de medición y 10–15 de ajuste (plan operativo propuesto: 15, a confirmar por el equipo). No confundirlos con el corpus PD-07 de cinco documentos ni inventar resultados. Utilizar el inventario/validador de `docs/evaluacion/`.
6. **No ejecutar AWS ni Terraform** como agente. Escribir IaC y runbooks para aprobación manual futura; ningún OIDC ni workflows con credenciales AWS. Antes de desplegar hace falta cotización oficial, costos aceptados y prueba del procedimiento de eliminación selectiva.

## Separación obligatoria

- **Demo descartable E90A:** sintéticos, recreada por sesión; la semilla API está **pendiente**. Destruye RDS bajo autorización manual y pierde datos entre sesiones.
- **Evaluación cuantitativa §6.3:** 50 sintéticos con oráculo precongelado y 30 preguntas RAG.
- **Validación funcional/operativa §6.4:** la realiza el equipo en entorno real bajo autorización; ni originales ni datos sensibles se transfieren a este repositorio, agente, CI o demo. Registrar solo resultados autorizados y no confidenciales.

## Pruebas y evidencias que se exigirán después

Para 6.2–6.6, leer `docs/evaluacion/Mapa_Evidencias_Pendientes_Capitulo_6.md`. Preservar evidencia real y saneada desde el primer incremento, asociada a RF/RN/RNF/EVD-01 y a versiones de código y oráculo. BDD expresa expectativas mediante `.feature`; la ejecución de esos escenarios y la evidencia UI/API siguen pendientes.

## Primer criterio de entrega

Proyecto ejecutable **localmente** con tests que pasan, base real pgvector y migraciones reproducibles, sin calls AWS y sin prometer capacidades que no existen. Informar archivos, trazabilidad, pruebas, pendientes y decisiones delegadas según `AGENTS.md`. No marcar criterios contractuales como «Cumple» sin evidencia.
