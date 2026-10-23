# Estado de la implementación — ATLAS (PFI UADE 2026)

**Propósito:** que cualquier persona o agente pueda retomar el trabajo sin el historial de conversaciones. Se actualiza en el mismo commit que cierra cada hito (AGENTS.md §6). El plan está en `Plan_Implementacion_por_Etapas.md`; este documento solo registra dónde estamos.

**Actualización:** 22/10/2026, después de la aplicación web (DO-2026-10-22-WEB). La Etapa 1 queda completa en local; nada se desplegó.
**Rama de trabajo:** `fundacion/local-backend` (no se hace merge a `main` sin revisión del equipo).
**Último commit con CI en verde en GitHub:** `2bb4dff` (hito 1.0; 677 pruebas aprobadas, 4 omitidas, cobertura total 98 % y los 73 módulos ≥ 90 %).
**Hito 1.0, ensayo de CI limpio local:** 677 pruebas aprobadas, 4 omitidas (EVD-A, EVD-B y las dos de nivel B de AWS), cobertura total 98 % y los 73 módulos ≥ 90 %; incluye la inicialización privilegiada contra el superusuario efímero de PostgreSQL.
**Hito 1.8, ensayo de CI limpio local** (`backend/herramientas_ci/ensayo_ci_limpio.sh`): 632 pruebas aprobadas, 4 omitidas (EVD-A, EVD-B y las dos de nivel B de AWS), cobertura total 98 % y los 65 módulos ≥ 90 %. Sin push: la CI de GitHub no corrió sobre este commit.

## Hitos de la Etapa 1

| Hito | Estado | Commit | Decisiones aprobadas | Punto de demo |
|---|---|---|---|---|
| Fundación local | Hecho | `b6df546`, `43cef95` | RC-P02, PD-04 (núcleo, migraciones 0001–0002) | — |
| 1.0 Preparación del despliegue manual | Hecho, solo local (Terraform validado sin AWS) | commit del hito 1.0 (`RC-P10…`) | DO-2026-10-22-OPS | — |
| Aplicación web (A a D) | Hecho, solo local (E2E contra el stack local) | commit de la aplicación web | DO-2026-10-22-WEB | **A a D** en la interfaz |
| 1.1 Primer ciclo en AWS | **Pendiente del equipo** (presupuesto, cotización oficial, ejecución manual) | — | DO-2026-10-21, DO-2026-10-21-E90A | — |
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

## Hito 1.0: qué quedó (DO-2026-10-22-OPS)

- **Aplicación lista para Lambda:**
  - modo mantenimiento leído de S3 (`active`, `draining`, `offline`) y `/salud` con el estado operativo;
  - conexión a la base con token IAM y TLS `verify-full`;
  - adaptador Mangum;
  - en demo, la aplicación no arranca sin esos controles.
- **Lambda privada de operaciones:** `inicializar_base`, `migrar`, `estado_migraciones`, `crear_administrador` y `verificar_drenaje`. La inicialización se probó en PostgreSQL 16 real como superusuario; en RDS el usuario maestro no lo es, así que queda por verificar en la sesión (V-DB).
- **Terraform** `bootstrap`, `persistent`, `runtime` y `demo`: `validate` y `fmt` en verde con el proveedor AWS 6.67.0. **Nunca se planificó contra una cuenta.**
- **Paquete arm64** de 36 MB. No se pudo probar su importación en arm64 en esta máquina: queda para el humo de la sesión.
- **Herramientas del operador:** semilla y exportación de evidencia por API, probadas contra el stack local, y vaciado de buckets versionados, probado con moto.
- **Documentación:** procedimiento concreto en `infra/terraform/README.md` y cotización por sesión en `docs/operacion/RC-P10-13_Cotizacion_Sesion_E90A.md` (≈ USD 0,21/h de base, sin oficializar).
- Diferencias nuevas: DIF-77 a DIF-86.

## Aplicación web: qué quedó (DO-2026-10-22-WEB)

- `frontend/`: React y TypeScript con el contrato generado del OpenAPI real.
- Áreas del trámite: Resumen, Documentos y datos (validación con el PDF y la fuente resaltada), Vínculos y controles, Consulta, Revisión e Historial.
- Bandeja y decisión del revisor; **Evidencia de la decisión** (ficha, cadena, versiones, datos validados, controles con sus entradas resaltadas y eventos); administración (plantillas, asignación y nombres).
- Backend nuevo: URL de lectura del original (F4), nombres visibles y directorio (F5), historial de consultas (F6) y validación `ausente` (F10, migración 0010).
- Semilla según EVD-B (F8). Procesamiento simulado y semilla local solo para desarrollo (F9).
- CORS en Terraform para la aplicación local del presentador (F7). Job de frontend en la CI (F13).
- DIF-21 cerrada como «No requiere cambio» (F12); DIF-67 resuelta con `ausente`; DIF-84 pasa al equipo (F11). Diferencias nuevas: DIF-87 a DIF-94.
- **Verificación:** pruebas de componentes y dos recorridos E2E (evidencia de la decisión observada y validación con fuente) contra el stack local con procesamiento simulado. **No probado contra AWS** (Cognito, API Gateway, IA real).

## Sesión AWS e90-ensayo-1 (22–23/10/2026, operador humano)

- Creadas `bootstrap` (bucket `atlas-estado-terraform-5566`, se conserva), `persistent` (42), `runtime` (8) y `demo` (35) con el paquete `93d4367`: los planes coincidieron con lo esperado.
- **Falla:** `inicializar_base` quedó a mitad de camino («PAM authentication failed» del maestro, `pg_hba +rds_iam`). Corregida en `002c5bd` (DIF-95: `rds_iam` al final) con pruebas y ensayo de CI limpio (698 aprobadas, 4 omitidas, 76 módulos ≥ 90 %). Se recreó solo la instancia RDS; la corrección **no llegó a probarse en AWS**.
- Retiro completo el 23/10/2026; verificación de residuos sin recursos salvo el bucket de estado. Sin datos ni documentos cargados.
- Paquete local `dist/atlas-lambda.zip` de `002c5bd` (SHA-256 `4ec77e9d…4a64b060`). `rds.force_ssl` con `pending-reboot` (sin diferencia perpetua en los planes).

## Sesión AWS e90-ensayo-2 (23/10/2026, operador humano)

- Creadas `persistent` (42), `runtime` (8) y `demo` (35); `inicializar_base` y `migrar` completos (`0010`, `al_dia: true`): DIF-95 verificada en RDS real.
- Fallas halladas y corregidas en la sesión, cada una con su commit: TLS hacia RDS Proxy con raíces de Amazon Trust (DIF-96, `75d2084`); ARN de la máquina en todas las Lambda (`9ca42d1`); firma `s3v4` solo para S3, Bedrock la rechazaba (DIF-97, `9b6c58b`); verificación previa de CORS respondida por el backend con ruta `OPTIONS` sin autorizador (DIF-98, `b9bc012`). Ensayo de CI limpio de `b9bc012`: 701 aprobadas, 4 omitidas, 76 módulos ≥ 90 %.
- **Verificado con servicios reales:** semilla EVD-B completa con Textract y Haiku 4.5 (las 22 sugerencias de C-v1, O-v1 y F-v2 coincidieron con el oráculo candidato; no es métrica de §6.3); nivel B 2/2 (extracción, y RAG con cita y abstención); aplicación web local contra API Gateway con Cognito, evidencia de la decisión, visor del PDF y consulta asistida.
- Residuos de la sesión: trámites 1 a 3 de intentos fallidos sin sugerencias; el 1 con trabajos abiertos (sin reconciliador, DIF-50), que impedirán `drenado: true`.
- Retiro el 23/10/2026 por decisión del operador con `trabajos_abiertos: 3` (residuo sintético del trámite 1): evidencia exportada y nivel B en `operaciones/sesiones/e90-ensayo-2/` (local, no versionado); verificación de residuos sin recursos salvo el bucket de estado.

## Próximo paso

**1.1 (equipo, manual):** sesión de demo con el paquete de `b9bc012` o posterior; mismo procedimiento que e90-ensayo-2 sin los tropiezos. Después: diseño del corpus E90 y del arnés de §6.3 (requiere aprobación).

**F11 (equipo):** oráculo v2 y regeneración de O y F con número estable.

Agente, cuando el equipo lo decida: Etapa 2 (RF-06, que habilita EVD-A y EVD-B y la versión nueva en la interfaz).

## Preguntas abiertas al equipo

- **DIF-84 (F11):** regenerar O y F con número estable y publicar el oráculo v2.
- **Registro de diferencias:** `docs/tesis/Registro_Diferencias_con_la_Tesis.md`, con 94 entradas pendientes de revisión por los autores.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Reglas del repositorio y forma de trabajo | `AGENTS.md` |
| Decisiones aprobadas por hito (P1…Pn) | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` (DO-2026-10-22-*) |
| Decisiones delegadas (modelo físico y rutas) y detalles técnicos (DT-*) | `docs/decisiones/Decisiones_Delegadas.md` |
| Diferencias con la tesis | `docs/tesis/Registro_Diferencias_con_la_Tesis.md` |
| Destinos y retención del contenido documental | `docs/operacion/Registro_Destinos_y_Retencion.md` |
| Puesta en marcha local, verificaciones y ensayo de CI limpio | `backend/README.md` |
