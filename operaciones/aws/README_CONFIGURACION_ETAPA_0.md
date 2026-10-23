# ATLAS — Etapa 0 / Runbook de configuración y aceptación

**Actualizado:** 21/10/2026 (DO-2026-10-21). **Estado:** preparación local; el equipo comunicó verificaciones AWS de esta fecha, con capturas formales pendientes de consolidación. El agente no accedió a la cuenta ni ejecutó cambios AWS durante esta tarea. Las instrucciones de mutación son exclusivamente para ejecución humana tras aprobar impacto y costos; no son autorización permanente.

Operación y compuertas: [runbook manual](README_OPERACION_MANUAL.md) y [política de costos](../../docs/operacion/Politica_Costos_AWS.md). ATLAS no funciona permanentemente en AWS durante el desarrollo.

> Referencias locales: `Plan_Implementacion_por_Etapas.md` (§ Etapa 0), `Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` (RC-P09, PD-07), `AGENTS.md`, `RC-P10_Diseno_Infraestructura.md`. En caso de contradicción, la tesis vigente y el orden de precedencia de `AGENTS.md` gobiernan las decisiones.
>
> Nunca adjuntar claves, contraseñas, tokens, estados Terraform, ARN sensibles ni capturas que contengan secretos al repositorio público. Los outputs de AWS pueden contener número de cuenta. Conservar evidencia técnica saneada y usar identificadores limitados.

## Criterio de avance

| ID | Acción | Prueba o evidencia | Estado | Responsable |
|---|---|---|---|---|
| 0.1 | Repositorio nuevo sin código anterior | URL y hash de commit inicial | PENDIENTE | Equipo |
| 0.2 | Documentos obligatorios | `docs/tesis/main.pdf` presente y leído; confirmar congelación/versionado contractual | PRESENTE; congelación pendiente | Equipo |
| 0.3 | Organizations + exclusión | Verificación efectiva comunicada el 21/10/2026 | VERIFICADO POR EQUIPO | Equipo |
| 0.4 | Cuatro modelos | Invocaciones exitosas comunicadas; perfiles y dimensiones en registro de destinos | ACCESO VERIFICADO POR EQUIPO; capturas pendientes; Titan 1024 pendiente | Equipo |
| 0.5 | Logging Bedrock desactivado | Verificación comunicada el 21/10/2026 | VERIFICADO POR EQUIPO; capturas pendientes | Equipo |
| 0.6 | AWS Budgets y costos | Dos presupuestos revisados el 21/10/2026; detalle en política de costos | REVISADOS POR EQUIPO; cotización/importe aceptado pendientes | Equipo |
| 0.7 | Preparar despliegue manual | Operador, plan exacto, costos, inventario, apagado y recuperación aprobados; sin OIDC de GitHub | DOCUMENTADO; implementación/verificación pendientes | Equipo |
| 0.8 | Corpus C-v1, ARCA y huellas | PDF + DOCX + oráculo + verificación de consulta ARCA | CANDIDATO, NO CONGELADO | Equipo |

## 0.1-0.2 — Repo y documentos

1. Crear repositorio privado o rama nueva, sin trasladar prototipo anterior.
2. Añadir `AGENTS.md` y copias de documentos vigentes en sus rutas esperadas:
   - `docs/tesis/main.pdf` **vigente** o fuente LaTeX equivalente: **no inferir que el E50 es el main vigente**.
   - `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md` y `Decisiones_Delegadas.md`.
   - `docs/aceptacion/Contrato_Aceptacion_Integral_Reconstruccion_PFI_2026-10-20_v1_1.md` y `EVD-01_Criterios_Aceptacion_Reconstruccion_APROBADO_2026-10-20.md`.
   - `docs/diseno/RC-P10_Diseno_Infraestructura.md`.
   - `docs/plan/Plan_Implementacion_por_Etapas.md`.
   - `docs/operacion/Registro_Destinos_y_Retencion.md`.
3. Copiar `corpus/` y `oraculos/` del paquete generado. NO marcar el CUIT como validado por ARCA hasta consultar el portal oficial.
4. Verificar que no hay credenciales en el repositorio, habilitar protección de `main` y revisión de PR.

## 0.3 — AWS Organizations / política opt-out

1. Entrar a AWS usando una identidad administradora con MFA; **no usar root para trabajo diario**. Confirmar cuenta objetivo y región principal `us-east-1`.
2. AWS Organizations -> crear organización si la cuenta está fuera de una; usar la modalidad de funciones completas que requiere la política. Si ya es miembro de otra organización, pedir al administrador de la organización que aplique la política (no intentar crear una nueva desde la cuenta miembro).
3. Organizations -> **AI services opt-out policies** -> habilitar tipo de política si está desactivado -> **Opt out from all services** -> confirmar y asociar la política a la raíz de la organización o a la cuenta correcta.
4. Verificar **política efectiva** de la cuenta: debe contener exclusión de uso de contenido para mejora de servicios, incluyendo **Amazon Textract**. No suponer que tener una política creada implica que está adjunta.
5. Guardar fecha UTC, identidad de rol (sin credenciales), cuenta parcialmente ocultada, política efectiva (sin otros datos privados). Esta política **no** impide el procesamiento temporal del servicio ni sustituye el inventario de destinos.

```bash
aws sts get-caller-identity --query '{Account:Account,Arn:Arn}'
aws organizations describe-organization --query 'Organization.{Id:Id,FeatureSet:FeatureSet}'
aws organizations describe-effective-policy --policy-type AISERVICES_OPT_OUT_POLICY --query 'EffectivePolicy.PolicyContent' --output text
```

Fuentes: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_ai-opt-out_all.html y https://docs.aws.amazon.com/cli/latest/reference/organizations/describe-effective-policy.html

## 0.4 — Bedrock y modelos

1. En consola: `us-east-1` -> Amazon Bedrock -> Model catalog. Buscar exactamente:
   - Anthropic Claude Haiku 4.5 (principal del procesamiento).
   - Anthropic Claude Sonnet 4.6 (comparación experimental posterior).
   - Cohere Embed Multilingual v3 (principal de embeddings).
   - Amazon Titan Text Embeddings V2 (comparación posterior).
2. En regiones comerciales, muchos modelos se habilitan al primer uso. Para modelos Anthropic completar el formulario de *First Time Use* si aparece, con la finalidad académica real y URL del proyecto/perfil real que efectivamente exista. Una URL inventada NO corresponde. Revisar y aceptar acuerdos de proveedor antes de su primer uso, bajo identidad administradora autorizada.
3. Si existen `AccessDeniedException`, revisar acceso de cuenta, requisitos de Marketplace / método de pago, permisos IAM, restricciones regionales y estado del acuerdo. El hecho de que aparezca en el catálogo **no demuestra** posibilidad de invocación.
4. Ejecutar `list-foundation-models` y `list-inference-profiles`. Para ambos Claude, identificar el **perfil geográfico US** que corresponde, NO usar perfiles Global. Para cada perfil seleccionado llamar `GetInferenceProfile` desde `us-east-1` y conservar todos sus `models[].modelArn` como destinos reales. No inferirlos del prefijo `us.`.
5. Identificar modalidad de uso efectiva de Cohere y Titan, dimensiones 1024 para la prueba comparable; verificar el soporte exacto en esa región y probar invocaciones mínimas **solo tras aprobar cualquier costo**. Las invocaciones reales no se realizan desde este paquete.
6. Registrar un inventario de ID de modelo, modalidad, perfil, destino, permiso, fecha, prueba y costo estimado. Las claves no deben figurar.

```bash
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[].[modelId,modelName,modelLifecycle.status]' --output table
aws bedrock list-inference-profiles --region us-east-1 --type-equals SYSTEM_DEFINED --query 'inferenceProfileSummaries[].[inferenceProfileId,inferenceProfileName,status]' --output table
# Cambiar PERFIL_US_VERIFICADO por el ID exacto que devolvió la cuenta:
aws bedrock get-inference-profile --region us-east-1 --inference-profile-identifier PERFIL_US_VERIFICADO --query '{Id:inferenceProfileId,Status:status,Models:models[].modelArn}'
```

**No copiar `PERFIL_US_VERIFICADO` literalmente.** No inventar identificadores de perfiles/ARN. Fuentes: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html y https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html

## 0.5 — Logging de invocaciones de Bedrock

1. En Bedrock (us-east-1), Configuration -> Model invocation logging: comprobar que ninguna modalidad de logging de entradas/salidas esté habilitada y que no se haya configurado un destino S3 o CloudWatch para capturar invocaciones.
2. Comprobar vía API/CLI. Registrar salida y hora. Si no existe configuración, documentar expresamente `sin configuración de logging` y confirmar por consola; no asumir que un error es siempre prueba de desactivación.
3. Revisar si existen otras regiones de origen activas: este control es regional. Desactivar el logging no equivale a apagar CloudTrail, ni autoriza a registrar prompts/respuestas en logs de la aplicación.

```bash
aws bedrock get-model-invocation-logging-configuration --region us-east-1
```

Fuente: https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html

## 0.6 — Presupuestos y aprobación económica

El equipo comunicó la revisión del 21/10/2026 de `tesis-dinero-real` (USD 1 mensual; real 50 %, previsto 100 %) y `tesis-uso-mensual` (USD 20 mensual; real 50/80/100 %, proyectado 100 %). Sin filtros por servicio o región; destinatarios `Active (legacy)`. Conservar capturas saneadas, todavía pendientes, y comprobar recepción efectiva: ese estado no acredita entrega inmediata.

No crear presupuestos duplicados ni cambiar los existentes como parte de esta tarea. Son alertas, no límites automáticos de gasto ni autorizaciones de despliegue. No está aceptado un importe para la arquitectura completa ni se afirma que USD 20 alcance.

Antes del primer recurso facturable completar RC-P10-13 según la [política de costos](../../docs/operacion/Politica_Costos_AWS.md): tarifas oficiales de `us-east-1`, hora/sesión/mes con inactividad, residuales, mínimos/redondeos y recuperación; registrar el presupuesto aceptado, operador y supervisión de apagado. Revisar costos reales después de cada sesión y reconciliarlos cuando aparezcan los cargos.

## 0.7 — Preparación de despliegues exclusivamente manuales

1. No configurar proveedor OIDC de GitHub ni roles IAM para Actions; no usar credenciales AWS en GitHub ni `aws-actions/configure-aws-credentials`. Sin workflows de operación AWS, tampoco con `workflow_dispatch`.
2. Preparar una identidad humana autorizada, con MFA y mínimo privilegio; su selección y permisos los revisa el equipo. No escribir credenciales en archivos del repositorio, GitHub o planes compartidos.
3. Preparar estado remoto cifrado/versionado/bloqueado, inventario previsto y planes por raíz `bootstrap → persistent → runtime → demo/tests`. No hay Terraform implementado todavía. Los planes y cualquier salida sensible se conservan en un destino de revisión restringido.
4. Registrar para cada operación: identidad/cuenta/región/entorno, commit/artefactos, plan exacto, recursos afectados, costo, aprobación expresa, ventana y responsable/suplente. El plan no es permiso de ejecución para el agente.
5. Antes de crear recursos: cumplir Etapa 1.0 y preparar apagado/recuperación. Después del despliegue técnico en `offline`: verificar el ciclo antes de habilitar demo, según [runbook manual](README_OPERACION_MANUAL.md).
6. Inicialización y migraciones: el humano invoca las Lambda privadas autorizadas, con conexión directa a RDS, IAM y usuarios de migración separados por entorno (RC-P10-15). La credencial maestra gestionada solo sirve para inicialización privilegiada; jamás se entrega a un runner.
7. GitHub Actions solo ejecuta CI sin AWS (linting, análisis estático, unitarias, cobertura, PostgreSQL temporal con pgvector). Las pruebas reales AWS se ejecutan en sesiones aprobadas fuera del runner.

La plantilla OIDC anterior fue retirada; el antecedente está en DO-2026-10-21. No se infiere que haya un proveedor o rol OIDC creado en la cuenta; si se descubre alguno, el equipo revisará manualmente su retirada mediante un cambio separado autorizado.

## 0.8 — Corpus sintético y consulta ARCA

1. Corpus preparado en `corpus/`: contrato C-v1 digital de 10 páginas y cuatro documentos administrativos de prueba O-v1, O-v2, F-v1 y F-v2.
2. **CUIT candidato** `30-96472518-3`: pasó prueba local de longitud, prefijo de sociedad (30) y dígito verificador. **NO está verificado como no asignado en ARCA**. Una búsqueda web general sin coincidencias no es comprobación suficiente.
3. Abrir el **buscador público oficial de ARCA** https://arca.gob.ar/buscador-consultas-publicas/ -> Constancia de inscripción o Estados administrativos de CUIT -> consultar los 11 dígitos `30964725183`. Guardar fecha, consulta y resultado (captura saneada). Si aparece una entidad real o surge incertidumbre, elegir nuevo CUIT ficticio, regenerar todos los documentos, exportar los PDF y congelar nuevos hashes.
4. Revisar manualmente que el CUIT aparezca igual en C/O/F, que no haya CAE, QR fiscal, personas reales, cuentas bancarias ni firmas reales. No llamar al CUIT “verificado” si la consulta oficial no se hizo.
5. Actualizar `oraculos/oraculo_PD07_preliminar.json` con evidencia ARCA y cambiar a `congelado` solo luego de validar contenido, páginas, hashes y documentos. Los hashes publicados se refieren solo a **esta versión candidata**.
6. Conservar la etiqueta visible **DOCUMENTO FICTICIO - SIN VALIDEZ COMERCIAL NI FISCAL**. 

## Entrega al agente: criterio de desbloqueo

Habilitar la Etapa 1 cuando:
- El repositorio tenga la **tesis vigente** y todos los documentos requeridos por `AGENTS.md`.
- Los controles de AWS 0.3 y 0.5 tengan evidencia de configuración efectiva, y los modelos necesarios para el hito a desarrollar puedan invocarse con permisos correctos.
- Los perfiles de inferencia y destinos estén documentados.
- Existan cotización oficial, presupuesto aceptado, inventario previsto, planes y costos aprobados y apagado/recuperación preparados antes del primer recurso facturable. Los budgets existentes solo alertan; no autorizan `terraform apply`.
- C-v1 esté disponible en PDF digital de 10 páginas y se documente el resultado ARCA. Una consulta pendiente **bloquea congelar el corpus como definitivo**.
- Solo el operador humano ejecuta las operaciones AWS, después de aprobar plan/impacto/costos; el agente no ejecuta `terraform apply/destroy`, despliegues, migraciones remotas ni cambios AWS. La habilitación de demo exige las verificaciones de 1.0/1.1, con evidencia, no solo este documento.

**Fecha y evidencia reales deben agregarse al completar cada paso; nunca declarar “Cumple” por seguir instrucciones o tener archivos preparados.**
