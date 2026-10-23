#!/usr/bin/env bash
# Publicación de la aplicación web en S3 + CloudFront (DO-2026-10-23-WEB-HOST P4, P6).
#
# Solo lo ejecuta el operador, con sus credenciales y después de aplicar la raíz `web`; nunca
# la CI (DO-2026-10-21). Dos modos:
#
#   infra/web/publicar.sh --aplicacion     # compila y sube los archivos estáticos
#   infra/web/publicar.sh --configuracion  # sube configuracion.json de la sesión actual
#
# `--configuracion` lee las salidas de `persistent` y `demo` (URL de la API y cliente de
# Cognito): se corre en cada sesión, después de aplicar `demo`. `--simular` muestra los
# comandos sin ejecutarlos. Ningún archivo publicado contiene secretos ni documentos.
set -euo pipefail

raiz="$(git rev-parse --show-toplevel)"
terraform="$raiz/infra/terraform"
modo=""
simular=0
for argumento in "$@"; do
  case "$argumento" in
    --aplicacion | --configuracion) modo="$argumento" ;;
    --simular) simular=1 ;;
    *) echo "Uso: $0 --aplicacion|--configuracion [--simular]" >&2; exit 2 ;;
  esac
done
[[ -n "$modo" ]] || { echo "Uso: $0 --aplicacion|--configuracion [--simular]" >&2; exit 2; }

correr() {
  if [[ $simular -eq 1 ]]; then echo "+ $*"; else "$@"; fi
}

salida() {  # salida <raíz> <nombre>
  if [[ $simular -eq 1 ]]; then echo "<$1.$2>"; else terraform -chdir="$terraform/$1" output -raw "$2"; fi
}

bucket="$(salida web bucket)"
distribucion="$(salida web distribucion_id)"

if [[ "$modo" == "--aplicacion" ]]; then
  # Sin URL de la API en el build: la toma de configuracion.json en cada sesión.
  correr env VITE_ATLAS_AUTENTICACION=cognito npm --prefix "$raiz/frontend" run build
  # Archivos con hash en el nombre: caché larga; el resto, siempre revalidado.
  correr aws s3 sync "$raiz/frontend/dist/assets" "s3://$bucket/assets" --delete \
    --cache-control "public,max-age=31536000,immutable"
  correr aws s3 sync "$raiz/frontend/dist" "s3://$bucket" --delete \
    --exclude "assets/*" --exclude "configuracion.json" --cache-control "no-cache"
  correr aws cloudfront create-invalidation --distribution-id "$distribucion" --paths "/index.html" "/"
else
  url_api="$(salida demo url_api)"
  cliente="$(salida persistent cognito_cliente_id)"
  archivo="$(mktemp)"
  trap 'rm -f "$archivo"' EXIT
  printf '{"apiUrl": "%s", "autenticacion": "cognito", "cognitoRegion": "us-east-1", "cognitoCliente": "%s"}\n' \
    "${url_api%/}" "$cliente" > "$archivo"
  [[ $simular -eq 1 ]] && cat "$archivo"
  correr aws s3 cp "$archivo" "s3://$bucket/configuracion.json" \
    --content-type application/json --cache-control "no-cache"
  correr aws cloudfront create-invalidation --distribution-id "$distribucion" --paths "/configuracion.json"
fi
echo "Publicado ($modo). URL: $(salida web origen)"
