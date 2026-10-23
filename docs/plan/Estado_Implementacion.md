# Estado de la implementación — ATLAS (PFI UADE 2026)

**Propósito:** que cualquier persona o agente pueda retomar el trabajo sin el historial de conversaciones. Se actualiza en el mismo commit que cierra cada hito (AGENTS.md §6). El plan está en `Plan_Implementacion_por_Etapas.md`; este documento solo registra dónde estamos.

**Actualización:** 22/10/2026, después del hito 1.0 preparado en local (la Etapa 1 queda completa en local; nada se desplegó).
**Rama de trabajo:** `fundacion/local-backend` (no se hace merge a `main` sin revisión del equipo).
**Último commit con CI en verde en GitHub:** `2bb4dff` (hito 1.0; 677 pruebas aprobadas, 4 omitidas, cobertura total 98 % y los 73 módulos ≥ 90 %).
**Hito 1.0, ensayo de CI limpio local:** 677 pruebas aprobadas, 4 omitidas (EVD-A, EVD-B y las dos de nivel B de AWS), cobertura total 98 % y los 73 módulos ≥ 90 %; incluye la inicialización privilegiada contra el superusuario efímero de PostgreSQL.
**Hito 1.8, ensayo de CI limpio local** (`backend/herramientas_ci/ensayo_ci_limpio.sh`): 632 pruebas aprobadas, 4 omitidas (EVD-A, EVD-B y las dos de nivel B de AWS), cobertura total 98 % y los 65 módulos ≥ 90 %. Sin push: la CI de GitHub no corrió sobre este commit.

## Hitos de la Etapa 1

| Hito | Estado | Commit | Decisiones aprobadas | Punto de demo |
|---|---|---|---|---|
| Fundación local | Hecho | `b6df546`, `43cef95` | RC-P02, PD-04 (núcleo, migraciones 0001–0002) | — |
| 1.0 Preparación del despliegue manual | Hecho, solo local (Terraform validado sin AWS) | commit del hito 1.0 (`RC-P10…`) | DO-2026-10-22-OPS | — |
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

## Próximo paso

**1.1 (equipo, manual):**
1. Descargar el paquete de certificados de RDS (`infra/certificados/README.md`).
2. Cotizar en Pricing Calculator, incluidos Textract `AnalyzeDocument` y Bedrock, y aprobar el presupuesto.
3. Ejecutar `infra/terraform/README.md` pasos A.1 a A.9 con planes revisados.
4. Verificar A, B-E90, IAM, V-DB, V-MT y E, y retirar con el paso B.

Agente, cuando el equipo lo decida:
- **interfaz web** para los puntos de demo;
- **Etapa 2:** RF-06, que habilita EVD-A y EVD-B.

Antes de implementar se propone el diseño y se espera la aprobación.

## Preguntas abiertas al equipo

- **DIF-21:** ¿RF-21 exige auditar los intentos rechazados (401 y 403)? Hoy quedan solo en los registros técnicos.
- **DIF-67:** confirmar el flujo exige todos los campos del esquema validados. Si un campo no consta en el documento, ¿cómo se registra «no consta»? Hoy bloquea la confirmación.
- **Interfaz web para la demo** (ver «Próximo paso»).
- **DIF-84:** el oráculo PD-07 no trae número ni razón social de la orden y la factura; la semilla los toma del generador del corpus. ¿Se agregan al oráculo al congelarlo?
- **Registro de diferencias:** `docs/tesis/Registro_Diferencias_con_la_Tesis.md`, con 86 entradas pendientes de revisión por los autores.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Reglas del repositorio y forma de trabajo | `AGENTS.md` |
| Decisiones aprobadas por hito (P1…Pn) | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` (DO-2026-10-22-*) |
| Decisiones delegadas (modelo físico y rutas) y detalles técnicos (DT-*) | `docs/decisiones/Decisiones_Delegadas.md` |
| Diferencias con la tesis | `docs/tesis/Registro_Diferencias_con_la_Tesis.md` |
| Destinos y retención del contenido documental | `docs/operacion/Registro_Destinos_y_Retencion.md` |
| Puesta en marcha local, verificaciones y ensayo de CI limpio | `backend/README.md` |

## Incremento aislado del corpus E90 — 22/10/2026

**Rama:** `codex/corpus-e90`, desde `1e2a6c6`. **Decisión:** DO-2026-10-22-CORPUS-CONSTRUCCION y aprobación posterior de cuatro fuentes contractuales públicas. **Commit de implementación:** `5970ebe` (DO-2026-10-22-CORPUS-CONSTRUCCION); ajuste de finales de línea CSV y cierre documental en el commit siguiente. Esta sección describe solo el alcance de la rama del corpus; no cambia el estado del frontend ni del despliegue que se trabaja en paralelo.

- Generados 65 documentos **candidatos**: 50 de medición y 15 de ajuste, con las cuatro familias por tipo del plan y tres adversariales dentro de medición. PD-07 permanece intacto y separado.
- Doce CUIT candidatos de dígito válido, consulta manual ARCA pendiente; lista en `docs/evaluacion/corpus_e90/CUIT_Candidatos_Para_ARCA.md`.
- Registros fuente previos, dependencias aisladas, fuentes públicas atribuidas, parámetros de simulaciones y versiones/hashes de herramientas/archivos registrados.
- Inventario real, 403 referencias de campos y 30 consultas candidatas preparadas sobre documentos construidos. Ningún oráculo revisado por los autores ni congelado; no se midieron modelos ni se ejecutó AWS.
- Auditoría estática de PD-07: hashes de cinco PDF y tres conjuntos esperados cotejados; ocho campos y localizadores incompletos en el oráculo. DIF-84 sigue abierta.
- Pruebas finales y evidencia: ver `docs/evaluacion/corpus_e90/Informe_Cierre_Incremento.md`; se completa con resultados observados al terminar los comandos.
- Diferencias provisionales: DIF-E90-01 a DIF-E90-07. Se renumeran al integrar con los registros de otras ramas.

**Próximo paso:** revisión técnica independiente del otro agente, consulta manual ARCA, revisión de fuentes/traducciones, registros y referencias por los autores. Si cambia un CUIT u otro contenido, generar una revisión nueva y verificar de nuevo hashes/localizadores/consultas. La congelación y las campañas de IA quedan fuera del incremento.

## Adenda corpus ARG_A — 22/10/2026

DO-2026-10-22-CORPUS-ARG-A incorpora CPAU MEPAU A-301 (9.ª edición, 2023) en **E90-M-CTR-03**, PDF digital de medición; sustituye una repetición de BASE_A. Las cuatro familias previas siguen representadas. Los otros 64 documentos y 128 auxiliares conservan sus hashes. El corpus mantiene 50+15, tres adversariales y 30 preguntas; solo Q12 cambia sus referencias de contenido. No se toca la demo PD-07 ni el frontend, backend o infraestructura.

Procedencia, asignación de licencia al archivo concreto, cambios y condiciones CC BY-NC-SA 4.0 documentados en `docs/evaluacion/corpus_e90/Incorporacion_ARG_A_CPAU.md`, evidencia en `fuentes/` y `Revision_ARG_A.json`, atribución dentro del contrato y en `corpus/e90/ATRIBUCIONES.md`. DIF-E90-08 provisional. **Commit de implementación: `35dad5b`** (cierre documental en el commit posterior). Resultados finales: raíz 46 aprobadas/una omitida; local con render 44 aprobadas; CI limpia backend 677 aprobadas/cuatro omitidas, 98 % total y 73 módulos ≥90 %. Detalle en el informe de incorporación. Ninguna decisión delegada.

Estado: candidato, no congelado y sin oráculos revisados. Se mantienen pendientes ARCA, revisión independiente y revisión de ambos autores. Un solo contrato argentino no permite afirmar representatividad del contexto nacional ni ausencia de sesgos; su diversidad estructural se inspecciona y documenta antes de medir.


## Actualización de consulta manual CUIT — 22/10/2026

El equipo informó y confirmó fecha de consulta ARCA **22/10/2026**, con resultado **«No existe» para los doce CUIT candidatos**. Coinciden exactamente con los usados en E90 y todos tienen dígito válido. Se registra como evidencia del equipo en `docs/evaluacion/corpus_e90/Verificacion_Manual_CUIT_ARCA_2026-10-22.md` y en `oraculos/e90/cuit_candidatos.json`; no se atribuye una consulta independiente del agente ni una garantía absoluta de inexistencia. No se aportaron capturas; fecha/resultado quedan documentados por declaración explícita del equipo.

No se necesita reemplazar números según este reporte. Los 65 documentos y sus 130 auxiliares conservan sus bytes/hashes; sus leyendas de ARCA pendiente describen la generación anterior al reporte y se actualizarán en una eventual revisión definitiva autorizada. El corpus y los CUIT siguen candidatos. Próximo paso: revisión independiente y de ambos autores antes de congelar; la consulta manual previa deja de estar pendiente a nivel del reporte recibido. Sin cambios de protocolo, código, dependencias ni diferencias nuevas con la tesis. Referencia Git: actualización con mensaje `DO-CORPUS: registrar consulta manual ARCA de doce CUIT`.


## Material para revisión de los autores — 22/10/2026

Preparada `docs/evaluacion/corpus_e90/Guia_Revision_Autores_E90.md`, con enlaces a los 65 archivos de entrada y tres cuadernos legibles: documentos/403 campos y fragmentos de texto; 30 preguntas RAG con fuentes/abstenciones; cinco familias contractuales con 43 cláusulas originales/adaptadas. Base de los datos: `b201471`. Referencia Git del material: commit con mensaje `IA-D/RC-P06.2: preparar guía completa de revisión de autores`.

Verificados los recuentos, la transcripción de los campos/preguntas/cláusulas, 488 enlaces locales y 95 anclas; las ocho fuentes canónicas y 195 artefactos conservan sus hashes. Suite raíz: 46 aprobadas y una omitida explícitamente. Se distingue la revisión previa del corpus/oráculos de la evaluación independiente de respuestas de IA (IA-M06) posterior a ejecutar. No se agregan criterios ni decisiones delegadas/diferencias nuevas; no se modifica código, corpus o JSON. Todas las casillas y revisiones de autores permanecen pendientes; se señalan metadatos heredados y decisiones de adecuación/naturalidad para revisar antes de congelar.


## Revisión técnica sustantiva del candidato E90 — 22/10/2026

Sobre `630d0da`, a pedido del equipo, el agente constructor realizó una autorrevisión técnica completa: 65 documentos / 104 páginas inspeccionadas, 403 campos (398 presentes y cinco ausencias), 43 extractos de cinco fuentes públicas y 30 preguntas/contextos. Todos los cotejos mecánicos de valores, localizadores y hashes resultaron consistentes. Suite raíz: 46 aprobadas/una omitida por render local optativo desactivado; validadores sin errores; Ruff sin hallazgos.

**Dictamen: integridad estructural verificada; todavía no apto para congelar ni medir definitivamente.** Q11–Q18 exigen un canal no preguntado; IDs/glosas agregadas facilitan artificialmente la clasificación; COM-08 no recibe la transformación de ambigüedad por la etiqueta compuesta. Otros pendientes: justificar FAC-08, fortalecer los ataques contrastables, desagregar afirmaciones y revisar diversidad RAG, sincronizar metadatos históricos de fuentes/ARCA. Detalle, propuestas acotadas y evidencia en `docs/evaluacion/corpus_e90/Revision_Tecnica_Agente_2026-10-22.md` y su JSON. IDs de revisión provisionales REV-E90-01 a REV-E90-06, sin renumerar DIF de otras ramas.

No se modificaron código, documentos del corpus ni ocho archivos canónicos; los 195 artefactos conservan hashes. No se ejecutó AWS, no se mezcló frontend y no se marcaron autores, oráculos o resultados como aprobados. No se cambia el protocolo ni se implementan aquí las correcciones propuestas. Próximo paso: resolver los hallazgos antes de la revisión/congelación humana y las campañas RC-P07, que siguen pendientes. Referencia Git: commit con mensaje `IA-D/RC-P06.2: documentar revisión técnica y hallazgos del corpus`.


## Revisión técnica de contraste del candidato E90 — 22/10/2026

Sobre `e871a59`, a pedido del equipo, un agente que no construyó el incremento revisó corpus, oráculos y generadores. Suite raíz: 46 aprobadas/una omitida; validador sin errores; integración con `fundacion/local-backend` sin conflictos. **Dictamen: no apto para congelar ni medir.** Confirma REV-E90-01 a REV-E90-06 y agrega REV-E90-07 a REV-E90-13: valores con un único formato y secuencias determinísticas, ID E90 como número documental y en 24 preguntas, ninguno de los cuatro casos ambiguos efectivamente ambiguo, aclaración embebida que neutraliza los tres adversariales, preguntas RAG sin recuperación real ni cláusulas contractuales, tríadas con proveedores y monedas distintos y 40 de 50 documentos de una página. Detalle en `docs/evaluacion/corpus_e90/Revision_Tecnica_Contraste_2026-10-22.md`.

No se modificaron corpus, oráculos, código ni hashes; no se ejecutó AWS ni se marcaron revisiones como aprobadas. Próximo paso: decisión del equipo sobre una revisión candidata v2 que aplique REV-E90-01 a 13 en conjunto, sin cambiar cantidades, particiones ni umbrales; luego revisión de autores y congelación. Pregunta abierta: si esta revisión cuenta como la revisión técnica independiente de P6. Referencia Git: commit con mensaje `IA-D/RC-P06.2: revisión técnica de contraste del corpus E90`.


## Aprobaciones posteriores a la revisión de contraste — 22/10/2026

DO-2026-10-22-CORPUS-REVISION: el equipo aprobó que la revisión de contraste cuente como revisión técnica independiente (P6) y aprobó en principio la regeneración v2. Se agregan REV-E90-14 (plantillas exclusivas de medición casi idénticas a las compartidas en tipos no contractuales) y REV-E90-15 (entidades y CUIT compartidos entre ajuste y medición; ID E90 en nombres de archivo y metadatos). Diseño v2 propuesto en `docs/evaluacion/corpus_e90/Propuesta_Corpus_V2.md`, **pendiente de aprobación**; no se regeneró nada. Referencia Git: commit con mensaje `DO-2026-10-22-CORPUS-REVISION: aprobaciones y propuesta de corpus v2`.


## Corpus E90 candidato v2 — 22/10/2026

DO-2026-10-22-CORPUS-REVISION, diseño P0–P16 aprobado por el equipo. Construido por Claude Code (P0). **Commit de datos y código: `2082a6e`**; documentación en el commit siguiente. Resuelve REV-E90-01 a 15 sin cambiar cantidades, particiones, plantillas, adversariales, reparto de preguntas ni umbrales: sujetos verosímiles y disjuntos por partición, formatos por familia, nombres de archivo neutros, estructuras propias de MED_C/MED_D, 20 no contractuales de medición con dos páginas, cuatro ambigüedades justificadas, adversariales contrastables, cuatro trámites coherentes y 30 preguntas sin IDs (cinco sobre cláusulas, abstenciones en seis contextos). Manifiesto e inventario v1 en `docs/evaluacion/corpus_e90/v1/`.

Verificación: validador sin errores; inventario válido; suite raíz 60 aprobadas y una omitida (58 con render local); ruff sin hallazgos; hoja de contactos de las 121 páginas. Detalle y límites en `docs/evaluacion/corpus_e90/Informe_Revision_V2.md`; cuadernos y guía de autores regenerados para la v2. Diferencias: DIF-E90-09 y 10, actualización de 06 y 07. Ninguna decisión delegada.

**Próximo paso:** el equipo verifica a mano las 18 razones sociales y los 6 CUIT de ajuste (`Verificaciones_Pendientes_V2.md`); revisión de contraste de la v2 por el otro agente; revisión de ambos autores y congelación. Campañas RC-P07 pendientes.


## Contraste técnico del corpus E90 v2 — 23/10/2026

P0 de DO-2026-10-22-CORPUS-REVISION: Codex revisó la v2 construida por Claude Code (`2082a6e`, documentación `d5f20ba`, base inspeccionada `f121f68`). Codex había construido la v1; la independencia declarada se limita a la construcción de la v2. **Dictamen: apto para revisión de autores, con observaciones; no congelado ni aprobado por autores.**

Reproducidos validadores e inventario sin errores; suite raíz 60 aprobadas/una omitida; render primero falló dentro del sandbox (57 aprobadas/una fallida, salida conservada) y pasó fuera con el mismo LibreOffice (58 aprobadas). Ruff y formato sin hallazgos. Cotejo separado: 403 campos, 727 fragmentos, 30 consultas y 121 páginas de referencia; muestra visual de 25 documentos/43 páginas, incluidas capturas finales y DOCX. Los 195 artefactos y 213 archivos protegidos en total mantienen sus hashes; corpus, oráculos y herramientas se conservaron en solo lectura.

Los quince hallazgos anteriores están sustantivamente abordados; persisten límites de dificultad/coherencia que se precisan en REV-E90-16 a REV-E90-19: IVA residual con diferencia de un centavo en PRE-05/PRE-09; condiciones de pago no conciliadas en T1/T2/T4; prefijo OC en el ambiguo OC-07; alcance de las referencias inglesas para Q11/Q12. Informe y evidencia: `docs/evaluacion/corpus_e90/Revision_Contraste_V2_2026-10-23.md` y su JSON. Se proponen correcciones sin aplicarlas ni cambiar umbrales.

Próximo paso: revisión de ambos autores y resolución/justificación de observaciones, verificaciones manuales de razones sociales/seis CUIT de ajuste; después, congelación y campañas RC-P07 aún pendientes. Sin consultas manuales simuladas, métricas de modelos, AWS, Terraform, frontend ni revisión humana marcada. Referencia Git: commit con mensaje `IA-D/RC-P06.2: contrastar corpus E90 v2 y documentar observaciones`.
