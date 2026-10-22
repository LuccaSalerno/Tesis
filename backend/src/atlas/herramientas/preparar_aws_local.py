"""Prepara el bucket y la máquina de estados ficticia en moto (DT-AWS-01). Solo desarrollo.

Uso: `python -m atlas.herramientas.preparar_aws_local`

Lee la configuración del proceso y se niega si no hay un endpoint local
configurado: nunca crea recursos en AWS. Es idempotente.
"""

import json
import sys

from atlas.configuracion import ErrorConfiguracion, obtener_configuracion
from atlas.integraciones.aws import crear_cliente
from atlas.integraciones.ciclo_vida_s3 import aplicar_ciclo_vida

_ROL_FICTICIO = "arn:aws:iam::123456789012:role/atlas-procesamiento-local"
ORIGENES_WEB_LOCALES = ("http://localhost:5173", "http://localhost:4173")


def main(argumentos: list[str] | None = None) -> int:
    configuracion = obtener_configuracion()
    try:
        configuracion.validar_servicios_aws()
    except ErrorConfiguracion as error:
        print(f"No se preparó: {error}", file=sys.stderr)
        return 1
    if configuracion.aws_endpoint_url is None:
        print(
            "No se preparó: falta ATLAS_AWS_ENDPOINT_URL (solo simulación local)", file=sys.stderr
        )
        return 1

    s3 = crear_cliente(configuracion, "s3")
    bucket = configuracion.s3_bucket_documentos
    if bucket not in {b["Name"] for b in s3.list_buckets().get("Buckets", [])}:
        s3.create_bucket(Bucket=bucket)
    # Como en AWS (RC-P10): bucket versionado y regla de respaldo para cargas temporales.
    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})
    aplicar_ciclo_vida(s3, bucket or "")
    # La aplicación web local carga y lee con URL prefirmada desde el navegador (WEB F7).
    s3.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedOrigins": list(ORIGENES_WEB_LOCALES),
                    "AllowedMethods": ["PUT", "GET"],
                    "AllowedHeaders": ["content-type", "range"],
                    "ExposeHeaders": ["content-length", "content-range", "accept-ranges"],
                    "MaxAgeSeconds": 300,
                }
            ]
        },
    )

    sfn = crear_cliente(configuracion, "stepfunctions")
    arn = configuracion.sfn_maquina_procesamiento_arn or ""
    existentes = {m["stateMachineArn"] for m in sfn.list_state_machines()["stateMachines"]}
    if arn not in existentes:
        sfn.create_state_machine(
            name=arn.rsplit(":", 1)[1],
            definition=json.dumps({"StartAt": "Fin", "States": {"Fin": {"Type": "Succeed"}}}),
            roleArn=_ROL_FICTICIO,
        )
    print(
        f"Simulación local lista en {configuracion.aws_endpoint_url}: bucket y máquina de estados"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
