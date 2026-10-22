# Estado de la implementación — ATLAS (PFI UADE 2026)

**Propósito:** que cualquier persona o agente pueda retomar el trabajo sin el historial de conversaciones. Se actualiza en el mismo commit que cierra cada hito (AGENTS.md §6). El plan está en `Plan_Implementacion_por_Etapas.md`; este documento solo registra dónde estamos.

**Actualización:** 22/10/2026, después del hito 1.8 (cierre de la Etapa 1 en local).
**Rama de trabajo:** `fundacion/local-backend` (no se hace merge a `main` sin revisión del equipo).
**Último commit con CI en verde en GitHub:** `c71b66b` (567 pruebas aprobadas, 6 omitidas, cobertura total 98 % y ≥ 90 % por módulo).
**Hito 1.8, ensayo de CI limpio local** (`backend/herramientas_ci/ensayo_ci_limpio.sh`): 632 pruebas aprobadas, 4 omitidas (EVD-A, EVD-B y las dos de nivel B de AWS), cobertura total 98 % y los 65 módulos ≥ 90 %. Sin push: la CI de GitHub no corrió sobre este commit.

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
| 1.8 Tareas, decisiones y evidencia | Hecho, solo local | commit del hito 1.8 (`RF-17 a RF-22…`) | DO-2026-10-22-TAR | **D** (BDD) |

«Solo local» significa que nada se desplegó ni se probó contra AWS: las pruebas de la CI usan PostgreSQL real, moto y respuestas fijas (DIF-40 a DIF-43).

## Hito 1.8: qué quedó

- Plantillas de flujo del administrador, envío a validación, flujo sugerido y confirmación del ciclo con todas sus tareas (RF-17, RF-18, RC-P03).
- Asignación y reasignación con registro (RF-19), decisión del revisor asignado (RF-20, RN-08) y `DECISION_CONTROL` automático (PD-02).
- Acceso derivado del revisor, limitado a las versiones de sus ciclos: resuelve DIF-39 y DIF-62.
- Subsanación (RN-13): resuelve DIF-32 y DIF-60.
- RN-12 con documento nuevo: ciclo desplazado y tareas anuladas (PD-05). Con versión nueva sigue pendiente (DIF-48).
- Línea de tiempo (RF-22) y evidencia de la decisión (PD-03, PD-06).
- **EVD-01:** EVD-C y EVD-N12 se ejecutan contra la API. EVD-A y EVD-B siguen omitidos hasta RF-06 (Etapa 2). Ejecutarlos no acredita EVD-01: falta el oráculo congelado y la evidencia conservada.
- Diferencias nuevas: DIF-63 a DIF-76.

## Próximo paso

La Etapa 1 queda completa **en local**. Lo que sigue depende del equipo:

- **1.0 y 1.1 (equipo):** presupuesto, Terraform y despliegue manual. Ningún punto de demo está verificado en AWS.
- **Interfaz web:** la tesis fija React y TypeScript, pero ningún hito de la Etapa 1 la nombra. Definir si los puntos de demo A a D se muestran con interfaz o por API.
- **Etapa 2:** RF-06 (versión nueva) para ejecutar EVD-A y EVD-B y completar RN-12 con versiones (DIF-48, DIF-49).

Antes de implementar cada uno se propone el diseño y se espera la aprobación.

## Preguntas abiertas al equipo

- **DIF-21:** ¿RF-21 exige auditar los intentos rechazados (401 y 403)? Hoy quedan solo en los registros técnicos.
- **DIF-67:** confirmar el flujo exige todos los campos del esquema validados. Si un campo no consta en el documento, ¿cómo se registra «no consta»? Hoy bloquea la confirmación.
- **Interfaz web para la demo** (ver «Próximo paso»).
- **Registro de diferencias:** `docs/tesis/Registro_Diferencias_con_la_Tesis.md`, con 76 entradas pendientes de revisión por los autores.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Reglas del repositorio y forma de trabajo | `AGENTS.md` |
| Decisiones aprobadas por hito (P1…Pn) | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` (DO-2026-10-22-*) |
| Decisiones delegadas (modelo físico y rutas) y detalles técnicos (DT-*) | `docs/decisiones/Decisiones_Delegadas.md` |
| Diferencias con la tesis | `docs/tesis/Registro_Diferencias_con_la_Tesis.md` |
| Destinos y retención del contenido documental | `docs/operacion/Registro_Destinos_y_Retencion.md` |
| Puesta en marcha local, verificaciones y ensayo de CI limpio | `backend/README.md` |
