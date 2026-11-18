# Cierre de la sesión e90-2026-10-24 (antes del retiro)

**Código desplegado:** `fd6b3ef`. **Cuenta:** 014574285566, us-east-1.

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

## Retiro selectivo y residuos (24/10/2026)

Destruidas, con plan revisado y confirmación del operador: `demo` (49 recursos), `runtime` (8;
el RDS Proxy tardó 22 min), `persistent` (protecciones quitadas con `retiro_autorizado`, bucket
de documentos vaciado: 563 versiones; luego 41 recursos, RDS sin snapshot final) y `evaluacion`
(6; bucket de copias de §6.3.1).

Verificación de residuos: sin instancias, proxies ni snapshots manuales de RDS; sin endpoints
ni VPC etiquetadas `proyecto=atlas`; sin funciones Lambda ni grupos de registros
`/aws/lambda/atlas*`; sin grupos de usuarios de Cognito; sin secretos (incluidos los en
eliminación programada). Quedan solo los buckets `atlas-estado-terraform-5566` (`bootstrap`,
estado remoto, intocable) y `atlas-web-5566` con su distribución de CloudFront (`web`, se
conserva entre sesiones). Revisar Billing en los días siguientes.

## Retiro total (DO-2026-10-24-RETIRO-TOTAL)

Después del cierre, el operador decidió bajar también `web` (8 recursos: CloudFront
`E3F2NWTWLS36DR` y el bucket `atlas-web-5566`) y `bootstrap` (bucket de estado vaciado: 102
versiones de `tfstate` y `tflock` sin recursos gestionados; luego 7 recursos, con
`prevent_destroy` desactivado solo para ese retiro y restaurado en el código). Verificación final:
ningún bucket ni distribución de CloudFront en la cuenta 014574285566. Para la exposición final se
reconstruye todo desde la Parte 1 de la guía.
