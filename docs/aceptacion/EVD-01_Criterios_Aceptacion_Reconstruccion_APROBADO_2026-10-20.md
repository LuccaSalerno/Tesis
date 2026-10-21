# EVD-01 — Criterios de aceptación para la reconstrucción del prototipo

**Proyecto:** PFI Ingeniería en Informática, UADE 2026  
**Estado:** especificación de aceptación propuesta; sin ejecución ni resultados  
**Contrato:** `main.pdf`, §§3.2.1–3.2.2, 3.3.1, 3.3.3–3.3.4, 5.2 (Figura 5.4) y 6; observaciones E50 30 y 35; Reglamento Maestro §§9.12–9.13 y 22.  
**No modifica** ningún RF, RN ni las relaciones del modelo lógico. Las referencias y evidencias de prueba se especifican como objetivos de reconstrucción, no como capacidades ya desarrolladas.

## 1. Alcance, niveles y reglas de aceptación

**Esenciales:** V1, V2, V3, V4, V7 y V9. Forman el núcleo de la demostración de reconstrucción de evidencia.  
**Complementarios:** V5, V6 y V8. Refuerzan y comprueban propiedades que también son obligaciones del sistema.  
**Ampliación EVD-01:** V10 y V11. No son requisitos opcionales del PFI: «ampliación» indica solamente que pueden probarse fuera del escenario mínimo de reconstrucción.

**Reglas no negociables:**

1. La tesis es el contrato: ningún RF, RN ni relación del modelo se altera para facilitar las pruebas o el desarrollo.
2. Validación humana → una **versión documental concreta**; tarea y decisión → **ciclo de revisión** y conjunto de versiones de ese ciclo; regla → **ejecución e inputs validados**; firma simulada → **una versión concreta**.
3. Toda verificación funcional debe tener una vía **UI o API autorizada** disponible al actor correspondiente. Consultar directamente la base puede servir como diagnóstico, pero no es prueba funcional por sí sola.
4. Los identificadores, resultados esperados, reglas seleccionadas, versiones y permisos se fijan en un **oráculo previo** a la ejecución. No adaptar el resultado esperado a lo que devuelva el software.
5. **V4 solo cumple** si, desde una decisión, se recuperan las ejecuciones de reglas efectivamente consideradas para tomarla. No cumple si `DECISION_CONTROL` existe solo en el diagrama o en una tabla vacía; tampoco si se devuelve la última ejecución del trámite sin relación estable con la decisión. Declarar la ausencia es honesto, pero **no constituye cumplimiento**.
6. Cualquier resultado no observado se rotula «pendiente de ejecución», nunca «aprobado». Registrar también resultados fallidos; no inventar resultados, porcentajes ni métricas calculadas.

### Requisito adicional de la reconstrucción: automatización de EVD-01 (aprobado)

Los cuatro recorridos **EVD-A, EVD-B, EVD-C y EVD-N12 deben implementarse como pruebas automatizadas contra la API de la aplicación**, no solo como guiones de ejecución manual. Es una exigencia de aceptación de la **reconstrucción**, añadida por el equipo; no se la atribuye retroactivamente a un RF o RN.

**Condiciones de aceptación de la suite automatizada:**

1. Cada recorrido es ejecutable de forma repetible en un entorno controlado, con datos sintéticos, precondiciones y resultado esperado determinados **antes** de ejecutar la prueba; los casos se aíslan o restablecen explícitamente.
2. Las operaciones se realizan mediante rutas funcionales de API **autenticadas y autorizadas**; se cubren tanto respuestas esperadas como acciones denegadas. No se aceptan consultas SQL directas como oráculo funcional ni cambios manuales en la base para fabricar el estado que se pretende validar.
3. La suite verifica cambios de estado y **persistencia observable mediante la API**: decisiones, ciclos, versiones consideradas, validaciones, ejecuciones de reglas y `DECISION_CONTROL` cuando corresponda. Una respuesta HTTP favorable sin cotejar el efecto de negocio no basta.
4. Se implementan aserciones negativas: tarea de ciclo anterior no resoluble, aprobación no transferida, corrección de datos sin versión ficticia, prohibición de alteraciones retroactivas y rechazo de acciones no autorizadas según el caso.
5. Las ejecuciones deben poder repetirse tras cambios del código (por ejemplo, en el mecanismo de integración continua elegido para el repositorio). Se conserva resultado por caso/criterio, fecha, versión del código, entorno, identificadores de correlación y evidencia de API sanitizada; un fallo no se convierte automáticamente en éxito por actualizar el oráculo.
6. Cuando intervengan servicios externos de IA/OCR, se podrán usar dobles controlados para validar la lógica de dominio, **identificando ese alcance**. Esos dobles no sustituyen las mediciones con proveedores y documentos del §6.3.1 ni las pruebas de integración necesarias.

**Para la Sección 6:** documentar los casos y su ejecución automatizada en §6.2, usar la interfaz para ilustrar el recorrido representativo de §6.4, y consignar resultados reales, versión de software y fallos en §6.5. Ni el simple código de los tests ni una captura de pantalla prueban por sí solos que todos hayan pasado.

### Mapa de casos

- **EVD-A — Aprobación y nueva versión antes del cierre (RN-12):** `CR-1 → DEC-1 aprueba → confirmación F-v2 → CR-2 → DEC-2` (con nueva decisión), sin firmar ni cerrar el trámite antes de F-v2.
- **EVD-B — Observación y corrección documental (RN-08, RN-09, RN-12):** `CR-1 → DEC-1 observa con motivo → confirmación F-v2 → CR-2 → DEC-2 aprueba`.
- **EVD-C — Subsanación sin cambio de contenido (RN-13):** `CR-1 → observación → corrección de datos o metadatos sin nueva versión → Pendiente de validación → nueva revisión`. Se prueba **por separado**: no agregar F-v2 en este caso.
- **EVD-N12 — Tarea abierta del ciclo desplazado (RN-12):** caso negativo complementario para comprobar que una tarea todavía abierta de un ciclo cuyo conjunto cambió ya no admite decisión. EVD-A con todas las tareas resueltas no cubre esta condición por sí solo.

## 2. Oráculo y evidencia transversal (a preparar antes de ejecutar)

**Datos sintéticos:** trámite `T-01`, contrato `C-v1`, orden de compra `O-v1`, factura `F-v1` y nueva factura `F-v2`; no son identificadores de la base, sino etiquetas del caso. Vincular únicamente documentos del mismo trámite. La composición `{C-v1, O-v1, F-v1}` corresponde al primer ciclo y `{C-v1, O-v1, F-v2}` al segundo. Los IDs reales de trámite/documento/archivo/versión/ciclo/tarea/decisión se registran al ejecutar.

**Fijar previamente:** archivos exactos y huellas; campos y valores sugeridos/esperados; referencia de fuente conocida y localizador cuando exista; quién valida; regla real de consistencia que se implementará (código, versión, entradas y resultado esperado); decisiones y motivos previstos; rol y tarea asignados; vínculos documentales; versiones de cada ciclo; estados esperados tras cada acción. No asumir que la tesis especifica una regla concreta de comparación de montos o tolerancias: si falta, resolverlo como decisión de implementación compatible con RF-16.

**Paquete probatorio por ejecución:** identificador de caso y criterio, versión del software, entorno y fecha, versión del conjunto de datos/oráculo, rol de la sesión, precondiciones, secuencia realizada, capturas o respuesta de API autorizada (redactadas si corresponde), IDs correlacionables, esperado vs. observado, estado `Cumple / No cumple / No ejecutado / Bloqueado`, incidencia y referencia a evidencias. Conservar registros históricos antes y después del cambio de versión; no depender de información «actual» que pueda variar.

## 3. Criterios de aceptación por ID

### V1 — Decisión → tarea → ciclo → versiones consideradas

**Prioridad:** esencial.  
**Aceptación verificable:** desde `DEC-1`, el usuario autorizado puede acceder a la tarea resuelta, su `CR-1` y el conjunto exacto `{C-v1,O-v1,F-v1}`. La asociación identifica versiones **consideradas entonces**, no la lista de versiones actualmente vigentes. El mismo principio se comprueba sobre `DEC-2` y `CR-2`.  
**Fundamento:** RF-18, RF-20; RN-09.  
**Entidades (§5.2):** `DECISION → TAREA → CICLO_REVISION → CICLO_REVISION_VERSION → VERSION_DOCUMENTAL` (con `DOCUMENTO` para identificar la pieza lógica).  
**Comprobación:** abrir la decisión y su contexto desde la interfaz de revisión/historial, **o** consultar ese contexto por una API autenticada/autorizada; verificar IDs de versión frente al oráculo.  
**Evidencia a guardar:** pantalla o respuesta de API con ID de decisión/tarea/ciclo y lista de IDs de versiones; oráculo de conjuntos de versiones; resultado de comparación.

### V2 — Valor validado → versión concreta → sugerencia y procedencia

**Prioridad:** esencial.  
**Aceptación verificable:** cada dato confirmado o corregido utilizado en EVD-01 permite recuperar su valor sugerido, valor validado, persona que validó y momento de intervención, **versión documental de origen** y referencia/localizador de fuente disponible. En un caso con localizador conocido, este identifica la fuente correcta; cuando no pueda precisarse, el sistema lo informa y no inventa una página o un fragmento. La corrección no borra el sugerido.  
**Fundamento:** RF-10, RF-11, RF-12; RN-02, RN-03, RN-09.  
**Entidades (§5.2):** `VALIDACION_HUMANA`, `VERSION_DOCUMENTAL`, `VALOR_SUGERIDO`, `REFERENCIA_FUENTE`, `ARCHIVO`, `USUARIO`. La referencia se vincula al archivo de origen; no presumir una FK directa versión→fuente distinta del modelo.  
**Comprobación:** UI de revisión de extracción y detalle/historial de validación, o respuesta de API autorizada que exponga esa cadena; cotejo con el archivo sintético y oráculo.  
**Evidencia a guardar:** respuesta/captura antes y después de corregir un campo; IDs de validación, versión, sugerencia y fuente; localizador real o mensaje de indisponibilidad; actor/instante; expected vs. observed.

### V3 — Regla ejecutada → entradas validadas → resultado

**Prioridad:** esencial.  
**Aceptación verificable:** una regla explícita sobre datos validados de documentos vinculados deja una ejecución identificable con **código y versión de regla, entradas referenciadas a validaciones concretas, versiones de origen, valores comparados y resultado**. Una sugerencia sin confirmar no puede alimentar la regla. Las advertencias resultantes no se convierten automáticamente en aprobación u observación.  
**Fundamento:** RF-16 (principal), RF-14/RF-15 como sustento de los vínculos; RN-02, RN-06.  
**Entidades (§5.2):** `EJECUCION_REGLA`, `ENTRADA_REGLA`, `VALIDACION_HUMANA`, `VERSION_DOCUMENTAL`, `VINCULO_DOCUMENTAL` y `TRAMITE`.  
**Comprobación:** UI de consistencia/detalle de regla o API autorizada; ejecutar sobre valores fijados en el oráculo y examinar los identificadores de las validaciones de entrada.  
**Evidencia a guardar:** configuración documentada de la regla escogida, origen de los valores, pantalla/respuesta de ejecución con código/versión/entradas/resultado, resultado esperado y observado; prueba de que una sugerencia sin confirmar no participa.

### V4 — Decisión → controles efectivamente considerados

**Prioridad:** esencial, **sin cumplimiento parcial**.  
**Aceptación verificable:** desde `DEC-1` o `DEC-2`, se pueden recuperar las **ejecuciones de reglas específicas consideradas al resolver esa decisión** y, a través de ellas, sus entradas y resultados, sin consultar ni sustituirlas por la última ejecución disponible. Al crear una ejecución nueva tras F-v2, la reconstrucción de `DEC-1` conserva el vínculo a los controles originales; la de `DEC-2` utiliza los que correspondan a CR-2.  
**Fundamento:** RF-16, RF-20, RF-21; RN-06, RN-09; en §5.2 se establece expresamente la posible asociación de decisiones con controles considerados.  
**Entidades (§5.2):** `DECISION → DECISION_CONTROL → EJECUCION_REGLA → ENTRADA_REGLA → VALIDACION_HUMANA`.  
**Comprobación:** UI de detalle/historial de decisión o API autorizada que devuelve los IDs de ejecución de reglas vinculados a esa decisión; contrastar con el oráculo y repetir después de recalcular reglas en CR-2.  
**Evidencia a guardar:** captura/respuesta de `DEC-1` y de `DEC-2` con IDs de controles considerados; detalle de entradas/resultados; comparación antes/después de F-v2. **Si no puede recuperarse esa relación: `No cumple`, nunca `Cumple con limitación`.**

### V5 — Auditoría de la secuencia funcional

**Prioridad:** complementaria.  
**Aceptación verificable:** el historial del trámite permite identificar para carga/confirmación, validación, control relevante, asignación, decisión, cambio de versión y cambio de estado los datos de auditoría exigidos: actor, instante, acción, entidad afectada, resultado y versión cuando corresponda. La línea de tiempo conserva la secuencia histórica y el acceso a versiones relacionadas. Las operaciones ordinarias de UI no permiten alterar ni borrar estos eventos.  
**Fundamento:** RF-19, RF-20, RF-21, RF-22; RN-10.  
**Entidades (§5.2):** `EVENTO_AUDITORIA`, `TRAMITE`, `USUARIO`, `VERSION_DOCUMENTAL`, `TAREA`, `DECISION`.  
**Comprobación:** línea de tiempo en UI y/o API autorizada de historial; intento ordinario de edición/eliminación que resulte rechazado, cuando exista el recorrido aplicable.  
**Evidencia a guardar:** historial antes y después de cada ciclo, enlaces a versiones y acciones, actor/fecha/resultado y rechazo documentado de cambios indebidos.

### V6 — Advertencias no sustituyen decisiones humanas

**Prioridad:** complementaria.  
**Aceptación verificable:** una advertencia de regla se muestra al revisor autorizado con su explicación, pero no decide ni cambia por sí sola el estado de una tarea. Solo el revisor/aprobador asignado puede **aprobar u observar**; observar exige registrar motivo. El administrador operativo no puede resolver la tarea por ese rol.  
**Fundamento:** RF-02, RF-16, RF-20; RN-06, RN-08.  
**Entidades (§5.2):** `EJECUCION_REGLA`, `TAREA`, `DECISION`, `USUARIO`, `USUARIO_ROL`, `EVENTO_AUDITORIA` y, cuando se vincula un control considerado, `DECISION_CONTROL`.  
**Comprobación:** UI de tarea y acciones autorizadas, o API autenticada; comprobar que advertencia sola no crea decisión y que una solicitud desde rol no habilitado se rechaza.  
**Evidencia a guardar:** advertencia y tarea aún pendiente; aprobación u observación manual atribuida al actor; motivo de la observación; respuesta de autorización denegada para actor no habilitado.

### V7 — Nueva versión no transfiere decisiones ni suprime historia

**Prioridad:** esencial.  
**Aceptación verificable:** al **confirmar** F-v2 antes del estado Cerrado, el sistema conserva F-v1 inmutable, su relación de predecesora y `DEC-1`/CR-1 históricos; deja el trámite en **Borrador** de acuerdo con RN-12 cuando cambia el conjunto considerado y no considera la aprobación anterior como autorización del nuevo ciclo. Las tareas anteriores que sigan abiertas ya no admiten decisiones. El cambio ocurre con la incorporación confirmada, no con una carga todavía pendiente.  
**Fundamento:** RF-04, RF-05, RF-07, RF-18, RF-20, RF-21; RN-09, RN-12.  
**Entidades (§5.2):** `ARCHIVO`, `DOCUMENTO`, `VERSION_DOCUMENTAL`, `TRAMITE`, `CICLO_REVISION`, `CICLO_REVISION_VERSION`, `TAREA`, `DECISION`, `EVENTO_AUDITORIA`.  
**Comprobación:** UI/API autorizada de incorporación y versionado, cambio de estado, historial de ciclos y resolución de tareas; incluir la prueba negativa EVD-N12 con tarea anterior abierta.  
**Evidencia a guardar:** estado y conjunto antes/después de la confirmación, línea de versiones, DEC-1 inalterada, tarea vieja rechazada, nuevo ciclo aún sin aprobación heredada, respuesta del intento no permitido.

### V8 — Validaciones y controles al cambiar el conjunto documental

**Prioridad:** complementaria.  
**Aceptación verificable:** F-v2 se procesa y exige confirmación humana propia antes de utilizar sus campos; **no hereda** validaciones de F-v1. Las versiones no modificadas C-v1 y O-v1 conservan sus validaciones, y las reglas pertinentes se vuelven a ejecutar con entradas correspondientes al conjunto nuevo.  
**Fundamento:** RF-07, RF-10, RF-11, RF-12, RF-16; RN-02, RN-09, RN-12.  
**Entidades (§5.2):** `VERSION_DOCUMENTAL`, `VALOR_SUGERIDO`, `VALIDACION_HUMANA`, `REFERENCIA_FUENTE`, `EJECUCION_REGLA`, `ENTRADA_REGLA`, `CICLO_REVISION_VERSION`.  
**Comprobación:** UI de validación/versiones y detalle de ejecución de reglas o API autorizada; comprobar IDs de validación en CR-1 vs. CR-2.  
**Evidencia a guardar:** matriz de valores por versión con validador e ID, F-v2 inicialmente sin validación heredada, conservación de validaciones en C-v1/O-v1, ejecuciones nuevas y entradas de reglas diferenciadas.

### V9 — Nuevo ciclo → nueva decisión → conjunto correcto

**Prioridad:** esencial.  
**Aceptación verificable:** tras confirmar F-v2, el nuevo flujo genera tareas vinculadas a `CR-2` y registra `DEC-2` sobre una tarea de ese ciclo. CR-2 considera exactamente `{C-v1,O-v1,F-v2}`; `DEC-2` no aparece en CR-1 ni utiliza F-v1 como versión considerada. Se comprueba tanto el recorrido de aprobación previa (EVD-A) como el de observación previa (EVD-B). Ninguna decisión de CR-1 se transfiere automáticamente.  
**Fundamento:** RF-17, RF-18, RF-20; RN-08, RN-09, RN-12.  
**Entidades (§5.2):** `CICLO_REVISION`, `CICLO_REVISION_VERSION`, `TAREA`, `DECISION`, `VERSION_DOCUMENTAL`, `TRAMITE`.  
**Comprobación:** UI de confirmación de flujo, tarea del revisor e historial de decisiones, o API autorizada que exponga los vínculos.  
**Evidencia a guardar:** manifiesto de CR-2 y sus versiones, asignación y resolución de la nueva tarea, identificadores de DEC-1/DEC-2 y conjuntos distintos, intentos rechazados de reutilización de decisión anterior.

### V10 — Reconstrucción sometida a autorización

**Prioridad:** ampliación EVD-01; **obligación general de seguridad del PFI**.  
**Aceptación verificable:** el responsable habilitado y el revisor con tarea asignada pueden consultar solo la evidencia del trámite/versiones que les corresponden. Una cuenta no habilitada, un usuario sin acceso o un administrador operativo sin permiso documental no pueden recuperar documentos, datos validados ni reconstrucciones sensibles de ese trámite; tampoco mediante una ruta de API que no se muestre en UI. Las denegaciones no filtran contenido.  
**Fundamento:** RF-01, RF-02, RF-13 y RF-22 en las operaciones aplicables; RN-01, RN-04; matriz de roles §3.3.1.  
**Entidades (§5.2):** `USUARIO`, `USUARIO_ROL`, `TRAMITE`, `TAREA`, `CICLO_REVISION`, `CICLO_REVISION_VERSION`, `VERSION_DOCUMENTAL`, `EVENTO_AUDITORIA`. **No inventar una tabla ACL de trámites:** §5.2 indica que el acceso se deriva de la responsabilidad o de una tarea asignada.  
**Comprobación:** UI y solicitudes a API con identidades/roles diferentes; aceptar códigos de error según contrato de API, siempre que se deniegue sin filtrar datos.  
**Evidencia a guardar:** matriz actor × operación × resultado esperado/observado, peticiones/respuestas depuradas, identidades ficticias y prueba de no exposición documental.

### V11 — Firma simulada de una versión y cierre terminal

**Prioridad:** ampliación EVD-01; **obligación general de cierre del PFI**.  
**Aceptación verificable:** sobre un ciclo aprobado, un revisor/aprobador con autorización específica puede aplicar **firma digital simulada** exclusivamente a una versión vigente comprendida en ese ciclo. La operación muestra inequívocamente que es una simulación, conserva firmante, fecha, versión y referencia de integridad, y deja el trámite en `Cerrado`. Desde `Cerrado` no se aceptan documentos/versiones nuevos ni nuevas decisiones; la historia sigue consultable por usuarios autorizados. No se presenta la simulación como firma jurídica real.  
**Fundamento:** RF-23 y RF-21/RF-22 para historia; RN-07, RN-09, RN-11, RN-15.  
**Entidades (§5.2):** `FIRMA_SIMULADA`, `CICLO_REVISION_VERSION`, `VERSION_DOCUMENTAL`, `CICLO_REVISION`, `USUARIO`, `TRAMITE`, `EVENTO_AUDITORIA`.  
**Comprobación:** UI de cierre y/o API autorizada; intentar firmar versión ajena al ciclo y crear versión nueva tras cerrar (operaciones rechazadas).  
**Evidencia a guardar:** detalle de firma simulada, ID de versión y ciclo, huella/referencia de integridad, actor/fecha, estado terminal y respuestas de denegación de operaciones posteriores.

## 4. Guiones de ejecución separados

### EVD-A — Aprobación antes de reemplazar una versión (RN-12)

**Precondición:** trámite no cerrado, documentos `C-v1`, `O-v1`, `F-v1` incorporados y validados, una regla real seleccionada, CR-1 confirmado con esas versiones.

1. Ejecutar el control pertinente, registrar entradas y resultado; mostrar la advertencia si corresponde.
2. Revisor autorizado resuelve tarea de CR-1 con **aprobación** `DEC-1`. Asegurar que el trámite alcanzó Aprobado si era la última tarea requerida.
3. Desde DEC-1 reconstruir V1–V4 por UI/API, guardar IDs exactos.
4. **Antes de firma/cierre**, cargar F-v2 (pendiente) y comprobar que aún no altera el conjunto; luego confirmar incorporación como nueva versión.
5. Comprobar retorno a Borrador, conservación de DEC-1 y ausencia de transferencia de aprobación (V7). Si quedan tareas anteriores abiertas en variante EVD-N12, intentar resolver una: debe denegarse.
6. Validar F-v2, conservar las validaciones de C-v1/O-v1, volver a ejecutar controles pertinentes (V8).
7. Confirmar flujo del nuevo conjunto `{C-v1,O-v1,F-v2}`, generar CR-2 y registrar una decisión nueva `DEC-2` (V9).
8. Recuperar DEC-1/DEC-2 y comprobar que controles, versiones y decisiones no se cruzan (V1,V3,V4,V7,V9).

### EVD-B — Observación seguida de corrección documental (RN-08/09/12)

**Precondición:** otro trámite sintético equivalente, con CR-1 activo y una tarea de revisión asignada; no reutilizar el estado mutado por EVD-A sin restablecer explícitamente el fixture.

1. Generar o mostrar un resultado de control relevante.
2. Revisor asignado **observa** mediante DEC-1, indicando motivo; conservar relación con CR-1 y el control considerado.
3. Responsable incorpora F-v2 como **nueva versión documental confirmada**; no tratarla como simple edición de metadatos.
4. Comprobar RN-12: retorno a Borrador, historial de observación preservado y no transferencia de tareas/decisiones.
5. Procesar, validar nueva versión, reejecutar reglas y confirmar CR-2 con el conjunto nuevo.
6. Revisor asignado **aprueba** mediante DEC-2. Reconstruir ambas decisiones y confirmar que conservan sus ciclos, versiones, controles y motivos correctos.

### EVD-C — Subsanación sin cambiar contenido (RN-13; independiente)

1. En un caso nuevo, obtener `Observado` mediante decisión autorizada con motivo. Si se quiere comprobar retención de aprobaciones históricas, utilizar más de una tarea y registrar una aprobación previa en CR-1.
2. Corregir únicamente **datos o metadatos**, sin incorporar un nuevo archivo documental como versión.
3. Confirmar que la versión vigente no cambia y que el trámite pasa a **Pendiente de validación**, no a Borrador por RN-12.
4. Comprobar que las aprobaciones anteriores continúan en el historial y no habilitan continuar automáticamente; realizar las validaciones y confirmar el flujo aplicable conforme al contrato del PFI.
5. Recuperar el historial del caso por UI/API y comprobar que no se fabricó una versión ficticia ni se transfirió una decisión previa.

**EVD-N12 — Variante negativa indispensable para RN-12:** en un ciclo iniciado con al menos una tarea todavía abierta, confirmar F-v2. La tarea abierta anterior debe dejar de admitir decisiones. Guardar la respuesta del intento de aprobarla/observarla y comprobar que no se creó una decisión válida. Esta prueba puede ejecutarse separadamente para no alterar los dos recorridos principales.

## 5. Pendientes de decisión para la reconstrucción (sin cambiar la tesis)

| ID | Punto no resuelto por el nivel de detalle de la tesis | Decisión necesaria antes de ejecutar EVD-01 |
|---|---|---|
| PD-01 | No hay un catálogo exhaustivo de reglas de consistencia, campos comparados y tolerancias en los RF/RN examinados. | Elegir e implementar una regla explícita sobre valores validados de documentos vinculados; documentar código, versión, entradas y resultado del caso, respetando RF-16/RN-06. |
| PD-02 | §5.2 define `DECISION_CONTROL`, pero no detalla en qué acción exacta se captura el conjunto de ejecuciones consideradas. | Definir y materializar el vínculo estable en el momento de decidir, sin alterar el modelo; especificar qué significa «considerado» y cómo se identifica en un ciclo. |
| PD-03 | RF-22 exige línea de tiempo, pero la tesis no establece una ruta o endpoint específico para la **reconstrucción transversal desde DECISION**. | Elegir UI, API autorizada o combinación para consultar V1–V4 y V7–V9, con permisos del §3.3.1. La implementación puede agregar vistas/API sin alterar las entidades lógicas de §5.2. |
| PD-04 | La Figura 5.4 es un **modelo lógico simplificado**; no enumera todos los campos físicos, fechas o índices de historial. | Resolver detalles físicos necesarios para actor/instante/eventos respetando RF-12, RF-21 y el modelo; documentar correspondencias, no asumir columnas inexistentes. |
| PD-05 | La tesis define estados y RN-12/RN-13, pero no detalla todas las microtransiciones de interfaz ni el mecanismo de control de concurrencia. | Especificar cómo se invalidan tareas anteriores y cómo se comprueban los cambios, sin cambiar resultados de estado, ciclos y permisos prescritos. |
| PD-06 | El requisito de reconstruir todas las relaciones desde una decisión no determina formato o contrato de la respuesta. | Definir qué IDs, versiones, referencias y enlaces devuelve la UI/API para que el evaluador pueda cotejarlos con el oráculo. |
| PD-07 | El ejemplo de prueba no fija aún datos documentales, reglas ni resultados esperados específicos. | Congelar los fixtures sintéticos, reglas, resultado esperado y el oráculo **antes** de implementar el caso automatizado/ejecutar la prueba. |
| PD-08 | No se especifica un volumen o número de repeticiones para EVD-01. | Decidir los casos y variantes a ejecutar y el método de registro, antes de obtener resultados. No introducir umbrales estadísticos ajenos a §6.3.1. |

**Advertencia:** la necesidad de instrumentar una vista, un endpoint o una transición no autoriza a modificar RF/RN ni a agregar una entidad que reemplace las relaciones existentes. Si una ambigüedad exigiera revisar una definición contractual de la tesis, elevarla al equipo como decisión académica separada antes de cambiarla.

## 6. Traslado posterior a la Sección 6

- **§6.1 Estrategia:** objetivo de EVD-01 y prioridades sin repetir §6.3.1.
- **§6.2 Pruebas funcionales:** casos EVD-A, EVD-B, EVD-C y EVD-N12 **automatizados contra la API autorizada**, criterios V1–V11, precondiciones, aserciones y oráculo.
- **§6.3.1 Procesamiento inteligente (DO-2026-10-21-E90-CORPUS):** conservar su evaluación cuantitativa independiente con **50 documentos sintéticos de medición** (3 adversariales incluidos), grupo de ajuste separado de 2–3 por tipo y 30 preguntas RAG; sin 16 adicionales ni conjunto público. Métricas y umbrales originales intactos. EVD-01 utiliza fixtures sintéticos representativos y **no representa ni sustituye** esas mediciones.
- **§6.4 Escenario representativo:** validación funcional/operativa integrada **independiente**, a cargo del equipo autorizado, con resultados no confidenciales, intervenciones y evidencia saneada; no se intercambian documentos con el corpus de 50 ni se usa como prueba de métricas de §6.3.1. Los EVD y la demo AWS descartable siguen utilizando exclusivamente datos sintéticos.
- **§6.5 Resultados y discusión:** solo resultados realmente observados, defectos, casos no ejecutados, cobertura de criterios y limitaciones.
- **§2.2.5:** no escribir «el aporte queda demostrado» antes de que la Sección 6 registre resultados suficientes. Nunca afirmar exclusividad comercial ni validez jurídica de la firma simulada.

**Estado final de este documento:** especificación aprobada para reconstrucción, con automatización de los cuatro recorridos exigida; no hay ejecución, evidencia generada ni porcentajes de cumplimiento.
