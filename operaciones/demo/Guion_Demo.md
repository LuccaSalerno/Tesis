# Guion de la demo de ATLAS

Para presentar ATLAS en vivo sobre la sesión AWS levantada con la [guía de la sección 6](../aws/Guia_Sesion_Seccion6.md) y sembrada con `sembrar_demo`. Datos **sintéticos** del oráculo PD-07 v2. Duración: 20–25 minutos; recorte de 10 minutos en §6.

## 1. Antes de empezar (30 minutos antes)

**Dirección:** la URL de CloudFront de la raíz `web`, que cambia en cada reconstrucción.

| Usuario (Cognito) | Persona | Para qué |
|---|---|---|
| `atlas-responsable` | Laura Méndez | Cargar, validar, consultar, vincular, enviar a revisión |
| `atlas-revisor` | Martín Ríos | Paso «Revisión legal» |
| `atlas-aprobador` | Sofía Herrera | Paso «Aprobación final» y firma |
| `atlas-admin` | Administración ATLAS | Estado general, plantillas, cuentas |

Las contraseñas son las del paso 2.6 de la guía; no se escriben en el repositorio.

- **Navegador:** cuatro perfiles o ventanas privadas, uno por cuenta, con la sesión iniciada y zoom al 110–125 %.
- **Archivos a mano:**

| Archivo | Qué es | Cuándo |
|---|---|---|
| [`O-v1_Orden_Compra.pdf`](../../corpus/O-v1_Orden_Compra.pdf) | Orden OC-2026-0042, emitida el **15/03/2027** (fuera de la vigencia) | 3.1 |
| [`F-v2_Factura.pdf`](../../corpus/F-v2_Factura.pdf) | Factura FC-A-0001-00000123 por $ 1.250.000,00 | 3.1 |
| [`O-v2_Orden_Compra.pdf`](../../corpus/O-v2_Orden_Compra.pdf) | La orden corregida, emitida el **15/09/2026** | 3.10, opcional |
| [`C-v1_Contrato_Mantenimiento_ATLAS.pdf`](../../corpus/C-v1_Contrato_Mantenimiento_ATLAS.pdf) | Contrato, ya cargado en el trámite en vivo | Solo si falta (§5) |

**Control previo**, con `atlas-responsable`:

- En **Trámites** están los cuatro de la semilla: «(en vivo)» en Borrador, el de respaldo en Observado, «(historia completa)» en Cerrado y «Mantenimiento de equipos (cancelado)».
- En el trámite en vivo, el contrato figura como «Contrato de mantenimiento», v1, con «Validar datos».
- `curl -s "${URL}salud"` responde `"operacion": "active"`.

## 2. Apertura (2 minutos)

Pantalla de ingreso, sin datos.

> «La contratación de un servicio deja un contrato, órdenes y facturas que hoy se controlan a mano, y después cuesta reconstruir por qué se aprobó. ATLAS extrae los datos con IA, pero **una persona los valida siempre**; controla la consistencia con reglas explícitas sobre esos valores; y deja **evidencia reconstruible** de cada decisión. Todo lo que van a ver es sintético.»

## 3. Recorrido en vivo

### 3.1 Carga anticipada (Laura, 2 minutos)

Trámite «(en vivo)» → **Documentos y datos** → «Cargar un archivo»: la orden O-v1 y la factura F-v2. Cada una tarda unos minutos en procesarse, por eso se cargan ahora.

> «El archivo va directo a un almacenamiento privado y el procesamiento sigue en segundo plano. Mientras tanto, validamos el contrato.»

### 3.2 Punto A: validación humana con fuente (Laura, 5 minutos)

1. «Contrato de mantenimiento» → **Validar datos** → clasificación «Contrato» → **Confirmar sugerencia**.
2. En **Vigencia hasta**, **Ver en el documento**: abre la **página 6**.
3. Confirmá los campos. Si una sugerencia no coincide, usá **Corregir**, en el mismo formato que muestra, y señalá que se ven el valor sugerido y el validado.

| Campo | Valor | Página |
|---|---|---|
| Contraparte | Servicios Integrales del Sur S.A. | 1 |
| CUIT de la contraparte | 30-96472518-3 | 1 |
| Fecha de celebración | 20/02/2026 | 1 |
| Vigencia desde | 01/03/2026 | 6 |
| Vigencia hasta | 28/02/2027 | 6 |
| Monto total | 1.250.000,00 | 5 |
| Moneda | ARS | 5 |

> «La IA sugiere y la persona valida. Cada sugerencia trae su página, y las reglas y decisiones usan solo lo que confirmó una persona.»

### 3.3 Punto B: consulta con cita y abstención (Laura, 3 minutos)

Pestaña **Consulta**:

1. **¿Hasta cuándo está vigente el contrato?** → 28/02/2027, con cita al contrato, v1, **página 6**.
2. **¿Cuál es el número de cuenta bancaria del proveedor?** → «No hay evidencia suficiente para responder».

> «Busca solo en los documentos vigentes del trámite y responde citando. Sin evidencia, se abstiene en lugar de inventar.»

### 3.4 Incorporar la orden y la factura (Laura, 3 minutos)

**Documentos y datos** → **Cargas**: con los dos en «Procesado», nombralos **Orden de compra** y **Factura** → **Incorporar como documento nuevo**. Después, validá cada uno.

| Campo | Orden de compra (O-v1) | Factura (F-v2) |
|---|---|---|
| Número | OC-2026-0042 | FC-A-0001-00000123 |
| Fecha | **15/03/2027** | 30/09/2026 |
| Proveedor / emisor | Servicios Integrales del Sur S.A. | Servicios Integrales del Sur S.A. |
| CUIT | 30-96472518-3 | 30-96472518-3 |
| Importe total | 1.250.000,00 | 1.250.000,00 |
| Moneda | ARS | ARS |

> «Un archivo cargado no produce efectos hasta que la responsable lo incorpora.»

Si van atrasados, detenete solo en la **fecha de la orden**, clave del punto C. Si el procesamiento sigue en curso, usá **Registrar valor**; si figura «Falla técnica», el botón de reintento.

### 3.5 Punto C: vínculos y reglas (Laura, 3 minutos)

1. **Vínculos y controles** → **Confirmar** los dos vínculos sugeridos, orden ↔ contrato y factura ↔ orden. Si no aparecen, crealos con la justificación «Comparten el CUIT validado del proveedor».
2. En **Controles de consistencia**, tres cumplen y una advierte:

| Control | Resultado |
|---|---|
| CUIT del emisor de la factura = CUIT del proveedor de la orden | Cumple |
| CUIT del proveedor de la orden = CUIT de la contraparte del contrato | Cumple |
| **Fecha de la orden dentro de la vigencia del contrato** | **Advertencia:** 15/03/2027 es posterior al 28/02/2027 |
| Total de la factura ≤ total de la orden, con la misma moneda | Cumple |

> «Los vínculos sugeridos no rigen hasta confirmarse. La advertencia no bloquea ni cambia el estado: decide una persona.»

### 3.6 Enviar a revisión (Laura, 1 minuto)

**Resumen** → **Enviar a validación**; **Revisión** → **Confirmar el flujo y enviar a aprobación** (Revisión legal: Martín Ríos; Aprobación final: Sofía Herrera). Si faltan datos, resolvelos en **Documentos y datos**, con «No consta / no aplica» si no están en el documento.

> «Cada confirmación abre un ciclo de revisión con un conjunto exacto de versiones.»

### 3.7 Punto D: el revisor aprueba (Martín, 2 minutos)

**Mis tareas** → «Revisión legal»: mostrá el contexto, las versiones y la advertencia de vigencia → **Aprobar**.

### 3.8 Punto D: la aprobadora observa (Sofía, 2 minutos)

**Mis tareas** → «Aprobación final» → **Observar**, con este motivo → **Registrar observación**:

> La fecha de emisión de la orden de compra (15/03/2027) está fuera de la vigencia del contrato (01/03/2026 a 28/02/2027). Corregir la orden antes de aprobar.

> «El motivo es obligatorio. La IA nunca aprobó ni observó nada: solo sugirió datos.»

### 3.9 Punto D: la evidencia de la decisión (Sofía, 3 minutos)

**Evidencia de la decisión**: recorré versiones consideradas, datos validados al decidir y controles considerados; abrí la decisión de Martín desde «Cadena de la evidencia» → **Exportar JSON**.

> «Este es el aporte central. Para cualquier decisión, ATLAS reconstruye qué tenía a la vista quien decidió. Si mañana se corrige un documento, esta evidencia no cambia.»

### 3.10 Opcional: versión nueva (Laura, 3 minutos)

Cargá la orden O-v2 → **Incorporar como versión nueva** (el trámite vuelve a Borrador) → validá con fecha **15/09/2026** → el control de vigencia pasa a **Cumple**.

> «La versión anterior queda en el historial y las decisiones del ciclo anterior no se trasladan.»

## 4. Cierre (3 minutos)

1. **Historia completa** (Laura): estado **Cerrado**, «Firma digital simulada», orden en v2 e **Historial** → «Revisión y decisiones».
2. **Cancelado:** estado y «Motivo de la cancelación».
3. **Administración:** «Estado general», «Plantillas de flujo» y «Cuentas», sin acceso al contenido documental.

> «La firma es simulada, sin validez legal, y está declarado así. En resumen: la IA acelera la carga, las personas validan y deciden, las reglas explican las inconsistencias, y cada decisión queda con su evidencia reconstruible.»

## 5. Planes B

| Problema | Qué hacer |
|---|---|
| El procesamiento tarda o falla | Pasá al trámite en **Observado**, que ya tiene A–D: sus pestañas y **Revisión** → **Evidencia de la decisión** |
| Falta el trámite en vivo | Con Laura, creá un trámite y cargá el contrato C-v1 al empezar; seguí desde 3.1 |
| La consulta tarda | Esperá hasta 30 s; si falla, mostrá «Tus consultas» del trámite **Observado** |
| «ATLAS está en mantenimiento» | La API no está en `active`: el operador repite el paso 2.7 de la guía |
| Venció una sesión | **Cerrar sesión** e ingresar de nuevo |
| No aparece la tarea | Con **Administración**, «Tareas sin asignar» → «Asignar a» |

## 6. Recorte de 10 minutos

Apertura (1 min) → 3.2 solo clasificación y vigencia con su página (2 min) → 3.3 solo la pregunta de vigencia (1 min) → en el trámite **Observado**: **Vínculos y controles** con la advertencia de vigencia (2 min) → su **Evidencia de la decisión** (3 min) → firma del trámite cerrado y cierre (1 min).
