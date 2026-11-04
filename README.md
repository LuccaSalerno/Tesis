# ATLAS — PFI UADE 2026

Prototipo de la tesis «Arquitectura para la gestión inteligente de documentos y contratos con extracción automática de información, trazabilidad y firma digital».

Antes de trabajar en el repositorio, leé [AGENTS.md](AGENTS.md): fija las reglas y el orden de los documentos que gobiernan el proyecto.

## Estado

- **Aplicación:** RF-01 a RF-26 implementados (backend FastAPI, frontend React). Detalle y próximos pasos en [Estado_Implementacion.md](docs/plan/Estado_Implementacion.md).
- **Evaluación:** resultados y pendientes del capítulo 6 en [Resumen_Estado_Seccion_6.md](docs/evaluacion/Resumen_Estado_Seccion_6.md); la evidencia está en [evaluacion/campanas](evaluacion/campanas).
- **AWS:** sin infraestructura activa hasta la exposición final (DO-2026-10-24-RETIRO-TOTAL). Las operaciones las ejecuta solo un integrante autorizado, de forma manual; la CI de GitHub no tiene acceso a AWS.
- **Datos:** el agente, la CI y la demo usan exclusivamente datos sintéticos.

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | API, servicios, procesamiento, migraciones y pruebas ([README](backend/README.md)) |
| `frontend/` | Aplicación web ([README](frontend/README.md)) |
| `infra/` | Terraform, base local con Docker y empaquetado ([README](infra/terraform/README.md)) |
| `operaciones/` | Guías de operación manual en AWS y guion de la demo |
| `corpus/`, `oraculos/` | Documentos sintéticos y oráculos, algunos congelados: no se modifican |
| `evaluacion/` | Campañas y evidencia de la sección 6 |
| `herramientas/`, `tests/` | Generación y validación del corpus; escenarios BDD en `tests/acceptance/` |
| `docs/` | Tesis, decisiones, contratos de aceptación, diseño, plan y operación |

## Levantar el entorno local

Requiere Python 3.12, Node 20.19 o superior y Docker. La primera vez, seguí la puesta en marcha de [backend/README.md](backend/README.md).

```bash
docker compose -f infra/local/docker-compose.yml up -d --wait
```

```bash
cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m atlas.herramientas.preparar_aws_local
```

```bash
cd backend && .venv/bin/uvicorn --factory atlas.principal:crear_aplicacion --no-access-log
```

```bash
cd backend && .venv/bin/python -m atlas.herramientas.sembrar_local
```

```bash
cd frontend && npm ci && npm run dev
```

La semilla imprime un token por rol para ingresar en <http://localhost:5173>. moto guarda los archivos en memoria: si se reinicia, hay que preparar moto y volver a sembrar, y los trámites anteriores dejan de mostrar su PDF.

## Verificar

Antes de commitear un hito, desde la raíz del repositorio:

```bash
backend/herramientas_ci/ensayo_ci_limpio.sh
```

Corre lint, tipos, pruebas y cobertura en contenedores limpios, sin tocar la base local. Los recorridos e2e se describen en [frontend/README.md](frontend/README.md).
