"""Respuestas fijas para probar la lógica propia del procesamiento (DO-2026-10-22-PROC, P1).

Construyen estructuras con la forma documentada de Textract y respuestas de herramienta
del modelo, con texto sintético. No juzgan la calidad de los servicios reales: eso se
verifica en las pruebas `aws_real` (nivel B).
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
    """Campos de C-v1 según el oráculo preliminar PD-07, con citas reales del DOCX."""
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
