# Campaña e90-oficial-1 (oficial)

## Modelo generativo: haiku

| Criterio | Indicador | Umbral | Serie | Promedio | Desvío | Resultado |
|---|---|---|---|---|---|---|
| IA-M01 | F1 macro de clasificación | ≥ 0.90 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |
| IA-M01 | Recall mínimo por categoría | ≥ 0.80 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |
| IA-M02 | F1 de extracción, tipo más bajo | ≥ 0.85 | 0.884, 0.884, 0.884 | 0.884 | 0.000 | Cumple |
| IA-M02 | F1 macro de extracción (sustitución) | — | 0.950, 0.950, 0.950 | 0.950 | 0.000 | — |
| IA-M02 | Exactitud crítica, campo más bajo | ≥ 0.90 | 0.778, 0.778, 0.778 | 0.778 | 0.000 | No cumple |
| IA-M02 | Valores inventados | ≤ 0.05 | 0.000, 0.000, 0.000 | 0.000 | 0.000 | Cumple |
| IA-M03 | Procedencia PDF con página correcta | ≥ 0.90 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |
| IA-M06 | Respuestas correctas | ≥ 0.80 | 0.875, 0.875, 0.875 | 0.875 | 0.000 | Cumple |
| IA-M06 | Afirmaciones respaldadas | ≥ 0.90 | 0.949, 0.949, 0.949 | 0.949 | 0.000 | Cumple |
| IA-M06 | Abstenciones correctas | ≥ 0.80 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |

IA-M07 (última repetición): 0 de 3 documentos adversariales con alteraciones.
Errores técnicos por repetición: 0, 0, 0.

## Modelo generativo: sonnet

| Criterio | Indicador | Umbral | Serie | Promedio | Desvío | Resultado |
|---|---|---|---|---|---|---|
| IA-M01 | F1 macro de clasificación | ≥ 0.90 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |
| IA-M01 | Recall mínimo por categoría | ≥ 0.80 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |
| IA-M02 | F1 de extracción, tipo más bajo | ≥ 0.85 | 0.847, 0.861, 0.847 | 0.852 | 0.008 | Cumple |
| IA-M02 | F1 macro de extracción (sustitución) | — | 0.935, 0.938, 0.935 | 0.936 | 0.002 | — |
| IA-M02 | Exactitud crítica, campo más bajo | ≥ 0.90 | 0.778, 0.778, 0.778 | 0.778 | 0.000 | No cumple |
| IA-M02 | Valores inventados | ≤ 0.05 | 0.000, 0.000, 0.000 | 0.000 | 0.000 | Cumple |
| IA-M03 | Procedencia PDF con página correcta | ≥ 0.90 | 1.000, 1.000, 1.000 | 1.000 | 0.000 | Cumple |
| IA-M06 | Respuestas correctas | ≥ 0.80 | 0.958, 0.958, 0.958 | 0.958 | 0.000 | Cumple |
| IA-M06 | Afirmaciones respaldadas | ≥ 0.90 | 0.980, 0.980, 0.980 | 0.980 | 0.000 | Cumple |
| IA-M06 | Abstenciones correctas | ≥ 0.80 | 0.833, 0.833, 0.833 | 0.833 | 0.000 | Cumple |

IA-M07 (última repetición): 0 de 3 documentos adversariales con alteraciones.
Errores técnicos por repetición: 0, 0, 0.

## Recuperación (IA-M05)

| Embeddings | Recall@5 | MRR | Preguntas | Resultado |
|---|---|---|---|---|
| cohere | 0.976 | 0.678 | 24 | Cumple |
| titan | 0.969 | 0.678 | 24 | Cumple |

## Reglas de sustitución (sobre promedios; decide el equipo)

- **generativo:** se conserva — {'sustituye': False, 'criterios_recuperados': [], 'nuevos_incumplimientos': [], 'mejora_f1_macro_extraccion': -0.013274953516684729}
- **embeddings:** se conserva — {'sustituye': False, 'mejora_recall_at_5': -0.006944444444444531}

La latencia IA-M08 se mide contra la API desplegada (fase 2).
