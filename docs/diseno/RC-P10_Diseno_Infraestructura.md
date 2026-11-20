# RC-P10 — Diseño de infraestructura AWS, aislamiento y operación

**Estado:** diseño aprobado (RC-P10-01 a RC-P10-12 y RC-P10-15). RC-P10-13 pendiente de cotización y mediciones; RC-P10-14 suspendida por DO-2026-10-21.
**Fuente:** consolidación del informe principal de RC-P10 y de su revisión complementaria (21/10/2026). Las decisiones aprobadas y sus precisiones están en `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md`; este documento aporta el detalle técnico para implementarlas.
**Importante:** la aprobación corresponde al diseño. Ninguna verificación se considera cumplida hasta ejecutarla. La actualización operativa del equipo del 21/10/2026 (DO-2026-10-21) sustituye las instrucciones anteriores de OIDC/CD; conserva la arquitectura. Todos los procedimientos siguientes son propuestos y pendientes de implementación y prueba.

---

## 1. Topología

- **Una cuenta AWS**, región principal **us-east-1**, sin NAT Gateway (como establece la tesis).
- **Una VPC** con subredes privadas de aplicación y de datos en **dos zonas de disponibilidad**.
- **Una instancia RDS PostgreSQL Multi-AZ** (primaria + reserva; no un clúster con réplicas legibles), con las bases lógicas `pfi_demo` y `pfi_tests`.
- **Un RDS Proxy compartido**, con su endpoint predeterminado (sin endpoints adicionales) y autenticación IAM de extremo a extremo.
- **Dos despliegues lógicos de la misma aplicación** (`demo` y `tests`): el mismo código, con identidades IAM, configuración, datos y recursos de ejecución propios.

### Endpoints de VPC

| Endpoint | Tipo | Uso |
|---|---|---|
| Amazon S3 | Gateway (sin cargo) | Verificar originales y recuperar resultados |
| Step Functions | Interface | Iniciar ejecuciones desde las Lambda privadas |
| Bedrock Runtime | Interface | Consulta asistida desde la API |
| AWS Lambda | Interface | Invocar funciones auxiliares fuera de la VPC |
| Secrets Manager | Interface, **temporal** | Solo durante la inicialización privilegiada de PostgreSQL (RC-P10-15) |

No se crean endpoints de otros servicios por anticipado. Si una integración lo necesita, se documenta la necesidad antes de agregarlo.

### Recursos por entorno (demo y tests)

| Recurso | Demo | Tests |
|---|---|---|
| API Gateway | Propio | Propio |
| Lambda (API, persistencia, reconciliador, procesamiento, operaciones de Cognito) | `atlas-demo-*` | `atlas-tests-*` |
| Máquina de Step Functions | Propia | Propia |
| Programación de EventBridge Scheduler | Propia | Propia |
| User Pool de Cognito | Propio | Propio |
| Bucket documental | Propio | Propio |
| Base PostgreSQL | `pfi_demo` | `pfi_tests` |
| Frontend (S3 + CloudFront) | Propio | Propio |

La configuración de cada despliegue fija **identificadores confiables**: base de datos, bucket, ARN de la máquina de estados, User Pool y rol IAM. **El cliente nunca envía un parámetro que decida el entorno.**

---

## 2. Aislamiento por capa

### 2.1. API Gateway y Lambda
- Dos API Gateway, cada uno integrado solo con las funciones de su entorno.
- Funciones Lambda físicamente separadas por entorno (no una función con aliases).
- Cada autorizador JWT valida solo el emisor y la audiencia del User Pool de su entorno. Las verificaciones de permisos del dominio siguen en el backend.

### 2.2. PostgreSQL y RDS Proxy

| Elemento | Demo | Tests |
|---|---|---|
| Base lógica | `pfi_demo` | `pfi_tests` |
| Usuario de aplicación | `atlas_demo_app` | `atlas_tests_app` |
| Usuario de migraciones | Exclusivo de demo | Exclusivo de tests |
| Permisos SQL | Solo su base | Solo su base |

Controles:
1. Revocar el `CONNECT` heredado por `PUBLIC` en ambas bases y conceder conexión solo a los usuarios autorizados, preservando los accesos internos que RDS Proxy necesita (por ejemplo, `rdsproxyadmin`).
2. Cada usuario accede solo a su base, esquemas, secuencias y tablas.
3. Los usuarios de aplicación no pueden crear bases ni administrar usuarios; los de migración solo cambian estructura en su entorno.
4. TLS en todas las conexiones; red restringida con security groups.
5. El aislamiento se verifica con **intentos reales de conexión cruzada**.

**Autenticación IAM de extremo a extremo:**

| Conexión | Principal IAM | Recurso autorizado (`rds-db:connect`) |
|---|---|---|
| Lambda demo → Proxy | Rol de ejecución demo | `arn:aws:rds-db:REGION:ACCOUNT:dbuser:prx-ID/atlas_demo_app` |
| Lambda tests → Proxy | Rol de ejecución tests | `arn:aws:rds-db:REGION:ACCOUNT:dbuser:prx-ID/atlas_tests_app` |
| Proxy → RDS | Rol asumido por RDS Proxy | `arn:aws:rds-db:REGION:ACCOUNT:dbuser:db-ID/atlas_demo_app` y `.../atlas_tests_app` |

- `prx-…` identifica al proxy; `db-…` (`DbiResourceId`) identifica a la instancia. **Ambos se obtienen dinámicamente de AWS; nunca se escriben a mano.**
- Al recrear el proxy cambian su identificador y, posiblemente, su DNS. `db-…` no cambia salvo que se reemplace la instancia.
- Los usuarios PostgreSQL de aplicación se configuran con `rds_iam`.
- Los usuarios administrativos y de migración usan conexión directa a RDS, no el proxy.
- Antes de implementar, **verificar** que la autenticación IAM de extremo a extremo de RDS Proxy esté disponible para la configuración elegida. Alternativa solo ante incompatibilidad comprobada: Secrets Manager para la autenticación del proxy.

### 2.3. S3 y URLs prefirmadas
- Buckets documentales separados; dentro de cada uno, prefijos para originales, cargas pendientes y resultados intermedios (estos últimos separados por **trabajo e intento**, RC-P08).
- Cada API genera URLs prefirmadas solo para su bucket. La clave del objeto la genera o valida el backend; no se aceptan buckets indicados por el navegador.
- Los roles de un entorno no tienen permisos sobre el bucket ni las claves KMS del otro.
- Vigencia de las URLs prefirmadas: **cinco minutos** inicialmente.

### 2.4. Step Functions, persistencia y reconciliador
- Cada entorno tiene su máquina de estados y sus funciones de procesamiento. Una ejecución de tests **no tiene permisos** para invocar funciones de demo.
- Las entradas de cada ejecución contienen solo identificadores mínimos de trabajo y objeto, nunca una base destino seleccionable.
- La función de persistencia recupera el trabajo desde su propia base y verifica que pertenezca a ese entorno; si recibe un trabajo incompatible, lo rechaza sin modificar registros.
- Control defensivo adicional: al iniciar, cada función verifica la combinación de bucket, base y máquina de estados de su despliegue.

### 2.5. CI y operación humana (DO-2026-10-21)

| Ejecución | Acceso AWS |
|---|---|
| GitHub Actions: linting, análisis estático, unitarias, cobertura y PostgreSQL temporal con pgvector | Ninguno; sin excepciones |
| Despliegue, encendido, apagado, migración remota y administración | Solo ejecución manual por integrante autorizado, con plan e impacto/costo aprobados |
| EVD-01 y evaluaciones que consumen AWS | Campaña iniciada y supervisada por operador en una sesión aprobada; fuera de GitHub Actions |

No configurar proveedor OIDC de GitHub, roles IAM para Actions, `aws-actions/configure-aws-credentials`, credenciales AWS en GitHub ni workflows que operen AWS, tampoco con disparador manual. Las identidades humanas y las de ejecución de la aplicación siguen separadas por mínimo privilegio. Los roles de Lambda, Proxy y Scheduler exigidos por la arquitectura se conservan.

La versión de defensa se fija por commit y artefactos identificables; un push o merge no despliega y un cambio de tests no se promueve automáticamente a demo. Antecedentes de OIDC y runners documentados en DO-2026-10-21, sin instrucciones de configuración vigentes.

---

**E90A — nueva decisión posterior del equipo (21/10/2026):** la demo es descartable. Cada encendido implica crear recursos nuevos y poblarlos con datos sintéticos, y cada apagado implica eliminación manual selectiva de los recursos propios de la sesión, incluida RDS. La persistencia entre sesiones no aplica al hito E90. [Decisión completa](../decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md) y [procedimiento de Terraform](../../infra/terraform/README.md).

## 3. Terraform

### 3.1. Estados

| Estado | Propietario de | Ciclo de vida |
|---|---|---|
| `bootstrap` | Bucket del estado remoto y sus controles | Se crea una vez |
| `persistent` | VPC, subredes, RDS, buckets de demo, Cognito de demo, **grupos de seguridad** (incluidos clientes de base y proxy), endpoint gateway S3 | **E90: se recrea y se retira por sesión**. El nombre es histórico y no implica conservación de datos |
| `runtime` | RDS Proxy, endpoints de interfaz, rol IAM del proxy | Se crea y elimina por sesiones |
| `demo` | API Gateway, Lambda, Step Functions, Scheduler, frontend, roles IAM y políticas `rds-db:connect` de demo | E90: se recrea y se retira por sesión |
| `tests` | Equivalentes de tests | No se despliega en el E90 inicial; requiere aprobación y aislamiento separado |

- Estado remoto en S3: privado, cifrado, versionado, con **bloqueo nativo** (`use_lockfile`), sin DynamoDB. Un objeto de estado por raíz.
- Dependencias: `bootstrap → persistent → runtime → demo / tests`, con outputs explícitos y referencias de estado remoto (sin secretos en outputs; acceso de lectura a los estados restringido).
- Protecciones: `prevent_destroy` y `deletion_protection` para impedir borrados accidentales, y prohibición absoluta de destruir `bootstrap` y recursos ajenos. En E90 el operador puede revisar y aprobar la retirada de raíces propias de la demo (`demo → runtime → persistent`) tras preparar su configuración para destrucción selectiva; sin deshabilitar protecciones globalmente, sin `state rm` y sin GitHub Actions. Los datos de RDS/S3/Cognito del entorno descartable se perderán entre sesiones.
- Terraform define **qué existe**; el operador ejecuta manualmente cada plan aprobado. En E90 la identidad de RDS, RDS Proxy, Cognito y otros recursos puede cambiar entre sesiones: el seed y los consumidores se configuran con los identificadores actuales. No se usa detención de RDS como política de inactividad de la modalidad A.
- Antes de aplicar o destruir: cuenta/región/estado, plan exacto e identificable, inventario de recursos propios de la sesión, costos, aprobación y confirmación de pérdida irreversible de datos. **Nunca** afectar `bootstrap` o infraestructura ajena. Un fallo o un plan distinto exige nueva revisión.
- Estado remoto sigue siendo obligatorio: un plan local no concede acceso permanente ni autoriza cambios. Ninguna operación Terraform se ejecuta como parte de esta actualización documental.
- Debe existir **una única autoridad** sobre el estado habilitado o deshabilitado de los schedules del reconciliador, para que Terraform no los reactive accidentalmente.

### 3.2. Referencias obsoletas
- Al destruir `runtime`, las Lambda conservan temporalmente la referencia a un proxy inexistente; es aceptable solo porque los entornos están en `offline`.
- Al recrear `runtime` es **obligatorio** reaplicar `demo` y `tests` antes de habilitar el servicio.
- No se planifican cambios ordinarios en `demo` o `tests` mientras `runtime` esté ausente.
- Si una recreación parcial falla: recuperar primero `runtime`, verificar su estado real y reaplicar los consumidores.

---

## 4. Inicialización y migraciones de PostgreSQL (RC-P10-15)

- **Inicialización única** (al crear RDS o tras una recuperación que lo requiera), mediante una **Lambda privada** con conexión directa a RDS, invocada solo por una identidad administrativa: crea las bases, los usuarios de aplicación y de migración, los esquemas, la extensión **pgvector** en ambas bases y los privilegios.
- La primera conexión usa la **credencial maestra administrada por RDS en Secrets Manager**, a través del endpoint temporal de Secrets Manager. Esa credencial se usa **solo** para inicialización y administración privilegiada; no sustituye la autenticación IAM de las aplicaciones.
- Comprobar la compatibilidad de pgvector con la versión de PostgreSQL elegida; su instalación pertenece a la inicialización privilegiada, no a las migraciones ordinarias.
- **Migraciones con Alembic**, ejecutadas por funciones privadas con autenticación IAM y el usuario de migración de cada entorno. El operador autorizado invoca manualmente la función privada del entorno después de aprobar la migración, su impacto y sus costos. Ningún runner de GitHub Actions tiene acceso a AWS ni a SQL, tampoco indirectamente por una invocación.
- Procedimiento de migración: verificar entorno y base de destino → conectividad privada → versión actual del esquema → bloqueo de migración → aplicar solo pendientes → validar objetos esperados → registrar resultado. Una migración fallida no habilita una versión incompatible de la aplicación.
- Las migraciones de demo y de tests son independientes. El CI no aplica cambios de esquema remotos en ningún entorno. Se conserva el registro de revisión y ejecución humana por migración.

---

## 5. Modo mantenimiento (RC-P10-09)

- Un **objeto de control en S3 por entorno**, independiente de PostgreSQL y del proxy, con estados:

| Estado | Operaciones funcionales | Trabajos existentes |
|---|---|---|
| `active` | Permitidas según los permisos del dominio | Procesamiento normal |
| `draining` | No se admiten nuevas | Se completan o recuperan los iniciados |
| `offline` | No se admiten | No se inician; se preservan los pendientes |

- Solo una operación administrativa manual del operador autorizado modifica el objeto; la aplicación solo lo lee. El objeto está **protegido y excluido** de la reinicialización de `pfi_tests`.
- Fuera de `active`, la API responde **HTTP 503** con un mensaje controlado y, si corresponde, `Retry-After`. Si el objeto no puede leerse o es inválido, **se deniega por defecto**.
- El endpoint de salud informa el estado operativo y no afirma disponibilidad fuera de `active` o cuando RDS no existe/todavía no está lista; en E90A cada sesión comienza con RDS nueva.
- En `draining`: no se emiten nuevas URLs prefirmadas, no se aceptan confirmaciones nuevas, se espera el vencimiento de las URLs emitidas (una transferencia iniciada antes del vencimiento puede seguir) y el reconciliador no inicia intentos nuevos.
- No se pasa a `offline` con operaciones críticas activas sin una decisión explícita de recuperación.

---

## 6. Ciclo E90A — crear, poblar, evaluar y destruir una demo descartable (RC-P10-08/09 modificados)

**Decisión posterior DO-2026-10-21-E90A. Propuesto, no implementado ni probado.** No se utiliza RDS `stopped`, snapshots entre sesiones ni restauración. La única base de AWS obligatoriamente retenida entre sesiones es `bootstrap` para el estado Terraform y los controles de cuenta/seguridad/budgets. Todas las acciones sobre AWS son manuales, aprobadas y supervisadas por el operador. No confundir «apagar todo» con destruir la cuenta o el estado remoto.

### 6.1. Inicio manual de una sesión

1. Aprobar cotización de la sesión completa (aprovisionar, migrar, sembrar, procesar, cerrar y eliminar), un inventario de recursos y el plan de creación/destrucción; verificar cuenta, región `us-east-1`, estado remoto y responsable del cierre.
2. Con `bootstrap` ya protegido, aplicar manualmente `persistent → runtime → demo` para una **sesión nueva**. En E90 `tests` no se despliega salvo aprobación independiente; no hay recursos compartidos con datos reales. Iniciar `offline`, reconciliadores deshabilitados.
3. Inicializar RDS PostgreSQL Multi-AZ nuevo y pgvector, migrar con Alembic mediante operación privada humana autorizada y confirmar IAM/TLS/aislamiento. El `DbiResourceId`, el `prx-…` y el DNS actuales se obtienen de AWS.
4. Ejecutar manualmente la **semilla sintética** aprobada por interfaces autenticadas; identidades ficticias, corpus PD-07, trámites, versiones, validaciones y estados según las funciones implementadas. Validar por API y oráculo, nunca insertar eventos de auditoría ficticios directamente en tablas. La integración AWS del seed no está implementada mientras no exista backend.
5. Autorizar explícitamente las invocaciones reales Textract/Bedrock necesarias y su costo. Completar smoke tests, verificar que RDS, S3 y auditoría sean recuperables por API durante esta misma sesión y pasar a `active` solo tras controles de salud y permisos.

### 6.2. Cierre y eliminación manual selectiva

1. Denegar cargas nuevas mediante `draining`; deshabilitar reconciliador y comprobar efectos reales, URLs prefirmadas, trabajos Step Functions y análisis Textract pendientes. Resolver y documentar operaciones inciertas antes de retirar dependencias.
2. Ejecutar recorridos de validación y **exportar evidencias académicas saneadas fuera de AWS**. Registrar versiones de código/corpus, resultados, IDs correlacionables, pruebas negativas e incidencias; la próxima sesión tendrá datos e identificadores nuevos.
3. Pasar a `offline`. Generar, comparar y aprobar los planes **exactos** de eliminación de recursos **propios de esa sesión**: `demo → runtime → persistent`, respetando dependencias. No ejecutar un `terraform destroy` global; no destruir `bootstrap`, Budgets, AWS Organizations, política de IA o datos ajenos.
4. Confirmar explícitamente: **RDS se borra definitivamente sin snapshot final y sin backups retenidos**, y los documentos, usuarios e historial de demo también se pierden. Solo hacerlo en el entorno descartable, una vez exportada la evidencia. No habilitar borrado funcional en la aplicación ni desactivar protecciones de otros entornos.
5. El operador ejecuta manualmente las retiradas autorizadas. Verificar RDS eliminado, proxy/endpoints ausentes, buckets vaciados realmente de **todas las versiones y marcadores** cuando aplique, CloudFront y servicios de aplicación retirados y no existen temporales facturables olvidados. Identificar snapshots manuales antiguos, secretos con eliminación diferida, logs y otros residuos; informar costos/limitaciones.
6. Comparar inventario AWS y estados remotos con el resultado esperado y esperar confirmación real de las eliminaciones (pueden ser asíncronas). Cerrar la sesión solo con conciliación; revisar Billing posteriormente por demoras de facturación.

### 6.3. Semilla y límites de evaluación

La semilla está implementada en `atlas.herramientas.sembrar_demo`. Las pruebas RNF-04/RN-10 siguen obligando a preservar la auditoría **mientras existe el trámite en una sesión**. La eliminación administrativa del entorno descarta también su base; la nueva sesión genera otro conjunto de identidades y registros. **Esto no demuestra la antigua verificación B (recuperar la misma evidencia tras apagar).** Si E90 exige esa demostración, debe constar como pendiente o realizarse un ensayo alternativo con backup/restauración aprobado para un hito posterior.

La destrucción de RDS no acarrea una tarifa directa de eliminación, pero la creación/uso, almacenamiento mientras exista, mínimos de facturación, backups retenidos y cargos residuales sí pueden costar dinero. Consultar la [procedimiento de Terraform](../../infra/terraform/README.md) antes de intentar cualquier ciclo.

---

## 7. Verificaciones obligatorias (pendientes de ejecución)

| ID | Verificación |
|---|---|
| A | Aislamiento efectivo con pruebas negativas reales: tests no puede consultar, modificar ni eliminar recursos de demo |
| B (original) / B-E90 | **Original no cubierto**: mismo trámite a través de apagado. En E90 verificar persistencia, versiones y auditoría **dentro de la misma sesión**; no equivalen |
| C | Recuperación de interrupciones y reintentos **dentro de una sesión activa** sin duplicar efectos; no prometer recuperación después de destrucción |
| D | Reinicialización segura de `pfi_tests` sin afectar demo |
| E | Ausencia de recursos facturables propios de la sesión después de la **eliminación**, incluidos RDS, proxy y endpoints; inventario de residuales |
| F | Protocolo de defensa: encender con margen, congelar despliegues de demo y prueba de humo del recorrido del contrato |
| V-RP | Recreación del proxy: nuevo identificador, políticas y configuración actualizadas, conexiones sin permisos cruzados |
| V-DB | Inicialización y migraciones desde la VPC, independientes por entorno |
| V-MT | Mantenimiento sin consultar PostgreSQL, cargas prefirmadas gestionadas, trabajos sin pérdidas ni duplicaciones |
| V-TF | Creación y eliminación manual completa de la demo y nueva creación + seed; sin tocar `bootstrap`; **no** misma identidad o datos |
| V-CO | Recursos activos e inactivos, créditos de CPU registrados y cotización oficial antes de cerrar RC-P10-13 |
| IAM | Cada entorno conecta con su usuario y su base; se le deniega el usuario y la base del otro |

Pruebas de conectividad tras cada encendido:

| Prueba | Resultado esperado |
|---|---|
| Lambda demo → `pfi_demo` | Permitido |
| Lambda demo con usuario de tests | Denegado |
| Lambda tests → `pfi_tests` | Permitido |
| Lambda tests con usuario de demo | Denegado |
| Usuario SQL demo → `pfi_tests` | Denegado |
| Usuario SQL tests → `pfi_demo` | Denegado |
| Proxy con destino RDS saludable | Correcto |
| API usa el endpoint vigente del proxy | Confirmado |
| Conexiones con TLS | Confirmado |
| Aplicaciones sin proxy disponible | Permanecen en mantenimiento |

---

## 8. Fallos compartidos y riesgos

| Fallo | Impacto |
|---|---|
| Caída de RDS o del proxy | Afecta a ambos entornos |
| Error de red o de endpoints compartidos | Puede afectar a ambos |
| Modificación incorrecta de IAM compartido | Puede comprometer ambos |
| Despliegue defectuoso solo en tests | Debe quedar limitado a tests |
| Saturación de RDS por pruebas | Puede degradar la demo |
| Cuotas compartidas de Textract o Bedrock | Pueden afectar a ambos |

Mitigación: limitar la concurrencia de tests (RC-P08) y, antes de la defensa, congelar los despliegues de demo y evitar pruebas intensivas.

---

## 9. Respaldo y recuperación (RC-P10-12)

- Backups automáticos de RDS con retención inicial de **siete días** y snapshots antes de cambios críticos **mientras la sesión está activa, cuando estén aprobados**. Al destruir deliberadamente la demo E90 no se crea snapshot final ni se retienen backups, salvo excepción aprobada que deja de ser modalidad A estricta y exige revisar costos.
- En **operación E90A** no se restaura ni retiene una instancia entre sesiones. La restauración a punto en el tiempo se conserva como capacidad arquitectónica para incidentes **durante una sesión** o evaluaciones posteriores, bajo decisión, costo y evidencia separada; no se afirma probada.
- Versionado de S3 en originales durante la sesión; resultados intermedios separados con retención definida. Sin Object Lock por ahora. Al retirar la demo descartable hay que eliminar explícitamente todas las versiones S3 y marcadores de eliminación para evitar residuos.
- Tras una restauración, verificar que cada versión documental tenga su objeto, que la huella coincida, que no haya objetos eliminados o reemplazados indebidamente y que las decisiones sigan referenciando sus versiones, validaciones y controles.
- La reinicialización de `pfi_tests` es una operación técnica de administración (RC-P10-10): confirmar cuenta, región y destino exacto; sin pruebas activas; identidad limitada a tests; reinicializar datos y esquemas autorizados; reaplicar migraciones; limpiar solo los objetos del bucket de tests; verificar que `pfi_demo` siga intacta.

---

## 10. Costos (RC-P10-13, pendiente)

**Cotización:** por sesión E90A, preliminar (retirada del repositorio; queda en el historial de git). No cierra RC-P10-13 ni autoriza despliegue.


- `db.t4g.medium` Multi-AZ es la **hipótesis inicial** de dimensionamiento, sujeta a pruebas. Las instancias T4g funcionan en modo ilimitado: monitorear `CPUCreditBalance`, `CPUSurplusCreditBalance` y `CPUSurplusCreditsCharged`.
- Con el prototipo inactivo siguen cobrándose: almacenamiento y backups de RDS, S3 (incluidas versiones), secretos y logs retenidos. Apagar no deja la factura en cero.
- Las cifras del informe original son solo ilustrativas. La estimación definitiva se obtiene con AWS Pricing Calculator y se contrasta con mediciones reales.
- AWS Budgets con alertas tempranas y etiquetas por entorno; las alertas no son un límite de gasto. Política, presupuestos comunicados por el equipo, fuentes oficiales de facturación, mínimos/redondeos y plantilla de estimación en `docs/operacion/Politica_Costos_AWS.md`.
- RC-P10-13 es condición previa al primer despliegue: costo por hora, sesión y mes con inactividad, residuales, créditos CPU, margen de recuperación y presupuesto aceptado. Las mediciones de Etapa 4 actualizan la cotización inicial. ATLAS no funciona permanentemente durante el desarrollo.
