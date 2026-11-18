"""Vaciado de un bucket versionado de la sesión antes del plan de retiro.

Uso (operador, solo en el paso de retiro aprobado del runbook):

    python -m atlas.herramientas.vaciar_bucket_versionado --bucket <nombre>            # simula
    python -m atlas.herramientas.vaciar_bucket_versionado --bucket <nombre> \\
        --confirmar <nombre> --ejecutar                                                   # borra

Borra **todas** las versiones y marcadores de eliminación. Es
irreversible. Se niega con un bucket que no tenga las etiquetas `proyecto=atlas` y
`entorno=demo`, o que pertenezca a `bootstrap` (estado remoto). Sin `--ejecutar`, solo
cuenta. Nunca lo ejecutan agentes ni GitHub Actions.
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Any


class BucketNoAutorizado(RuntimeError):
    pass


@dataclass
class Resultado:
    versiones: int = 0
    marcadores: int = 0
    eliminados: int = 0


def verificar_etiquetas(s3: Any, bucket: str) -> None:
    try:
        etiquetas = {e["Key"]: e["Value"] for e in s3.get_bucket_tagging(Bucket=bucket)["TagSet"]}
    except s3.exceptions.ClientError as error:
        raise BucketNoAutorizado("El bucket no tiene etiquetas: no se vacía") from error
    if etiquetas.get("raiz") == "bootstrap":
        raise BucketNoAutorizado("Es el estado remoto (bootstrap): nunca se vacía")
    if etiquetas.get("proyecto") != "atlas" or etiquetas.get("entorno") != "demo":
        raise BucketNoAutorizado("El bucket no es de la demo de ATLAS")


def vaciar(s3: Any, bucket: str, *, ejecutar: bool) -> Resultado:
    verificar_etiquetas(s3, bucket)
    resultado = Resultado()
    for pagina in s3.get_paginator("list_object_versions").paginate(Bucket=bucket):
        lote = [{"Key": v["Key"], "VersionId": v["VersionId"]} for v in pagina.get("Versions", [])]
        marcadores = [
            {"Key": m["Key"], "VersionId": m["VersionId"]} for m in pagina.get("DeleteMarkers", [])
        ]
        resultado.versiones += len(lote)
        resultado.marcadores += len(marcadores)
        objetos = lote + marcadores
        if ejecutar and objetos:
            for inicio in range(0, len(objetos), 1000):
                respuesta = s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": objetos[inicio : inicio + 1000], "Quiet": True},
                )
                if respuesta.get("Errors"):
                    raise RuntimeError(f"{len(respuesta['Errors'])} objetos no se eliminaron")
                resultado.eliminados += len(objetos[inicio : inicio + 1000])
    return resultado


def main(argumentos: list[str] | None = None, s3: Any = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--bucket", required=True)
    analizador.add_argument("--confirmar", help="Repetir el nombre del bucket para ejecutar")
    analizador.add_argument("--ejecutar", action="store_true")
    analizador.add_argument("--region", default="us-east-1")
    opciones = analizador.parse_args(argumentos)
    if opciones.ejecutar and opciones.confirmar != opciones.bucket:
        print("Para ejecutar, --confirmar debe repetir exactamente el nombre", file=sys.stderr)
        return 2
    if s3 is None:  # pragma: no cover - solo con AWS real, en manos del operador
        import boto3

        s3 = boto3.client("s3", region_name=opciones.region)
    try:
        resultado = vaciar(s3, opciones.bucket, ejecutar=opciones.ejecutar)
    except BucketNoAutorizado as error:
        print(f"No se vacía: {error}", file=sys.stderr)
        return 1
    total = resultado.versiones + resultado.marcadores
    detalle = f"{resultado.eliminados} eliminados" if opciones.ejecutar else f"{total} a eliminar"
    print(
        f"{opciones.bucket}: {resultado.versiones} versiones y {resultado.marcadores} marcadores; "
        f"{detalle}{'' if opciones.ejecutar else ' (simulación)'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
