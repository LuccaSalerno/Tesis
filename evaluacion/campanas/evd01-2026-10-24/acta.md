# Acta de verificación EVD-01 — cadena de evidencia documental

**Fecha:** 2026-10-24. **Código:** `d461b6a` (sin cambios sin commitear). **Oráculo:** `oraculos/oraculo_PD07_v2.json` (PD-07-ATLAS-V2-CONGELADO-2026-10-23, CONGELADO, SHA-256 `3991b9e17df21555…`). **Ejecutor:** `backend/tests/aceptacion/test_evd01_acreditacion.py` (también corre en cada CI). **Paquete probatorio:** `evd01.json` (esperado y observado de cada comprobación, con identificadores).

**Entorno:** local: API FastAPI (TestClient) + PostgreSQL 16 con pgvector; procesamiento con dobles controlados (EVD-01 §1, condición 6).

| Criterio | Prioridad | Comprobaciones | Estado |
|---|---|---|---|
| V1 | esencial | 6 | **Cumple** |
| V2 | esencial | 5 | **Cumple** |
| V3 | esencial | 12 | **Cumple** |
| V4 | esencial | 11 | **Cumple** |
| V5 | complementario | 2 | **Cumple** |
| V6 | complementario | 4 | **Cumple** |
| V7 | esencial | 16 | **Cumple** |
| V8 | complementario | 6 | **Cumple** |
| V9 | esencial | 7 | **Cumple** |
| V10 | ampliación | 3 | **Cumple** |
| V11 | ampliación | 6 | **Cumple** |

**Resultado:** 78 de 78 comprobaciones cumplen; los 11 criterios cumplen.

**Recorridos y conjuntos (del oráculo):**

- **EVD-A:** CR-1 `{C-v1, O-v2, F-v1}` (R4 advierte) aprobado → F-v2 confirmada como versión nueva → CR-2 `{C-v1, O-v2, F-v2}` (R1–R4 cumplen) con decisión nueva. Incluye la corrección humana de un dato mal sugerido (V2) y la matriz de autorización (V10).
- **EVD-B:** CR-1 `{C-v1, O-v1, F-v2}` (R3 advierte) observado con motivo → O-v2 confirmada → CR-2 aprobado → firma simulada sobre C-v1 y cierre (V11).
- **EVD-C:** subsanación sin archivo nuevo: misma versión, Pendiente de validación (RN-13), sin herencia de decisiones.
- **EVD-N12:** la tarea abierta del ciclo desplazado rechaza la decisión (409), sin alterar la evidencia previa.

**Alcance declarado (EVD-01 §1, condición 6):** Textract y Bedrock se reemplazan por dobles controlados que devuelven los valores del oráculo; las cuentas ficticias se crean como precondición. El recorrido de EVD-B también se ejecutó en AWS real (semilla y recorrido manual en la interfaz; ver `../semilla-e90-2026-10-24/`), pero esta acta acredita la ejecución local contra el oráculo.

**Nota de la ejecución:** en la primera corrida una comprobación de V4 propia del ejecutor exigía que DEC-1 y DEC-2 no compartieran controles; el contrato no lo pide (R2 y R3 comparan contrato y orden, que no cambian entre los ciclos). Se reemplazó por las comprobaciones que sí exige: que los controles de DEC-2 consideren solo versiones de CR-2 y que los compartidos no involucren la factura reemplazada.
