# Especificación BDD — no son pruebas implementadas

Los archivos `.feature` recogen el comportamiento **requerido**, no reflejan ejecuciones satisfactorias. Pendiente: elegir y registrar en `docs/decisiones/Decisiones_Delegadas.md` o solicitar aprobación para un runner BDD compatible con pytest; desarrollar step definitions, API real, fixtures/oráculos congelados, aislamiento entre casos y reportes. `pytest-bdd` es una propuesta de integración, no una dependencia actualmente instalada.

No se acepta dar por cubierto EVD-01 solo por estos cuatro escenarios declarativos: deben ejecutarse, probar sus invariantes por API, verificar V1–V11, pruebas negativas y carreras previstas por el contrato (incluida PD-08), y vincularse a evidencia real. Las pruebas de UI y RNF-07 se implementan aparte y no sustituyen API-AUTO.

Referencia: [correspondencia y decisión BDD](../../docs/aceptacion/Correspondencia_EVD01_BDD_Tesis.md).
