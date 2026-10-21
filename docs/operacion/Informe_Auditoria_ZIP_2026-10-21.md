**AVISO POSTERIOR E90A:** auditoría anterior a la decisión de demo descartable. Las menciones a RDS detenido y persistencia entre sesiones reflejan el estado en que fue redactada, no la política operativa vigente. Ver DO-2026-10-21-E90A.

# Auditoría del ZIP del repositorio ATLAS — 21/10/2026

**Entrada auditada:** `Tesis.zip` (SHA-256: `29c29f6c2b5e9ede394ac3f55f5d6d2a2505c816936d2fb8dab9dfeb1392a4db`). **Rama Git embebida:** `codex/aws-manual-costos`.

**Alcance:** lectura local del archivo comprimido, documentación y configuración, consistencia básica de rutas y fuentes, verificación estática de scripts/oráculo y revisión focal de PDF. Sin AWS, sin mutaciones cloud, sin Terraform y sin commits ni pushes. Esta auditoría no certifica la ingeniería completa de una aplicación que todavía no está en el ZIP.

## 1. Evaluación ejecutiva

**Valoración:** **adecuado como repositorio de preparación documental de Etapa 0**, **NO listo para desplegar la demo en AWS**. La política nueva se encuentra implementada documentalmente y no se observa infraestructura/prototipo reconstruido en este ZIP. La documentación no debe confundirse con pruebas reales de infraestructura, apagado, integridad o calidad de IA.

### Correcto y recomendable conservar

1. **DO-2026-10-21** está registrada; `AGENTS.md`, RC-P02, RC-P10, plan, README y runbooks coinciden en **sin GitHub OIDC, sin AWS desde Actions, despliegues y migraciones únicamente por operador**. GitHub Actions para CI sin AWS se mantiene permitido en diseño, aunque no existen workflows todavía.
2. **Terraform** permanece como enfoque previsto, con cinco raíces `bootstrap/persistent/runtime/demo/tests` y protecciones conceptuales para persistentes. No se lo reemplazó por scripts ad hoc ni se debilitó la arquitectura funcional.
3. El plan incorpora **1.0 antes del primer despliegue facturable** y 1.1 para comprobar el ciclo real; ya **no posterga la preparación del apagado a Etapa 3**. Siguen sin implementarse estas compuertas.
4. El runbook distingue `active/draining/offline`, IAM/TLS, migraciones privadas, reconexión al recrear proxy, preservación de S3/RDS, verificación de aislamiento e integridad y manejo de fallos. Está correctamente rotulado como **propuesto, no probado**.
5. `Politica_Costos_AWS.md` diferencia budgets (USD 1 y USD 20) de autorización económica; reconoce el reinicio de RDS a los siete días y costos residuales. El registro RNF-03/RC-P09 **no inventa evidencias**: anota las invocaciones de los cuatro modelos como verificaciones comunicadas por el equipo y mantiene pendiente Textract y retención efectiva.
6. Se conservaron documentos sintéticos C/O/F, sus versiones y oráculo preliminar; la revisión oficial de CUIT en ARCA está marcada **pendiente** y el corpus no figura congelado.
7. No aparecen workflows GitHub, trust OIDC, credenciales AWS en texto ni Terraform activo en el inventario de este ZIP. Los enlaces Markdown relativos comprobados no estaban rotos antes de los cambios de esta auditoría.

### Defectos concretos y riesgos

| Prioridad | Hallazgo en el ZIP | Acción o estado |
|---|---|---|
| **P0** | **Sin aplicación, Terraform ni pruebas del apagado:** un plan narrativo no acredita capacidad real de mantener la factura controlada. | No desplegar hasta implementar 1.0/1.1 y cumplir compuertas económicas. **Pendiente**. |
| **P0** | **RDS vuelve a iniciarse después de siete días**. La inspección o las alertas no impiden el reinicio ni los cargos. | Asignar operador/suplente y procedimiento manual verificable, o no crear RDS. **Pendiente**. |
| **P0** | **RC-P10-13 no tenía modelo numérico integrado**; USD 20 de Budget no alcanza para 24/7 con los supuestos básicos. | Se agrega informe y planilla. Falta cálculo oficial y aprobación: **PENDIENTE**. |
| **P1** | `oraculos/oraculo_PD07_preliminar.json` y `oraculos/README_ESTADO_CUIT_Y_CORPUS.md` referenciaban `fuentes/generar_corpus.py`, ruta inexistente. | **Corregido** a `herramientas/generar_corpus.py`, sin cambiar el corpus ni sus valores. |
| **P1** | El informe numérico anterior tenía una matriz de «cambios pendientes» que ya fue tratada por el ZIP presente. | La planilla incorporada actualiza **estado actual vs. pendiente real**. |
| **P1** | `docs/tesis/main.pdf` existe (149 páginas) pero no se identifica una versión contractual congelada; README de tesis lo reconoce. | Equipo debe confirmar versión/hash y correspondencia con RF/RN/RNF actuales. **Pendiente**. |
| **P1** | Los corpus contienen un CUIT candidato con dígito verificador correcto, pero **no hay consulta oficial ARCA**. | No congelar el corpus ni afirmar que el CUIT está desasignado. **Pendiente**. |
| **P1** | El ZIP conserva `.git` y su rama, pero en la copia inspeccionada `git status` mostró documentación y corpus **untracked**; el primer commit contiene solo el README de origen. | Revisar con `git status`, agregar y commitear explícitamente en rama de trabajo antes de confiar en clonación remota; **no se hizo commit** en esta auditoría. |
| **P2** | Faltaba `.gitignore`; futuros estados y planes Terraform, secretos/env y caches podrían subirse inadvertidamente. | **Creado** con exclusiones defensivas, sin bloquear `*.tf` ni ejemplos versionables. |
| **P2** | El alcance inicial exige una demo el sábado 24/10, con tareas 1.0/1.1 aún sin implementar. Riesgo de cronograma. | Mantener alternativa prevista en plan; **no omitir los controles** por la fecha. |

**Observación sobre la tesis:** las páginas iniciales de `main.pdf` contienen encabezados de «Agradecimientos» y «Resumen» sin desarrollo visible en las páginas consultadas; esto es una revisión focal, no una auditoría académica íntegra de las 149 páginas. No se modificó ni reescribió el PDF.

## 2. Cambios incorporados por esta auditoría

- `docs/operacion/RC-P10-13_Cotizacion_Preliminar_2026-10-21.md`: informe de arquitectura y costos, cifras bajo supuestos, riesgos y referencias.
- `docs/operacion/RC-P10-13_Modelo_Costos_2026-10-21.xlsx`: planilla editable con tarifas, fórmulas, escenarios, riesgos y matriz de cambios **actualizada respecto al ZIP recibido**.
- `docs/operacion/Informe_Auditoria_ZIP_2026-10-21.md`: este informe.
- `.gitignore`: higiene mínima para Terraform, secretos, archivos de entorno y cachés.
- Referencias cruzadas añadidas en `README_PRIMERO.md`, `docs/operacion/Politica_Costos_AWS.md`, `docs/plan/Plan_Implementacion_por_Etapas.md`, `operaciones/aws/README_OPERACION_MANUAL.md` y la adenda de `docs/operacion/Informe_Actualizacion_Manual_AWS_2026-10-21.md`.
- Corrección de ruta en `oraculos/README_ESTADO_CUIT_Y_CORPUS.md` y `oraculos/oraculo_PD07_preliminar.json`.

**No se tocaron** `docs/tesis/main.pdf`, PDFs/DOCX del corpus, RF/RN/RNF, diagramas, decisiones de arquitectura, roles IAM ni recursos de AWS. La creación del informe no cambia el estado de RC-P10-13: **PENDIENTE**.

## 3. Validación y cierre pendiente

Verificaciones realizadas/por repetir en esta copia: abrir ZIP íntegro, parsear JSON y enlaces Markdown, `bash -n` de scripts, `compile()` de Python sin generar pycache, revisión de rutas y lectura focal del PDF; ninguna de ellas evalúa la ejecución funcional de ATLAS.

**Próximas decisiones humanas:** aprobar la estimación final en AWS Pricing Calculator con parámetros definitivos, identificar responsables de cada sesión y del reinicio RDS, aceptar un presupuesto que contemple fallos/recuperación, desarrollar y validar apagado/encendido, congelar corpus tras consulta ARCA, y establecer pruebas del software implementado. Hasta entonces no hay autorización económica ni operativa para un despliegue de producción o demo.
