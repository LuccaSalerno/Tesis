"""Verificaciones de solo lectura en la cuenta: SEG-02 (configuración) y SEG-04 (registros).

Solo las ejecuta el operador, con sus credenciales, en una sesión E90A. No crean,
modifican ni borran recursos. El informe guarda nombres, banderas y conteos: nunca valores de
variables de entorno, políticas completas ni mensajes de registro.
"""

import json
import re
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, Final

Cliente = Callable[[str], Any]

FUNCIONES: Final = ("api", "procesamiento", "persistencia", "operaciones")
# Un nombre que sugiere un secreto no debe estar en las variables de entorno (RNF-02).
NOMBRE_SECRETO: Final = re.compile(r"(CLAVE|SECRET|PASSWORD|TOKEN|PRIVATE)", re.IGNORECASE)
NOMBRES_ADMITIDOS: Final = re.compile(r"_ARN$")  # un ARN identifica, no es un secreto


def _verificacion(nombre: str, cumple: bool, detalle: str) -> dict[str, Any]:
    return {"verificacion": nombre, "cumple": cumple, "detalle": detalle}


def configuracion(cliente: Cliente, *, prefijo: str, bucket: str, rds: str) -> list[dict[str, Any]]:
    """SEG-02: cifrado, TLS, bloqueo público, secretos y destinos frente a lo declarado."""
    s3, salida = cliente("s3"), []
    cifrado = s3.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"]["Rules"]
    salida.append(
        _verificacion(
            "s3_cifrado",
            bool(cifrado),
            cifrado[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"],
        )
    )
    politica = json.loads(s3.get_bucket_policy(Bucket=bucket)["Policy"])
    solo_tls = any(
        d.get("Effect") == "Deny"
        and d.get("Condition", {}).get("Bool", {}).get("aws:SecureTransport") == "false"
        for d in politica.get("Statement", [])
    )
    salida.append(_verificacion("s3_solo_tls", solo_tls, "Deny sin aws:SecureTransport"))
    bloqueo = s3.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
    salida.append(
        _verificacion(
            "s3_bloqueo_publico",
            all(bloqueo.values()),
            ",".join(k for k, v in bloqueo.items() if v),
        )
    )

    rds_cliente = cliente("rds")
    instancia = rds_cliente.describe_db_instances(DBInstanceIdentifier=rds)["DBInstances"][0]
    salida.append(
        _verificacion("rds_cifrado", bool(instancia["StorageEncrypted"]), "StorageEncrypted")
    )
    salida.append(
        _verificacion(
            "rds_sin_acceso_publico", not instancia["PubliclyAccessible"], "PubliclyAccessible"
        )
    )
    # Valor efectivo, de cualquier origen y en todas las páginas: en PostgreSQL 16 el valor 1
    # es el predeterminado y RDS lo informa con origen «system» aunque Terraform lo fije
    # (e90-seguridad-1 lo buscaba solo con Source=user). El grupo debe estar aplicado.
    grupo_instancia = instancia["DBParameterGroups"][0]
    grupo = grupo_instancia["DBParameterGroupName"]
    aplicado = grupo_instancia.get("ParameterApplyStatus")
    valor = next(
        (
            p.get("ParameterValue")
            for pagina in rds_cliente.get_paginator("describe_db_parameters").paginate(
                DBParameterGroupName=grupo
            )
            for p in pagina["Parameters"]
            if p["ParameterName"] == "rds.force_ssl"
        ),
        None,
    )
    salida.append(
        _verificacion(
            "rds_force_ssl",
            valor == "1" and aplicado == "in-sync",
            f"{grupo}: rds.force_ssl={valor}, {aplicado}",
        )
    )

    lambda_cliente, logs = cliente("lambda"), cliente("logs")
    for funcion in FUNCIONES:
        nombre = f"{prefijo}-{funcion}"
        variables = (
            lambda_cliente.get_function_configuration(FunctionName=nombre)
            .get("Environment", {})
            .get("Variables", {})
        )
        sospechosas = sorted(
            v for v in variables if NOMBRE_SECRETO.search(v) and not NOMBRES_ADMITIDOS.search(v)
        )
        salida.append(
            _verificacion(
                f"lambda_{funcion}_sin_secretos",
                not sospechosas,
                ",".join(sospechosas) or "ninguna",
            )
        )
        grupos = logs.describe_log_groups(logGroupNamePrefix=f"/aws/lambda/{nombre}")["logGroups"]
        retencion = grupos[0].get("retentionInDays") if grupos else None
        salida.append(
            _verificacion(f"logs_{funcion}_retencion", retencion is not None, f"{retencion} días")
        )

    registro_bedrock = (
        cliente("bedrock").get_model_invocation_logging_configuration().get("loggingConfig")
    )
    salida.append(
        _verificacion("bedrock_sin_registro_de_invocaciones", not registro_bedrock, "loggingConfig")
    )
    endpoints = cliente("ec2").describe_vpc_endpoints(
        Filters=[{"Name": "tag:proyecto", "Values": ["atlas"]}]
    )["VpcEndpoints"]
    servicios = sorted(e["ServiceName"].rsplit(".", 1)[-1] for e in endpoints)
    salida.append(
        _verificacion(
            "sin_endpoint_secrets_manager", "secretsmanager" not in servicios, ",".join(servicios)
        )
    )
    return salida


def buscar_marcadores(
    cliente: Cliente,
    *,
    prefijo: str,
    maquina_arn: str,
    marcadores: Iterable[str],
    desde: datetime,
) -> list[dict[str, Any]]:
    """SEG-04: ningún marcador en CloudWatch Logs ni en los historiales de Step Functions; y sí
    los identificadores de correlación (solicitudes atendidas y trabajos)."""
    logs, salida = cliente("logs"), []
    inicio_ms = int(desde.timestamp() * 1000)
    lista = list(marcadores)
    for funcion in FUNCIONES:
        grupo = f"/aws/lambda/{prefijo}-{funcion}"
        for marcador in lista:
            eventos = _eventos(logs, grupo, f'"{marcador}"', inicio_ms)
            salida.append(
                _verificacion(
                    f"logs_{funcion}_sin_{marcador[:14]}", eventos == 0, f"{eventos} eventos"
                )
            )
    correlacion = _eventos(logs, f"/aws/lambda/{prefijo}-api", '"solicitud_atendida"', inicio_ms)
    salida.append(
        _verificacion("logs_api_con_correlacion", correlacion > 0, f"{correlacion} solicitudes")
    )
    trabajos = _eventos(logs, f"/aws/lambda/{prefijo}-persistencia", '"trabajo_id"', inicio_ms)
    salida.append(
        _verificacion("logs_persistencia_con_trabajo_id", trabajos > 0, f"{trabajos} eventos")
    )

    sfn = cliente("stepfunctions")
    ejecuciones = [
        e
        for p in sfn.get_paginator("list_executions").paginate(stateMachineArn=maquina_arn)
        for e in p["executions"]
        if e["startDate"] >= desde
    ]
    con_marcador = 0
    for ejecucion in ejecuciones:
        historial = json.dumps(
            [
                ev
                for p in sfn.get_paginator("get_execution_history").paginate(
                    executionArn=ejecucion["executionArn"]
                )
                for ev in p["events"]
            ],
            default=str,
        )
        con_marcador += any(m in historial for m in lista)
    salida.append(
        _verificacion(
            "stepfunctions_sin_marcadores",
            con_marcador == 0,
            f"{len(ejecuciones)} ejecuciones, {con_marcador} con marcador",
        )
    )
    fallidas = sum(e["status"] == "FAILED" for e in ejecuciones)
    salida.append(
        _verificacion(
            "camino_de_error_ejercitado", fallidas > 0, f"{fallidas} ejecuciones fallidas"
        )
    )
    return salida


def _eventos(logs: Any, grupo: str, patron: str, inicio_ms: int) -> int:
    total = 0
    for pagina in logs.get_paginator("filter_log_events").paginate(
        logGroupName=grupo, filterPattern=patron, startTime=inicio_ms
    ):
        total += len(pagina.get("events", []))
    return total
