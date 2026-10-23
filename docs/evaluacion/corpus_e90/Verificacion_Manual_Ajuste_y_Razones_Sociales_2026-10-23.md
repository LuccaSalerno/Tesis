# Consulta manual de los CUIT de ajuste y de las razones sociales — reporte del equipo

Requisitos: P2 y P3 de DO-2026-10-22-CORPUS-REVISION (verificaciones manuales antes de congelar). Fuente de evidencia: resultados de consultas manuales informados por el equipo en el chat el **23/10/2026**; el agente registra la declaración recibida. El informe no indica la fecha exacta de cada consulta: se registra la fecha del informe. No se aportaron capturas ni constancias, y no se fabrican verificaciones independientes.

## CUIT de ajuste (ARCA)

| CUIT consultado, sin guiones | CUIT del registro | Resultado informado |
|---|---|---|
| 30986410143 | 30-98641014-3 | No existe |
| 30986410151 | 30-98641015-1 | No existe |
| 30986410178 | 30-98641017-8 | No existe |
| 30986410186 | 30-98641018-6 | No existe |
| 30986410194 | 30-98641019-4 | No existe |
| 30986410208 | 30-98641020-8 | No existe |

Los seis coinciden exactamente con los CUIT de ajuste de `oraculos/e90/cuit_candidatos.json`. Los doce de medición ya estaban registrados como «No existe» el 22/10/2026 ([registro anterior](Verificacion_Manual_CUIT_ARCA_2026-10-22.md)). Con esto, los 18 CUIT del corpus tienen consulta informada.

## Razones sociales

Las 18 denominaciones de [Verificaciones_Pendientes_V2.md](Verificaciones_Pendientes_V2.md) se consultaron manualmente y el equipo informó **«Sin coincidencia observada»** para todas.

## Efectos

- No se reemplaza ningún CUIT ni ninguna razón social, por lo que no hace falta regenerar: los 65 documentos de la candidata v3 conservan sus bytes y hashes.
- `cuit_candidatos.json` registra la consulta de los seis CUIT de ajuste, con esta evidencia. `preparar.py` todavía prepara esos seis como pendientes: si el corpus se regenera desde cero con los mismos números, hay que trasladar esta evidencia, sin simular una nueva consulta.
- Ninguna consulta acredita la inexistencia absoluta ni impide una asignación futura.
- Con esto quedan completas las verificaciones manuales previas a la congelación. Faltan la revisión de ambos autores de la v3 y la congelación.
