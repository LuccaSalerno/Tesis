# Especificación BDD — no son pruebas implementadas

Los archivos `.feature` recogen el comportamiento **requerido**, no reflejan ejecuciones satisfactorias. **Runner:** `pytest-bdd`, aprobado por el equipo el 22/10/2026 (DO-2026-10-22-BDD). Las definiciones de pasos están en `backend/tests/aceptacion/` y se ejecutan contra la API real con pytest. Cada escenario se implementa cuando existen las capacidades que verifica. Los escenarios EVD-01 se recolectan pero se **omiten con un motivo explícito** hasta que existan ciclos de revisión, tareas y decisiones (hitos 1.7–1.8); la salida de pytest los informa como omitidos, nunca como aprobados.

No se acepta dar por cubierto EVD-01 solo por estos cuatro escenarios declarativos: deben ejecutarse, probar sus invariantes por API, verificar V1–V11, pruebas negativas y carreras previstas por el contrato (incluida PD-08), y vincularse a evidencia real. Las pruebas de UI y RNF-07 se implementan aparte y no sustituyen API-AUTO.

Referencia: [correspondencia y decisión BDD](../../docs/aceptacion/Correspondencia_EVD01_BDD_Tesis.md).
