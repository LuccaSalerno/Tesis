# Recálculo de las métricas de e90-oficial-1 con el normalizador corregido

**Qué es:** las **mismas salidas de los modelos** registradas en la campaña oficial
(`../clasificacion_extraccion.jsonl`, `../respuestas.jsonl`) puntuadas de nuevo después de
corregir el normalizador de fechas con año de dos dígitos (DIF-124, commit `538ccab`). No se
volvió a llamar a Textract ni a los modelos; la métrica normaliza al comparar, por eso el
recálculo es determinista. En la campaña oficial las tres repeticiones de cada modelo dieron
salidas idénticas en extracción.

**Qué no es:** una medición nueva ni un reemplazo. **El resultado oficial de la campaña sigue
siendo el de `../informe.md`** (exactitud crítica de fecha 0,778, no cumple).

**Resultado:** con el normalizador corregido, Haiku 4.5 alcanza exactitud crítica mínima 1,000
(fecha 45/45), F1 de extracción por tipo mínimo 1,000 y F1 macro 1,000; Sonnet 4.6, exactitud
crítica mínima 0,950 (número 38/40; fecha 45/45), F1 mínimo 0,964 y F1 macro 0,987. El resto de
los indicadores no cambia. La regla de sustitución sigue conservando Haiku.

**Limitación:** el defecto se identificó al analizar los errores de la medición sobre el mismo
corpus; no hay un conjunto independiente que confirme el resultado posterior a la corrección.
