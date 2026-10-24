# Análisis del criterio «espera sin sobreasignación» (e90-confiabilidad-1)

**Resultado registrado:** 5 de 6 criterios; `espera_sin_sobreasignacion = false` con
`max_en_curso_observado = 4` y límite 3. El resultado no se modifica (AGENTS.md §2.9).

**Cómo lo calcula el ejecutor:** el máximo entre (a) la suma de los estados devueltos al
confirmar cada una de las 6 cargas, enviadas en paralelo, y (b) los sondeos cada 30 s. Los
estados de (a) se toman en instantes distintos: un trabajo que ya terminó cuenta igual como
«en curso» si estaba pendiente cuando se confirmó su carga.

**Lo que muestran los tiempos reales** (`ejecuciones_step_functions.txt`, listado de Step
Functions del 24/10, hora -03:00; el trabajo N corresponde al archivo N del registro):

| Trabajo | Inicio | Fin |
|---|---|---|
| 71 | 14:12:07,214 | 14:12:11,970 |
| 72 | 14:12:10,880 | 14:12:15,393 |
| 73 | 14:12:11,003 | 14:12:19,300 |
| 75 | 14:12:12,740 | 14:12:17,151 |
| 74 | 14:16:15,602 | 14:16:20,263 |
| 76 | 14:16:15,652 | 14:16:20,501 |

El trabajo 75 empezó después de que terminara el 71: la admisión le asignó el cupo liberado.
El máximo de ejecuciones simultáneas fue **3**, igual al límite; los sondeos tampoco vieron
más de 3. 74 y 76 quedaron «En espera» y los admitió el reconciliador en su ciclo siguiente.

**Conclusión:** el incumplimiento proviene del método de medición (suma de estados no
simultáneos), no de una sobreasignación de la admisión. Se informa el resultado tal cual y
este análisis como evidencia complementaria.
