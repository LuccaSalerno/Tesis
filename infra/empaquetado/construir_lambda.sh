#!/usr/bin/env bash
# Paquete único arm64 de las funciones Lambda de ATLAS (DO-2026-10-22-OPS P6).
#
# Instala en un contenedor limpio las dependencias de ejecución del backend con las versiones
# de backend/requisitos-bloqueados.txt (wheels manylinux aarch64, glibc ≤ 2.34 como el
# runtime python3.12 de Lambda en Amazon Linux 2023), y agrega el código, las
# migraciones y el paquete de certificados de RDS. No contacta AWS ni publica nada: el zip
# lo sube Terraform (raíz demo) cuando el operador aplica el plan aprobado.
#
# Uso, desde la raíz del repositorio:
#   infra/empaquetado/construir_lambda.sh                  # exige los dos .pem de infra/certificados
#   infra/empaquetado/construir_lambda.sh --sin-certificados   # solo para ensayar el armado en local
set -euo pipefail

raiz="$(git rev-parse --show-toplevel)"
certificado="$raiz/infra/certificados/rds-global-bundle.pem"
# RDS Proxy presenta un certificado de ACM: su cadena termina en Amazon Root CA (DIF-96).
raices_amazon="$raiz/infra/certificados/amazon-trust-raices.pem"
salida="$raiz/dist/atlas-lambda.zip"
sin_certificados=0
[[ "${1:-}" == "--sin-certificados" ]] && sin_certificados=1

for requerido in "$certificado" "$raices_amazon"; do
  if [[ $sin_certificados -eq 0 && ! -s "$requerido" ]]; then
    echo "Falta $requerido (ver infra/certificados/README.md)" >&2
    exit 1
  fi
done

trabajo="$(mktemp -d)"
trap 'docker run --rm -v "$trabajo":/t python:3.12-slim rm -rf /t/paquete >/dev/null 2>&1 || true; rm -rf "$trabajo"' EXIT
mkdir -p "$trabajo/paquete" "$raiz/dist"

docker run --rm -v "$raiz/backend":/backend:ro -v "$trabajo/paquete":/paquete python:3.12-slim bash -euc '
  python - <<PY > /tmp/dependencias.txt
import tomllib
print("\n".join(tomllib.load(open("/backend/pyproject.toml", "rb"))["project"]["dependencies"]))
PY
  pip install -q --root-user-action=ignore --no-compile --target /paquete \
    --platform manylinux_2_34_aarch64 --platform manylinux_2_28_aarch64 --platform manylinux2014_aarch64 \
    --implementation cp --python-version 3.12 --only-binary=:all: \
    -c /backend/requisitos-bloqueados.txt -r /tmp/dependencias.txt
  cp -r /backend/src/atlas /paquete/atlas
  # El arnés de §6.3 lo ejecuta el operador; no va a Lambda (DO-2026-10-23-E90-MEDICION P2).
  rm -rf /paquete/atlas/evaluacion
  mkdir -p /paquete/migraciones
  cp -r /backend/migraciones/versions /backend/migraciones/env.py /backend/migraciones/script.py.mako /paquete/migraciones/
  find /paquete -name "__pycache__" -type d -prune -exec rm -rf {} +
  chown -R '"$(id -u):$(id -g)"' /paquete
'

if [[ $sin_certificados -eq 0 ]]; then
  mkdir -p "$trabajo/paquete/certificados"
  # Un solo archivo de CA para la instancia (RDS) y el proxy (ACM).
  cat "$certificado" "$raices_amazon" > "$trabajo/paquete/certificados/ca-bd.pem"
fi

rm -f "$salida"
(cd "$trabajo/paquete" && python3 -c "
import os, zipfile
with zipfile.ZipFile('$salida', 'w', zipfile.ZIP_DEFLATED) as z:
    for base, _, archivos in sorted(os.walk('.')):
        for a in sorted(archivos):
            ruta = os.path.join(base, a)
            info = zipfile.ZipInfo(ruta[2:], date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            z.writestr(info, open(ruta, 'rb').read(), zipfile.ZIP_DEFLATED)
")
echo "Paquete: $salida ($(du -h "$salida" | cut -f1), sha256 $(sha256sum "$salida" | cut -c1-16)…)"
[[ $sin_certificados -eq 1 ]] && echo "AVISO: sin certificados de RDS; no desplegar este paquete." >&2
exit 0
