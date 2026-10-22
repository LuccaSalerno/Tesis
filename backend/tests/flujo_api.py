"""Pasos del recorrido de carga por la API, compartidos por las pruebas y los escenarios BDD."""

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

TIPO_PDF = "application/pdf"


@dataclass
class Contexto:
    cliente: TestClient
    motor: Engine
    usuario_id: int
    encabezados: dict[str, str]


def crear_tramite(ctx: Contexto, titulo: str = "Contrato de mantenimiento ATLAS") -> dict[str, Any]:
    respuesta = ctx.cliente.post("/tramites", json={"titulo": titulo}, headers=ctx.encabezados)
    assert respuesta.status_code == 201, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


def autorizar(
    ctx: Contexto, tramite_id: int, datos: bytes, formato: str = "pdf", tamano: int | None = None
) -> dict[str, Any]:
    respuesta = ctx.cliente.post(
        f"/tramites/{tramite_id}/cargas",
        json={
            "nombre": f"C-v1.{formato}",
            "formato": formato,
            "tamano_bytes": len(datos) if tamano is None else tamano,
        },
        headers=ctx.encabezados,
    )
    assert respuesta.status_code == 201, respuesta.text
    carga: dict[str, Any] = respuesta.json()
    return carga


def transferir(carga: dict[str, Any], datos: bytes) -> None:
    """Lo que hace el navegador: PUT directo a la URL prefirmada, sin pasar por la API."""
    respuesta = httpx.put(carga["url"], content=datos, headers=carga["encabezados"])
    assert respuesta.status_code == 200


def confirmar(ctx: Contexto, tramite_id: int, carga_id: int) -> httpx.Response:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/cargas/{carga_id}/confirmacion", headers=ctx.encabezados
    )


def cargar(ctx: Contexto, tramite_id: int, datos: bytes, formato: str = "pdf") -> dict[str, Any]:
    carga = autorizar(ctx, tramite_id, datos, formato)
    transferir(carga, datos)
    respuesta = confirmar(ctx, tramite_id, carga["id"])
    assert respuesta.status_code == 201, respuesta.text
    archivo: dict[str, Any] = respuesta.json()
    return archivo


def incorporar(ctx: Contexto, tramite_id: int, archivo_id: int, **cuerpo: Any) -> httpx.Response:
    return ctx.cliente.post(
        f"/tramites/{tramite_id}/archivos/{archivo_id}/incorporacion",
        json=cuerpo or None,
        headers=ctx.encabezados,
    )


def eventos_del_tramite(motor: Engine, tramite_id: int) -> list[dict[str, Any]]:
    with motor.connect() as conexion:
        return [
            dict(f)
            for f in conexion.execute(
                text(
                    "SELECT accion, entidad_tipo, entidad_id, actor_id, version_id"
                    " FROM atlas.evento_auditoria WHERE tramite_id = :t ORDER BY id"
                ),
                {"t": tramite_id},
            ).mappings()
        ]


def contar(motor: Engine, tabla: str, tramite_id: int) -> int:
    with motor.connect() as conexion:
        return int(
            conexion.execute(
                text(f"SELECT count(*) FROM atlas.{tabla} WHERE tramite_id = :t"),  # noqa: S608
                {"t": tramite_id},
            ).scalar_one()
        )
