# Sincronización documental ATLAS E90 — 22/10/2026

## Qué cambió

- Se incorporó íntegramente `main(8).pdf` a `docs/tesis/main.pdf`. SHA-256: `ceab527c15fa72fa8b6dfc5711cf62db8cb2e8a06e1943c6d3f67d8cab77b618`.
- Se actualizó el Markdown de 6.0–6.3 con las modificaciones académicas observables en ese PDF: relaciones RN-09/RN-12/RN-13; versión incorporada confirmada; matriz de permisos de Tabla 3.II; criterios previos de selección; latencia de 90 solicitudes; eliminación de una frase redundante sobre repeticiones de embeddings; rechazo de entradas inválidas en RNF-06; precisión de la asignación de RNF.
- Se corrigieron los avisos de `AGENTS.md`, `README_PRIMERO.md`, `INICIO_CODEx_E90.md`, `docs/aceptacion/Correspondencia_EVD01_BDD_Tesis.md` y el README de la tesis para que no indiquen que el capítulo 6 sigue pendiente de recompilar.

## Qué NO cambió

- Ningún RF, RN, RNF, umbral, modelo de datos ni contrato EVD-01 se modificó; este sigue correspondiendo a la «Verificación de la cadena de evidencia documental» en 6.2.
- BDD/Gherkin sigue previsto para aceptación; los archivos `.feature` son especificaciones, no resultados.
- El corpus E90 sigue siendo **50 sintéticos de medición**, tres adversariales dentro, **10–15 sintéticos de ajuste** (15 propuestos, no aprobados ni generados en esta copia), 30 consultas RAG (24+6). El plan de 65 filas no es inventario real ni corpus congelado.
- Permanecen las restricciones de AWS manual, los contratos técnicos, el plan de implementación y el historial previo del repositorio.

## Compuertas reales

El ZIP actualizado es un paquete **documental listo para iniciar implementación local**. No incluye aplicación, infraestructura verificada, corpus E90 construido ni pruebas/mediciones ejecutadas. La validación operativa 6.4, los resultados 6.5 y el ajuste de 6.6 siguen pendientes de evidencia. El proyecto LaTeX fuente no está incluido en este paquete; el PDF es una copia compilada entregada por los autores.

La sustitución de la tesis también incluye revisiones editoriales fuera del capítulo 6, especialmente en §§2 y 5.4; no se trasladaron estas revisiones a la historia de decisiones técnicas. Ante una divergencia sustantiva al implementar, consultar al equipo en vez de resolverla silenciosamente.
