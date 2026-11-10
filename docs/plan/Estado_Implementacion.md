# Estado de la implementación — ATLAS (PFI UADE 2026)

**Propósito:** retomar el trabajo sin el historial de conversaciones. Se actualiza al cerrar cada hito (AGENTS.md §6). El plan está en `Plan_Implementacion_por_Etapas.md`.

**Actualización:** 04/11/2026.
**Rama de trabajo:** `fundacion/local-backend`, con commits locales sin push; no se hace merge a `main` sin revisión del equipo.

## Estado actual

- **Aplicación:** RF-01 a RF-26 implementados, con backend y frontend.
- **AWS:** sin infraestructura activa hasta la exposición final (DO-2026-10-24-RETIRO-TOTAL). Para reconstruirla: `operaciones/aws/Guia_Sesion_Seccion6.md`, desde la Parte 1.
- **Corpus E90:** congelado (DO-2026-10-23-E90-CONGELACION).
- **Evidencia del capítulo 6:** `evaluacion/campanas/`. Incluye la campaña `e90-oficial-1`, medida en `b872e0c`.
- **EVD-01:** V1 a V11 verificados en `e0faadf` contra el oráculo PD-07 v2 (`evaluacion/campanas/evd01-2026-10-24/acta.md`). El código posterior no hereda esa verificación.
- **Último ensayo de CI limpio:** 842 pruebas aprobadas y 2 omitidas; herramientas del corpus, 71 aprobadas y 1 omitida; cobertura 98 % y los 110 módulos ≥ 90 %.

## Hitos de la Etapa 1

| Hito | Estado | Commit | Decisiones aprobadas | Punto de demo |
|---|---|---|---|---|
| Fundación local | Hecho | `b6df546`, `43cef95` | RC-P02, PD-04 (núcleo, migraciones 0001–0002) | — |
| 1.0 Preparación del despliegue manual | Hecho, solo local (Terraform validado sin AWS) | commit del hito 1.0 (`RC-P10…`) | DO-2026-10-22-OPS | — |
| Aplicación web (A a D) | Hecho, solo local (E2E contra el stack local) | commit de la aplicación web | DO-2026-10-22-WEB | **A a D** en la interfaz |
| 1.1 Primer ciclo en AWS | Hecho por el operador: sesiones e90-ensayo-1, e90-ensayo-2 y e90-2026-10-24; infraestructura retirada después | — | DO-2026-10-21, DO-2026-10-21-E90A, DO-2026-10-24-RETIRO-TOTAL | — |
| 1.2 Autenticación, roles y cuentas | Hecho, solo local | `32b00af` | DT-AUT-01, DT-AUT-02 | — |
| 1.3 Trámite, carga e incorporación | Hecho, solo local | `a954137`, `6cc7afa` | DT-AWS-01, DO-2026-10-22-CARGAS | — |
| 1.4 Procesamiento (Textract y Haiku 4.5) | Hecho, solo local; nivel B sin ejecutar | `b1a7207` | DO-2026-10-22-PROC | — |
| 1.5 Validación humana | Hecho, solo local | `10e9f5f` | DO-2026-10-22-VAL | **A** (BDD) |
| 1.6 Consulta asistida | Hecho, solo local; nivel B sin ejecutar | `494986a` | DO-2026-10-22-RAG | **B** (BDD) |
| 1.7 Vínculos y reglas R1 a R4 | Hecho, solo local | `c71b66b` | DO-2026-10-22-REG | **C** (BDD) |
| 1.8 Tareas, decisiones y evidencia | Hecho, solo local | commit del hito 1.8 (`RF-17 a RF-22…`) | DO-2026-10-22-TAR | **D** (BDD) |

«Solo local» significa que el hito se verificó sin AWS, con PostgreSQL real, moto y respuestas fijas (DIF-40 a DIF-43).

## Simplificación del 04/11/2026

Sin cambios de reglas ni del contrato de la API: `5a007aa` (interfaz sin referencias a requisitos y frontend), `68f800b` (backend), `ecf301f` (pruebas y documentación de entrada) y la limpieza de documentación que sigue a esos commits.

**Documentos retirados:** informes de preparación, revisiones intermedias del corpus, cuadernos generados, borradores para redactar la tesis y este estado en su versión detallada. Algunas decisiones y registros históricos todavía los citan. Se recuperan con:

```bash
git show ecf301f:docs/plan/Estado_Implementacion.md
```

La lista completa de archivos retirados se obtiene con `git log --diff-filter=D --name-only`.

## Escenario de demostración SurDelta (09/11/2026)

DO-2026-11-09-DEMO-SURDELTA, rama `demo/surdelta`. Sin cambios de reglas, estados, API ni interfaz.

- **Documentos:** 9 PDF sintéticos en `corpus/surdelta/` (el contrato SD-C1 tiene 10 páginas, como el de PD-07), generados con `herramientas/generar_corpus_surdelta.py`; oráculo `oraculos/oraculo_surdelta_v1.json`. CUIT: el de PD-07 y tres de la partición de ajuste de E90, todos ya consultados en ARCA.
- **Semilla:** `sembrar_demo --escenario surdelta` (compra observada por R1, renovación pendiente de aprobación, limpieza cancelada; el mantenimiento de planta se crea en vivo y las pruebas verifican su recorrido completo por la API). El escenario PD-07 sigue siendo el predeterminado.
- **Guion:** dos videos de 5 minutos en `operaciones/demo/Guion_Demo.md` §7.
- **Ensayo de CI limpio:** 845 pruebas aprobadas y 2 omitidas; herramientas del corpus, 75 aprobadas y 1 omitida; cobertura 98 % y los 110 módulos ≥ 90 %. La tesis sigue citando las 842 de su versión (§6.5).
- **Sin ejecutar en AWS:** las sugerencias reales de la IA sobre estos PDF se ven en la próxima sesión.

## Flujos de revisión en la interfaz (09/11/2026)

DO-2026-11-09-WEB-FLUJOS: Administración muestra un flujo por alcance con Editar y Volver a usar, Cuentas permite otorgar la autorización de cierre y el trámite muestra el ciclo como recorrido de pasos. Solo frontend. Pendiente para después de la entrega: decidir si hay varios flujos activos que el responsable elige al confirmar.

## Fotos de la base para la demo (09/11/2026, temporal)

DO-2026-11-09-ESTADOS-DEMO: `guardar_estado` y `restablecer_estado` en la Lambda de operaciones para volver al estado recién sembrado en segundos (`Guion_Demo.md` §7.1 bis). Requiere aplicar el permiso IAM nuevo de `demo` y redesplegar el paquete Lambda. Retirar después de la exposición.

## Próximo paso

- **Videos:** sesión AWS manual del operador, semilla `--escenario surdelta` y grabación según `Guion_Demo.md` §7.
- **Local:** repetir el e2e sobre el código final, con la base recién sembrada (`README.md`).
- **Equipo:** decidir si se repite EVD-01 sobre el código final.
- **Exposición final:** reconstruir la infraestructura y seguir `operaciones/demo/Guion_Demo.md`.

## Preguntas abiertas al equipo

- **Registro de diferencias:** `docs/tesis/Registro_Diferencias_con_la_Tesis.md`, con entradas pendientes de revisión por los autores.
- **`herramientas/validar_inventario_e90.py`:** confirmar si sigue haciendo falta ahora que el corpus está congelado.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Reglas del repositorio y forma de trabajo | `AGENTS.md` |
| Decisiones aprobadas por hito | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` |
| Decisiones delegadas y detalles técnicos (DT-*) | `docs/decisiones/Decisiones_Delegadas.md` |
| Diferencias con la tesis | `docs/tesis/Registro_Diferencias_con_la_Tesis.md` |
| Destinos y retención del contenido documental | `docs/operacion/Registro_Destinos_y_Retencion.md` |
| Puesta en marcha local y ensayo de CI limpio | `backend/README.md` |
| Operación en AWS | `operaciones/aws/Guia_Sesion_Seccion6.md`, `infra/terraform/README.md` |
