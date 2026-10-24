# Estado de la Sección 6 — qué está escrito, qué se midió y qué falta

**Fecha:** 23/10/2026. **Propósito:** punto de partida para completar el capítulo 6. Resume material existente; no agrega resultados ni reemplaza los contratos de aceptación, el [mapa de evidencias](Mapa_Evidencias_Pendientes_Capitulo_6.md) ni el [protocolo E90](Protocolo_E90_Corpus_y_Validacion.md).

## 1. Texto ya redactado

Fuentes: `docs/tesis/main.pdf` y `docs/tesis/ATLAS_Seccion_6_Version_Final_6_0_a_6_3.md`.

| Sección | Contenido |
|---|---|
| 6.1 Estrategia | Distingue verificación funcional, cobertura, evaluación de IA y confiabilidad/seguridad/rendimiento; el escenario representativo complementa, no reemplaza |
| 6.2 Funcionales | BDD Gherkin por 5 grupos de RF; cadena de evidencia documental (4 recorridos EVD-A/B/C/N12); cobertura ≥ 85 % |
| 6.3.1 IA | 50 documentos sintéticos (10 por tipo), ajuste separado de 10–15, 3 adversariales; 30 preguntas RAG (24 respondibles + 6 sin evidencia); Haiku vs. Sonnet y Cohere vs. Titan con 3 repeticiones y reglas de sustitución previas |
| 6.3.2 Confiabilidad | Demoras, reintentos, errores definitivos, idempotencia, huérfanos, reconciliador |
| 6.3.3 Seguridad | Matriz Tabla 3.II, acceso directo por ID, consulta cruzada, auditoría inmutable, adversarial, marcadores en logs |
| 6.3.4 Rendimiento | Concurrencia 1/5/10, mediana y p95, sin extrapolar |
| 6.4 Escenario representativo | **Vacía en el PDF** |
| 6.5 Resultados y discusión | **Vacía en el PDF** |
| 6.6 Limitaciones | Dos párrafos ya escritos: corpus sintético más regular que el real; 50 documentos no permiten generalizar |

## 2. Resultados reales ya medidos

### Campaña oficial `e90-oficial-1` (§6.3.1)

Evidencia: `evaluacion/campanas/e90-oficial-1/` (`informe.md`, `metricas.json`). Corpus v3 congelado, 3 repeticiones, commit `b872e0c`.

| Indicador | Umbral | Haiku 4.5 | Sonnet 4.6 |
|---|---|---|---|
| F1 macro de clasificación | ≥ 0,90 | 1,000 — Cumple | 1,000 — Cumple |
| Recall mínimo por categoría | ≥ 0,80 | 1,000 — Cumple | 1,000 — Cumple |
| F1 de extracción, tipo más bajo (contrato) | ≥ 0,85 | 0,884 — Cumple | 0,852 — Cumple |
| F1 macro de extracción (para sustitución) | — | 0,950 | 0,936 |
| **Exactitud crítica, campo más bajo** | ≥ 0,90 | **0,778 — No cumple** | **0,778 — No cumple** |
| Valores inventados | ≤ 5 % | 0 % — Cumple | 0 % — Cumple |
| Procedencia PDF (página correcta) | ≥ 0,90 | 1,000 (212/212) — Cumple | 1,000 — Cumple |
| Procedencia DOCX (sin umbral) | — | 0,785 | 0,989 |
| Adversariales con alteraciones | 0 | 0/3 — Cumple | 0/3 — Cumple |

- **Incumplimiento:** el campo **fecha** (35 de 45 correctas en ambos modelos). Importe, número y CUIT de la contraparte entre 0,95 y 1,00.
- **Por formato (Haiku):** DOCX y PDF fotografiado F1 1,00; PDF digital 0,94; PDF escaneado 0,84.
- **Recuperación (IA-M05):** Cohere Recall@5 0,976; Titan 0,969; ambos cumplen; MRR 0,678 en ambos.
- **Sustitución:** se conservan Haiku 4.5 y Cohere (ninguna alternativa mejora 5 puntos); la decisión final es del equipo.
- Errores técnicos: 0 en cada repetición.

### Nivel B con servicios reales (sesión e90-2026-10-24)

Evidencia: `evaluacion/campanas/nivel-b/`. C-v1 (10 páginas): tipo correcto y 7 de 7 campos correctos en la página esperada, 25,7 s. RAG: la consulta de vigencia cita la página 6; la consulta sin evidencia se abstiene sin citar. Verificación puntual, **no es métrica de §6.3**.

### Pruebas locales y de CI (insumo para 6.2)

- 677 pruebas aprobadas, 4 omitidas; cobertura total 98 %, los 73 módulos ≥ 90 % (ver `docs/plan/Estado_Implementacion.md`).
- Los cuatro recorridos EVD-01 se ejecutan en la CI, pero **no acreditan EVD-01** sin oráculo congelado ni evidencia conservada.
- §6.3.2 y §6.3.3: nivel A ejecutado en la CI contra la aplicación local, sin fallas. Nivel B (AWS) sin ejecutar.

## 3. Pendiente para completar el capítulo

1. **Respuestas RAG (IA-M06):** las planillas `planillas/autor_a.csv` y `autor_b.csv` tienen 0 de 65 filas calificadas. Sin ellas no hay corrección (≥ 80 %), respaldo (≥ 90 %), abstención (≥ 80 %) ni acuerdo entre autores.
2. **Latencia IA-M08** (90 solicitudes por modelo) y **rendimiento §6.3.4**: se miden contra la API desplegada; sin ejecutar.
3. **Nivel B de §6.3.2 y §6.3.3** en AWS.
4. **6.2:** matriz RF/RN → escenario → estado; capturas de RNF-07 en la interfaz.
5. **6.4:** validación operativa del equipo, separada, autorizada y fuera del repositorio; nada registrado.
6. **6.5:** tabla por dimensión (criterio / medido / cumple / evidencia / interpretación), con el incumplimiento de fecha, la selección de modelos y las desviaciones.
7. **6.6:** agregar limitaciones observadas (OCR en escaneados, selección de modelos sobre el mismo corpus, ataques acotados, carga ensayada).
