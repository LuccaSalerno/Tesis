# Cierre de la sesión e90-2026-10-24 (antes del retiro)

**Código desplegado:** `6232839`. **Cuenta:** 014574285566, us-east-1.

## Drenaje

`verificar_drenaje` (24/10/2026, después de 5 minutos en `draining`):

```json
{"urls_vigentes": 0, "cargas_pendientes": 32, "trabajos_abiertos": 0, "ejecuciones_activas": 0, "drenado": false}
```

Sin URLs vigentes, trabajos abiertos ni ejecuciones activas. Las 32 cargas pendientes son
archivos de medición procesados y no incorporados a propósito: §6.3.4 carga asincrónica
(1 + 5 + 10), §6.3.2 en las dos campañas (6 + 1 cada una) y el escenario de §6.3.3. El
operador decidió no descartarlas (son sintéticas y se pierden con el retiro) y seguir con la
exportación y el retiro.

## Evidencia exportada

`evidencia/` (71 archivos, índice con SHA-256 en `evidencia/indice.json`), por la API:

| Trámite | Estado | Contenido |
|---|---|---|
| observado-1 | Observado | Semilla: A–D, revisión legal aprobada, observación por R3 |
| en_vivo-2 | **Cerrado** | Recorrido completo hecho por las personas en la interfaz (demo y continuación): O-v1 y F-v2, observación por R3, O-v2 como versión nueva, ciclo 2 aprobado y firma simulada |
| reemplazado-3 | Cancelado | Primer intento del «historia completa», interrumpido por el token de Textract (DIF-122) |
| cerrado-4 | Cerrado | Semilla: historia completa con versión nueva por número y firma simulada |
| cancelado-5 | Cancelado | Semilla: cancelación con motivo |

`manifiesto_seed.json` es la copia del manifiesto de la semilla (`operaciones/sesiones/` no se
versiona); contiene identificadores y huellas, sin tokens. No acredita EVD-01.
