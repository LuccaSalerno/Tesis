# Decisiones delegadas al agente de código

Registro de las decisiones que el agente toma por su cuenta dentro de lo permitido por `AGENTS.md` §4 (PD-04, PD-06, RC-P01). Se completa en el momento de tomar cada decisión; el equipo las revisa al terminar cada bloque.

| Fecha | ID | Decisión | Justificación | Requisito o decisión que sirve | Revisada por el equipo |
|---|---|---|---|---|---|
| 22/10/2026 | RC-P01-001 | `GET /salud` sin autenticación y sin consultar PostgreSQL; responde `{"estado": "ok", "entorno": <entorno configurado>}` | Verificar el proceso y el entorno configurado del servidor sin depender de la base; el entorno nunca se toma de la petición | RC-P10 (separación por configuración); base para el modo de mantenimiento de RC-P10-08 | Pendiente |
| 22/10/2026 | RC-P01-002 | Toda respuesta lleva la cabecera `X-Solicitud-Id`; un error no controlado responde 500 `{"detalle": "Error interno", "solicitud_id": …}` y se registra solo por el tipo de excepción | Correlacionar solicitudes y errores sin que mensajes de excepción o valores lleguen a los registros | AGENTS.md §2.5, RNF-03 | Pendiente |
| 22/10/2026 | PD-04-001 | Tablas en el esquema `atlas`, propiedad del usuario de migración; `alembic_version` en ese esquema; convención fija de nombres de restricciones (`pk_`, `fk_`, `uq_`, `ix_`, `ck_`) | Migraciones deterministas y privilegios acotados a un esquema | PD-04, RC-P10-15 | Pendiente |
| 22/10/2026 | PD-04-002 | Por base lógica, un usuario de migración y uno de aplicación. El de aplicación solo conecta a su base y recibe por defecto SELECT/INSERT/UPDATE y uso de secuencias, sin DELETE, TRUNCATE ni CREATE. Cualquier excepción se otorga por tabla en su migración, justificada | Refuerza en la base la inexistencia de borrado funcional y el aislamiento entre bases. La inmutabilidad frente a UPDATE de versiones y auditoría se fija por tabla al crearlas | RNF-04, RN-10, RC-P10 (matriz de aislamiento V-DB) | Pendiente |
| 22/10/2026 | PD-04-003 | pgvector y el esquema se crean en la inicialización privilegiada (`infra/local/inicializar_base.sh` en local); la revisión Alembic `0001` solo verifica que existan. Las migraciones toman un bloqueo consultivo de sesión | Separar la inicialización privilegiada de las migraciones ordinarias e impedir migraciones concurrentes | RC-P10-15 | Pendiente |

## Elecciones técnicas consultadas y aprobadas (no delegadas)

Consultadas según AGENTS.md §4 y aprobadas por Lucca Salerno el 22/10/2026 para la fundación local:

- Dependencias con pip y `pyproject.toml`; versiones exactas en `backend/requisitos-bloqueados.txt`.
- SQLAlchemy 2.1, psycopg 3 y pydantic-settings; ruff y mypy (estricto) para linting y análisis estático.
- PostgreSQL 16 con pgvector 0.8.1 (`pgvector/pgvector:0.8.1-pg16`) **provisorio** en local y CI. Confirmar contra la versión de RDS antes de RC-P10-15.
- Bases locales `atlas_dev` y `atlas_tests` (usuarios `<base>_app` y `<base>_migracion`). En AWS rigen `pfi_demo` y `pfi_tests` según RC-P10.
