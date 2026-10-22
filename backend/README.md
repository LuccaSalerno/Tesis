# Backend ATLAS — desarrollo local

FastAPI + SQLAlchemy 2 + Alembic sobre PostgreSQL 16 con pgvector. Sin llamadas a AWS.
Reglas del repositorio: [AGENTS.md](../AGENTS.md).

## Puesta en marcha

Requiere Python 3.12 (con `python3.12-venv`) y Docker.

1. Base local (solo escucha en 127.0.0.1):
   - Copiar `infra/local/.env.example` a `infra/local/.env` y completar claves locales propias.
   - `docker compose -f infra/local/docker-compose.yml up -d --wait`
   - El script `infra/local/inicializar_base.sh` corre una sola vez al crear el volumen: crea
     `atlas_dev` y `atlas_tests`, sus usuarios, el esquema `atlas` y pgvector. Para recrearla:
     `docker compose -f infra/local/docker-compose.yml down -v` (borra solo la base local).
2. Entorno Python, desde `backend/`:
   - `python3 -m venv .venv`
   - `.venv/bin/pip install -c requisitos-bloqueados.txt -e ".[desarrollo]"`
3. Configuración: copiar `.env.example` a `.env` (desarrollo) y `.env.tests.example` a
   `.env.tests` (pruebas), con las claves de `infra/local/.env`. Ninguno se versiona.
4. Migraciones: `.venv/bin/alembic upgrade head` (usa el usuario de migración de `.env`).
5. API: `.venv/bin/uvicorn --factory atlas.principal:crear_aplicacion --no-access-log`
   y consultar `GET /salud`.

## Verificaciones

```
.venv/bin/ruff format --check src tests migraciones
.venv/bin/ruff check src tests migraciones
.venv/bin/mypy
.venv/bin/pytest --cov
```

Las pruebas marcadas `integracion` usan la base real `atlas_tests` y fallan (no se omiten) si
no está disponible. Solo corren con `ATLAS_ENTORNO=tests` sobre una base `*_tests`.
Las de `tests/` en la raíz (herramientas del corpus) se ejecutan con `python -m pytest tests`.

## Registro

Los registros son JSON con un código de evento fijo y metadatos de una lista cerrada
(`atlas.registro.METADATOS_PERMITIDOS`). Nunca se registra contenido documental, mensajes de
excepción, argumentos de mensajes de bibliotecas ni la ruta concreta o la consulta.
