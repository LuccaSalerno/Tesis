# Guion de la demo de ATLAS

Guion para presentar ATLAS en vivo sobre la sesión AWS levantada con la [guía de la sección 6](../aws/Guia_Sesion_Seccion6.md) y sembrada con `sembrar_demo` (Parte 3). Datos **sintéticos** del oráculo PD-07 v2: nada de lo que se ve es un documento real.

Duración: **20–25 minutos** el recorrido completo; hay un recorte de 10 minutos al final.

---

## 1. Antes de empezar (30 minutos antes)

### 1.1 Datos de acceso

- **Dirección:** https://d1gbq6j3u4z7af.cloudfront.net
- **Cuentas que se usan en la demo:**

| Usuario (Cognito) | Persona en pantalla | Rol | Para qué |
|---|---|---|---|
| `atlas-responsable` | Laura Méndez | Responsable del trámite | Cargar, validar, consultar, vincular, enviar a revisión |
| `atlas-revisor` | Martín Ríos | Revisor/aprobador | Paso «Revisión legal» |
| `atlas-aprobador` | Sofía Herrera | Revisor/aprobador con autorización de cierre | Paso «Aprobación final» y firma |
| `atlas-admin` | Administración ATLAS | Administrador operativo | Estado general, plantillas, cuentas |

- **Contraseñas:** son las que definiste en el paso 2.6 de la guía y guardaste en tu gestor de contraseñas. **No se escriben en este archivo ni en el repositorio**: es una regla del proyecto (AGENTS.md §3).
- **Si perdiste alguna:** el operador la redefine desde la terminal (con `read -rs`, así no queda en el historial):

```bash
POOL=$(terraform -chdir=infra/terraform/persistent output -raw cognito_user_pool_id)
read -rs -p "Nueva clave de atlas-revisor: " CLAVE; echo
aws cognito-idp admin-set-user-password --user-pool-id "$POOL" --username atlas-revisor --password "$CLAVE" --permanent
```

- `atlas-responsable-2`, `atlas-revisor-2` y `atlas-deshabilitada` son para las pruebas de la sección 6: **no se usan en la demo**.

### 1.2 Navegador

- **Cuatro perfiles o ventanas privadas**, una por cuenta, cada una ya con la sesión iniciada. Así cambiás de persona con un clic en lugar de cerrar e iniciar sesión delante del público. Ponele a cada ventana el nombre de la persona.
- Zoom del navegador al 110–125 % para el proyector.
- Abrí la carpeta [documentos_a_cargar](documentos_a_cargar/) en el explorador de archivos, lista para arrastrar:

| Archivo | Qué es | Cuándo se carga |
|---|---|---|
| `1_Orden_de_compra_O-v1.pdf` | Orden OC-2026-0042, emitida el **15/03/2027** (fuera de la vigencia del contrato) | Paso 3.1 |
| `2_Factura_F-v2.pdf` | Factura FC-A-0001-00000123 por $ 1.250.000,00 | Paso 3.1 |
| `3_Orden_de_compra_corregida_O-v2.pdf` | La misma orden corregida, emitida el **15/09/2026** | Paso 3.10 (opcional) |
| `0_Contrato_C-v1_(respaldo).pdf` | El contrato. **Ya está cargado** en el trámite en vivo; es solo de respaldo | Solo si falta el trámite en vivo (§5) |

### 1.3 Control previo

Con `atlas-responsable`, en **Trámites**, tienen que estar los cuatro que dejó la semilla:

| Trámite | Estado | Para qué |
|---|---|---|
| Servicio de mantenimiento de laboratorio **(en vivo)** | Borrador | El recorrido en vivo |
| Servicio de mantenimiento de laboratorio | Observado | Respaldo de los puntos A–D ya hechos |
| Servicio de mantenimiento de laboratorio **(historia completa)** | Cerrado | La historia con versión nueva y firma |
| Mantenimiento de equipos (cancelado) | Cancelado | Cancelación con motivo |

Revisá también:
- En el trámite en vivo, **Documentos y datos**: el contrato aparece como «Contrato de mantenimiento», v1, con «Validar datos».
- La API responde `"operacion": "active"`: `curl -s "${URL}salud"`. Si no está en `active`, la interfaz muestra «ATLAS está en mantenimiento» y no deja hacer cambios.

---

## 2. Apertura (2 minutos)

**Qué mostrar:** la pantalla de ingreso, sin datos.

**Qué decir:**

> «En una organización, la contratación de un servicio deja un contrato, órdenes de compra y facturas. Hoy se controlan a mano: alguien lee el contrato, busca la vigencia, la compara con la fecha de la orden y aprueba. Si después alguien pregunta por qué se aprobó, cuesta reconstruirlo.
>
> ATLAS hace tres cosas: extrae los datos con inteligencia artificial, pero **una persona los valida siempre**; controla la consistencia entre documentos con reglas explícitas sobre esos valores validados; y deja **evidencia reconstruible** de cada decisión: quién decidió, cuándo, sobre qué versiones y con qué advertencias a la vista.
>
> Todo lo que van a ver es sintético: un contrato de mantenimiento ficticio entre un laboratorio y un proveedor, con CUIT de prueba sin inscripción en ARCA.»

---

## 3. Recorrido en vivo

### 3.1 Ingreso y carga anticipada (Laura, 2 minutos)

**Qué hacer:**
1. En la ventana de **Laura Méndez**: **Trámites** → «Servicio de mantenimiento de laboratorio (en vivo)».
2. Pestaña **Documentos y datos** → «Cargar un archivo» → elegí `1_Orden_de_compra_O-v1.pdf`.
3. Repetí con `2_Factura_F-v2.pdf`.

**Qué decir:**

> «Laura es la responsable del trámite. Ya cargó el contrato; ahora sumo la orden de compra y la factura. El archivo va directo a un almacenamiento privado con una URL temporal, y el procesamiento sigue en segundo plano: lectura con Textract y clasificación y extracción con Claude Haiku. Mientras tanto, validamos el contrato.»

> **Por qué ahora:** cada documento tarda unos minutos en procesarse. Cargándolos al principio, están listos cuando se necesitan (paso 3.4).

### 3.2 Punto A: validación humana con fuente (Laura, 5 minutos)

**Qué hacer:**
1. En «Contrato de mantenimiento» → **Validar datos**.
2. **Clasificación:** la sugerencia es «Contrato» → **Confirmar sugerencia**. Los campos aparecen recién después de validar la clasificación.
3. En **Vigencia hasta**, hacé clic en **Ver en el documento**: el visor abre la **página 6** del PDF. Mostralo.
4. Confirmá los siete campos. Si alguna sugerencia no coincide con esta tabla, usá **Corregir** y escribí el valor de la tabla, en el mismo formato que muestra la sugerencia (las fechas y los importes se guardan en formato canónico):

| Campo | Valor esperado | Página |
|---|---|---|
| Contraparte | Servicios Integrales del Sur S.A. | 1 |
| CUIT de la contraparte | 30-96472518-3 | 1 |
| Fecha de celebración | 20/02/2026 | 1 |
| Vigencia desde | 01/03/2026 | 6 |
| Vigencia hasta | 28/02/2027 | 6 |
| Monto total | 1.250.000,00 | 5 |
| Moneda | ARS | 5 |

5. Si hacés una corrección, mostrá que se ven a la vez el valor **sugerido** y el **validado**.

**Qué decir:**

> «La IA sugiere y la persona valida. Cada sugerencia trae la página de la que sale: si la cita del modelo no aparece en esa página, el sistema no muestra el localizador. Nunca se usa un valor sin validar: las reglas y las decisiones trabajan solo con lo que confirmó una persona. Queda registrado el valor sugerido, el validado, quién, cuándo, en qué versión y con qué fuente.»

> **Si una sugerencia es incorrecta, mejor:** corregirla delante del público muestra exactamente el punto de la validación humana.

### 3.3 Punto B: consulta con cita y abstención (Laura, 3 minutos)

**Qué hacer:**
1. Pestaña **Consulta**.
2. Escribí: **¿Hasta cuándo está vigente el contrato?** → **Consultar**.
3. Mostrá la respuesta, el 28/02/2027, con la cita al contrato, versión 1, **página 6**.
4. Escribí: **¿Cuál es el número de cuenta bancaria del proveedor?** → **Consultar**.
5. Mostrá «No hay evidencia suficiente para responder».

**Qué decir:**

> «La consulta busca solo en los documentos vigentes de este trámite, con embeddings de Cohere en PostgreSQL con pgvector, y Claude responde citando los fragmentos. Si una afirmación no tiene cita, se descarta. Y si no hay evidencia, el sistema se abstiene en lugar de inventar: el contrato no tiene datos bancarios, y no responde. Todas las consultas quedan registradas con los fragmentos usados.»

### 3.4 Incorporar la orden y la factura (Laura, 3 minutos)

**Qué hacer:**
1. Volvé a **Documentos y datos** → panel **Cargas**: los dos archivos tienen que figurar como «Procesado».
2. En la orden, escribí el nombre **Orden de compra** → **Incorporar como documento nuevo**.
3. En la factura, escribí **Factura** → **Incorporar como documento nuevo**.
4. Validá cada uno (**Validar datos**, primero la clasificación y después los campos):

| Orden de compra (O-v1) | Valor |
|---|---|
| Clasificación | Orden de compra |
| Número | OC-2026-0042 |
| Fecha | **15/03/2027** |
| Proveedor | Servicios Integrales del Sur S.A. |
| CUIT del proveedor | 30-96472518-3 |
| Importe total | 1.250.000,00 |
| Moneda | ARS |

| Factura (F-v2) | Valor |
|---|---|
| Clasificación | Factura |
| Número | FC-A-0001-00000123 |
| Fecha de emisión | 30/09/2026 |
| Emisor | Servicios Integrales del Sur S.A. |
| CUIT del emisor | 30-96472518-3 |
| Importe total | 1.250.000,00 |
| Moneda | ARS |

**Qué decir:**

> «Un archivo cargado no produce efectos hasta que la responsable lo incorpora. Así no entra nada al expediente por error.»

> **Si van atrasados:** validá la factura rápido, con «Confirmar sugerencia» en cada campo, y detenete solo en la **fecha de la orden**, que es la clave del punto C.

> **Si el procesamiento sigue en curso:** podés registrar los valores a mano con **Registrar valor**. Si figura «Falla técnica», usá el botón de reintento. Si no hay tiempo, pasá al trámite «Observado» (§5).

### 3.5 Punto C: vínculos y reglas (Laura, 3 minutos)

**Qué hacer:**
1. Pestaña **Vínculos y controles**.
2. En «Sugeridos, pendientes de confirmación» aparecen orden ↔ contrato y factura ↔ orden, con la etiqueta «Sugerido por el sistema» → **Confirmar** en cada uno.
   - Si no aparecen: en «Documento» elegí *Orden de compra*, en «Relacionado con» *Contrato de mantenimiento*, justificación «Comparten el CUIT validado del proveedor» → **Vincular**. Repetí con *Factura* → *Orden de compra*.
3. En **Controles de consistencia**, mostrá los resultados:

| Regla | Qué compara | Resultado |
|---|---|---|
| R1 | CUIT del emisor de la factura = CUIT del proveedor de la orden | Cumple |
| R2 | CUIT del proveedor de la orden = CUIT de la contraparte del contrato | Cumple |
| **R3** | Fecha de emisión de la orden dentro de la vigencia del contrato | **Advertencia**: 15/03/2027 está después del 28/02/2027 |
| R4 | Total de la factura ≤ total de la orden, en la misma moneda | Cumple |

**Qué decir:**

> «El sistema sugiere los vínculos porque coinciden los CUIT validados, pero los vínculos sugeridos no rigen hasta que la responsable los confirma. Con los vínculos, las reglas comparan valores validados y explican el resultado. R3 advierte que la orden se emitió el 15 de marzo de 2027, cuando el contrato venció el 28 de febrero. Es una advertencia, no una decisión: no bloquea ni cambia el estado del trámite. Decide una persona.»

### 3.6 Enviar a revisión (Laura, 1 minuto)

**Qué hacer:**
1. **Resumen** → **Enviar a validación**.
2. **Revisión** → aparece el «Flujo de revisión sugerido»: plantilla «Revisión de contratos», con **Revisión legal** (Martín Ríos) y **Aprobación final** (Sofía Herrera).
3. **Confirmar el flujo y enviar a aprobación**.

> **Si aparece «Faltan datos por resolver antes de confirmar»:** te falta un campo. Volvé a **Documentos y datos** y resolvelo; si un dato no está en el documento, usá «No consta / no aplica».

**Qué decir:**

> «El flujo se sugiere según los tipos documentales y no crea tareas hasta que la responsable lo confirma. Cada confirmación abre un ciclo de revisión con un conjunto exacto de versiones.»

### 3.7 Punto D, parte 1: el revisor aprueba (Martín, 2 minutos)

**Qué hacer:**
1. Pasá a la ventana de **Martín Ríos** → **Mis tareas** → «Revisión legal» del trámite en vivo.
2. Mostrá el «Contexto para decidir»: documentos del ciclo, versiones consideradas y la advertencia de R3 en «Controles que se registrarán con tu decisión».
3. **Aprobar**.

**Qué decir:**

> «Martín ve las versiones exactas que va a evaluar y las advertencias. Las advertencias informan; la decisión es suya. Aprueba la revisión legal.»

### 3.8 Punto D, parte 2: la aprobadora observa (Sofía, 2 minutos)

**Qué hacer:**
1. Pasá a la ventana de **Sofía Herrera** → **Mis tareas** → «Aprobación final».
2. **Observar** → en «Motivo de la observación» pegá:

   > La fecha de emisión de la orden de compra (15/03/2027) está fuera de la vigencia del contrato (01/03/2026 a 28/02/2027). Corregir la orden antes de aprobar.

3. **Registrar observación**. El trámite pasa a **Observado**.

**Qué decir:**

> «Sofía tiene en cuenta la advertencia y observa. El motivo es obligatorio. Fíjense que la IA nunca aprobó ni observó nada: solo sugirió datos.»

### 3.9 Punto D, parte 3: la evidencia de la decisión (Sofía, 3 minutos)

**Qué hacer:**
1. En la tarea, **Evidencia de la decisión**.
2. Recorré «Reconstrucción al momento de decidir»: decisión, quién, cuándo, motivo, **Versiones consideradas** («el conjunto exacto del ciclo, no las versiones vigentes hoy»), **Datos validados al decidir** (sugerido, validado, quién y cuándo, fuente) y **Controles considerados** con R3.
3. Desde «Cadena de la evidencia», **Ver su evidencia** de la decisión de Martín.
4. **Exportar JSON**.

**Qué decir (es el diferencial, decilo despacio):**

> «Este es el aporte central. Para cualquier decisión, ATLAS reconstruye qué tenía a la vista quien decidió: las versiones exactas, los valores validados con su fuente y las advertencias de ese momento. Si mañana se corrige un documento, esta evidencia no cambia, porque está atada al ciclo y a sus versiones. Y se puede exportar.»

### 3.10 Opcional: corrección con versión nueva (Laura, 3 minutos)

Hacelo solo si hay tiempo. Si no, mostrá el trámite «historia completa» (paso 4.1).

**Qué hacer:**
1. Ventana de **Laura**, trámite en vivo (en Observado) → **Documentos y datos** → cargá `3_Orden_de_compra_corregida_O-v2.pdf`.
2. Cuando quede «Procesado», aparece «Posible versión nueva de «Orden de compra»» → **Incorporar como versión nueva**. El trámite vuelve a Borrador.
3. Validá la orden v2 (los mismos valores de la O-v1, pero con fecha **15/09/2026**).
4. **Vínculos y controles**: R3 pasa a **Cumple**.

**Qué decir:**

> «La orden corregida comparte el número OC-2026-0042, y el sistema sugiere que es una versión nueva, no un documento distinto. La responsable lo confirma. La versión anterior no se borra: queda en el historial. Las decisiones del ciclo anterior no se trasladan; hace falta un ciclo nuevo.»

---

## 4. Cierre de la historia (3 minutos)

### 4.1 El trámite cerrado

**Qué hacer:** ventana de **Laura** → «Servicio de mantenimiento de laboratorio (historia completa)».
1. **Resumen**: estado **Cerrado** y panel «Firma digital simulada» (versión firmada, firmante Sofía Herrera, referencia de integridad SHA-256).
2. **Documentos y datos**: la orden tiene v2 vigente.
3. **Historial** → filtro «Revisión y decisiones»: ciclo 1 observado, ciclo 2 aprobado y firma.

**Qué decir:**

> «Esta es la historia completa: después de la observación, la orden corregida entró como versión nueva, el segundo ciclo se aprobó y Sofía, que tiene autorización de cierre, aplicó la firma. Es una firma simulada: no tiene validez legal y está declarado así. Es una referencia de integridad sobre la versión del contrato aprobada en ese ciclo. Nada se borra: no existen operaciones para eliminar trámites, versiones ni eventos.»

### 4.2 El cancelado y la administración

1. «Mantenimiento de equipos (cancelado)»: estado **Cancelado** y «Motivo de la cancelación».
2. Ventana de **Administración ATLAS** → **Administración** → «Estado general» (trámites, tareas y procesamiento), «Plantillas de flujo» y «Cuentas».

**Qué decir:**

> «El administrador coordina sin acceso al contenido documental: ve el estado, asigna tareas y administra las plantillas y las cuentas, pero no lee los documentos.»

### 4.3 Frase de cierre

> «En resumen: la IA acelera la carga, las personas validan y deciden, las reglas explican las inconsistencias, y cada decisión queda con su evidencia reconstruible. Corre en AWS con servicios administrados, y los registros técnicos nunca contienen el contenido de los documentos.»

---

## 5. Planes B

| Problema | Qué hacer |
|---|---|
| El procesamiento tarda o falla en vivo | Pasá al trámite «Servicio de mantenimiento de laboratorio» (**Observado**): ya tiene A–D hechos. Mostrá sus pestañas y la evidencia de la decisión desde **Revisión** → **Evidencia de la decisión** |
| Falta el trámite en vivo | Con Laura, **Trámites** → nuevo trámite → cargá `0_Contrato_C-v1_(respaldo).pdf` al principio de la apertura y seguí desde 3.1 |
| La consulta tarda | Esperá hasta 30 s; si falla, mostrá «Tus consultas» del trámite **Observado** o seguí y volvé después |
| «ATLAS está en mantenimiento» | La API no está en `active`: el operador repite el paso 2.7 de la guía |
| Una sesión del navegador venció | **Cerrar sesión** e ingresar de nuevo con esa cuenta |
| No aparece la tarea en «Mis tareas» | Con **Administración**, «Tareas sin asignar» → «Asignar a» la persona |

## 6. Recorte de 10 minutos

Apertura (1 min) → 3.2 solo clasificación y vigencia con su página (2 min) → 3.3 solo la pregunta de vigencia (1 min) → en el trámite **Observado**: **Vínculos y controles** con R3 (2 min) → su **Evidencia de la decisión** (3 min) → firma del trámite cerrado y cierre (1 min).

## 7. Preguntas probables

| Pregunta | Respuesta corta |
|---|---|
| ¿Y si la IA se equivoca? | Nunca se usa un valor sin validar: lo confirma o corrige una persona, y queda registrado lo sugerido y lo validado. La calidad de la IA se mide aparte, en §6.3.1, con un corpus sintético de 50 documentos |
| ¿La IA puede aprobar? | No. No aprueba, no observa y no cambia estados: solo sugiere datos y responde consultas con cita |
| ¿La firma es legal? | No: es una firma **simulada**, con una referencia de integridad. Integrar una firma digital con validez legal queda fuera del alcance |
| ¿Se puede borrar algo? | No existen operaciones para borrar trámites, versiones ni eventos de auditoría (RNF-04, RN-10) |
| ¿Dónde están los datos? | En AWS, us-east-1: S3 privado con cifrado, RDS PostgreSQL cifrada, Textract y Bedrock. Los registros solo contienen identificadores |
| ¿Por qué documentos sintéticos? | Por confidencialidad. La validación con documentos reales es un procedimiento aparte del equipo (§6.4) |
| ¿Qué pasa si cambia un documento después de aprobar? | La versión nueva desplaza el ciclo en curso y exige uno nuevo; la evidencia de las decisiones anteriores no cambia (RN-12) |
