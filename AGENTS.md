# AGENTS.md — Instrucciones para el agente de código (ATLAS · PFI UADE 2026)

Este repositorio contiene la **reconstrucción desde cero** del prototipo ATLAS, descrito en la tesis «Arquitectura para la gestión inteligente de documentos y contratos con extracción automática de información, trazabilidad y firma digital».

Leé este archivo completo antes de cualquier tarea. Sus reglas tienen prioridad sobre cualquier costumbre o preferencia propia.

---

## 1. Documentos que gobiernan el trabajo

Leelos en este orden. Ante una contradicción, prevalece el de número menor.

| # | Documento | Ubicación | Qué define |
|---|---|---|---|
| 1 | Tesis vigente | `docs/tesis/` | **El contrato.** RF, RN, RNF, modelo de datos (Sección 5.2), arquitectura (Sección 5), validación (Sección 6) |
| 2 | Decisiones técnicas | `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` | Todo lo que la tesis no especifica y el equipo ya decidió |
| 3 | Contrato de aceptación integral (v1.1) | `docs/aceptacion/` | Cómo se verifica cada RF, RN y RNF |
| 4 | Criterios EVD-01 | `docs/aceptacion/` | Cadena de evidencia: V1–V11 y recorridos EVD-A, EVD-B, EVD-C, EVD-N12 |
| 5 | Diseño de infraestructura RC-P10 | `docs/diseno/RC-P10_Diseno_Infraestructura.md` | Detalle de la infraestructura AWS aprobada |
| 6 | Plan por etapas | `docs/plan/Plan_Implementacion_por_Etapas.md` | Qué se construye primero y qué entra en cada etapa |
| 7 | Protocolo E90 de evaluación | `docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md` | Decisión vigente sobre particiones sintéticas y separación de validación operativa |

Si un documento de esta lista no está en el repositorio, **detenete y avisá**. No lo reemplaces con suposiciones.

---

## 2. Reglas inviolables

1. **La tesis es el contrato.** No modifiques ni reinterpretes RF, RN, RNF, entidades o relaciones del modelo de datos, estados del trámite ni umbrales de la Sección 6 para facilitar la implementación. **Excepción documental explícita y acotada:** el equipo aprobó DO-2026-10-21-E90-CORPUS y revisó los criterios IA-D03 a IA-D07 para cambiar *solo* cantidades/composición del corpus §6.3.1. El PDF incluido todavía contiene el diseño anterior; sus autores lo actualizarán. Para implementar el corpus, seguí esta decisión más reciente y no restaures los 16 casos adicionales ni el conjunto público.
2. **Nada de código previo.** El prototipo anterior no se usa como base. Si encontrás código viejo en algún lado, ignoralo y avisá.
3. **No inventes requisitos.** Si algo no está en la tesis ni en las decisiones técnicas y no es una decisión delegada (ver §4), **detenete y preguntá**. No elijas un comportamiento funcional por tu cuenta.
4. **Para el agente, la CI y la demo: exclusivamente datos sintéticos.** Nunca ingieras, proceses, copies, publiques ni subas a AWS documentos reales, anonimizados o no, desde este repositorio o mediante el agente. Los datos de medición y prueba se generan en `corpus/`. **La validación operativa real (§6.4) es un procedimiento distinto y autorizado del equipo**, no una fuente de documentos para el agente, la CI o la demo: exige controles propios de confidencialidad, consentimiento/permiso y destinos RNF-03/RC-P09, y solo puede aportar resultados/evidencia saneados y autorizados. No falsifiques ni inventes su ejecución.
5. **El contenido documental nunca va a los registros.** Logs, trazas, errores y salidas de Step Functions solo contienen identificadores y metadatos técnicos (texto extraído, valores, fragmentos, consultas y respuestas quedan afuera).
6. **No existen operaciones funcionales para borrar** trámites, versiones ni eventos de auditoría (RNF-04, RN-10).
7. **Las reglas de consistencia usan solo valores validados**, nunca sugerencias de la IA (RN-02, RN-06). La IA nunca aprueba, observa ni cambia el estado del trámite.
8. **La separación entre demo y pruebas** se establece por despliegue y configuración del servidor, nunca por un parámetro de la petición (RC-P10).
9. **No ocultes resultados.** Si una prueba falla, se informa. No ajustes umbrales, oráculos ni datos para que pase.
10. **Dos evaluaciones separadas (DO-2026-10-21-E90-CORPUS):** §6.3 es cuantitativa y sintética (50 de medición; 10–15 de ajuste separados; 3 adversariales incluidos; 30 preguntas RAG); §6.4 es validación funcional/operativa independiente del equipo con resultados no confidenciales. No intercambiar muestras, métricas ni evidencias. El corpus de cinco PDF de PD-07 es un escenario EVD/demo candidato, **no** sustituye el corpus de 50.

---

## 3. Seguridad operativa (AWS, Terraform y Git)

- **Decisión del equipo del 21/10/2026 (DO-2026-10-21): operaciones AWS exclusivamente manuales.** Solo un integrante autorizado del equipo ejecuta creación, modificación, despliegue, inicio, detención, eliminación, migraciones remotas e invocaciones operativas de servicios AWS, después de revisar y aprobar expresamente el plan, el impacto y los costos. Los agentes preparan cambios y planes para revisión; no ejecutan esas operaciones, aun si se aprueba el plan.
- Ningún GitHub Action, push, merge, agente ni automatización puede operar infraestructura AWS. No configurar el proveedor OIDC de GitHub, roles IAM para Actions, `aws-actions/configure-aws-credentials`, credenciales AWS ni permisos `id-token: write` en workflows. Tampoco se admiten despliegues con `workflow_dispatch`: iniciar un workflow manualmente no equivale a ejecución manual por un operador.
- Terraform se conserva con estado remoto cifrado, versionado y bloqueado. Un plan preparado localmente no autoriza cambios; los planes con costos requieren estimación y presupuesto aceptado antes de la ejecución humana. Nunca ejecutar Terraform durante la presente tarea documental.
- ATLAS opera en sesiones controladas; E90 adopta infraestructura descartable: creación, migraciones, seed, pruebas y eliminación manual por sesión. Antes del primer recurso facturable debe existir presupuesto aprobado, inventario, plan de creación y **plan de destrucción selectiva** preparados y revisados. AWS Budgets alerta, no limita gasto ni autoriza despliegues.
- La prohibición operativa no elimina el procesamiento funcional de la tesis (Step Functions, Lambda y reconciliador de trabajos) dentro de una sesión autorizada; esas identidades no administran infraestructura. Ver DO-2026-10-21 y el runbook manual.
- **Modalidad E90A adoptada (DO-2026-10-21-E90A):** demo AWS descartable, sin persistencia entre sesiones. En E90 el operador humano puede aprobar y ejecutar la eliminación de recursos **identificados como propios de esa sesión**, incluida RDS, tras exportar evidencia y confirmar la pérdida de datos. La prohibición original de destruir `persistent` se sustituye **solo** en ese alcance: `bootstrap` (estado remoto), cuenta/Organizations/Budgets/privacidad y recursos ajenos siguen intocables. Proteger la destrucción con planes revisados y confirmación humana específica; nunca apagar con un `terraform destroy` indiscriminado ni usar `state rm` para saltarse protecciones.
- Conservar RF/RN/RNF: nunca habilitar borrado funcional de trámites, versiones ni auditoría. La eliminación de la infraestructura descartable es administrativa y **no acredita** persistencia entre despliegues ni recuperación de los mismos datos tras una destrucción.
- Una semilla sintética ejecutada manualmente prepara cada sesión nueva, por API y sin falsificar auditoría; no hay script de carga a AWS implementado aún porque falta la API y el esquema definitivo.
- No guardes credenciales, secretos ni claves en el repositorio ni en GitHub. GitHub Actions se limita a CI sin acceso a AWS: linting, análisis estático, pruebas unitarias, cobertura y PostgreSQL temporal con pgvector en el runner.
- Trabajá en **ramas de trabajo**. Podés hacer commits en tu rama con mensajes que citen los requisitos (por ejemplo, `RF-12: validación humana de campos extraídos`). **No hagas push ni merge a `main`** ni despliegues en el entorno `demo` sin revisión del equipo.
- Ante cualquier operación destructiva o irreversible, detenete y preguntá.

---

## 4. Decisiones delegadas

Podés decidir por tu cuenta **solo** estos tres temas (sección «Decisiones delegadas al agente de código» del documento de decisiones):

- **PD-04:** detalles físicos del modelo de datos (tipos, índices, restricciones). Toda entidad y relación de la Figura 5.4 debe existir; podés agregar columnas técnicas, nunca quitar ni renombrar conceptos de la tesis. **Los nombres de entidades del dominio respetan los de la Figura 5.4.**
- **PD-06:** formato de respuesta del endpoint de reconstrucción de evidencia (contenido fijado en PD-03).
- **RC-P01:** rutas y esquemas del resto de la API.

Cada decisión delegada se registra en `docs/decisiones/Decisiones_Delegadas.md` en el momento de tomarla: qué se decidió, por qué y qué requisito sirve. El modelo físico queda en las migraciones de Alembic y la API en la especificación OpenAPI que genera FastAPI.

Cualquier otra elección técnica no trivial (una biblioteca nueva, un servicio AWS no previsto, un cambio de patrón) **se consulta antes**.

---

## 5. Stack y convenciones

Lo que fija la tesis o las decisiones (no cambiar):

- **Backend:** Python, FastAPI en AWS Lambda, detrás de Amazon API Gateway. Migraciones con **Alembic**.
- **Base de datos:** Amazon RDS PostgreSQL con **pgvector**, acceso mediante RDS Proxy con autenticación IAM.
- **Procesamiento:** AWS Step Functions Standard, Amazon Textract, Amazon Bedrock (Claude Haiku 4.5; Cohere Embed Multilingual v3), EventBridge Scheduler para el reconciliador.
- **Autenticación:** Amazon Cognito.
- **Frontend:** React y TypeScript, servido con S3 y CloudFront.
- **Infraestructura:** Terraform, con los estados `bootstrap`, `persistent`, `runtime`, `demo` y `tests` (RC-P10-07).
- **Pruebas:** pytest (+ pytest-cov, objetivo ≥ 85 %), PostgreSQL con pgvector real para las pruebas de persistencia, Playwright para los recorridos críticos.
- **CI:** GitHub Actions sin acceso a AWS (RC-P02 y DO-2026-10-21). Despliegue y operación manual por el equipo.

Convenciones:

- Cada funcionalidad, migración, endpoint y prueba se **traza** a un RF, RN, RNF o decisión (ID en el nombre de la prueba, en el docstring o en el mensaje de commit).
- Idioma consistente en todo el código. Los conceptos del dominio usan los nombres de la tesis.
- Mantené actualizado `docs/operacion/Registro_Destinos_y_Retencion.md` (RNF-03, RC-P09): cada servicio que recibe contenido documental, su región o perfil, su retención y su verificación.

---

## 6. Cómo trabajar cada tarea

1. **Ubicá la tarea** en `docs/plan/Plan_Implementacion_por_Etapas.md` y en los requisitos que cubre.
2. **Leé** los RF, RN y RNF involucrados y las decisiones técnicas relacionadas.
3. **Proponé un plan corto** antes de escribir código si la tarea toca infraestructura, el modelo de datos o más de un módulo.
4. **Implementá en incrementos chicos**, con sus pruebas en el mismo cambio.
5. **Ejecutá las pruebas** que correspondan. No declares una tarea terminada con pruebas fallando o sin pruebas.
6. **Informá** con este formato:

```
Tarea: <hito del plan>
Requisitos cubiertos: <IDs>
Archivos modificados: <lista>
Decisiones delegadas tomadas: <IDs o «ninguna»>
Pruebas: <qué se ejecutó y resultado>
Pendientes o bloqueos: <lista>
Preguntas para el equipo: <lista o «ninguna»>
```

---

## 7. Definición de «terminado»

Una tarea está terminada cuando:

- cumple los requisitos citados sin contradecir la tesis ni las decisiones;
- tiene pruebas automatizadas que pasan, incluidas las negativas de autorización cuando corresponde;
- no registra contenido documental en logs;
- las decisiones delegadas están documentadas;
- el informe de §6 está completo.

**Una verificación de los contratos de aceptación solo puede marcarse como `Cumple` si se ejecutó contra su oráculo y se conservó la evidencia.** Que el código exista no la cumple.
