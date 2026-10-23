"""Escenario propio de la verificación de seguridad, armado por la API (P2, P3).

Las mismas llamadas sirven contra la aplicación local (CI) y contra la API desplegada. Crea:

- A: trámite del dueño con un contrato validado, flujo confirmado y un ciclo con la tarea
  pendiente del revisor y la tarea en espera del aprobador.
- A2: trámite del dueño en Borrador con un contrato sin validar, dos documentos con tipo
  validado y un archivo cargado sin incorporar, para validar, vincular, desvincular e
  incorporar (incorporar en A desplazaría el ciclo, PD-05).
- A3: trámite del dueño listo para confirmar el flujo.
- B: trámite del responsable ajeno, con su propio documento y marcador.
- F: trámite del dueño con un DOCX vacío cuyo procesamiento falla (camino de error, SEG-04).

Al final, el administrador deshabilita la cuenta `deshabilitada`.
"""

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Final

from atlas.evaluacion.seguridad import documentos
from atlas.herramientas.cliente_api import ClienteApi, sub_del_token

DUENO: Final = "dueno"
AJENO: Final = "ajeno"
REVISOR: Final = "revisor"
REVISOR_SIN_TAREA: Final = "revisor_sin_tarea"
APROBADOR: Final = "aprobador"
ADMINISTRADOR: Final = "administrador"
DESHABILITADA: Final = "deshabilitada"
SIN_TOKEN: Final = "sin_token"  # noqa: S105  # nombre de actor, no una clave
ACTORES: Final = (
    DUENO,
    AJENO,
    REVISOR,
    REVISOR_SIN_TAREA,
    APROBADOR,
    ADMINISTRADOR,
    DESHABILITADA,
    SIN_TOKEN,
)

ROLES: Final = {
    DUENO: "responsable_tramite",
    AJENO: "responsable_tramite",
    DESHABILITADA: "responsable_tramite",
    REVISOR: "revisor_aprobador",
    REVISOR_SIN_TAREA: "revisor_aprobador",
    APROBADOR: "revisor_aprobador",
}

CAMPOS_CONTRATO: Final = {
    "contraparte": "Servicios Ficticios de Seguridad S.A.",
    "cuit_contraparte": "30-71234567-1",
    "fecha_celebracion": "2026-02-01",
    "vigencia_desde": "2026-03-01",
    "vigencia_hasta": "2027-02-28",
    "monto_total": "1000000.00",
    "moneda": "ARS",
}

# Espera hasta que el trabajo del archivo termine; en la CI no hay procesamiento asíncrono.
Esperar = Callable[[ClienteApi, str, int, int], None]
ESPERA_MAXIMA_S: Final = 1800.0


def esperar_trabajo(
    api: ClienteApi,
    actor: str,
    tramite_id: int,
    archivo_id: int,
    *,
    dormir: Callable[[float], None] = time.sleep,
    maximo_s: float = ESPERA_MAXIMA_S,
) -> None:
    """Nivel B: el procesamiento real termina antes de incorporar (completado o fallido)."""
    inicio = time.monotonic()
    while True:
        archivos = api.get(f"/tramites/{tramite_id}/archivos", actor)
        trabajo = next((a.get("trabajo") or {} for a in archivos if a["id"] == archivo_id), {})
        if trabajo.get("estado") in ("completado", "fallido"):
            return
        if time.monotonic() - inicio > maximo_s:
            raise RuntimeError("procesamiento_sin_terminar")
        dormir(10.0)


@dataclass
class Escenario:
    ids: dict[str, int] = field(default_factory=dict)
    usuarios: dict[str, int] = field(default_factory=dict)
    marcadores: dict[str, str] = field(default_factory=dict)
    plantilla: dict[str, int] = field(default_factory=dict)

    def __getitem__(self, clave: str) -> int:
        return self.ids[clave]


def nuevos_marcadores() -> dict[str, str]:
    """Marcadores únicos por corrida; solo letras y dígitos para buscarlos sin ambigüedad."""
    base = secrets.token_hex(6).upper()
    return {
        nombre: f"SEGMARCA{nombre.upper()}{base}"
        for nombre in ("a", "b", "titulo", "archivo", "pregunta", "fallo")
    }


def _cuentas(api: ClienteApi, escenario: Escenario) -> None:
    escenario.usuarios[ADMINISTRADOR] = api.get("/usuarios/yo", ADMINISTRADOR)["id"]
    existentes = {c["identificador_externo"]: c for c in api.get("/usuarios", ADMINISTRADOR)}
    for actor, rol in ROLES.items():
        sub = sub_del_token(api.tokens[actor])
        cuenta = existentes.get(sub) or api.post(
            "/usuarios", ADMINISTRADOR, {"identificador_externo": sub}
        )
        api.put(f"/usuarios/{cuenta['id']}/estado", ADMINISTRADOR, {"estado": "habilitada"})
        api.put(f"/usuarios/{cuenta['id']}/roles/{rol}", ADMINISTRADOR)
        escenario.usuarios[actor] = cuenta["id"]
    api.put(
        f"/usuarios/{escenario.usuarios[APROBADOR]}/autorizacion-cierre",
        ADMINISTRADOR,
        {"otorgada": True},
    )


def _subir(
    api: ClienteApi, actor: str, tramite_id: int, nombre: str, datos: bytes, esperar: Esperar | None
) -> dict[str, Any]:
    carga = api.post(
        f"/tramites/{tramite_id}/cargas",
        actor,
        {"nombre": nombre, "formato": "docx", "tamano_bytes": len(datos)},
    )
    api.transferir(carga["url"], carga["encabezados"], datos)
    archivo: dict[str, Any] = api.post(
        f"/tramites/{tramite_id}/cargas/{carga['id']}/confirmacion", actor
    )
    if esperar is not None:
        esperar(api, actor, tramite_id, archivo["id"])
    return archivo


def _documento(
    api: ClienteApi,
    actor: str,
    tramite_id: int,
    nombre: str,
    datos: bytes,
    esperar: Esperar | None,
    tipo: str | None = None,
    campos: dict[str, str] | None = None,
) -> dict[str, Any]:
    archivo = _subir(api, actor, tramite_id, nombre, datos, esperar)
    documento: dict[str, Any] = api.post(
        f"/tramites/{tramite_id}/archivos/{archivo['id']}/incorporacion", actor, {"nombre": nombre}
    )
    validaciones = ({"tipo_documental": tipo} if tipo else {}) | (campos or {})
    for campo, valor in validaciones.items():
        api.post(
            f"/tramites/{tramite_id}/documentos/{documento['id']}/validaciones",
            actor,
            {"campo": campo, "valor_validado": valor},
        )
    return documento


def construir(api: ClienteApi, *, esperar: Esperar | None = None) -> Escenario:
    escenario = Escenario(marcadores=nuevos_marcadores())
    m = escenario.marcadores
    _cuentas(api, escenario)
    plantilla = api.post(
        "/plantillas-flujo",
        ADMINISTRADOR,
        {
            "nombre": "Seguridad: revisión de contratos",
            "alcance": "contrato",
            "pasos": [
                {"nombre": "Revisión", "revisor_por_defecto_id": escenario.usuarios[REVISOR]},
                {"nombre": "Aprobación", "revisor_por_defecto_id": escenario.usuarios[APROBADOR]},
            ],
        },
    )
    escenario.plantilla = {"id": plantilla["id"], "version": plantilla["version"]}

    # Trámite A: documentos validados, flujo confirmado y ciclo en curso.
    a = api.post("/tramites", DUENO, {"titulo": f"Seguridad A {m['titulo']}"})["id"]
    contrato = _documento(
        api,
        DUENO,
        a,
        f"contrato-{m['archivo']}.docx",
        documentos.contrato(m["a"], adversarial=True),
        esperar,
        "contrato",
        CAMPOS_CONTRATO,
    )
    api.post(f"/tramites/{a}/envio-a-validacion", DUENO)
    ciclo = api.post(
        f"/tramites/{a}/ciclos",
        DUENO,
        {"plantilla_id": plantilla["id"], "version_plantilla": plantilla["version"]},
    )
    tareas = {t["asignada_a_id"]: t["id"] for t in ciclo["tareas"]}
    escenario.ids |= {
        "tramite_a": a,
        "documento_a": contrato["id"],
        "version_a": contrato["version_vigente"]["id"],
        "tarea_revisor": tareas[escenario.usuarios[REVISOR]],
        "tarea_aprobador": tareas[escenario.usuarios[APROBADOR]],
    }

    # Trámite A2: Borrador para validar, vincular y desvincular.
    a2 = api.post("/tramites", DUENO, {"titulo": "Seguridad A2"})["id"]
    sin_validar = _documento(
        api, DUENO, a2, "contrato-a2.docx", documentos.contrato(m["a"]), esperar
    )
    c2 = _documento(
        api, DUENO, a2, "contrato-a2b.docx", documentos.contrato(m["a"]), esperar, "contrato"
    )
    o2 = _documento(
        api, DUENO, a2, "orden-a2.docx", documentos.orden(m["a"]), esperar, "orden_compra"
    )
    # Cargado sin incorporar: en A2, porque incorporar en A desplazaría el ciclo (PD-05).
    pendiente = _subir(api, DUENO, a2, "pendiente.docx", documentos.orden(m["a"]), esperar)
    descartable = _subir(api, DUENO, a2, "descartable.docx", documentos.orden(m["a"]), esperar)
    vinculo = api.post(
        f"/tramites/{a2}/vinculos",
        DUENO,
        {
            "documento_origen_id": o2["id"],
            "documento_destino_id": c2["id"],
            "tipo": "referencia",
            "justificacion": "Vínculo del escenario de seguridad",
        },
    )
    escenario.ids |= {
        "tramite_a2": a2,
        "documento_a2_sin_validar": sin_validar["id"],
        "documento_a2_contrato": c2["id"],
        "documento_a2_orden": o2["id"],
        "vinculo_a2": vinculo["id"],
        "archivo_pendiente_a2": pendiente["id"],
        "archivo_descartable_a2": descartable["id"],
    }

    # Trámite A3: validado y enviado, listo para confirmar el flujo.
    a3 = api.post("/tramites", DUENO, {"titulo": "Seguridad A3"})["id"]
    _documento(
        api,
        DUENO,
        a3,
        "contrato-a3.docx",
        documentos.contrato(m["a"]),
        esperar,
        "contrato",
        CAMPOS_CONTRATO,
    )
    api.post(f"/tramites/{a3}/envio-a-validacion", DUENO)
    escenario.ids["tramite_a3"] = a3

    # Trámite B del responsable ajeno.
    b = api.post("/tramites", AJENO, {"titulo": "Seguridad B"})["id"]
    documento_b = _documento(api, AJENO, b, "contrato-b.docx", documentos.contrato(m["b"]), esperar)
    escenario.ids |= {
        "tramite_b": b,
        "documento_b": documento_b["id"],
        "version_b": documento_b["version_vigente"]["id"],
    }

    # Trámite F: el procesamiento del DOCX vacío falla (camino de error de SEG-04).
    f = api.post("/tramites", DUENO, {"titulo": f"Seguridad F {m['fallo']}"})["id"]
    _subir(api, DUENO, f, f"vacio-{m['fallo']}.docx", documentos.vacio(), None)
    escenario.ids["tramite_f"] = f

    api.put(
        f"/usuarios/{escenario.usuarios[DESHABILITADA]}/estado",
        ADMINISTRADOR,
        {"estado": "deshabilitada"},
    )
    return escenario
