# Estado de la implementación — ATLAS (PFI UADE 2026)

**Propósito:** que cualquier persona o agente pueda retomar el trabajo sin el historial de conversaciones. Se actualiza en el mismo commit que cierra cada hito (AGENTS.md §6). El plan está en `Plan_Implementacion_por_Etapas.md`; este documento solo registra dónde estamos.

**Actualización:** 22/10/2026, después del hito 1.7.
**Rama de trabajo:** `fundacion/local-backend` (no se hace merge a `main` sin revisión del equipo).
**Último commit con CI en verde en GitHub:** `c71b66b` (567 pruebas aprobadas, 6 omitidas, cobertura total 98 % y ≥ 90 % por módulo).

## Hitos de la Etapa 1

| Hito | Estado | Commit | Decisiones aprobadas | Punto de demo |
|---|---|---|---|---|
| Fundación local | Hecho | `b6df546`, `43cef95` | RC-P02, PD-04 (núcleo, migraciones 0001–0002) | — |
| 1.0 y 1.1 | **Pendiente del equipo** (AWS manual, presupuesto, Terraform) | — | DO-2026-10-21, DO-2026-10-21-E90A | — |
| 1.2 Autenticación, roles y cuentas | Hecho, solo local | `32b00af` | DT-AUT-01, DT-AUT-02 | — |
| 1.3 Trámite, carga e incorporación | Hecho, solo local | `a954137`, `6cc7afa` | DT-AWS-01, DO-2026-10-22-CARGAS | — |
| 1.4 Procesamiento (Textract y Haiku 4.5) | Hecho, solo local; nivel B sin ejecutar | `b1a7207` | DO-2026-10-22-PROC | — |
| 1.5 Validación humana | Hecho, solo local | `10e9f5f` | DO-2026-10-22-VAL | **A** (BDD) |
| 1.6 Consulta asistida | Hecho, solo local; nivel B sin ejecutar | `494986a` | DO-2026-10-22-RAG | **B** (BDD) |
| 1.7 Vínculos y reglas R1 a R4 | Hecho, solo local | `c71b66b` | DO-2026-10-22-REG | **C** (BDD) |
| 1.8 Tareas, decisiones y evidencia | **Próximo** | — | Por proponer | **D** |

«Solo local» significa que nada se desplegó ni se probó contra AWS: las pruebas de la CI usan PostgreSQL real, moto y respuestas fijas (DIF-40 a DIF-43).

## Próximo paso: hito 1.8

**Contenido:**
- flujo de tareas desde plantilla;
- decisión del revisor;
- registro automático en `DECISION_CONTROL` (PD-02);
- vista «Evidencia de la decisión» (PD-03).

**Requisitos:** RF-17 a RF-20, RF-22, RC-P03.1. También RN-07, RN-08, RN-09, RN-12 y RN-13.

**Pendiente de hitos anteriores:**
- acceso del revisor con tarea asignada: consulta asistida, vínculos y controles (DIF-39, DIF-62);
- validación y vínculos en Observado con la subsanación (DIF-32, DIF-60);
- anulación de tareas al incorporar una versión (DIF-48).

**Señal de cierre:** los escenarios EVD-01 de `tests/acceptance/features/cadena_evidencia.feature` dejan de omitirse y se ejecutan contra la API.

Antes de implementar se propone el diseño y se espera la aprobación.

## Preguntas abiertas al equipo

- **DIF-21:** ¿RF-21 exige auditar los intentos rechazados (401 y 403)? Hoy quedan solo en los registros técnicos.
- **Registro de diferencias:** `docs/tesis/Registro_Diferencias_con_la_Tesis.md`, con 62 entradas pendientes de revisión por los autores.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Reglas del repositorio y forma de trabajo | `AGENTS.md` |
| Decisiones aprobadas por hito (P1…Pn) | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` (DO-2026-10-22-*) |
| Decisiones delegadas (modelo físico y rutas) y detalles técnicos (DT-*) | `docs/decisiones/Decisiones_Delegadas.md` |
| Diferencias con la tesis | `docs/tesis/Registro_Diferencias_con_la_Tesis.md` |
| Destinos y retención del contenido documental | `docs/operacion/Registro_Destinos_y_Retencion.md` |
| Puesta en marcha local, verificaciones y ensayo de CI limpio | `backend/README.md` |
