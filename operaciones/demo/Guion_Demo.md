# Guion de la demo de ATLAS

Para presentar ATLAS en vivo sobre la sesión AWS levantada con la [guía de la sección 6](../aws/Guia_Sesion_Seccion6.md) y sembrada con `sembrar_demo`. Datos **sintéticos** del oráculo PD-07 v2. Duración: 20–25 minutos; recorte de 10 minutos en §6. Los **dos videos de 5 minutos con la historia SurDelta** están en §7 (DO-2026-11-09-DEMO-SURDELTA).

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

## 7. Videos SurDelta (2 × 5 minutos)

Historia: SurDelta Componentes S.R.L. recibe una factura de mantenimiento **ARS 1.200.000 más cara** que la orden de compra (R4). Martín la observa, la factura corregida entra como **versión nueva** y el trámite se cierra con la evidencia de cada decisión. La OC está fechada antes de la vigencia (R3): Martín la acepta con la advertencia a la vista. Todo es ficticio.

### 7.1 Preparación

- Semilla: `python -m atlas.herramientas.sembrar_demo --escenario surdelta …` (mismos argumentos que la semilla PD-07, manifiesto nuevo). Deja cuatro trámites: «Mantenimiento integral de planta (historia completa)» Cerrado, «Compra de equipos para el área comercial» Observado por R1, «Renovación de soporte informático» Pendiente de aprobación y «Contratación de limpieza» Cancelado. No admite `--reanudar`.
- Archivos de la grabación, en `corpus/surdelta/`: `SD-C1_Contrato_Mantenimiento_Planta.pdf`, `SD-O1_Orden_Compra_OC-2026-118.pdf`, `SD-F1_Factura_0004-00001248.pdf` y `SD-F2_Factura_0004-00001263.pdf`.
- Las esperas del procesamiento se cortan en la edición. Si algo falla, se graba sobre el trámite de historia completa y se dice.

| Campo | Contrato (SD-C1) | Orden (SD-O1) | Factura v1 (SD-F1) | Factura v2 (SD-F2) |
|---|---|---|---|---|
| Número | — | OC-2026-118 | 0004-00001248 | 0004-00001263 |
| Fecha | Celebración 15/09/2026 | **25/09/2026** | 31/10/2026 | 05/11/2026 |
| Contraparte / proveedor / emisor | Andes Sistemas S.A. | Andes Sistemas S.A. | Andes Sistemas S.A. | Andes Sistemas S.A. |
| CUIT | 30-96472518-3 | 30-96472518-3 | 30-96472518-3 | 30-96472518-3 |
| Vigencia | 01/10/2026 a 30/09/2027 (página 2) | — | — | — |
| Importe | 96.000.000,00 | 8.000.000,00 | **9.200.000,00** | 8.000.000,00 |
| Moneda | ARS | ARS | ARS | ARS |

### 7.1 bis Repetir la demo desde el estado recién sembrado (temporal)

Una vez, después de la semilla, se guarda una foto de la base; cada vez que se quiere volver a empezar, se restablece en segundos (DO-2026-11-09-ESTADOS-DEMO). Lo ejecuta el operador. Los PDF de S3 no se tocan y las cuentas de Cognito siguen iguales.

```bash
FN=$(terraform -chdir=infra/terraform/demo output -raw funcion_operaciones)
BUCKET=$(terraform -chdir=infra/terraform/persistent output -raw bucket_documentos)
BASE=$(aws lambda get-function-configuration --function-name "$FN" \
  --query 'Environment.Variables.ATLAS_BD_NOMBRE' --output text)
modo() { echo "{\"estado\":\"$1\"}" | aws s3 cp - "s3://$BUCKET/control/mantenimiento.json" --content-type application/json; }
foto() {  # foto guardar_estado semilla | foto restablecer_estado semilla
  aws lambda invoke --function-name "$FN" --cli-read-timeout 320 --cli-binary-format raw-in-base64-out \
    --payload "{\"accion\":\"$1\",\"nombre\":\"$2\",\"confirmar\":\"$BASE\"}" /dev/stdout; echo
}

# Una sola vez, con la semilla terminada:
modo offline && sleep 20 && foto guardar_estado semilla && modo active

# Cada vez que se quiere volver a la cartera recién sembrada:
modo offline && sleep 20 && foto restablecer_estado semilla && modo active
```

- Rechaza si la operación no está en `offline`, si queda algún procesamiento en curso (`operacion_no_drenada`: esperar y repetir) o si la confirmación no es el nombre de la base.
- Después de restablecer, recargar la página en el navegador. Si se aplica una migración nueva, la foto queda inválida (`estado_incompatible_con_el_esquema`): volver a sembrar y guardar.

### 7.2 Video 2: la factura que no cierra

1. **Contexto (20 s):** «SurDelta fabrica componentes industriales. Llegó la factura de octubre del mantenimiento de planta; antes de pagarla, Laura arma el expediente».
2. **Laura** crea «Mantenimiento integral de planta» y carga contrato, orden y factura v1. Corte. Los incorpora como documento nuevo.
3. **Validación:** en el contrato, **Ver en el documento** de *Vigencia hasta* (página 2); confirma el resto. Valida la orden y la factura.
4. **Vínculos y controles:** confirma los dos vínculos sugeridos (mismo CUIT). R1 y R2 cumplen; **R4 advierte que la factura supera la orden en 1.200.000**; R3 advierte la fecha de la orden.
   > «Si nadie lo veía, SurDelta pagaba 1,2 millones de más. En un mes, con un solo proveedor.»
5. **Consulta:** «¿El contrato permite facturar trabajos adicionales sin autorización?» → cláusula 5, página 2.

### 7.3 Video 3: la decisión y su evidencia

1. **Laura** envía a validación y confirma el flujo (Revisión legal: Martín; Aprobación final: Sofía).
2. **Martín** → **Mis tareas** → «Revisión legal» → **Observar**, con el motivo de `MOTIVO_OBSERVACION_SURDELTA` de la semilla: la factura supera la OC por 40 horas sin autorización (cláusula 5); la fecha de la orden es aceptable.
3. **Laura** carga la factura v2. Corte. El sistema la sugiere como **versión nueva** de la v1 (mismo CUIT del emisor) → la confirma y la valida. R4 pasa a cumplir; R3 sigue advirtiendo.
   > «No se pisa el archivo: la v1 queda en el historial y sus validaciones no se heredan.»
4. Nuevo ciclo: Martín aprueba con R3 a la vista; Sofía aprueba y aplica la **firma simulada** sobre el contrato → **Cerrado**.
5. **Seis meses después:** **Historial** y **Evidencia de la decisión**: versiones consideradas, observación con su motivo y controles que se veían al aprobar.
6. **Cartera (20 s):** «Compra de equipos» (la factura llegó con el CUIT de otra empresa: R1 advierte, sin vínculo sugerido, observada), «Renovación de soporte» y «Contratación de limpieza» cancelada.
   > «El producto no es el caso de mantenimiento: es poder reconstruir cualquier decisión documental.»
