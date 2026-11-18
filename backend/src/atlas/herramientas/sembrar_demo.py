"""Semilla sintética de una sesión E90A, solo por la API (DO-2026-10-22-OPS P11, PD-07).

Uso (operador, con la API en `active` y solo cuentas ficticias):

    ATLAS_SEED_CLAVE_ADMINISTRADOR=… ATLAS_SEED_CLAVE_RESPONSABLE=… \\
    ATLAS_SEED_CLAVE_REVISOR=… ATLAS_SEED_CLAVE_APROBADOR=… \\
    python -m atlas.herramientas.sembrar_demo --url-api https://… --region us-east-1 \\
        --cliente-cognito <id> --usuarios admin=… responsable=… revisor=… aprobador=… \\
        --manifiesto operaciones/sesiones/<sesion>/manifiesto_seed.json

Deja cuatro trámites (DO-2026-10-22-WEB F8, DO-2026-10-23-VER P9, DO-2026-10-23-CIERRE P11):

1. **observado** (puntos de demo A a D): C-v1, O-v1 y F-v2 procesados, validados contra el
   oráculo y vinculados (R3 advierte que la orden está fuera de la vigencia); flujo
   confirmado; la revisión legal aprueba y la aprobación final observa con motivo.
2. **en vivo**: C-v1 procesado e incorporado, en Borrador, para recorrer A a D en vivo
   (validar, consultar, incorporar O-v1 y F-v2, decidir, cargar O-v2 como versión nueva).
3. **cerrado**: la historia completa. Tras la observación, O-v2 se carga, el sistema sugiere
   que es una versión nueva de O-v1 (RF-06) y el responsable la confirma (RF-07); se valida,
   R3 vuelve a ejecutarse, el ciclo 2 aprueba y el aprobador aplica la firma simulada sobre
   C-v1 (RF-23): el trámite queda Cerrado.
4. **cancelado**: sin documentos, cancelado por su responsable con motivo (RF-26).

Cada dato se valida como lo haría una persona: si la sugerencia coincide con el oráculo se
confirma; si no, se corrige al valor del oráculo; sin sugerencia, se registra. Un
procesamiento fallido detiene la semilla antes de incorporar: no se valida a mano lo que la
IA no llegó a sugerir. Nada se inserta en la base ni se falsifica auditoría.

`--escenario surdelta` (DO-2026-11-09-DEMO-SURDELTA) siembra en cambio la cartera de SurDelta
con los documentos de `demo/surdelta/documentos/` y su oráculo: la provisión de acero de la planta,
cerrada sin advertencias, una compra de equipos observada por R1 (la factura llegó con el
CUIT de otra empresa), una renovación de soporte pendiente de
aprobación y una contratación cancelada. El mantenimiento de planta (la factura v1 supera la
orden, R4; la v2 la corrige como versión nueva) queda en Borrador con la orden y la factura
validadas y sin vínculos: en la grabación se carga el contrato y se confirman los vínculos.
No admite `--reanudar`: ante un fallo se siembra una sesión nueva.

`--reanudar` continúa una semilla interrumpida sobre el mismo manifiesto, sin repetir ni
ocultar lo hecho: reintenta por la API los procesamientos fallidos del trámite en vivo
(RNF-06) y, si el trámite «cerrado» quedó a medias, lo cancela con el motivo real y siembra
uno nuevo. El reemplazado queda en el manifiesto (`reemplazados`).

Aunque el oráculo PD-07 v2 está congelado, la semilla prepara la demo: no acredita EVD-01 ni
métricas. El manifiesto guarda identificadores y huellas, nunca tokens.
"""

import argparse
import hashlib
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from atlas.herramientas.cliente_api import ClienteApi, ErrorApi, sub_del_token, tokens_cognito

RAIZ_REPOSITORIO: Final = Path(__file__).resolve().parents[4]
CORPUS: Final = RAIZ_REPOSITORIO / "demo" / "cadena_evidencia" / "documentos"
# Oráculo PD-07 v2, congelado: número estable en O y F (DO-2026-10-23-CIERRE D4,
# DO-2026-10-23-DIF, DIF-84).
ORACULO: Final = CORPUS.parent / "oraculo_PD07_v2.json"
ROLES: Final = ("administrador", "responsable", "revisor", "aprobador")

ARCHIVOS: Final = {
    "C-v1": "C-v1_Contrato_Mantenimiento_ATLAS.pdf",
    "O-v1": "O-v1_Orden_Compra.pdf",
    "F-v2": "F-v2_Factura.pdf",
    "O-v2": "O-v2_Orden_Compra.pdf",
}
NOMBRES: Final = {
    "C-v1": "Contrato de mantenimiento",
    "O-v1": "Orden de compra",
    "F-v2": "Factura",
}
# Personas ficticias del escenario (las de los mockups de §3.4 y §5.5).
NOMBRES_VISIBLES: Final = {
    "administrador": "Administración ATLAS",
    "responsable": "Laura Méndez",
    "revisor": "Martín Ríos",
    "aprobador": "Sofía Herrera",
}
MOTIVO_CANCELACION: Final = "El laboratorio resolvió no contratar el servicio este año."
MOTIVO_REEMPLAZO: Final = (
    "Semilla interrumpida por un fallo técnico de procesamiento al preparar la sesión; se"
    " reemplaza por un trámite nuevo con la historia completa."
)
MOTIVO_OBSERVACION: Final = (
    "La fecha de emisión de la orden de compra (15/03/2027) está fuera de la vigencia del"
    " contrato (01/03/2026 a 28/02/2027). Corregir la orden antes de aprobar."
)

# Razón social del proveedor y emisor: en el oráculo v2 (`razon_social`) y en la fuente
# reproducible (generadores/cadena_evidencia.py del repositorio atlas-tesis-datasets).
RAZON_SOCIAL_PROVEEDOR: Final = "Servicios Integrales del Sur S.A."

# Escenario SurDelta (DO-2026-11-09-DEMO-SURDELTA): fuente reproducible en
# generadores/surdelta.py del repositorio atlas-tesis-datasets; el oráculo guarda tipo,
# campos y huella por código.
CORPUS_SURDELTA: Final = RAIZ_REPOSITORIO / "demo" / "surdelta" / "documentos"
ORACULO_SURDELTA: Final = CORPUS_SURDELTA.parent / "oraculo_surdelta_v1.json"
NOMBRES_SURDELTA: Final = {
    "SD-C1": "Contrato de mantenimiento integral",
    "SD-O1": "Orden de compra OC-2026-118",
    "SD-F1": "Factura de octubre",
    "SD-P2": "Presupuesto de equipos",
    "SD-O2": "Orden de compra OC-2026-131",
    "SD-F3": "Factura de equipos",
    "SD-C3": "Contrato de soporte informático",
    "SD-P3": "Presupuesto de soporte",
    "SD-C4": "Contrato de provisión de acero",
    "SD-O4": "Orden de compra OC-2026-112",
    "SD-F4": "Factura de la entrega de octubre",
}
MOTIVO_OBSERVACION_SURDELTA: Final = (
    "La factura 0004-00001248 supera la orden de compra OC-2026-118 en ARS 1.200.000 por 40"
    " horas adicionales sin autorización previa por escrito (cláusula 5 del contrato). La"
    " fecha de la orden, anterior al inicio de la vigencia, es aceptable: corresponde al"
    " abono de octubre."
)
MOTIVO_OBSERVACION_CUIT: Final = (
    "La factura 0002-00000519 fue emitida por Horizonte Servicios S.R.L. (CUIT"
    " 30-98641014-3), que no es el proveedor de la orden de compra OC-2026-131. Pedir la"
    " factura al proveedor correcto antes de aprobar."
)
MOTIVO_CANCELACION_SURDELTA: Final = "SurDelta resolvió internalizar la limpieza de la planta."


def escenario(oraculo: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Tipo validado y valores esperados por documento, con los nombres del esquema."""
    c, o, f, o2 = (oraculo["documentos"][k] for k in ("C-v1", "O-v1", "F-v2", "O-v2"))
    return {
        "C-v1": {
            "tipo_documental": "contrato",
            **{
                k: c[k]
                for k in (
                    "contraparte",
                    "cuit_contraparte",
                    "fecha_celebracion",
                    "vigencia_desde",
                    "vigencia_hasta",
                    "monto_total",
                    "moneda",
                )
            },
        },
        "O-v1": {
            "tipo_documental": "orden_compra",
            "numero": o["numero"],
            "fecha": o["fecha_emision"],
            "proveedor": RAZON_SOCIAL_PROVEEDOR,
            "cuit_proveedor": o["cuit_proveedor"],
            "importe_total": o["total"],
            "moneda": o["moneda"],
        },
        "O-v2": {
            "tipo_documental": "orden_compra",
            "numero": o2["numero"],
            "fecha": o2["fecha_emision"],
            "proveedor": RAZON_SOCIAL_PROVEEDOR,
            "cuit_proveedor": o2["cuit_proveedor"],
            "importe_total": o2["total"],
            "moneda": o2["moneda"],
        },
        "F-v2": {
            "tipo_documental": "factura",
            "numero": f["numero"],
            "fecha_emision": f["fecha_emision"],
            "emisor": RAZON_SOCIAL_PROVEEDOR,
            "cuit_emisor": f["cuit_emisor"],
            "importe_total": f["total"],
            "moneda": f["moneda"],
        },
    }


EsperarProcesamiento = Callable[[ClienteApi, int, list[int]], None]


def esperar_procesamiento(
    cliente: ClienteApi,
    tramite_id: int,
    archivos: list[int],
    *,
    maximo_s: float = 900,
    intervalo_s: float = 10,
) -> None:
    """Espera a que cada trabajo termine (Step Functions, Textract y Bedrock reales)."""
    limite = time.monotonic() + maximo_s
    while True:
        estados = {
            a["id"]: (a.get("trabajo") or {}).get("estado")
            for a in cliente.get(f"/tramites/{tramite_id}/archivos", "responsable")
            if a["id"] in archivos
        }
        if all(e in ("completado", "fallido") for e in estados.values()):
            return
        if time.monotonic() > limite:
            raise RuntimeError("El procesamiento no terminó dentro del tiempo máximo")
        time.sleep(intervalo_s)


@dataclass
class Manifiesto:
    sesion: str
    url_api: str
    oraculo: str
    corpus: dict[str, str]
    iniciado_en: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    cuentas: dict[str, int] = field(default_factory=dict)
    plantilla_id: int | None = None
    plantilla_general_id: int | None = None
    tramites: dict[str, dict[str, Any]] = field(default_factory=dict)
    reemplazados: list[dict[str, Any]] = field(default_factory=list)
    reanudaciones: list[str] = field(default_factory=list)
    terminado_en: str | None = None
    resultado: str = "en_curso"


class Sembrador:
    def __init__(
        self,
        cliente: ClienteApi,
        manifiesto: Manifiesto,
        oraculo: dict[str, Any],
        esperar: EsperarProcesamiento = esperar_procesamiento,
    ) -> None:
        self.api = cliente
        self.m = manifiesto
        self.esperar = esperar
        self._preparar(oraculo)

    def _preparar(self, oraculo: dict[str, Any]) -> None:
        """Valores esperados, archivos y nombres de los documentos del escenario."""
        self.valores = escenario(oraculo)
        self.archivos = {c: CORPUS / a for c, a in ARCHIVOS.items()}
        self.nombres = dict(NOMBRES)

    # --- Cuentas y plantilla --------------------------------------------------------

    def preparar_cuentas(self) -> None:
        """El administrador inicial ya existe (crear_administrador). Las demás cuentas se dan
        de alta por su `sub` de Cognito, con roles mínimos (RF-25, RC-P03)."""
        yo = self.api.get("/usuarios/yo", "administrador")
        self.m.cuentas["administrador"] = yo["id"]
        self.api.put(
            f"/usuarios/{yo['id']}/nombre",
            "administrador",
            {"nombre_visible": NOMBRES_VISIBLES["administrador"]},
        )
        existentes = {
            c["identificador_externo"]: c for c in self.api.get("/usuarios", "administrador")
        }
        roles = {
            "responsable": "responsable_tramite",
            "revisor": "revisor_aprobador",
            "aprobador": "revisor_aprobador",
        }
        for clave, rol in roles.items():
            sub = sub_del_token(self.api.tokens[clave])
            cuenta = existentes.get(sub) or self.api.post(
                "/usuarios", "administrador", {"identificador_externo": sub}
            )
            self.api.put(
                f"/usuarios/{cuenta['id']}/nombre",
                "administrador",
                {"nombre_visible": NOMBRES_VISIBLES[clave]},
            )
            self.api.put(f"/usuarios/{cuenta['id']}/roles/{rol}", "administrador")
            if clave == "aprobador":
                self.api.put(
                    f"/usuarios/{cuenta['id']}/autorizacion-cierre",
                    "administrador",
                    {"otorgada": True},
                )
            self.m.cuentas[clave] = cuenta["id"]

    def crear_plantilla(
        self, alcance: str = "contrato", nombre: str = "Revisión de contratos"
    ) -> int:
        plantilla = self.api.post(
            "/plantillas-flujo",
            "administrador",
            {
                "nombre": nombre,
                "alcance": alcance,
                "pasos": [
                    {
                        "nombre": "Revisión legal",
                        "revisor_por_defecto_id": self.m.cuentas["revisor"],
                    },
                    {
                        "nombre": "Aprobación final",
                        "revisor_por_defecto_id": self.m.cuentas["aprobador"],
                    },
                ],
            },
        )
        if alcance == "contrato":
            self.m.plantilla_id = plantilla["id"]
        identificador: int = plantilla["id"]
        return identificador

    # --- Documentos -----------------------------------------------------------------

    def _cargar(self, tramite_id: int, codigo: str) -> int:
        ruta = self.archivos[codigo]
        datos = ruta.read_bytes()
        carga = self.api.post(
            f"/tramites/{tramite_id}/cargas",
            "responsable",
            {"nombre": ruta.name, "formato": "pdf", "tamano_bytes": len(datos)},
        )
        self.api.transferir(carga["url"], carga["encabezados"], datos)
        confirmado = self.api.post(
            f"/tramites/{tramite_id}/cargas/{carga['id']}/confirmacion", "responsable"
        )
        archivo_id: int = confirmado["id"]
        return archivo_id

    def _estados_trabajo(self, tramite_id: int, archivos: list[int]) -> dict[int, str | None]:
        return {
            a["id"]: (a.get("trabajo") or {}).get("estado")
            for a in self.api.get(f"/tramites/{tramite_id}/archivos", "responsable")
            if a["id"] in archivos
        }

    def _procesar(self, tramite_id: int, archivos: list[int]) -> None:
        """Espera y exige que cada trabajo haya terminado bien."""
        self.esperar(self.api, tramite_id, archivos)
        fallidos = sorted(
            a for a, e in self._estados_trabajo(tramite_id, archivos).items() if e != "completado"
        )
        if fallidos:
            raise RuntimeError(
                f"Procesamiento fallido de los archivos {fallidos} del trámite {tramite_id}"
            )

    def _incorporar(self, registro: dict[str, Any]) -> None:
        for codigo, archivo_id in registro["archivos"].items():
            if codigo in registro["documentos"]:
                continue
            documento = self.api.post(
                f"/tramites/{registro['id']}/archivos/{archivo_id}/incorporacion",
                "responsable",
                {"nombre": self.nombres[codigo]},
            )
            registro["documentos"][codigo] = documento["id"]

    def cargar_documentos(
        self, clave: str, titulo: str, codigos: tuple[str, ...]
    ) -> dict[str, Any]:
        tramite = self.api.post("/tramites", "responsable", {"titulo": titulo})
        registro: dict[str, Any] = {"id": tramite["id"], "documentos": {}, "archivos": {}}
        self.m.tramites[clave] = registro
        for codigo in codigos:
            registro["archivos"][codigo] = self._cargar(tramite["id"], codigo)
        self._procesar(tramite["id"], list(registro["archivos"].values()))
        self._incorporar(registro)
        return registro

    def reintentar_fallidos(self, registro: dict[str, Any]) -> None:
        """RNF-06: intento nuevo, por la API, de cada procesamiento fallido del trámite."""
        archivos = list(registro["archivos"].values())
        fallidos = [
            a for a, e in self._estados_trabajo(registro["id"], archivos).items() if e == "fallido"
        ]
        for archivo_id in fallidos:
            self.api.post(
                f"/tramites/{registro['id']}/archivos/{archivo_id}/reintento", "responsable"
            )
        registro.setdefault("reintentos", []).extend(fallidos)
        self._procesar(registro["id"], archivos)
        self._incorporar(registro)

    def _validar_dato(
        self, tramite_id: int, documento_id: int, dato: dict[str, Any], valor: str
    ) -> str:
        sugerencia = dato.get("sugerencia")
        vigente = dato.get("vigente")
        registrada = self.api.post(
            f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones",
            "responsable",
            {
                "campo": dato["campo"],
                "valor_validado": valor,
                "valor_sugerido_id": sugerencia["id"] if sugerencia else None,
                "reemplaza_a_id": vigente["id"] if vigente else None,
            },
        )
        tipo: str = registrada["tipo"]
        return tipo

    def _validar_documento(self, tramite_id: int, documento_id: int, codigo: str) -> dict[str, str]:
        """Clasificación primero (DO-2026-10-22-VAL P3) y después cada campo del esquema."""
        ruta = f"/tramites/{tramite_id}/documentos/{documento_id}/validaciones"
        valores = self.valores[codigo]
        tipos = {
            "tipo_documental": self._validar_dato(
                tramite_id,
                documento_id,
                self.api.get(ruta, "responsable")["clasificacion"],
                valores["tipo_documental"],
            )
        }
        for dato in self.api.get(ruta, "responsable")["campos"]:
            tipos[dato["campo"]] = self._validar_dato(
                tramite_id, documento_id, dato, valores[dato["campo"]]
            )
        return tipos

    def validar(self, registro: dict[str, Any]) -> None:
        registro["validaciones"] = {
            codigo: self._validar_documento(registro["id"], documento_id, codigo)
            for codigo, documento_id in registro["documentos"].items()
        }

    def _controles(self, tramite_id: int) -> dict[str, str]:
        controles = self.api.get(f"/tramites/{tramite_id}/controles", "responsable")["vigentes"]
        return {c["codigo_regla"][:2]: c["resultado"] for c in controles}

    def vincular(
        self,
        registro: dict[str, Any],
        pares: tuple[tuple[str, str], ...] = (("O-v1", "C-v1"), ("F-v2", "O-v1")),
        tipo: str = "campos",
        justificacion: str = "Comparten el CUIT validado del proveedor",
    ) -> None:
        """RF-15: confirma el vínculo sugerido; si no lo hay, lo crea (RF-14)."""
        tramite_id, docs = registro["id"], registro["documentos"]
        registro["vinculos"] = []
        for origen, destino in pares:
            par = {docs[origen], docs[destino]}
            sugeridos = self.api.get(f"/tramites/{tramite_id}/vinculos", "responsable")["sugeridos"]
            sugerido = next(
                (
                    v
                    for v in sugeridos
                    if {v["documento_origen_id"], v["documento_destino_id"]} == par
                ),
                None,
            )
            if sugerido is not None:
                vinculo = self.api.post(
                    f"/tramites/{tramite_id}/vinculos/{sugerido['id']}/confirmacion", "responsable"
                )
            else:
                vinculo = self.api.post(
                    f"/tramites/{tramite_id}/vinculos",
                    "responsable",
                    {
                        "documento_origen_id": docs[origen],
                        "documento_destino_id": docs[destino],
                        "tipo": tipo,
                        "justificacion": justificacion,
                    },
                )
            registro["vinculos"].append(vinculo["id"])
        registro["controles"] = self._controles(tramite_id)

    def _ciclo(self, tramite_id: int) -> dict[str, Any]:
        self.api.post(f"/tramites/{tramite_id}/envio-a-validacion", "responsable")
        sugerido = self.api.get(f"/tramites/{tramite_id}/flujo-sugerido", "responsable")
        ciclo: dict[str, Any] = self.api.post(
            f"/tramites/{tramite_id}/ciclos",
            "responsable",
            {
                "plantilla_id": sugerido["plantilla_id"],
                "version_plantilla": sugerido["version_plantilla"],
            },
        )
        return ciclo

    def revisar(
        self, registro: dict[str, Any], observa: str = "aprobador", motivo: str = MOTIVO_OBSERVACION
    ) -> None:
        """Ciclo 1: observa el revisor en la primera tarea (las siguientes se descartan) o
        el aprobador en la última, después de que el revisor apruebe la suya."""
        tramite_id = registro["id"]
        ciclo = self._ciclo(tramite_id)
        registro["ciclo"] = ciclo["id"]
        legal, final = ciclo["tareas"]
        observar = {"tipo": "observacion", "motivo": motivo}
        if observa == "revisor":
            decisiones = [self.api.post(f"/tareas/{legal['id']}/decision", "revisor", observar)]
        else:
            decisiones = [
                self.api.post(f"/tareas/{legal['id']}/decision", "revisor", {"tipo": "aprobacion"}),
                self.api.post(f"/tareas/{final['id']}/decision", "aprobador", observar),
            ]
        registro["decisiones"] = [d["id"] for d in decisiones]
        registro["estado"] = self.api.get(f"/tramites/{tramite_id}", "responsable")["estado"]

    def corregir_con_version(
        self, registro: dict[str, Any], nueva: str = "O-v2", anterior: str = "O-v1"
    ) -> None:
        """EVD-B 3: la versión nueva confirmada del documento observado. Solo se confirma la
        relación que sugiere el sistema (RF-06); si no la sugiere, la semilla se detiene."""
        tramite_id = registro["id"]
        archivo_id = self._cargar(tramite_id, nueva)
        registro["archivos"][nueva] = archivo_id
        self._procesar(tramite_id, [archivo_id])
        archivo = next(
            a
            for a in self.api.get(f"/tramites/{tramite_id}/archivos", "responsable")
            if a["id"] == archivo_id
        )
        sugerencia = archivo.get("sugerencia_version") or {}
        if sugerencia.get("documento_id") != registro["documentos"][anterior]:
            raise RuntimeError(f"RF-06 no sugirió {nueva} como versión nueva de {anterior}")
        registro["criterio_version"] = sugerencia["criterio"]
        documento = self.api.post(
            f"/tramites/{tramite_id}/archivos/{archivo_id}/version", "responsable"
        )
        registro["version_nueva"] = documento["version_vigente"]["id"]
        registro["validaciones"][nueva] = self._validar_documento(
            tramite_id, documento["id"], nueva
        )
        registro["controles_corregidos"] = self._controles(tramite_id)

    def cerrar(self, registro: dict[str, Any], contrato: str = "C-v1") -> None:
        """EVD-B 4 y V11: ciclo 2 aprobado por las dos tareas y firma simulada del contrato."""
        tramite_id = registro["id"]
        ciclo = self._ciclo(tramite_id)
        registro["ciclo_2"] = ciclo["id"]
        legal, final = ciclo["tareas"]
        registro["decisiones_2"] = [
            self.api.post(f"/tareas/{legal['id']}/decision", "revisor", {"tipo": "aprobacion"})[
                "id"
            ],
            self.api.post(f"/tareas/{final['id']}/decision", "aprobador", {"tipo": "aprobacion"})[
                "id"
            ],
        ]
        firmada = next(
            v for v in ciclo["versiones"] if v["documento_id"] == registro["documentos"][contrato]
        )
        firma = self.api.post(
            f"/tramites/{tramite_id}/firma", "aprobador", {"version_id": firmada["version_id"]}
        )
        registro["firma"] = {
            "id": firma["id"],
            "version_id": firma["version_id"],
            "referencia_integridad": firma["referencia_integridad"],
        }
        registro["estado"] = self.api.get(f"/tramites/{tramite_id}", "responsable")["estado"]

    # --- Recorrido completo ---------------------------------------------------------

    def _exigir_active(self) -> None:
        if self.api.get("/salud")["operacion"] != "active":
            raise RuntimeError("La API no está en active: no se siembra")

    def _estado(self, registro: dict[str, Any]) -> None:
        registro["estado"] = self.api.get(f"/tramites/{registro['id']}", "responsable")["estado"]

    def sembrar_observado(self) -> None:
        observado = self.cargar_documentos(
            "observado", "Servicio de mantenimiento de laboratorio", ("C-v1", "O-v1", "F-v2")
        )
        self.validar(observado)
        self.vincular(observado)
        self.revisar(observado)

    def sembrar_en_vivo(self) -> None:
        en_vivo = self.cargar_documentos(
            "en_vivo", "Servicio de mantenimiento de laboratorio (en vivo)", ("C-v1",)
        )
        self._estado(en_vivo)

    def sembrar_cerrado(self) -> None:
        cerrado = self.cargar_documentos(
            "cerrado",
            "Servicio de mantenimiento de laboratorio (historia completa)",
            ("C-v1", "O-v1", "F-v2"),
        )
        self.validar(cerrado)
        self.vincular(cerrado)
        self.revisar(cerrado)
        self.corregir_con_version(cerrado)
        self.cerrar(cerrado)

    def sembrar_cancelado(
        self,
        titulo: str = "Mantenimiento de equipos (cancelado)",
        motivo: str = MOTIVO_CANCELACION,
    ) -> None:
        tramite = self.api.post("/tramites", "responsable", {"titulo": titulo})
        cancelado = self.api.post(
            f"/tramites/{tramite['id']}/cancelacion", "responsable", {"motivo": motivo}
        )
        self.m.tramites["cancelado"] = {"id": tramite["id"], "estado": cancelado["estado"]}

    def _terminar(self) -> Manifiesto:
        self.m.resultado = "completado"
        self.m.terminado_en = datetime.now(UTC).isoformat()
        return self.m

    def ejecutar(self) -> Manifiesto:
        self._exigir_active()
        self.preparar_cuentas()
        self.crear_plantilla()
        self.sembrar_observado()
        self.sembrar_en_vivo()
        self.sembrar_cerrado()
        self.sembrar_cancelado()
        return self._terminar()

    def reanudar(self) -> Manifiesto:
        """Continúa una semilla interrumpida. Lo ya hecho no se repite; lo que quedó a medias
        se completa por la API (en vivo) o se cancela con su motivo y se reemplaza (cerrado)."""
        self._exigir_active()
        self.m.reanudaciones.append(datetime.now(UTC).isoformat())
        if (
            self.m.plantilla_id is None
            or self.m.tramites.get("observado", {}).get("estado") != "observado"
        ):
            raise RuntimeError("El trámite observado no quedó completo: sembrar de nuevo")
        en_vivo = self.m.tramites.get("en_vivo")
        if en_vivo is None:
            self.sembrar_en_vivo()
        else:
            self.reintentar_fallidos(en_vivo)
            self._estado(en_vivo)
        cerrado = self.m.tramites.get("cerrado")
        if cerrado is not None and cerrado.get("estado") != "cerrado":
            respuesta = self.api.post(
                f"/tramites/{cerrado['id']}/cancelacion",
                "responsable",
                {"motivo": MOTIVO_REEMPLAZO},
            )
            cerrado["estado"] = respuesta["estado"]
            cerrado["motivo_cancelacion"] = MOTIVO_REEMPLAZO
            self.m.reemplazados.append(self.m.tramites.pop("cerrado"))
        if "cerrado" not in self.m.tramites:
            self.sembrar_cerrado()
        if "cancelado" not in self.m.tramites:
            self.sembrar_cancelado()
        return self._terminar()


def escenario_surdelta(oraculo: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Tipo validado y valores esperados por código, tal como los guarda el oráculo."""
    return {
        codigo: {"tipo_documental": doc["tipo_documental"], **doc["campos"]}
        for codigo, doc in oraculo["documentos"].items()
    }


class SembradorSurDelta(Sembrador):
    """La cartera de SurDelta (DO-2026-11-09-DEMO-SURDELTA), con los mismos pasos por la API."""

    def _preparar(self, oraculo: dict[str, Any]) -> None:
        self.valores = escenario_surdelta(oraculo)
        self.archivos = {
            c: CORPUS_SURDELTA / d["archivo"] for c, d in oraculo["documentos"].items()
        }
        self.nombres = dict(NOMBRES_SURDELTA)

    def sembrar_historia(self) -> None:
        """El recorrido de los videos: la factura v1 supera la orden (R4) y la fecha de la
        orden es anterior a la vigencia (R3); el revisor observa, la v2 corrige la factura y
        el ciclo 2 cierra. No forma parte de la cartera (en la grabación se crea en vivo y un
        duplicado confundiría); lo usan las pruebas para verificar la historia por la API."""
        historia = self.cargar_documentos(
            "cerrado", "Mantenimiento integral de planta", ("SD-C1", "SD-O1", "SD-F1")
        )
        self.validar(historia)
        self.vincular(historia, (("SD-O1", "SD-C1"), ("SD-F1", "SD-O1")))
        self.revisar(historia, observa="revisor", motivo=MOTIVO_OBSERVACION_SURDELTA)
        self.corregir_con_version(historia, nueva="SD-F2", anterior="SD-F1")
        self.cerrar(historia, contrato="SD-C1")

    def sembrar_en_vivo(self) -> None:
        """El trámite de la grabación, a medio armar para que entre en 5 minutos: la orden y
        la factura v1 ya validadas, sin vínculos confirmados (ningún control corre todavía).
        En el video la responsable carga y valida el contrato y confirma los vínculos."""
        en_vivo = self.cargar_documentos(
            "en_vivo", "Mantenimiento integral de planta", ("SD-O1", "SD-F1")
        )
        self.validar(en_vivo)
        self._estado(en_vivo)

    def sembrar_suministro(self) -> None:
        """El caso habitual de la planta: contrato, orden y factura coinciden y cierra."""
        suministro = self.cargar_documentos(
            "suministro",
            "Provisión de acero inoxidable para la línea de válvulas",
            ("SD-C4", "SD-O4", "SD-F4"),
        )
        self.validar(suministro)
        self.vincular(suministro, (("SD-O4", "SD-C4"), ("SD-F4", "SD-O4")))
        self.cerrar(suministro, contrato="SD-C4")

    def sembrar_compra(self) -> None:
        """La factura llegó con el CUIT de otra empresa: sin vínculo sugerido, R1 advierte."""
        compra = self.cargar_documentos(
            "observado", "Compra de equipos para el área comercial", ("SD-P2", "SD-O2", "SD-F3")
        )
        self.validar(compra)
        self.vincular(
            compra,
            (("SD-F3", "SD-O2"),),
            tipo="referencia",
            justificacion="La factura cita la orden de compra OC-2026-131",
        )
        self.revisar(compra, observa="revisor", motivo=MOTIVO_OBSERVACION_CUIT)

    def sembrar_renovacion(self) -> None:
        renovacion = self.cargar_documentos(
            "pendiente", "Renovación de soporte informático", ("SD-C3", "SD-P3")
        )
        self.validar(renovacion)
        renovacion["ciclo"] = self._ciclo(renovacion["id"])["id"]
        self._estado(renovacion)

    def ejecutar(self) -> Manifiesto:
        self._exigir_active()
        self.preparar_cuentas()
        self.crear_plantilla()
        self.m.plantilla_general_id = self.crear_plantilla("general", "Revisión de compras")
        self.sembrar_suministro()
        self.sembrar_en_vivo()
        self.sembrar_compra()
        self.sembrar_renovacion()
        self.sembrar_cancelado("Contratación de limpieza", MOTIVO_CANCELACION_SURDELTA)
        return self._terminar()

    def reanudar(self) -> Manifiesto:
        raise RuntimeError("El escenario SurDelta no se reanuda: sembrar una sesión nueva")


def huellas_surdelta(oraculo: dict[str, Any]) -> dict[str, str]:
    return {
        d["archivo"]: hashlib.sha256((CORPUS_SURDELTA / d["archivo"]).read_bytes()).hexdigest()
        for d in oraculo["documentos"].values()
    }


def verificar_corpus_surdelta(oraculo: dict[str, Any]) -> dict[str, str]:
    """Rechaza documentos que no coinciden con las huellas del oráculo SurDelta."""
    huellas = huellas_surdelta(oraculo)
    for doc in oraculo["documentos"].values():
        if huellas[doc["archivo"]] != doc["sha256"]:
            raise RuntimeError(f"La huella de {doc['archivo']} no coincide con el oráculo")
    return huellas


def huellas_corpus() -> dict[str, str]:
    return {a: hashlib.sha256((CORPUS / a).read_bytes()).hexdigest() for a in ARCHIVOS.values()}


def verificar_corpus(oraculo: dict[str, Any]) -> dict[str, str]:
    """Rechaza un corpus que no coincide con las huellas del oráculo (PD-07)."""
    huellas = huellas_corpus()
    for archivo, huella in huellas.items():
        if oraculo["archivos_pdf"][archivo]["sha256"] != huella:
            raise RuntimeError(f"La huella de {archivo} no coincide con el oráculo")
    return huellas


def guardar(manifiesto: Manifiesto, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(manifiesto.__dict__, indent=2, ensure_ascii=False) + "\n")


def main(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--url-api", required=True)
    analizador.add_argument("--sesion", required=True)
    analizador.add_argument("--region", default="us-east-1")
    analizador.add_argument("--cliente-cognito", required=True)
    analizador.add_argument(
        "--usuarios", nargs=4, required=True, metavar="ROL=USUARIO", help="Los cuatro roles"
    )
    analizador.add_argument("--manifiesto", required=True, type=Path)
    analizador.add_argument(
        "--reanudar",
        action="store_true",
        help="Continúa la semilla interrumpida del manifiesto (misma sesión y API)",
    )
    analizador.add_argument(
        "--escenario",
        choices=("pd07", "surdelta"),
        default="pd07",
        help="pd07 (predeterminado) o la cartera SurDelta (DO-2026-11-09-DEMO-SURDELTA)",
    )
    opciones = analizador.parse_args(argumentos)
    usuarios = dict(u.split("=", 1) for u in opciones.usuarios)
    if set(usuarios) != set(ROLES):
        print(f"Se esperan exactamente los roles {', '.join(ROLES)}", file=sys.stderr)
        return 2
    surdelta = opciones.escenario == "surdelta"
    if surdelta and opciones.reanudar:
        print("El escenario SurDelta no se reanuda: sembrar una sesión nueva", file=sys.stderr)
        return 2
    oraculo = json.loads((ORACULO_SURDELTA if surdelta else ORACULO).read_text(encoding="utf-8"))
    corpus = verificar_corpus_surdelta(oraculo) if surdelta else verificar_corpus(oraculo)
    if opciones.reanudar:
        if not opciones.manifiesto.exists():
            print("No hay manifiesto que reanudar", file=sys.stderr)
            return 1
        manifiesto = Manifiesto(**json.loads(opciones.manifiesto.read_text(encoding="utf-8")))
        if not manifiesto.resultado.startswith("fallido") or (
            manifiesto.sesion,
            manifiesto.url_api,
            manifiesto.corpus,
        ) != (opciones.sesion, opciones.url_api, corpus):
            print(
                "Solo se reanuda una semilla interrumpida de la misma sesión, API y corpus",
                file=sys.stderr,
            )
            return 1
    elif opciones.manifiesto.exists():
        print(
            "El manifiesto ya existe: no se repite una semilla sobre datos sin auditar",
            file=sys.stderr,
        )
        return 1
    else:
        manifiesto = Manifiesto(
            sesion=opciones.sesion,
            url_api=opciones.url_api,
            oraculo=f"{oraculo['id']} ({oraculo['estado']})",
            corpus=corpus,
        )
    cliente = ClienteApi(
        opciones.url_api, tokens_cognito(opciones.region, opciones.cliente_cognito, usuarios)
    )
    sembrador = (SembradorSurDelta if surdelta else Sembrador)(cliente, manifiesto, oraculo)
    try:
        sembrador.reanudar() if opciones.reanudar else sembrador.ejecutar()
    except (ErrorApi, RuntimeError) as error:
        manifiesto.resultado = f"fallido: {error}"
        guardar(manifiesto, opciones.manifiesto)
        print(f"Semilla interrumpida: {error}. Mantener offline y revisar.", file=sys.stderr)
        return 1
    guardar(manifiesto, opciones.manifiesto)
    print(f"Semilla completa: {len(manifiesto.tramites)} trámites ({opciones.manifiesto})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
