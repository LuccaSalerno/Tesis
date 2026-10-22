"""Recorrido de las etapas del procesamiento con respuestas fijas (P1), compartido por las
pruebas de procesamiento, de validación humana y los escenarios BDD."""

import json
from typing import Any

from sqlalchemy import Engine, text

from atlas.procesamiento import esquemas, etapas
from tests.procesamiento_fijo import ModeloFijo, textract_fijo

LIMITES = etapas.LimitesProcesamiento(
    max_tokens_clasificacion=256, max_tokens_extraccion=2048, caracteres_maximos=400_000
)
CLAVES_DE_SALIDA = {
    "formato",
    "clave_objeto",
    "job_id",
    "estado",
    "contenido",
    "clasificacion",
    "extraccion",
    "resultado",
    "registrado",
}
PALABRAS_DEL_DOCUMENTO = ("Servicios Integrales", "1.250.000", "30-96472518-3", "febrero")


class AnalizadorFijo:
    """Sustituto de Textract con resultado fijo (P1)."""

    def __init__(self, paginas: list[Any]) -> None:
        self.paginas = paginas
        self.iniciados: list[tuple[str, int, int]] = []

    def iniciar(self, clave: str, trabajo_id: int, intento: int) -> str:
        self.iniciados.append((clave, trabajo_id, intento))
        return "job-fijo"

    def estado(self, job_id: str) -> str:
        return "completado"

    def resultado(self, job_id: str) -> list[dict[str, Any]]:
        return textract_fijo(self.paginas)


def trabajo_de(motor: Engine, archivo_id: int) -> int:
    with motor.connect() as conexion:
        return int(
            conexion.execute(
                text("SELECT id FROM atlas.trabajo_procesamiento WHERE archivo_id = :a"),
                {"a": archivo_id},
            ).scalar_one()
        )


def en_sesion(aplicacion: Any, funcion: Any, **parametros: Any) -> Any:
    with aplicacion.state.fabrica_sesiones() as sesion:
        resultado = funcion(sesion, **parametros)
        sesion.commit()
        return resultado


def salida_sin_contenido(salida: dict[str, Any]) -> None:
    """Regla 5: lo que vuelve a Step Functions son referencias, nunca datos del documento."""
    assert set(salida) <= CLAVES_DE_SALIDA
    serializada = json.dumps(salida, ensure_ascii=False)
    assert not any(p in serializada for p in PALABRAS_DEL_DOCUMENTO)


def recorrer(
    aplicacion: Any, trabajo_id: int, modelo: ModeloFijo, analizador: AnalizadorFijo | None = None
) -> list[dict[str, Any]]:
    """Ejecuta las etapas en el orden de la máquina de estados."""
    almacen = aplicacion.state.almacen
    salidas = [en_sesion(aplicacion, etapas.preparar, trabajo_id=trabajo_id, intento=1)]
    clave = salidas[0]["clave_objeto"]
    if salidas[0]["formato"] == "pdf":
        assert analizador is not None
        salidas.append(
            etapas.iniciar_textract(
                analizador, clave_objeto=clave, trabajo_id=trabajo_id, intento=1
            )
        )  # type: ignore[arg-type]
        salidas.append(etapas.consultar_textract(analizador, job_id="job-fijo"))  # type: ignore[arg-type]
        salidas.append(
            etapas.normalizar_textract(
                analizador, almacen, job_id="job-fijo", trabajo_id=trabajo_id, intento=1
            )  # type: ignore[arg-type]
        )
    else:
        salidas.append(
            etapas.normalizar_docx(almacen, clave_objeto=clave, trabajo_id=trabajo_id, intento=1)
        )
    contenido = salidas[-1]["contenido"]
    salidas.append(
        etapas.clasificar(
            almacen, modelo, LIMITES, contenido=contenido, trabajo_id=trabajo_id, intento=1
        )
    )
    clasificacion = salidas[-1]["clasificacion"]
    salidas.append(
        etapas.extraer(
            almacen,
            modelo,
            LIMITES,
            contenido=contenido,
            clasificacion=clasificacion,
            trabajo_id=trabajo_id,
            intento=1,
        )
    )
    salidas.append(
        en_sesion(
            aplicacion,
            etapas.persistir,
            almacen=almacen,
            clasificacion=clasificacion,
            extraccion=salidas[-1]["extraccion"],
            trabajo_id=trabajo_id,
            intento=1,
        )
    )
    return salidas


def modelo_contrato(extraccion: dict[str, Any]) -> ModeloFijo:
    return ModeloFijo(
        {
            esquemas.HERRAMIENTA_CLASIFICACION: {"tipo": "contrato"},
            esquemas.HERRAMIENTA_EXTRACCION: extraccion,
        }
    )


PAGINAS_C_V1 = [
    [
        ("titulo", "Carátula y celebración"),
        ("linea", "Contraparte: Servicios Integrales del Sur S.A."),
        ("linea", "CUIT de la contraparte: 30-96472518-3"),
        ("linea", "Celebrado el 20 de febrero de 2026"),
    ],
    [("titulo", "1. Objeto"), ("linea", "Mantenimiento y soporte documental ficticio")],
    [("titulo", "2. Alcance"), ("linea", "Prestaciones descriptas en el anexo")],
    [("titulo", "3. Servicio"), ("linea", "Atención según niveles acordados")],
    [
        ("titulo", "4. Condiciones económicas y forma de pago"),
        ("tabla", [["Monto total", "ARS 1.250.000,00"], ["Moneda", "ARS"]]),
    ],
    [
        ("titulo", "5. Plazo de ejecución y vigencia"),
        ("linea", "Vigencia desde el 01/03/2026 hasta el 28/02/2027 inclusive"),
    ],
]


def extraccion_c_v1_pdf() -> dict[str, Any]:
    """Campos de C-v1 con las páginas del oráculo preliminar PD-07 (ubicacion_campos)."""
    from tests.procesamiento_fijo import dato

    return {
        "contraparte": dato(
            "Servicios Integrales del Sur S.A.", "Servicios Integrales del Sur S.A.", 1
        ),
        "cuit_contraparte": dato("30-96472518-3", "CUIT de la contraparte: 30-96472518-3", 1),
        "fecha_celebracion": dato("20 de febrero de 2026", "Celebrado el 20 de febrero de 2026", 1),
        "vigencia_desde": dato("01/03/2026", "Vigencia desde el 01/03/2026", 6),
        "vigencia_hasta": dato("28/02/2027", "hasta el 28/02/2027", 6),
        "monto_total": dato("ARS 1.250.000,00", "Monto total | ARS 1.250.000,00", 5),
        "moneda": dato("ARS", "Moneda | ARS", 5),
    }


def contrato_procesado_e_incorporado(aplicacion: Any, ctx: Any) -> dict[str, Any]:
    """C-v1 (PDF del corpus) cargado, procesado con respuestas fijas e incorporado."""
    from tests import archivos
    from tests.flujo_api import cargar, crear_tramite, incorporar

    tramite = crear_tramite(ctx)
    archivo = cargar(ctx, tramite["id"], archivos.CONTRATO_PDF.read_bytes())
    trabajo_id = trabajo_de(ctx.motor, archivo["id"])
    recorrer(
        aplicacion, trabajo_id, modelo_contrato(extraccion_c_v1_pdf()), AnalizadorFijo(PAGINAS_C_V1)
    )
    respuesta = incorporar(ctx, tramite["id"], archivo["id"], nombre="Contrato C-v1")
    assert respuesta.status_code == 201, respuesta.text
    return {
        "tramite": tramite,
        "archivo": archivo,
        "documento": respuesta.json(),
        "trabajo_id": trabajo_id,
    }
