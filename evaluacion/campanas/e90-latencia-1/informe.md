# Campaña API e90-latencia-1 (oficial)

## Latencia de la consulta (IA-M08: mediana ≤ 5 s, p95 ≤ 10 s)

Línea de base de red (`GET /salud`): mediana 0.55 s, p95 0.95 s.

| Modelo | n | Mediana | p95 | Máximo | Errores | Arranques en frío | Perfil distinto | Resultado |
|---|---|---|---|---|---|---|---|---|
| haiku | 90 | 2.17 s | 3.58 s | 6.69 s | 0 | 1 | 0 | Cumple |
| sonnet | 90 | 2.25 s | 5.20 s | 8.88 s | 0 | 2 | 0 | Cumple |

## Concurrencia (§6.3.4)

| Operación y nivel | n | Mediana | p95 | Errores |
|---|---|---|---|---|
| consulta_1 | 30 | 2.32 s | 3.07 s | 0 |
| lectura_1 | 30 | 0.59 s | 0.97 s | 0 |
| consulta_5 | 30 | 2.23 s | 7.93 s | 0 |
| lectura_5 | 30 | 0.57 s | 0.61 s | 0 |
| consulta_10 | 30 | 2.11 s | 7.76 s | 0 |
| lectura_10 | 30 | 0.54 s | 0.59 s | 0 |
| trabajos_1 | 1 | 16.75 s | 16.75 s | 0 |
| trabajos_5 | 5 | 17.75 s | 88.94 s | 0 |
| trabajos_10 | 10 | 289.11 s | 889.76 s | 0 |
