# ATLAS — PFI UADE 2026

Prototipo de la tesis «Arquitectura para la gestión inteligente de documentos y contratos con extracción automática de información, trazabilidad y firma digital».

## Estado

- **Aplicación:** RF-01 a RF-26 implementados (backend FastAPI, frontend React).
- **Evaluación:** los resultados del capítulo 6 están en la tesis. El arnés de medición y sus campañas quedan en el tag `evaluacion-e90`; el corpus y sus generadores, en [atlas-tesis-datasets](https://github.com/LuccaSalerno/atlas-tesis-datasets).
- **AWS:** sin infraestructura activa. Se levanta por sesión, de forma manual ([infra/terraform/README.md](infra/terraform/README.md)).

## Reglas

- **Solo datos sintéticos** en el repositorio, la CI y la demo. Nunca documentos reales, ni anonimizados.
- **El contenido documental nunca va a los registros:** logs, errores y salidas de Step Functions llevan solo identificadores y metadatos técnicos.
- **No hay borrado funcional** de trámites, versiones ni eventos de auditoría (RN-10, RNF-04).
- **La IA sugiere y una persona valida:** las reglas de consistencia usan solo valores validados y la IA nunca aprueba, observa ni cambia el estado de un trámite (RN-02, RN-06).
- **AWS se opera a mano:** ningún push, merge ni GitHub Action despliega u opera infraestructura. La CI corre sin credenciales de AWS.
- **Sin secretos** en el repositorio.
- Cada prueba, migración y endpoint se traza a un RF, RN o RNF de la tesis.

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | API, servicios, procesamiento, migraciones y pruebas ([README](backend/README.md)) |
| `frontend/` | Aplicación web ([README](frontend/README.md)) |
| `infra/` | Terraform, base local con Docker y empaquetado ([README](infra/terraform/README.md)) |
| `demo/` | Documentos sintéticos y oráculos de las dos demos (cadena de evidencia y SurDelta): no se modifican |
| `tests/acceptance/` | Escenarios BDD (Gherkin) |
| `docs/tesis/` | La tesis (`main.pdf`): requisitos, modelo de datos y arquitectura |

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

Antes de commitear, desde la raíz del repositorio:

```bash
backend/herramientas_ci/ensayo_ci_limpio.sh
```

Corre lint, tipos, pruebas y cobertura en contenedores limpios, sin tocar la base local. Los recorridos e2e se describen en [frontend/README.md](frontend/README.md).
