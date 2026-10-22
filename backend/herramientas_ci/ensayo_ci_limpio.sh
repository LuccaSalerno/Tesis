#!/usr/bin/env bash
# Ensayo local de la CI (.github/workflows/ci.yml) en contenedores limpios, sin AWS.
#
# Copia el árbol de trabajo (archivos versionados y nuevos no ignorados, sin .env ni
# .venv), crea un PostgreSQL con pgvector descartable e instala el backend desde cero
# con las dependencias bloqueadas. No toca la base local ni el índice de git.
# Uso, desde la raíz del repositorio: backend/herramientas_ci/ensayo_ci_limpio.sh
set -euo pipefail

raiz="$(git rev-parse --show-toplevel)"
copia="$(mktemp -d)"
red="atlas-ensayo-ci-$$"
base="atlas-ensayo-pg-$$"

limpiar() {
  docker stop "$base" >/dev/null 2>&1 || true
  docker network rm "$red" >/dev/null 2>&1 || true
  # El contenedor escribe como root: se borra desde otro contenedor.
  docker run --rm -v "$copia":/copia python:3.12-slim rm -rf /copia/repo >/dev/null 2>&1 || true
  rm -rf "$copia"
}
trap limpiar EXIT

mkdir -p "$copia/repo"
(cd "$raiz" && git ls-files -z --cached --others --exclude-standard \
  | xargs -0 -I{} sh -c 'test -e "{}" && printf "%s\0" "{}"' \
  | tar --null -cf - -T -) | tar -xf - -C "$copia/repo"

docker network create "$red" >/dev/null
docker run -d --rm --name "$base" --network "$red" \
  -e POSTGRES_HOST_AUTH_METHOD=trust pgvector/pgvector:0.8.1-pg16 >/dev/null

docker run --rm --network "$red" -v "$copia/repo":/repo -w /repo/backend \
  -e PGHOST="$base" -e POSTGRES_USER=postgres -e ATLAS_ENTORNO=tests \
  -e ATLAS_BD_HOST="$base" -e ATLAS_BD_PUERTO=5432 -e ATLAS_BD_NOMBRE=atlas_tests \
  -e ATLAS_BD_USUARIO=atlas_tests_app -e ATLAS_BD_USUARIO_MIGRACION=atlas_tests_migracion \
  -e ATLAS_PRUEBAS_PG_SUPERUSUARIO="host=$base user=postgres" \
  python:3.12-slim bash -euc '
    apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq postgresql-client >/dev/null 2>&1
    until pg_isready -q; do sleep 1; done
    python -m pip install -q --root-user-action=ignore --upgrade pip >/dev/null 2>&1
    pip install -q --root-user-action=ignore -c requisitos-bloqueados.txt -e ".[desarrollo]"
    ../infra/local/inicializar_base.sh >/dev/null && echo "== base inicializada"
    ruff format --check src tests migraciones herramientas_ci
    ruff check src tests migraciones herramientas_ci
    mypy
    pytest -q --cov --cov-report=term --cov-report=json -rs 2>&1 | grep -E "TOTAL|passed|failed|FAILED|ERROR"
    python -m herramientas_ci.verificar_cobertura coverage.json --minimo 90
    cd /repo && python -m pytest -q tests 2>&1 | tail -1
  '
