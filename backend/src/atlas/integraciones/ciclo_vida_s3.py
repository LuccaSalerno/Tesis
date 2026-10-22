"""Regla de S3 Lifecycle de respaldo para las cargas temporales (DO-2026-10-22-CARGAS).

Es la única definición de la regla: la herramienta local la aplica a moto y la
IaC futura debe replicarla literalmente. Actúa solo sobre el prefijo exclusivo de
cargas temporales; el prefijo de documentos confirmados queda fuera. No garantiza
el vencimiento exacto: lo garantiza la aplicación (24 h) y la limpieza idempotente.
"""

from typing import Any, Final

PREFIJO_CARGAS_TEMPORALES: Final = "cargas-temporales/"
PREFIJO_DOCUMENTOS: Final = "documentos/"
DIAS_RESPALDO: Final = 2

REGLAS_CICLO_VIDA: Final[list[dict[str, Any]]] = [
    {
        "ID": "atlas-cargas-temporales-respaldo",
        "Filter": {"Prefix": PREFIJO_CARGAS_TEMPORALES},
        "Status": "Enabled",
        "Expiration": {"Days": DIAS_RESPALDO},
        "NoncurrentVersionExpiration": {"NoncurrentDays": DIAS_RESPALDO},
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": DIAS_RESPALDO},
    },
    {
        # Retira los marcadores de eliminación que quedan sin versiones (bucket versionado).
        "ID": "atlas-cargas-temporales-marcadores",
        "Filter": {"Prefix": PREFIJO_CARGAS_TEMPORALES},
        "Status": "Enabled",
        "Expiration": {"ExpiredObjectDeleteMarker": True},
    },
]


def aplicar_ciclo_vida(cliente_s3: Any, bucket: str) -> None:
    cliente_s3.put_bucket_lifecycle_configuration(
        Bucket=bucket, LifecycleConfiguration={"Rules": REGLAS_CICLO_VIDA}
    )
