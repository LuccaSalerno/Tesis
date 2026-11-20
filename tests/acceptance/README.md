# Escenarios BDD

Los archivos `.feature` describen el comportamiento requerido por la tesis en Gherkin (Dado–Cuando–Entonces). Se ejecutan con `pytest-bdd` como parte de la suite del backend: las definiciones de pasos están en `backend/tests/aceptacion/` y corren contra la API real con PostgreSQL y pgvector.

Los cuatro recorridos de la cadena de evidencia (EVD-A, EVD-B, EVD-C y EVD-N12) verifican los criterios V1 a V11 contra el oráculo de `demo/cadena_evidencia/`. Las pruebas de interfaz se hacen aparte, con Playwright (`frontend/`).
