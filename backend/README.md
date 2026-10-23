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

## Autenticación local (DT-AUT-01, DT-AUT-02)

El backend verifica tokens de acceso con la forma de los de Cognito. En local se firman con
claves propias guardadas en `backend/.claves_locales/` (no versionado):

1. Emitir un token (la primera vez también genera las claves y el JWKS que lee el servidor):
   `.venv/bin/python -m atlas.herramientas.token_local --sub sub-admin-local`
2. Crear el primer administrador (operación manual, una sola vez por base):
   `.venv/bin/python -m atlas.herramientas.inicializar_administrador --identificador-externo sub-admin-local`
3. Usar el token como `Authorization: Bearer <token>`. Las demás cuentas las da de alta el
   administrador con `POST /usuarios`. La documentación interactiva queda en `/docs`.

`token_local` se niega a funcionar con `ATLAS_ENTORNO=demo`.

## S3 y Step Functions simulados (DT-AWS-01)

`docker compose -f infra/local/docker-compose.yml up -d --wait` levanta también moto en
`127.0.0.1:5000`. Con las variables `ATLAS_AWS_*`, `ATLAS_S3_*` y `ATLAS_SFN_*` de `.env.example`:

- `.venv/bin/python -m atlas.herramientas.preparar_aws_local` crea el bucket y la máquina de estados
  ficticia. Es idempotente y se niega a funcionar sin un endpoint local.
- La carga sigue el recorrido de la tesis: `POST /tramites/{id}/cargas` devuelve una URL prefirmada,
  el archivo se transfiere con `PUT` directo a esa URL, y después se confirma con
  `POST /tramites/{id}/cargas/{carga_id}/confirmacion`.

Vencimiento (DO-2026-10-22-CARGAS): la URL prefirmada dura 5 minutos y la carga tiene 24 horas para
incorporarse. `.venv/bin/python -m atlas.herramientas.limpiar_cargas_vencidas` limpia de forma
idempotente los objetos temporales vencidos (todas sus versiones) y las multipartes incompletas.

En AWS no se define `ATLAS_AWS_ENDPOINT_URL`: el servidor en demo no arranca si está definida.
Las pruebas levantan su propio moto dentro de pytest, así que no necesitan el contenedor.

## Procesamiento documental (hito 1.4, DO-2026-10-22-PROC)

`src/atlas/procesamiento/` contiene las etapas de la máquina de estados (`maquina_estados.asl.json`):
Textract o lectura del DOCX, normalización, clasificación y extracción con Claude Haiku 4.5
(Bedrock Converse) y persistencia de las sugerencias con su procedencia. En local y en la CI se
prueban con respuestas fijas, sin contactar AWS. Las pruebas de `tests/aws_real/` usan los servicios
reales y solo las ejecuta el equipo, en una sesión autorizada:

```
ATLAS_PRUEBAS_AWS_REAL=1 ATLAS_EVIDENCIA_AWS_REAL=evidencia.json .venv/bin/pytest tests/aws_real -m aws_real
```

## Revisión, decisiones y evidencia (hito 1.8, DO-2026-10-22-TAR)

Recorrido por la API, con cuentas sintéticas:

1. El administrador crea la plantilla de contratos: `POST /plantillas-flujo` con dos pasos. El revisor del último paso necesita autorización de cierre.
2. El responsable valida la clasificación y todos los campos de cada documento, y envía el trámite a validación: `POST /tramites/{id}/envio-a-validacion`.
3. Consulta la sugerencia (`GET /tramites/{id}/flujo-sugerido`) y la confirma (`POST /tramites/{id}/ciclos`).
4. Cada revisor ve sus tareas (`GET /tareas`, `GET /tareas/{id}`) y decide: `POST /tareas/{id}/decision`.
5. La evidencia se reconstruye con `GET /decisiones/{id}/evidencia` y el historial con `GET /tramites/{id}/linea-tiempo`.

Si un trámite queda Observado, el responsable lo subsana (`POST /tramites/{id}/subsanacion`), corrige y confirma un ciclo nuevo.

## Despliegue manual en AWS (hito 1.0, DO-2026-10-22-OPS)

Preparado y validado sin AWS; solo lo ejecuta el operador autorizado, con plan y costos
aprobados. Procedimiento completo: [infra/terraform/README.md](../infra/terraform/README.md).

- `atlas.lambda_api.manejar`: la API detrás de API Gateway (Mangum).
- `atlas.operacion.lambda_operaciones.manejar`: Lambda privada de operaciones (inicializar la
  base, migrar, crear el primer administrador, verificar el drenaje).
- Modo mantenimiento: `ATLAS_MANTENIMIENTO_FUENTE=s3` lee `control/mantenimiento.json`; en local
  y en la CI es `fija_active`.
- Base con IAM: `ATLAS_BD_AUTENTICACION=iam` y `ATLAS_BD_CA_CERTIFICADOS` (TLS `verify-full`).
- Herramientas del operador: `sembrar_demo`, `exportar_evidencia` y `vaciar_bucket_versionado`
  (en `atlas.herramientas`).

## Aplicación web y desarrollo local (DO-2026-10-22-WEB)

- `python -m atlas.herramientas.exportar_openapi ../frontend/openapi.json`: contrato para el frontend.
- `python -m atlas.herramientas.sembrar_local`: semilla PD-07 contra la API local con el
  **procesamiento simulado** (`procesar_simulado`); imprime un token por rol. Solo desarrollo.
- Detalle en [frontend/README.md](../frontend/README.md).

## Verificaciones

```
.venv/bin/ruff format --check src tests migraciones
.venv/bin/ruff check src tests migraciones
.venv/bin/mypy
.venv/bin/pytest --cov --cov-report=json
.venv/bin/python -m herramientas_ci.verificar_cobertura coverage.json --minimo 90
```

La CI exige al menos un 90 % de cobertura en **cada módulo**, no solo en el total.

Los escenarios de aceptación en Gherkin (`tests/acceptance/features/`, en la raíz) se ejecutan con
`pytest-bdd` como parte de la misma corrida; sus pasos están en `tests/aceptacion/`. Los cuatro
recorridos EVD-01 se ejecutan; ejecutarlos no acredita EVD-01 sin el oráculo congelado.

Las pruebas marcadas `integracion` usan la base real `atlas_tests` y fallan (no se omiten) si
no está disponible. Solo corren con `ATLAS_ENTORNO=tests` sobre una base `*_tests`.
Las de `tests/` en la raíz (herramientas del corpus) se ejecutan con `python -m pytest tests`.

## Ensayo de CI limpio (antes de cada commit de hito)

Reproduce la CI en contenedores descartables, con el árbol de trabajo actual (incluidos los
archivos nuevos sin commitear) y dependencias instaladas desde cero. Desde la raíz del repositorio:

```
backend/herramientas_ci/ensayo_ci_limpio.sh
```

Tarda unos 5 minutos. No usa la base local ni modifica el índice de git, y al terminar borra
los contenedores y la copia.

No se corren dos `pytest` en paralelo contra la base local `atlas_tests`: comparten la base y
se producen fallas falsas. El ensayo limpio usa su propia base, así que puede correr junto a una
ejecución local.

## Registro

Los registros son JSON con un código de evento fijo y metadatos de una lista cerrada
(`atlas.registro.METADATOS_PERMITIDOS`). Nunca se registra contenido documental, mensajes de
excepción, argumentos de mensajes de bibliotecas ni la ruta concreta o la consulta.
