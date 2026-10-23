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
confirma; si no, se corrige al valor del oráculo; sin sugerencia, se registra. Nada se
inserta en la base ni se falsifica auditoría. El oráculo es **preliminar** (P14): la semilla
no acredita EVD-01 ni métricas. El manifiesto guarda identificadores y huellas, nunca tokens.
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
CORPUS: Final = RAIZ_REPOSITORIO / "corpus"
# Oráculo v2 preliminar: número estable en O y F (DO-2026-10-23-CIERRE D4, DIF-84).
ORACULO: Final = RAIZ_REPOSITORIO / "oraculos" / "oraculo_PD07_v2_preliminar.json"
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
MOTIVO_OBSERVACION: Final = (
    "La fecha de emisión de la orden de compra (15/03/2027) está fuera de la vigencia del"
    " contrato (01/03/2026 a 28/02/2027). Corregir la orden antes de aprobar."
)

# Razón social del proveedor y emisor: en el oráculo v2 (`razon_social`) y en la fuente
# reproducible del corpus (herramientas/generar_corpus.py, «Proveedor / emisor»).
RAZON_SOCIAL_PROVEEDOR: Final = "Servicios Integrales del Sur S.A."


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
    tramites: dict[str, dict[str, Any]] = field(default_factory=dict)
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
        self.valores = escenario(oraculo)
        self.esperar = esperar

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

    def crear_plantilla(self) -> None:
        plantilla = self.api.post(
            "/plantillas-flujo",
            "administrador",
            {
                "nombre": "Revisión de contratos",
                "alcance": "contrato",
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
        self.m.plantilla_id = plantilla["id"]

    # --- Documentos -----------------------------------------------------------------

    def _cargar(self, tramite_id: int, codigo: str) -> int:
        archivo = ARCHIVOS[codigo]
        datos = (CORPUS / archivo).read_bytes()
        carga = self.api.post(
            f"/tramites/{tramite_id}/cargas",
            "responsable",
            {"nombre": archivo, "formato": "pdf", "tamano_bytes": len(datos)},
        )
        self.api.transferir(carga["url"], carga["encabezados"], datos)
        confirmado = self.api.post(
            f"/tramites/{tramite_id}/cargas/{carga['id']}/confirmacion", "responsable"
        )
        archivo_id: int = confirmado["id"]
        return archivo_id

    def cargar_documentos(
        self, clave: str, titulo: str, codigos: tuple[str, ...]
    ) -> dict[str, Any]:
        tramite = self.api.post("/tramites", "responsable", {"titulo": titulo})
        registro: dict[str, Any] = {"id": tramite["id"], "documentos": {}, "archivos": {}}
        self.m.tramites[clave] = registro
        for codigo in codigos:
            registro["archivos"][codigo] = self._cargar(tramite["id"], codigo)
        self.esperar(self.api, tramite["id"], list(registro["archivos"].values()))
        for codigo, archivo_id in registro["archivos"].items():
            documento = self.api.post(
                f"/tramites/{tramite['id']}/archivos/{archivo_id}/incorporacion",
                "responsable",
                {"nombre": NOMBRES[codigo]},
            )
            registro["documentos"][codigo] = documento["id"]
        return registro

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

    def vincular(self, registro: dict[str, Any]) -> None:
        """RF-15: confirma el vínculo sugerido; si no lo hay, lo crea (RF-14)."""
        tramite_id, docs = registro["id"], registro["documentos"]
        registro["vinculos"] = []
        for origen, destino in (("O-v1", "C-v1"), ("F-v2", "O-v1")):
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
                        "tipo": "campos",
                        "justificacion": "Comparten el CUIT validado del proveedor",
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

    def revisar(self, registro: dict[str, Any]) -> None:
        tramite_id = registro["id"]
        ciclo = self._ciclo(tramite_id)
        registro["ciclo"] = ciclo["id"]
        legal, final = ciclo["tareas"]
        aprobacion = self.api.post(
            f"/tareas/{legal['id']}/decision", "revisor", {"tipo": "aprobacion"}
        )
        observacion = self.api.post(
            f"/tareas/{final['id']}/decision",
            "aprobador",
            {"tipo": "observacion", "motivo": MOTIVO_OBSERVACION},
        )
        registro["decisiones"] = [aprobacion["id"], observacion["id"]]
        registro["estado"] = self.api.get(f"/tramites/{tramite_id}", "responsable")["estado"]

    def corregir_con_version(self, registro: dict[str, Any]) -> None:
        """EVD-B 3: O-v2 como versión nueva confirmada de O-v1. Solo se confirma la relación
        que sugiere el sistema (RF-06); si no la sugiere, la semilla se detiene."""
        tramite_id = registro["id"]
        archivo_id = self._cargar(tramite_id, "O-v2")
        registro["archivos"]["O-v2"] = archivo_id
        self.esperar(self.api, tramite_id, [archivo_id])
        archivo = next(
            a
            for a in self.api.get(f"/tramites/{tramite_id}/archivos", "responsable")
            if a["id"] == archivo_id
        )
        sugerencia = archivo.get("sugerencia_version") or {}
        if sugerencia.get("documento_id") != registro["documentos"]["O-v1"]:
            raise RuntimeError("RF-06 no sugirió O-v2 como versión nueva de O-v1")
        registro["criterio_version"] = sugerencia["criterio"]
        documento = self.api.post(
            f"/tramites/{tramite_id}/archivos/{archivo_id}/version", "responsable"
        )
        registro["version_nueva"] = documento["version_vigente"]["id"]
        registro["validaciones"]["O-v2"] = self._validar_documento(
            tramite_id, documento["id"], "O-v2"
        )
        registro["controles_corregidos"] = self._controles(tramite_id)

    def cerrar(self, registro: dict[str, Any]) -> None:
        """EVD-B 4 y V11: ciclo 2 aprobado por las dos tareas y firma simulada de C-v1."""
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
        contrato = next(
            v for v in ciclo["versiones"] if v["documento_id"] == registro["documentos"]["C-v1"]
        )
        firma = self.api.post(
            f"/tramites/{tramite_id}/firma", "aprobador", {"version_id": contrato["version_id"]}
        )
        registro["firma"] = {
            "id": firma["id"],
            "version_id": firma["version_id"],
            "referencia_integridad": firma["referencia_integridad"],
        }
        registro["estado"] = self.api.get(f"/tramites/{tramite_id}", "responsable")["estado"]

    # --- Recorrido completo ---------------------------------------------------------

    def ejecutar(self) -> Manifiesto:
        salud = self.api.get("/salud")
        if salud["operacion"] != "active":
            raise RuntimeError("La API no está en active: no se siembra")
        self.preparar_cuentas()
        self.crear_plantilla()
        observado = self.cargar_documentos(
            "observado", "Servicio de mantenimiento de laboratorio", ("C-v1", "O-v1", "F-v2")
        )
        self.validar(observado)
        self.vincular(observado)
        self.revisar(observado)
        en_vivo = self.cargar_documentos(
            "en_vivo", "Servicio de mantenimiento de laboratorio (en vivo)", ("C-v1",)
        )
        en_vivo["estado"] = self.api.get(f"/tramites/{en_vivo['id']}", "responsable")["estado"]
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
        tramite = self.api.post(
            "/tramites", "responsable", {"titulo": "Mantenimiento de equipos (cancelado)"}
        )
        cancelado = self.api.post(
            f"/tramites/{tramite['id']}/cancelacion", "responsable", {"motivo": MOTIVO_CANCELACION}
        )
        self.m.tramites["cancelado"] = {"id": tramite["id"], "estado": cancelado["estado"]}
        self.m.resultado = "completado"
        self.m.terminado_en = datetime.now(UTC).isoformat()
        return self.m


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
    opciones = analizador.parse_args(argumentos)
    if opciones.manifiesto.exists():
        print(
            "El manifiesto ya existe: no se repite una semilla sobre datos sin auditar",
            file=sys.stderr,
        )
        return 1
    usuarios = dict(u.split("=", 1) for u in opciones.usuarios)
    if set(usuarios) != set(ROLES):
        print(f"Se esperan exactamente los roles {', '.join(ROLES)}", file=sys.stderr)
        return 2
    oraculo = json.loads(ORACULO.read_text(encoding="utf-8"))
    manifiesto = Manifiesto(
        sesion=opciones.sesion,
        url_api=opciones.url_api,
        oraculo=f"{oraculo['id']} ({oraculo['estado']})",
        corpus=verificar_corpus(oraculo),
    )
    cliente = ClienteApi(
        opciones.url_api, tokens_cognito(opciones.region, opciones.cliente_cognito, usuarios)
    )
    try:
        Sembrador(cliente, manifiesto, oraculo).ejecutar()
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
