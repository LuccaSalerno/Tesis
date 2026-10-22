# Registro de destinos y retención (RNF-03, RC-P09)

**Actualización:** 21/10/2026. Cada servicio que almacena o procesa información se contrasta con la cuenta **antes de la primera carga** y después de cada cambio de configuración. Los destinos de abajo describen el diseño; no acreditan recursos desplegados.

**Origen de las observaciones:** verificaciones del 21/10/2026 comunicadas expresamente por el equipo en esta tarea. El agente no accedió a AWS ni repitió las invocaciones. **Capturas formales pendientes de consolidación**, sin rutas de evidencia todavía. Los resultados de acceso no acreditan calidad, latencia, costo medido ni cumplimiento integral de RNF-03/RNF-09. Lo no observado queda pendiente.

| Destino | ¿Puede contener documentos o fragmentos? | Región o perfil | Finalidad | Retención | Controles de exclusión / registro | Verificación comunicada / pendientes |
|---|---|---|---|---|---|---|
| S3 documental demo | Sí | us-east-1 | Originales, cargas pendientes y resultados por trabajo/intento; control de mantenimiento protegido | Versionado previsto; originales sin expiración indiscriminada; política efectiva pendiente | Cifrado y acceso exclusivo demo previstos | Sin verificación de despliegue/retención |
| S3 documental tests | Sí | us-east-1 | Equivalentes de pruebas, separados de demo | Política efectiva pendiente; control de mantenimiento excluido de reinicialización | Sin permisos cruzados | Sin verificación de despliegue/retención |
| S3 estado remoto | No como destino documental; puede contener datos sensibles de infraestructura | us-east-1 | Estados bootstrap/persistent/runtime/demo/tests | Versionado, cifrado y bloqueo nativo previstos; retención efectiva pendiente | Acceso restringido; no publicar estado/planes ni secretos | Sin verificación de despliegue |
| RDS PostgreSQL | Sí (valores validados, fragmentos y embeddings) | us-east-1 | Datos y auditoría; bases pfi_demo/pfi_tests | Backups iniciales propuestos de 7 días; configuración efectiva pendiente | Cifrado, TLS, IAM y usuarios separados; inmutabilidad funcional de auditoría | Sin verificación de despliegue/retención |
| Textract | Sí | us-east-1 | Análisis asíncrono de PDF | Resultados cifrados 7 días según tesis §5.4.3; verificar configuración efectiva | Política efectiva de exclusión de Organizations comunicada como verificada | 21/10: exclusión verificada por equipo; invocación Textract/retención no informadas; capturas pendientes |
| Bedrock — Claude Haiku 4.5 | Sí | `us.anthropic.claude-haiku-4-5-20251001-v1:0`; origen us-east-1; destinos us-east-1, us-east-2, us-west-2 | Clasificación, extracción y consulta asistida | Condición aplicable al modelo/modalidad según tesis; documentación/evidencia formal pendiente | Perfil geográfico US activo; logging desactivado según equipo | 21/10: Converse `OK`, 17 tokens entrada / 4 salida; capturas pendientes |
| Bedrock — Claude Sonnet 4.6 | Sí | `us.anthropic.claude-sonnet-4-6`; origen us-east-1; destinos us-east-1, us-east-2, us-west-2 | Comparación experimental, no sustitución del modelo principal | Verificar condición específica de modelo/modalidad; no inferir de Haiku | Perfil geográfico US activo; logging desactivado según equipo | 21/10: Converse `OK`, 17 tokens entrada / 4 salida; capturas pendientes |
| Bedrock — Cohere Embed Multilingual v3 | Sí | Invocación en us-east-1 | Embeddings principales | Verificar condición específica de modelo/modalidad | Logging desactivado según equipo | 21/10: invocación exitosa, un vector de 1024 dimensiones; capturas pendientes |
| Bedrock — Titan Text Embeddings V2 | Sí | Invocación en us-east-1 | Comparación de embeddings | Verificar condición específica de modelo/modalidad | Logging desactivado según equipo | 21/10: smoke test exitoso, un vector de 256 dimensiones, 12 tokens entrada; comparación 1024 pendiente; capturas pendientes |
| Lambda y RDS Proxy | Sí, en tránsito/procesamiento de aplicación | us-east-1 | API, procesamiento, persistencia y acceso SQL | Sin contenido en logs; retención efectiva de registros pendiente | Roles mínimos separados, TLS; verificar errores y reintentos | Sin verificación de despliegue |
| Step Functions Standard / Scheduler | No (solo IDs y metadatos técnicos) | us-east-1 | Orquestación y activación del reconciliador funcional | Historial y retención efectiva pendientes de inspección | Sin documentos, valores, prompts ni respuestas en entradas/salidas; Scheduler manualmente deshabilitado al apagar | Sin verificación de despliegue |
| CloudWatch / trazas OpenTelemetry | No (solo metadatos técnicos) | us-east-1 | Diagnóstico y correlación | Política efectiva pendiente | Excluir texto, valores, fragmentos, consultas/respuestas y secretos incluso en errores | Búsqueda de marcadores RNF-09 pendiente |
| Cognito | No (solo identidades) | us-east-1 | Autenticación de usuarios por entorno | Política efectiva pendiente | Dos User Pools; OIDC/OAuth2 funcional conservado | Sin verificación de despliegue |
| S3 web / CloudFront / API Gateway | API puede transportar valores/documentos autorizados; frontend solo artefactos estáticos | S3/API: us-east-1; distribución CloudFront global según diseño | Entrega web y acceso autenticado | Configuración de caché/retención pendiente; no cachear contenido sensible en distribución web | Sin contenido en access logs; autorización/cifrado y configuración por verificar | Sin verificación de despliegue |

## Notas de implementación (código local, 22/10/2026)

Hechos del código del repositorio, verificados con pruebas automatizadas locales sin AWS. No acreditan recursos desplegados ni retención efectiva.

- **S3 documental:** los originales se guardan con la clave `tramites/{tramite_id}/cargas/{uuid}`. El navegador los transfiere directamente mediante una URL prefirmada de PUT (vigencia configurable, 15 min por defecto); el binario no pasa por la API. Al confirmar, la API lee el objeto para validar su contenido y calcular su huella SHA-256.
- **Objetos no confirmados o rechazados:** permanecen en el bucket, porque la aplicación no borra objetos. **Pendiente:** definir en la IaC una regla de ciclo de vida que expire las cargas que no llegaron a registrarse como archivo. Hay que decidir el plazo y comprobar que la regla no afecte a los originales registrados.
- **Step Functions:** la entrada de cada ejecución contiene solo `{"trabajo_id", "intento"}`, y su nombre es `trabajo-{id}-intento-{n}`. Una prueba automatizada lo verifica contra moto.
- **Registros de la API:** se verificó que no contengan el token, la URL prefirmada firmada, el título del trámite ni el nombre del archivo.
- **moto (desarrollo y CI):** es una simulación local en `127.0.0.1` o dentro del proceso de pruebas, no un destino. Solo recibe documentos sintéticos del corpus o generados por las pruebas.

## Configuración efectiva comunicada de la cuenta

- **AWS Organizations:** política efectiva de exclusión del uso de contenido por servicios de IA verificada por el equipo el 21/10/2026; capturas pendientes. No implica que el servicio no procese o conserve temporalmente resultados.
- **Bedrock Model Invocation Logging:** desactivado según verificación del equipo del 21/10/2026. Consolidar evidencia y alcance regional; comprobar cada región de origen que se utilice. No habilitar logging de prompts/respuestas para obtener métricas.
- **Perfiles Claude:** ambos activos con los tres destinos estadounidenses indicados. No usar el prefijo `us.` como evidencia autónoma de los destinos. Consolidar la evidencia formal de consulta de perfiles y su fecha; no inventar respuestas de API ni ARN.
- **Titan 256:** fue solo una prueba mínima de acceso. RC-P07 conserva **1024 dimensiones** para ambos embeddings en la comparación, con sus parámetros fijados; no se alteran migraciones, esquema vectorial ni protocolo a partir del smoke test.

Los tokens y dimensiones comunicados son metadatos de las pruebas mínimas, no costos medidos ni resultados del corpus. Los presupuestos están en [Política de costos AWS](Politica_Costos_AWS.md). La conservación de estas notas no marca ninguna verificación contractual como `Cumple`.
