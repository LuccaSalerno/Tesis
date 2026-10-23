"""Corpus, oráculos y compuerta de congelación (DO-2026-10-23-E90-MEDICION P4).

Lee el inventario, los oráculos de campos, fragmentos y consultas, y los objetivos de los
documentos adversariales. El modo `oficial` exige oráculos congelados y revisados por los
autores; el modo `ensayo` solo admite la partición de ajuste, para que nadie vea resultados
de la medición antes de congelar (IA-M12).
"""

import csv
import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

from atlas.dominio.enumeraciones import TipoDocumental

ESTADO_CONGELADO: Final = "CONGELADO"


class Modo(StrEnum):
    ENSAYO = "ensayo"
    OFICIAL = "oficial"


class ErrorOraculo(Exception):
    """El corpus o los oráculos no permiten la campaña pedida."""


@dataclass(frozen=True)
class Documento:
    doc_id: str
    grupo: str
    tipo: TipoDocumental
    formato: str
    ruta: Path
    sha256: str
    adversarial: bool

    @property
    def es_docx(self) -> bool:
        return self.formato == "docx"


@dataclass(frozen=True)
class CampoEsperado:
    doc_id: str
    campo: str
    presente: bool
    valor: str | None
    localizador: dict[str, Any] | None


@dataclass(frozen=True)
class Fragmento:
    fragmento_id: str
    doc_id: str
    texto: str
    pagina: int | None


@dataclass(frozen=True)
class Consulta:
    pregunta_id: str
    pregunta: str
    clase: str
    categoria: str
    documentos: tuple[str, ...]
    fragmentos_relevantes: tuple[str, ...]
    afirmaciones_esperadas: tuple[str, ...]
    motivo_abstencion: str | None

    @property
    def respondible(self) -> bool:
        return self.clase == "respondible"


@dataclass(frozen=True)
class Oraculos:
    raiz: Path
    documentos: dict[str, Documento]
    campos: tuple[CampoEsperado, ...]
    fragmentos: dict[str, Fragmento]
    consultas: tuple[Consulta, ...]
    adversariales: dict[str, dict[str, str]]
    congelado: bool
    hashes: dict[str, str] = field(default_factory=dict)

    def campos_de(self, doc_id: str) -> list[CampoEsperado]:
        return [c for c in self.campos if c.doc_id == doc_id]


def sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _unico(directorio: Path, patron: str) -> Path:
    encontrados = sorted(directorio.glob(patron))
    if len(encontrados) != 1:
        raise ErrorOraculo(f"se_esperaba_un_archivo:{patron}:{len(encontrados)}")
    return encontrados[0]


def _congelado(datos: dict[str, Any]) -> bool:
    return datos.get("estado") == ESTADO_CONGELADO and datos.get("revisado_por_autores") is True


def cargar(raiz: Path, directorio_oraculos: Path | None = None) -> Oraculos:
    """`raiz` es la raíz del repositorio; los oráculos se buscan por patrón para admitir los
    nombres de la versión congelada sin cambiar el código."""
    directorio = directorio_oraculos or raiz / "oraculos" / "e90"
    rutas = {
        "inventario": _unico(directorio, "inventario*.csv"),
        "campos": _unico(directorio, "campos*.json"),
        "fragmentos": _unico(directorio, "fragmentos*.json"),
        "consultas": _unico(directorio, "consultas*.json"),
        "registros": raiz / "corpus" / "e90" / "registros_fuente.json",
    }
    datos = {
        nombre: json.loads(ruta.read_text("utf-8"))
        for nombre, ruta in rutas.items()
        if ruta.suffix == ".json"
    }
    with rutas["inventario"].open(encoding="utf-8", newline="") as archivo:
        inventario = list(csv.DictReader(archivo))

    documentos = {
        fila["doc_id"]: Documento(
            doc_id=fila["doc_id"],
            grupo=fila["grupo"],
            tipo=TipoDocumental(fila["tipo"]),
            formato=fila["formato"],
            ruta=raiz / fila["ruta"],
            sha256=fila["sha256"],
            adversarial=fila["prompt_injection"] == "si",
        )
        for fila in inventario
    }
    campos = tuple(
        CampoEsperado(
            doc_id=c["doc_id"],
            campo=c["campo"],
            presente=bool(c["presente"]),
            valor=c["valor_esperado"],
            localizador=c["localizador"],
        )
        for c in datos["campos"]["campos"]
        if c.get("aplicable", True)
    )
    fragmentos = {
        f["fragmento_id"]: Fragmento(
            fragmento_id=f["fragmento_id"],
            doc_id=f["doc_id"],
            texto=f["texto"],
            pagina=(f.get("localizador") or {}).get("pagina"),
        )
        for f in datos["fragmentos"]["fragmentos"]
    }
    consultas = tuple(
        Consulta(
            pregunta_id=q["pregunta_id"],
            pregunta=q["pregunta"],
            clase=q["clase"],
            categoria=q["categoria"],
            documentos=tuple(q["documentos_autorizados"]),
            fragmentos_relevantes=tuple(q["fragmentos_relevantes"]),
            afirmaciones_esperadas=tuple(q["afirmaciones_esperadas"]),
            motivo_abstencion=q.get("motivo_abstencion"),
        )
        for q in datos["consultas"]["consultas"]
    )
    registros = datos["registros"]
    registros = registros["registros"] if isinstance(registros, dict) else registros
    adversariales = {
        r["doc_id"]: {k: str(v) for k, v in r["adversarial"]["objetivos"].items()}
        for r in registros
        if r.get("adversarial")
    }
    congelado = all(_congelado(datos[n]) for n in ("campos", "fragmentos", "consultas"))
    return Oraculos(
        raiz=raiz,
        documentos=documentos,
        campos=campos,
        fragmentos=fragmentos,
        consultas=consultas,
        adversariales=adversariales,
        congelado=congelado,
        hashes={
            str(ruta.relative_to(raiz)) if ruta.is_relative_to(raiz) else str(ruta): sha256(ruta)
            for ruta in rutas.values()
        },
    )


def seleccionar(oraculos: Oraculos, modo: Modo) -> list[Documento]:
    """Compuerta P4: qué documentos puede usar una campaña, con sus archivos verificados."""
    if modo is Modo.OFICIAL:
        if not oraculos.congelado:
            raise ErrorOraculo("oraculos_no_congelados")
        grupo = "medicion"
    else:
        grupo = "ajuste"
    elegidos = sorted(
        (d for d in oraculos.documentos.values() if d.grupo == grupo), key=lambda d: d.doc_id
    )
    for documento in elegidos:
        if not documento.ruta.is_file() or sha256(documento.ruta) != documento.sha256:
            raise ErrorOraculo(f"archivo_no_coincide:{documento.doc_id}")
    return elegidos


def consultas_de(oraculos: Oraculos, modo: Modo) -> list[Consulta]:
    """Las 30 preguntas son de la partición de medición: el ensayo no las usa (P4)."""
    if modo is Modo.ENSAYO:
        return []
    if not oraculos.congelado:
        raise ErrorOraculo("oraculos_no_congelados")
    return list(oraculos.consultas)
