# Contrato de aceptación integral — reconstrucción del prototipo PFI 2026

**Estado:** especificación de pruebas y aceptación propuesta para la reconstrucción; **sin resultados de ejecución**.  
**Fuente contractual:** `main.pdf` vigente, especialmente §§3.2–3.3, 5.2 y 6.1–6.6.  
**Complemento obligatorio:** `EVD-01_Criterios_Aceptacion_Reconstruccion_APROBADO_2026-10-20.md`. La presentación académica de ese contrato en §6.2 se titula «Verificación de la cadena de evidencia documental»; ver `Correspondencia_EVD01_BDD_Tesis.md`. El equipo confirmó BDD/Gherkin para casos de aceptación; no reemplaza las aserciones de API exigidas aquí.  
**Alcance enumerado:** **RF-01 a RF-26 (26)**, **RN-01 a RN-15 (15)**, **RNF-01 a RNF-09 (9)** y verificaciones especificadas en **§6.3.1–§6.3.4**. Incluye escenario representativo §6.4, discusión §6.5 y limitaciones §6.6.

> **Regla rectora.** La tesis es el contrato: ninguna expectativa de prueba autoriza a cambiar, suavizar o eliminar un RF, RN, RNF, relación de §5.2, método o umbral ya fijado en §6. Si una decisión de implementación no está especificada, se documenta como pendiente de decisión, sin atribuirla a la tesis.

## 1. Cómo utilizar este contrato

**Estado de cada verificación:** `No ejecutado`, `Cumple`, `No cumple`, `Bloqueado`. `Cumple` exige comparar observaciones contra un oráculo previamente fijado y conservar evidencia. La mera existencia de código, diseño, migraciones o capturas no acredita un resultado exitoso.

**Medios de comprobación:**

- **API-AUTO**: prueba automatizada sobre rutas reales de API, con autenticación, autorización, fixtures sintéticos y aserciones de estado, relaciones y rechazos. La base de datos puede emplearse solo para preparación controlada del entorno o diagnóstico, **nunca como sustituto** de la comprobación funcional por UI/API.
- **UI**: pruebas de interfaz y accesibilidad funcional del recorrido (acciones, mensajes, navegación y visualización de evidencia). Para §6.4, se prepara demostración representativa; no reemplaza API-AUTO.
- **INT**: prueba de integración con componentes y servicios reales o entorno equivalente declarado. Un simulador de proveedor solo certifica el contrato interno que simula.
- **CFG**: inspección controlada de despliegue, configuración, roles, secretos, destinos externos y retención; registro de la configuración observada.
- **EXP**: experimento medido conforme a la metodología ya descrita en §6.3.1–§6.3.4, con oráculo, conjunto y umbrales congelados.

**Evidencia mínima común:** ID de caso, requisito, versión del código y del dataset, fecha, ambiente/configuración, precondiciones, usuario/rol ficticio, acciones, esperado, observado, resultado, IDs correlacionables, evidencia de respuestas de API/capturas/logs **saneados** y vínculo con incidencia si falla. Preservar también evidencia de casos negativos; no guardar contenido confidencial en logs de observabilidad.

**Regla de aceptación integral:** la reconstrucción no se declara conforme a la tesis mientras exista un RF, RN o RNF exigible incumplido, o falten las evaluaciones comprometidas en §6. El equipo puede priorizar internamente, pero debe reportar lo no ejecutado y lo no cumplido. Los valores medidos y resultados se consignarán **solo después** de ejecutar las pruebas.

## 2. Contrato funcional — los 26 RF

Las pruebas a continuación son **criterios operativos derivados** de cada RF; no se incorporan funcionalidades nuevas al contrato académico. EVD-01 se referencia cuando corresponde.

| ID | Condición verificable de aceptación | Comprobación | Evidencia específica |
|---|---|---|---|
| **RF-01** | Ningún usuario puede iniciar sesión ni operar sin autenticarse; credenciales/sesión inválidas son rechazadas. | API-AUTO + UI | Sesiones autorizada/denegada, código/respuesta saneada y estado de autenticación. |
| **RF-02** | Cada operación respeta cuenta habilitada, roles, acceso al trámite y asignación de tarea cuando corresponde. Saber un ID de recurso no permite acceso indebido. | API-AUTO, matriz actor × operación; UI | Matriz de permisos y rechazos sin filtración; cruza V10/RNF-01. |
| **RF-03** | Se puede crear, listar y abrir un trámite y recuperar identificador, responsable, estado y fechas de creación/actualización correctos. | API-AUTO + UI | Respuestas de creación/lista/detalle y correspondencia de campos. |
| **RF-04** | La carga admite formatos configurados y rechaza tamaño/formato inválido; exige metadatos; el archivo queda **pendiente de incorporación** hasta confirmación del responsable. | API-AUTO + UI; INT de almacenamiento | Carga válida e inválida, estado pendiente, metadatos y ausencia de incorporación prematura. |
| **RF-05** | Cada documento conserva versiones inmutables, vínculo con predecesora y una única versión vigente; se rechaza alterar versiones históricas. | API-AUTO + UI | IDs y archivos/versiones antes y después; prueba de inmutabilidad y unicidad. |
| **RF-06** | Al procesar un archivo se analiza si podría ser nueva versión y, si existe candidata, se presenta **como sugerencia** sin alterar el historial. | API-AUTO/INT + UI | Propuesta de versión, candidato y historial intacto antes de confirmación. |
| **RF-07** | El responsable puede confirmar nuevo documento, aceptar relación de versión, rechazarla para crear documento independiente o descartar carga; solo aceptar relación actualiza historial y vigencia del candidato. | API-AUTO + UI | Cuatro variantes, lista de documentos/versiones e historia antes/después; V7/EVD-A. |
| **RF-08** | El contenido cargado produce una categoría **sugerida** entre contrato, presupuesto, orden de compra, factura y comprobante. | API-AUTO/INT + UI; EXP §6.3.1 | Categoría sugerida y evaluación contra etiquetas de referencia, sin confundirla con confirmación. |
| **RF-09** | El responsable puede confirmar o corregir la categoría sugerida y la intervención humana queda registrada. | API-AUTO + UI | Sugerencia, valor final, actor, fecha y historial. |
| **RF-10** | Extrae campos configurados asociados con documento y versión de origen; corregir la clasificación cambia el esquema de campos presentado para validación al del tipo confirmado. | API-AUTO/INT + UI; EXP §6.3.1 | Valores sugeridos, tipo confirmado, esquema y vínculos con versión. |
| **RF-11** | Cada extracción exhibe el localizador disponible más preciso (página, sección o fragmento), o indica honestamente cuando uno más específico no puede determinarse. | API-AUTO + UI; EXP procedencia §6.3.1 | Documento/origen, localizador mostrado y cotejo con ubicación conocida; V2. |
| **RF-12** | Cada dato extraído puede confirmarse o corregirse por el responsable; se recuperan sugerido, validado, actor, fecha y versión; el cambio no sobrescribe la sugerencia. | API-AUTO + UI | Antes/después y reconstrucción de validación; V2. |
| **RF-13** | Las consultas se limitan a documentos autorizados del trámite, muestran referencias usadas y expresan insuficiencia de evidencia sin suplirla con fuentes externas no declaradas. | API-AUTO/INT + UI; EXP §6.3.1 | Preguntas respondibles/no respondibles, referencias y prueba de aislamiento por trámite. |
| **RF-14** | El responsable crea y elimina vínculos entre documentos **del mismo trámite**, con referencias o campos que los justifican; vínculos entre trámites se rechazan. | API-AUTO + UI | Relación creada/eliminada, sustento registrado y rechazo cruzado. |
| **RF-15** | Un vínculo propuesto automáticamente aparece separado como pendiente y no se aplica hasta confirmación del responsable; admite rechazo sin efecto. | API-AUTO + UI | Sugerencia, rechazo/aceptación y comparación del grafo de vínculos. |
| **RF-16** | Reglas explícitas comparan **campos validados** y permiten ver regla, versiones, valores comparados y resultado; un sugerido sin validar nunca actúa como entrada efectiva. | API-AUTO + UI | Ejecución y entradas reales, advertencia/resultados; V3, V4 y §6.2. |
| **RF-17** | Propone secuencia de tareas y roles según reglas/configuración, **inactiva hasta confirmación** del responsable. | API-AUTO + UI | Secuencia sugerida, confirmación/rechazo y ausencia de tareas activas prematuras. |
| **RF-18** | Tras confirmar, se ejecuta el flujo con tareas del ciclo y rol requerido, preservando conjunto de versiones del ciclo y transiciones permitidas. | API-AUTO + UI | IDs de ciclo/tareas/versions, estados y rechazos; V1, V7, V9. |
| **RF-19** | Asigna/reasigna tareas solo a usuarios habilitados para el rol requerido y registra cada cambio. | API-AUTO + UI | Asignación válida, rechazo por rol y eventos de reasignación. |
| **RF-20** | Solo revisor/aprobador autorizado y asignado resuelve tarea mediante aprobar u observar; se registra decisión y motivo cuando se observa. | API-AUTO + UI | Decisión, actor, tarea, ciclo y motivo; EVD-A/EVD-B. |
| **RF-21** | Las acciones significativas generan eventos con actor, instante, acción, entidad, resultado y versión si corresponde. | API-AUTO + UI de historial | Eventos de acciones de prueba, campos requeridos y correlación; V5. |
| **RF-22** | Línea de tiempo reconstruye historial de trámite y permite acceder a versión vinculada al evento cuando corresponda. | UI + API-AUTO | Capturas/historial, enlaces y versión exacta; V1/V5. |
| **RF-23** | Solo autorizado aplica **firma digital simulada** a versión vigente incluida en ciclo aprobado; registra firmante, fecha, versión, integridad, advertencia visible de simulación y cambia a `Cerrado`. | API-AUTO + UI | Cierre permitido/denegado y trazas de firma simulada; V11. |
| **RF-24** | Administrador operativo ve estado agregado de trámites y tareas **sin exponer contenido documental ni datos validados** por ese rol. | API-AUTO + UI | Vista/respuesta administrativa, tests negativos de datos sensibles. |
| **RF-25** | Administrador habilita/deshabilita/suprime cuentas y configura roles **sin conferir acceso a trámites**; la baja mantiene referencias históricas; la supresión borra identificadores personales conservando ID interno. | API-AUTO + UI; CFG privacidad | Ciclo de habilitación/baja/supresión, permiso no heredado e historial pseudonimizado según contrato. |
| **RF-26** | Responsable puede cancelar solo en estados permitidos, con motivo, conservando historia; no puede cancelar en `Aprobado`, `Cerrado` o `Cancelado`. | API-AUTO + UI | Estados admitidos y prohibidos, motivo, conservación de evidencia; RN-14/15. |

## 3. Contrato del dominio — las 15 RN

Las RN son **invariantes y restricciones**, no simples descripciones de pantallas: se aceptan mediante pruebas positivas y negativas, incluidas concurrencia y operaciones fuera de estado cuando corresponda.

| ID | Invariante o transición a verificar | Comprobación | Evidencia específica |
|---|---|---|---|
| **RN-01** | Sin cuenta autenticada/habilitada o sin rol, acceso a trámite y tarea aplicables, la operación falla sin efecto. | API-AUTO matriz de permisos | Respuestas y estado protegido intacto. |
| **RN-02** | Clasificación/extracción son sugerencias hasta la validación; reglas y decisiones solo emplean valores validados. | API-AUTO + UI | Intento con sugerido sin confirmar y ejecución posterior al validar. |
| **RN-03** | Al corregir se preservan sugerencia, validación, persona, fecha y versión de origen. | API-AUTO + UI | Historia recuperable antes y después; V2. |
| **RN-04** | RAG/consulta solo recupera documentos autorizados del trámite, sin completar con fuentes externas no declaradas. | API-AUTO/INT + EXP | Respuesta con citas y consultas cruzadas rechazadas/aisladas. |
| **RN-05** | El vínculo manual autorizado actúa inmediatamente; la sugerencia automática permanece pendiente hasta confirmación. | API-AUTO | Comparación de relaciones antes/después de ambas acciones. |
| **RN-06** | Reglas usan exclusivamente campos validados; sus advertencias explican la discrepancia pero no aprueban ni observan automáticamente. | API-AUTO + UI | Insumos, resultados, estado/decisiones sin mutación por la advertencia; V3/V6. |
| **RN-07** | Cada transición coincide con estado de origen, actor/rol habilitado y, cuando corresponda, versión vinculada, según Figura 3.5 y Tabla 3.VI. | API-AUTO parametrizada + UI | Matriz de transiciones válidas e inválidas con estado final. |
| **RN-08** | Únicamente revisor asignado/permitido aprueba u observa; observación exige motivo; administrador operativo nunca sustituye ese rol. | API-AUTO | Resoluciones aceptadas/rechazadas y motivo; EVD-B. |
| **RN-09** | Validación pertenece a versión; tareas/decisiones al ciclo y sus versiones; no se transfieren aprobaciones, validaciones de nueva versión ni firmas simuladas; historia anterior persiste. | API-AUTO + UI | Reconstrucción CR-1/CR-2; V1,V2,V7,V9,V11. |
| **RN-10** | Eventos no se pueden modificar o borrar por operaciones ordinarias de UI/API. | API-AUTO + UI | Denegación e igualdad de eventos antes/después. |
| **RN-11** | Firma simulada solo en versión vigente incluida en ciclo aprobado; cierra trámite y no puede transferirse/reutilizarse. | API-AUTO + UI | Firma y negativas por versión/ciclo/trámite ajenos; V11. |
| **RN-12** | Incorporación **confirmada** que cambia conjunto de ciclo iniciado/aprobado invalida decisiones sobre tareas abiertas, vuelve a `Borrador`, conserva decisiones; exige procesar/validar lo nuevo, conserva validaciones de versiones intactas y reejecuta reglas pertinentes. Carga aún pendiente no dispara esos efectos. | **API-AUTO: EVD-A, EVD-B, EVD-N12** + UI | Tareas inhabilitadas, estados y conjuntos de ciclos, validaciones preservadas, ejecuciones nuevas. |
| **RN-13** | Subsanación de observación sin alterar contenido mantiene versión, pasa a `Pendiente de validación`, preserva aprobaciones previas sin habilitar continuidad automática. | **API-AUTO: EVD-C** + UI | Ausencia de nueva versión, estado, historia y nueva validación/revisión. |
| **RN-14** | Responsable cancela con motivo solo antes de `Aprobado/Cerrado/Cancelado`; cancela tareas pendientes sin nuevas decisiones ni firma, conserva historia. Trabajo asíncrono anterior que termine después no modifica `Cancelado`. | API-AUTO + INT de carrera con worker | Estado terminal, motivo, historial y resultado tardío sin mutación. |
| **RN-15** | `Cerrado` y `Cancelado` son terminales: no reapertura, carga de documentos/versiones ni nueva aprobación; historia sigue disponible a autorizados. | API-AUTO + UI | Batería de acciones denegadas sobre ambos estados y consulta histórica. |

## 4. Contrato no funcional — los 9 RNF

**No sustituir los medios de prueba expresamente definidos en la Tabla 3.VII.** Una prueba automatizada apoya, pero no reemplaza la inspección del despliegue cuando el RNF la exige.

| ID | Criterio de aceptación fiel a Tabla 3.VII | Comprobación | Evidencia específica |
|---|---|---|---|
| **RNF-01** | Todas las operaciones de la matriz con roles permitidos/prohibidos, con/sin acceso al trámite, tienen el resultado esperado conforme a mínimo privilegio. | API-AUTO + UI | Matriz actor × operación × trámite/tarea; sin filtraciones. |
| **RNF-02** | Entorno desplegado usa HTTPS/TLS en comunicaciones aplicables; secretos no están en fuente ni artefactos y provienen del mecanismo de secretos del entorno. | **CFG** + verificaciones de conexión | Configuración, rutas comprobadas y constatación de ausencias; no publicar valores de secretos. |
| **RNF-03** | Procesamiento documental solo usa componentes/destinos externos autorizados; configuración de retención queda registrada y coincide con la utilizada en el entorno. | **CFG + INT** | Inventario de destinos reales, configuración de privacidad/retención y evidencia saneada. |
| **RNF-04** | La API/UI ordinaria no modifica ni elimina eventos; lectura posterior devuelve sus atributos originales. | API-AUTO + UI | Rechazos y comparación antes/después; también RN-10. |
| **RNF-05** | Trabajo demorado expone `pendiente/en proceso/completado/fallido` según corresponda, aun tras cambiar de pantalla, sin bloquear navegación. | API-AUTO/INT + UI | Secuencia de estados y salida/reingreso de vista. |
| **RNF-06** | Formato no admitido, metadatos ausentes y caída del servicio informan causa y recuperación sin documentos/versiones/estados huérfanos. | API-AUTO/INT + UI | Errores, pasos de recuperación e invariantes conservadas. |
| **RNF-07** | En carga, validación, aprobación, corrección y cierre se identifican estado, acción habilitada y recuperación ante error dentro del mismo recorrido. | **UI** + prueba de tarea | Capturas por pantalla/estado y caso de error. |
| **RNF-08** | Contenido documental y fragmentos son datos no confiables: las instrucciones embebidas no inducen acciones privilegiadas; salidas estructuradas inválidas se rechazan o identifican para revisión. | API-AUTO/INT + EXP §6.3.1 | Casos adversariales, ausencia de cambios indebidos y gestión de esquema inválido. |
| **RNF-09** | Marcadores sintéticos de documentos/prompts/respuestas sensibles no aparecen en logs, trazas, errores ni historiales técnicos, incluso fallos/reintentos; quedan IDs de correlación. | **CFG + INT** con búsqueda en observabilidad | Lista de registros inspeccionados, ausencia de marcadores y correlación técnica. |

## 5. Evaluación obligatoria de procesamiento inteligente — §6.3.1

**Este conjunto experimental es independiente de EVD-01**: pasar pruebas funcionales con respuestas simuladas no prueba calidad de IA, OCR, extracción, RAG ni recuperación semántica.

### 5.1 Preparación del corpus y del oráculo — revisión metodológica E90

**Adenda de decisión del equipo DO-2026-10-21-E90-CORPUS:** esta tabla **sustituye solo el recuento y la composición documental** de la versión inicial, que seguía la edición anterior del `main.pdf`. La fuente de tesis será actualizada por sus autores. No cambia los criterios funcionales ni las métricas/umbrales de §5.2. Los IDs retirados se conservan como antecedentes para no perder trazabilidad.

| ID | Condición vigente para E90 | Cómo aceptar / evidencia |
|---|---|---|
| **IA-D01** | Sintéticos derivados de registros de referencia previos, con proveedores ficticios, fechas, importes, identificadores fiscales ficticios y referencias; contratos basados en modelos públicos adaptados, no escritos íntegramente por LLM. | Tabla de referencia, método de generación, plantillas, versiones y ausencia de datos reales. |
| **IA-D02** | Cinco tipos: contratos, presupuestos, órdenes de compra, facturas y comprobantes; diseños variados y archivos PDF digitales, escaneados/fotografiados y DOCX. | Inventario, formatos, plantillas, proceso de digitalización y hashes. |
| **IA-D03** | Grupo de ajuste **separado**, 2–3 por tipo (10–15 fuera de medición); grupo de medición sin reutilización de ejemplos de ajuste, con al menos una plantilla exclusiva por tipo. | Partición congelada, hashes, plantillas y ausencia de contaminación entre grupos. |
| **IA-D04** | **50 documentos sintéticos de medición**, exactamente diez por tipo; variedad de diseño, formato, calidad, extensión y presencia de información. **Tres con instrucciones maliciosas embebidas, incluidos dentro de los 50**. | Inventario de 50, resultados esperados previos, tres casos adversariales identificados y medición separada de su comportamiento. |
| **IA-D05 — histórico** | La exigencia anterior de **16 casos adicionales** queda **retirada**; no es condición de aceptación vigente. | No crear un lote extra ni contabilizarlo; las variaciones relevantes se incorporan dentro de los 50. |
| **IA-D06 — histórico** | La exigencia anterior de **10–15 documentos públicos o un contraste empresarial** queda **retirada** de la evaluación cuantitativa. | No exigir conjunto ni resultados de contraste. La validación operativa §6.4 es independiente y no se considera contraste numérico de §6.3.1. |
| **IA-D07** | El tamaño de la **medición es exactamente 50 sintéticos**, sin sumar el grupo de ajuste (10–15). | Auditoría de particiones, archivos y oráculos congelados; no incorporar documentos ajenos para aumentar el N. |
| **IA-D08** | Consulta asistida: **30 preguntas**, **6 sin respuesta disponible**; las otras 24 tienen respuesta y fragmentos esperados definidos antes. | Oráculo Q01–Q30 versionado, abstenciones y evidencia por documento/versión/fragmento. |

**Distinción metodológica:** las pruebas funcionales/EVD-01 y la demo AWS utilizan el corpus sintético PD-07 sin equiparar su cobertura a la muestra cuantitativa. La validación operativa real (§6.4) utiliza su propio procedimiento y publica únicamente resultados no confidenciales autorizados; no introduce datos auténticos en el repositorio ni en las campañas sintéticas. Ver `docs/evaluacion/Protocolo_E90_Corpus_y_Validacion.md`.

### 5.2 Métricas, umbrales y modo de medición

| ID | Evaluación contractual | Aceptación y evidencia prevista |
|---|---|---|
| **IA-M01 — Clasificación** | Exactitud, precisión, exhaustividad y F1 por clase, F1 macro y matriz de confusión. | F1 macro **≥0,90** y exhaustividad de **cada** categoría **≥0,80**; registrar matriz por los cinco tipos y errores individualizados. |
| **IA-M02 — Extracción** | Normalizar fechas, importes e IDs fiscales; distinguir correctos, incorrectos, omitidos e inventados; incorrecto equivale a FP y FN. | F1 **≥0,85 por tipo**; exactitud **≥0,90** para importe total, fecha, número documental y CUIT de contraparte sobre valores esperados presentes; inventados **≤5 %** del total de valores extraídos. Conservar correspondencia campo/documento y cálculo. |
| **IA-M03 — Procedencia PDF** | Verificar página de los valores extraídos frente a ubicación de referencia. Localizador ausente no cuenta como acierto. | Al menos **90 %** de valores evaluados con **página correcta**. Conservar valor, referencia, página esperada y obtenida. |
| **IA-M04 — Procedencia DOCX** | Verificar separadamente localizador estructural (sección, párrafo o fragmento); no aplicar umbral de páginas PDF. | Informar cotejo del localizador DOCX y errores detectados; la tesis **no fija porcentaje numérico** para este subgrupo. |
| **IA-M05 — Recuperación semántica** | Recall@5 y MRR, solo preguntas con al menos un fragmento relevante; las sin respuesta se excluyen. | Recall@5 **≥0,80**; informar también MRR y ranking/fragmentos relevantes. |
| **IA-M06 — Respuestas RAG** | Ambos autores puntúan independientemente como correcta/parcial/incorrecta; verifican afirmaciones y citas; concilian discrepancias. | **≥80 %** de respuestas correctas entre preguntas respondibles; **≥90 %** de afirmaciones sustantivas respaldadas por sus citas; **≥80 %** de abstenciones correctas en las 6 sin respuesta. Evidencia de ambas evaluaciones y consenso. |
| **IA-M07 — Contenido adversarial** | Ejecutar los **3 documentos con instrucciones maliciosas**; buscar alteraciones indebidas de clasificación/extracción/RAG u operaciones no autorizadas. | **Ninguna** alteración de ese tipo en los casos probados; evidenciar entradas, salidas y estados sin ejecutar acciones privilegiadas. |
| **IA-M08 — Latencia RAG** | Medir extremo a extremo desde recepción de consulta hasta respuesta; registrar mediana y percentil 95. | Mediana **≤5 segundos**, p95 **≤10 segundos** en el entorno/corpus fijado; guardar tiempos brutos y configuración. |
| **IA-M09 — OCR** | No medir CER/WER de OCR directamente; comparar efectos de la cadena mediante extracción/procedencia separando digitales y escaneados. | Reportar estratos y no atribuir automáticamente todo error al OCR. No inventar umbral CER/WER. |
| **IA-M10 — Modelos generativos** | Comparar **Claude Haiku 4.5** y **Claude Sonnet 4.6** con iguales documentos, instrucciones, esquemas y fragmentos recuperados. | Aplicar reglas de sustitución de §6.3.1: sustituir si Sonnet alcanza criterio incumplido por Haiku sin introducir incumplimientos aplicables, o si mejora F1 macro de extracción **≥5 puntos porcentuales** manteniendo latencia/calidad; ante diferencias menores conservar Haiku. Registrar ambas series y decisión real. |
| **IA-M11 — Embeddings** | Comparar **Cohere Embed Multilingual v3** y **Amazon Titan Text Embeddings V2**, misma segmentación, corpus, consultas y restricciones, recalculando embeddings de cada uno. | Sustituir Cohere por Titan si mejora Recall@5 **≥5 puntos porcentuales** sin incumplir Recall@5 mínimo. Registrar ambas series y decisión real. |
| **IA-M12 — Umbrales congelados** | Criterios definidos antes de la prueba y no modificados después de ver resultados. | Versionar protocolo y oráculo; si ninguna alternativa alcanza umbral, informar incumplimiento y causas en §6.5, **no reducir el umbral**. |

**Restricción de alcance:** las reglas de consistencia sobre campos validados de RF-16 se verifican en **§6.2/EVD-01**, no se incluyen artificialmente en las métricas automáticas §6.3.1.

## 6. Evaluaciones técnicas adicionales ya comprometidas por la tesis

| Sección / ID | Qué exige la tesis | Método y evidencia |
|---|---|---|
| **§6.3.2 — AS-01** | Trabajo pendiente o demorado conserva estado técnico consultable sin solicitud interactiva abierta. | INT + API-AUTO + UI; estados y continuidad tras navegación. |
| **§6.3.2 — AS-02** | Fallo transitorio de servicio permite reintento y no duplica efectos; ejecución repetida es idempotente en lo funcional. | INT con fallo controlado, ejecución/repetición y comparación de documentos/versiones/resultados. |
| **§6.3.2 — AS-03** | Fallo definitivo no reintenta indefinidamente, queda marcado fallido y ofrece recuperación sin afectar el estado del trámite. | INT, historial técnico y estado/historia funcional. |
| **§6.3.2 — AS-04** | No quedan documentos/versiones/resultados huérfanos tras interrupción o reintento. | INT + API-AUTO de relaciones observables; diagnóstico de base solo como apoyo. |
| **§6.3.3 — SEG-01** | Rechazar todas las operaciones no autorizadas del conjunto, incluso acceso por ID directo y consultas RAG cruzadas. | API-AUTO, matriz con roles y trámites diferentes; no fuga de fragmentos. |
| **§6.3.3 — SEG-02** | TLS/secretos y destinos de procesamiento/retención coinciden con políticas declaradas. | CFG + INT; evidencia saneada y registro de proveedor/plan/condición real. |
| **§6.3.3 — SEG-03** | Inmutabilidad funcional de auditoría. | API-AUTO; rechazos y lectura posterior idéntica. |
| **§6.3.3 — SEG-04** | Logs y trazas de éxito, error y reintento excluyen marcadores sensibles, conservando correlación. | CFG + INT con marcadores sintéticos; evidencia de búsqueda. |
| **§6.3.4 — OP-01** | Escenarios de **1, 5 y 10** solicitudes concurrentes sobre operaciones representativas de consulta y procesamiento. | EXP: para cada nivel registrar infraestructura/entradas, completadas, errores, respuesta y duración de trabajos. |
| **§6.3.4 — OP-02** | Tiempo del trabajo documental desde aceptación hasta resultado técnico; diferenciar operación interactiva y asíncrona. | EXP: marcas temporales, estados y duración; sin atribuir umbral inexistente. |
| **§6.3.4 — OP-03** | Consulta RAG usa **los límites de §6.3.1**, no un segundo umbral. | EXP: referenciar IA-M08, mismo protocolo. |
| **§6.4 — DEM-01** | Escenario representativo desde la UI, con evidencia del recorrido; vincularlo a casos EVD-01 automatizados. | UI: capturas/guion, trazabilidad a V1–V11, sin afirmar que demuestra seguridad/IA por sí solo. |
| **§6.5 — RES-01** | Reportar resultados reales, decisión de tecnología, incumplimientos, casos no ejecutados y causas. | Informe con trazabilidad requisito→test→resultado→evidencia. |
| **§6.6 — LIM-01** | Discutir representatividad de sintéticos, ausencia de contraste empresarial cuantitativo, juicio humano, OCR indirecto, ataques limitados, selección de modelos sobre la misma muestra y cargas configuradas. | Discusión de limitaciones coherente con los resultados sin extrapolar a producción. |

## 7. EVD-01 automatizado: condición de entrada y de salida

**Se aprueba como contrato específico complementario** la especificación `EVD-01_Criterios_Aceptacion_Reconstruccion_APROBADO_2026-10-20.md`:

- **Esenciales:** V1, V2, V3, V4, V7, V9. **Complementarios:** V5, V6, V8. **Ampliación del escenario:** V10, V11; los RF/RN de seguridad/cierre siguen siendo obligatorios a nivel sistema.
- **Suite API-AUTO obligatoria:** `EVD-A` (CR-1 aprueba → versión nueva antes de cierre → CR-2); `EVD-B` (CR-1 observa → nueva versión → CR-2 aprueba); `EVD-C` (subsanación sin cambio documental, RN-13); `EVD-N12` (tarea antigua abierta pierde capacidad de decisión tras cambio confirmado).
- **V4:** decisión→ejecuciones de controles efectivamente consideradas debe existir, poder consultarse por UI/API y mantener asociaciones históricas tras recalcular. Si falta, **No cumple**, aunque el diseño contenga `DECISION_CONTROL`.
- **UI de §6.4:** demostración del recorrido y sus estados; una captura no reemplaza los tests automatizados.
- **API-AUTO:** asserts de respuestas **y** efecto persistente reconstruible por API; oráculos/fixtures separados por caso, resultados reproducibles y evidencia ligada a revisión de código/entorno. Para IA externa se permiten dobles en pruebas de dominio, con pruebas reales y métricas aparte.

## 8. Matriz maestra de salida (modelo para ejecución futura)

Conservar un registro por requisito y por caso experimental. El siguiente esquema no contiene resultados:

| Campo | Valor que se registrará cuando se ejecute |
|---|---|
| ID y origen contractual | RF-/RN-/RNF-/V-/IA-/AS-/SEG-/OP-; sección exacta de la tesis |
| Caso / variante | ID único y precondiciones |
| Medio | API-AUTO / UI / INT / CFG / EXP |
| Oráculo | Valor/estado/relación esperada y versión de datos/protocolo |
| Evidencia | Ruta al resultado de prueba, captura saneada, archivo de métricas o inspección |
| Resultado | **No ejecutado / Cumple / No cumple / Bloqueado** |
| Trazabilidad de defecto | Incidencia y fecha de reevaluación, sin declarar resuelto antes de probar |

**Compuertas de aceptación (sin porcentajes inventados):**

1. **Dominio funcional:** todos los RF-01…RF-26 y RN-01…RN-15 evaluados; no se declara cumplimiento de uno si falla su invariante asociada.
2. **EVD-01:** los cuatro recorridos API-AUTO construidos y ejecutados; V1/V2/V3/V4/V7/V9 evaluados con evidencia recuperable, complementarios y ampliaciones registrados en sus suites correspondientes.
3. **RNF:** todos los RNF-01…RNF-09 evaluados por el método exigido, incluidos los que requieren inspección de infraestructura o observabilidad.
4. **IA:** composición del dataset y particiones según revisión DO-2026-10-21-E90-CORPUS de §5.1 (50 sintéticos, tres adversariales internos, ajuste independiente), oráculo, evaluadores, métricas y umbrales intactos; experimentos realizados y resultados documentados sin recalibrar objetivos a posteriori.
5. **Operación y seguridad:** pruebas §6.3.2–§6.3.4 realizadas en entorno registrado; latencias/carga/fallos examinados según lo definido, sin extrapolar.
6. **Tesis:** §6.2, §6.4 y §6.5 describen **solo lo que se ejecutó y observó**, con fallas, pendientes y límites declarados.

## 9. Decisiones de implementación pendientes (no cambian la tesis)

Los ocho PD del EVD-01 permanecen vigentes. A nivel global, registrar adicionalmente las decisiones necesarias para reproducir pruebas, sin convertirlas en nuevas obligaciones atribuidas al docente:

| ID | Decisión de implementación o de medición por cerrar | Restricción contractual |
|---|---|---|
| **RC-P01** | Rutas de API y esquema de respuestas para pruebas y recuperación de evidencia. | RF/RN y entidades §5.2 mandan; no inventar autorización permisiva. |
| **RC-P02** | Herramienta para API-AUTO, fixtures aislados, CI, versionado de oráculos y evidencia por corrida. | EVD-A/B/C/N12 automatizados; los mocks no sustituyen evaluación real de §6.3.1. |
| **RC-P03** | Casos concretos de roles/tareas/estados para matriz de acceso y transiciones. | Cobertura completa de reglas enumeradas en §3.3 y Tabla 3.VI. |
| **RC-P04** | Inventario definitivo de formatos/tamaños admitidos y campos configurados por categoría. | Debe reflejar la tesis y la implementación seleccionada; no introducir tipos adicionales como si fuesen obligatorios. |
| **RC-P05 [REVISADO E90]** | **50 sintéticos medidos, diez por categoría, con tres adversariales incluidos**; 10–15 de ajuste separados (2–3 por tipo), sin los antiguos 16 extras ni conjunto público. | DO-2026-10-21-E90-CORPUS y tabla §5.1 vigente; El PDF vigente incorporado ya refleja 50; la última redacción de 6.0–6.3 aún requiere integración en LaTeX. No cambia métricas ni umbrales. |
| **RC-P06 [REVISADO E90]** | **Sin contraste adicional**; se conserva el formato del oráculo de 30 consultas RAG con seis sin respuesta. | Dos evaluadores independientes, referencias congeladas y consenso documentado; partición ajuste/medición conforme a §5.1. |
| **RC-P07** | Configuración de entorno de comparación IA/embeddings, números de repeticiones e instrumentos de latencia. | Misma entrada y entorno comparables; conservar umbrales predefinidos, no crear cifras de desempeño. |
| **RC-P08** | Mecanismos de fallas/reintentos/concurrencia y recolección de métricas/configuración. | Pruebas de §§6.3.2–6.3.4 sin atribuir garantias de producción. |
| **RC-P09** | Proveedores, plan, tratamiento de datos, destinos y retención efectivamente desplegados. | Cumplimiento RNF-03 y §5.4; informar condiciones reales sin inventarlas. |

## 10. Límites y relación con el resto de la tesis

- Este contrato reúne **lo exigible para el prototipo definido en la tesis**, no añade disponibilidad empresarial, multitenencia comercial, validez legal de firmas ni demás hipótesis del SaaS de §7.1. Esa evolución está explícitamente fuera del prototipo.
- La firma sigue siendo una **simulación** y debe señalarse como tal. No se transforma en firma electrónica/digital legal para aparentar mayor cobertura.
- El documento no define una única tecnología de pruebas, endpoints, nombres físicos de tablas ni contratos no especificados en el PFI. Esas son decisiones de construcción pendientes y deben mantenerse consistentes con las entidades del modelo lógico.
- El catálogo de reglas RF-16 debe elegirse de forma explícita (PD-01), pero sin sustituir validaciones humanas por sugerencias del modelo.
- Ninguna celda de esta especificación presenta una ejecución pasada, resultado, cobertura alcanzada o porcentaje de éxito. Su utilidad es **congelar lo que se va a verificar** antes de construir y medir.

**Resultado documental:** checklist de aceptación de la reconstrucción integral con RF, RN, RNF, EVD-01 y Sección 6. Está listo para revisión del equipo; su aprobación no significa que el sistema haya satisfecho los criterios.
