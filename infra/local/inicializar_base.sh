#!/usr/bin/env bash
# Inicialización privilegiada local de PostgreSQL: equivalente local de RC-P10-15.
#
# Crea, por cada base lógica, un usuario de migración (propietario del esquema
# `atlas`) y un usuario de aplicación que solo puede conectarse a su propia base
# y tiene SELECT/INSERT/UPDATE, sin DELETE ni TRUNCATE (RNF-04, RN-10). La
# extensión pgvector se instala aquí y no en las migraciones ordinarias.
#
# Se ejecuta una sola vez: como script de /docker-entrypoint-initdb.d en Docker
# Compose, o con psql contra el servicio temporal de la CI. Las claves llegan
# por entorno; si están vacías (CI con autenticación trust) los roles no tienen clave.
set -euo pipefail

psql_admin() {
  psql -v ON_ERROR_STOP=1 --no-psqlrc --quiet --username "${POSTGRES_USER:-postgres}" "$@"
}

inicializar_base() {
  local base="$1"
  local app="${base}_app"
  local migracion="${base}_migracion"

  psql_admin --dbname postgres \
    -v base="$base" -v app="$app" -v migracion="$migracion" \
    -v clave_app="${ATLAS_LOCAL_CLAVE_APP:-}" \
    -v clave_migracion="${ATLAS_LOCAL_CLAVE_MIGRACION:-}" <<'SQL'
CREATE ROLE :"migracion" LOGIN;
CREATE ROLE :"app" LOGIN;
SELECT format('ALTER ROLE %I PASSWORD %L', :'migracion', :'clave_migracion')
  WHERE :'clave_migracion' <> '' \gexec
SELECT format('ALTER ROLE %I PASSWORD %L', :'app', :'clave_app')
  WHERE :'clave_app' <> '' \gexec
CREATE DATABASE :"base" OWNER :"migracion";
REVOKE ALL ON DATABASE :"base" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"base" TO :"app";
ALTER ROLE :"app" IN DATABASE :"base" SET search_path = atlas, public;
ALTER ROLE :"migracion" IN DATABASE :"base" SET search_path = atlas, public;

\connect :"base"
CREATE EXTENSION IF NOT EXISTS vector;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA atlas AUTHORIZATION :"migracion";
GRANT USAGE ON SCHEMA atlas TO :"app";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migracion" IN SCHEMA atlas
  GRANT SELECT, INSERT, UPDATE ON TABLES TO :"app";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migracion" IN SCHEMA atlas
  GRANT USAGE, SELECT ON SEQUENCES TO :"app";
SQL
}

inicializar_base atlas_dev
inicializar_base atlas_tests
