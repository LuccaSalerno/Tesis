"""Respuestas fijas para probar la lógica propia del procesamiento.

Construyen estructuras con la forma documentada de Textract y respuestas de herramienta
del modelo, con texto sintético. No juzgan la calidad de los servicios reales: eso se
midió en la evaluación de §6.3.
"""

from dataclasses import dataclass, field
from typing import Any

Elemento = tuple[str, Any]  # ("titulo" | "linea", texto) o ("tabla", [[celda, ...], ...])


def textract_fijo(paginas: list[list[Elemento]], *, por_respuesta: int = 0) -> list[dict[str, Any]]:
    """Bloques de `GetDocumentAnalysis` (PAGE, LINE, WORD, TABLE, CELL, LAYOUT_*).

    Con `por_respuesta` > 0 reparte los bloques en varias respuestas, como la paginación
    con `NextToken`.
    """
    bloques: list[dict[str, Any]] = []
    contador = 0

    def nuevo(tipo: str, pagina: int, arriba: float, **extra: Any) -> dict[str, Any]:
        nonlocal contador
        contador += 1
        bloque = {
            "BlockType": tipo,
            "Id": f"b{contador}",
            "Page": pagina,
            "Geometry": {"BoundingBox": {"Top": arriba, "Left": 0.1, "Width": 0.8, "Height": 0.02}},
            **extra,
        }
        bloques.append(bloque)
        return bloque

    def palabras(texto: str, pagina: int, arriba: float) -> list[str]:
        return [nuevo("WORD", pagina, arriba, Text=p)["Id"] for p in texto.split()]

    for numero, elementos in enumerate(paginas, start=1):
        nuevo("PAGE", numero, 0.0)
        for posicion, (clase, valor) in enumerate(elementos):
            arriba = 0.05 + posicion * 0.05
            if clase in ("titulo", "linea"):
                ids = palabras(valor, numero, arriba)
                linea = nuevo(
                    "LINE",
                    numero,
                    arriba,
                    Text=valor,
                    Relationships=[{"Type": "CHILD", "Ids": ids}],
                )
                if clase == "titulo":
                    nuevo(
                        "LAYOUT_SECTION_HEADER",
                        numero,
                        arriba,
                        Relationships=[{"Type": "CHILD", "Ids": [linea["Id"]]}],
                    )
            else:
                celdas = []
                for fila, valores in enumerate(valor, start=1):
                    for columna, texto in enumerate(valores, start=1):
                        ids = palabras(texto, numero, arriba)
                        # Textract también emite las líneas de texto de cada celda.
                        nuevo(
                            "LINE",
                            numero,
                            arriba,
                            Text=texto,
                            Relationships=[{"Type": "CHILD", "Ids": ids}],
                        )
                        celdas.append(
                            nuevo(
                                "CELL",
                                numero,
                                arriba,
                                RowIndex=fila,
                                ColumnIndex=columna,
                                Relationships=[{"Type": "CHILD", "Ids": ids}],
                            )["Id"]
                        )
                nuevo("TABLE", numero, arriba, Relationships=[{"Type": "CHILD", "Ids": celdas}])
    if por_respuesta <= 0:
        return [{"Blocks": bloques}]
    return [
        {"Blocks": bloques[i : i + por_respuesta]} for i in range(0, len(bloques), por_respuesta)
    ]


@dataclass
class ModeloFijo:
    """Devuelve la entrada de herramienta configurada y registra cada invocación."""

    respuestas: dict[str, Any]
    identificador: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    invocaciones: list[dict[str, Any]] = field(default_factory=list)

    def invocar_herramienta(
        self, *, instrucciones: str, contenido: str, herramienta: dict[str, Any], max_tokens: int
    ) -> Any:
        from atlas.procesamiento.modelo import RespuestaHerramienta

        self.invocaciones.append(
            {
                "instrucciones": instrucciones,
                "contenido": contenido,
                "herramienta": herramienta,
                "max_tokens": max_tokens,
            }
        )
        return RespuestaHerramienta(
            entrada=self.respuestas[herramienta["name"]],
            modelo=self.identificador,
            tokens_entrada=1000,
            tokens_salida=100,
        )


def dato(valor: str | None, cita: str | None = None, pagina: int | None = None) -> dict[str, Any]:
    return {"valor": valor, "pagina": pagina, "cita": cita}


def extraccion_c_v1_docx() -> dict[str, Any]:
    """Campos de C-v1 según el oráculo preliminar con citas reales del DOCX."""
    return {
        "contraparte": dato(
            "Servicios Integrales del Sur S.A.", "Servicios Integrales del Sur S.A."
        ),
        "cuit_contraparte": dato(
            "30-96472518-3", "CUIT de la contraparte (dato de prueba) | 30-96472518-3"
        ),
        "fecha_celebracion": dato(
            "20 de febrero de 2026", "a los 20 días del mes de febrero de 2026"
        ),
        "vigencia_desde": dato("01/03/2026", "Inicio de vigencia | 01/03/2026"),
        "vigencia_hasta": dato("28/02/2027", "Fin de vigencia | 28/02/2027"),
        "monto_total": dato("ARS 1.250.000,00", "Monto total | ARS 1.250.000,00"),
        "moneda": dato("ARS", "Moneda | ARS - pesos argentinos"),
    }


@dataclass
class EmbeddingsFijos:
    """Vectores deterministas y léxicos: bolsa de palabras proyectada en 1024
    dimensiones y normalizada. Textos con palabras en común quedan cerca; no simula la
    calidad semántica de Cohere, que se mide solo con el servicio real."""

    identificador: str = "cohere.embed-multilingual-v3"
    llamadas: list[tuple[str, int]] = field(default_factory=list)

    def embeber(self, textos: list[str], tipo: str) -> list[list[float]]:
        import hashlib
        import math
        import re

        self.llamadas.append((tipo, len(textos)))
        vectores = []
        for texto in textos:
            vector = [0.0] * 1024
            for palabra in re.findall(r"\w{3,}", texto.casefold()):
                vector[int(hashlib.sha256(palabra.encode()).hexdigest(), 16) % 1024] += 1.0
            norma = math.sqrt(sum(v * v for v in vector)) or 1.0
            vectores.append(
                [v / norma if norma else 0.0 for v in vector]
                if any(vector)
                else [1.0] + [0.0] * 1023
            )
        return vectores


@dataclass
class ModeloConsultaFijo:
    """Respuesta fija de la consulta asistida: cita el fragmento recuperado cuyo texto
    contiene `buscar`. Permite verificar el recorrido sin juzgar la calidad del modelo."""

    buscar: str | None = None
    afirmacion: str = "El contrato está vigente hasta el 28/02/2027."
    suficiente: bool = True
    etiquetas_extra: tuple[str, ...] = ()
    entrada_cruda: Any = None
    identificador: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    invocaciones: list[dict[str, Any]] = field(default_factory=list)

    def invocar_herramienta(
        self, *, instrucciones: str, contenido: str, herramienta: dict[str, Any], max_tokens: int
    ) -> Any:
        import re

        from atlas.procesamiento.modelo import RespuestaHerramienta

        self.invocaciones.append({"instrucciones": instrucciones, "contenido": contenido})
        if self.entrada_cruda is not None:
            entrada = self.entrada_cruda
        else:
            etiquetas = [
                e
                for e, texto in re.findall(
                    r'<fragmento id="(F\d+)"[^>]*>\n(.*?)\n</fragmento>', contenido, re.S
                )
                if self.buscar and self.buscar in texto
            ][:1]
            entrada = {
                "suficiente": self.suficiente,
                "afirmaciones": (
                    [{"texto": self.afirmacion, "fragmentos": [*etiquetas, *self.etiquetas_extra]}]
                    if self.suficiente
                    else []
                ),
            }
        return RespuestaHerramienta(
            entrada=entrada, modelo=self.identificador, tokens_entrada=900, tokens_salida=40
        )
