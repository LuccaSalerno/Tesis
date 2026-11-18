"""Arnés de medición de §6.3 (IA-M01 a IA-M12).

Sin AWS: corpus en miniatura, OCR en caché con la forma de Textract y modelos fijos. Las
métricas se verifican contra valores calculados a mano; la calidad real de los modelos se
mide solo en una campaña del operador.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from atlas.evaluacion import campana as cmp
from atlas.evaluacion import informe, metricas, planillas, recuperacion
from atlas.evaluacion.__main__ import main as cli
from atlas.evaluacion.contenidos import FuenteContenidos, clave_cache
from atlas.evaluacion.ejecucion import con_reintentos, medir_documentos, orden_modelos
from atlas.evaluacion.oraculos import ErrorOraculo, Modo, cargar, consultas_de, seleccionar
from atlas.evaluacion.registro import Registro
from atlas.procesamiento import esquemas
from atlas.procesamiento.errores import ErrorPermanente, ErrorTransitorio
from atlas.procesamiento.modelo import RespuestaHerramienta
from tests import evaluacion_fijo as fijo
from tests.procesamiento_fijo import EmbeddingsFijos, ModeloConsultaFijo, textract_fijo


@dataclass
class ModeloDocumentos:
    """Clasifica por el contenido y devuelve la extracción fija de cada documento."""

    tipo_contrato: str = "contrato"
    falla: Exception | None = None
    identificador: str = "modelo-fijo"
    invocaciones: list[str] = field(default_factory=list)

    def invocar_herramienta(
        self, *, instrucciones: str, contenido: str, herramienta: dict[str, Any], max_tokens: int
    ) -> RespuestaHerramienta:
        self.invocaciones.append(herramienta["name"])
        if self.falla is not None:
            raise self.falla
        factura = "Factura N.º" in contenido
        if herramienta["name"] == esquemas.HERRAMIENTA_CLASIFICACION:
            entrada: dict[str, Any] = {"tipo": "factura" if factura else self.tipo_contrato}
        else:
            entrada = (
                fijo.respuesta_extraccion_factura()
                if factura
                else fijo.respuesta_extraccion_contrato()
            )
        return RespuestaHerramienta(entrada, self.identificador, 100, 10)


@pytest.fixture
def raiz(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fijo.construir(tmp_path, congelado=True)
    # El commit se toma de git; aquí se fija para no depender del entorno de la prueba.
    monkeypatch.setattr(
        cmp, "_commit", lambda _: {"commit": "abc1234", "cambios_sin_commit": False}
    )
    return tmp_path


def _fuente(raiz: Path) -> FuenteContenidos:
    return FuenteContenidos(raiz / "evaluacion" / "cache_ocr")


def _medir(raiz: Path, modelos: dict[str, Any], repeticiones: int = 1) -> list[dict[str, Any]]:
    oraculos = cargar(raiz)
    registro = Registro(raiz / "medicion.jsonl")
    medir_documentos(
        seleccionar(oraculos, Modo.OFICIAL),
        _fuente(raiz),
        modelos,
        registro,
        repeticiones=repeticiones,
        max_tokens_clasificacion=256,
        max_tokens_extraccion=2048,
        caracteres_maximos=400_000,
        esperar=lambda _: None,
    )
    return registro.leer()


# --- Oráculos y compuerta -------------------------------------------------------------


def test_ensayo_solo_ajuste_y_oficial_exige_congelado(tmp_path: Path) -> None:
    fijo.construir(tmp_path, congelado=False)
    oraculos = cargar(tmp_path)
    assert len(oraculos.documentos) == 3 and not oraculos.congelado
    assert [d.doc_id for d in seleccionar(oraculos, Modo.ENSAYO)] == ["E90-A-CTR-01"]
    assert consultas_de(oraculos, Modo.ENSAYO) == []
    with pytest.raises(ErrorOraculo, match="oraculos_no_congelados"):
        seleccionar(oraculos, Modo.OFICIAL)
    with pytest.raises(ErrorOraculo, match="oraculos_no_congelados"):
        consultas_de(oraculos, Modo.OFICIAL)


def test_oficial_con_oraculos_congelados_y_archivos_verificados(raiz: Path) -> None:
    oraculos = cargar(raiz)
    assert [d.doc_id for d in seleccionar(oraculos, Modo.OFICIAL)] == [
        "E90-M-CTR-01",
        "E90-M-FAC-01",
    ]
    assert len(consultas_de(oraculos, Modo.OFICIAL)) == 2
    assert oraculos.adversariales["E90-M-FAC-01"]["importe_total"] == "0.00"
    (raiz / "corpus/e90/medicion/doc-aaaa0001.pdf").write_bytes(b"alterado")
    with pytest.raises(ErrorOraculo, match="archivo_no_coincide:E90-M-CTR-01"):
        seleccionar(oraculos, Modo.OFICIAL)


def test_un_solo_archivo_por_oraculo(raiz: Path) -> None:
    (raiz / "oraculos/e90/campos_congelados.json").write_text("{}", "utf-8")
    with pytest.raises(ErrorOraculo, match="se_esperaba_un_archivo:campos"):
        cargar(raiz)


# --- Contenidos y OCR una sola vez ----------------------------------------------------


@dataclass
class AnalizadorFijo:
    estados: list[str]
    iniciados: list[tuple[str, int, int]] = field(default_factory=list)

    def iniciar(self, clave: str, trabajo: int, intento: int) -> str:
        self.iniciados.append((clave, trabajo, intento))
        return "job-1"

    def estado(self, job_id: str) -> str:
        return self.estados.pop(0)

    def resultado(self, job_id: str) -> list[dict[str, Any]]:
        return textract_fijo([fijo.PAGINA_CONTRATO])


@dataclass
class AlmacenFijo:
    escritos: list[str] = field(default_factory=list)

    def escribir(self, clave: str, datos: bytes, tipo_contenido: str) -> None:
        self.escritos.append(clave)


def test_ocr_una_vez_en_cache_y_docx_local(raiz: Path) -> None:
    oraculos = cargar(raiz)
    documento = oraculos.documentos["E90-M-CTR-01"]
    (raiz / "evaluacion/cache_ocr" / clave_cache(documento)).unlink()
    eventos: list[dict[str, Any]] = []
    analizador = AnalizadorFijo(["en_curso", "completado"])
    fuente = FuenteContenidos(
        raiz / "evaluacion/cache_ocr",
        analizador,  # type: ignore[arg-type]
        AlmacenFijo(),
        registrar=eventos.append,
        esperar=lambda _: None,
    )
    contenido = fuente.obtener(documento)
    assert contenido.paginado and "Servicios Sur" in contenido.paginas[0].texto()
    assert fuente.obtener(documento) is contenido  # memoria: sin segundo OCR
    assert len(analizador.iniciados) == 1 and eventos[0]["paginas"] == 1
    assert (raiz / "evaluacion/cache_ocr" / clave_cache(documento)).is_file()
    docx = fuente.obtener(oraculos.documentos["E90-M-FAC-01"])
    assert not docx.paginado


def test_ocr_fallido_o_sin_servicios(raiz: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    oraculos = cargar(raiz)
    documento = oraculos.documentos["E90-M-CTR-01"]
    (raiz / "evaluacion/cache_ocr" / clave_cache(documento)).unlink()
    with pytest.raises(RuntimeError, match="falta_ocr_en_cache"):
        _fuente(raiz).obtener(documento)
    fallido = FuenteContenidos(raiz / "x", AnalizadorFijo(["fallido"]), AlmacenFijo())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="textract_fallido"):
        fallido.obtener(documento)
    monkeypatch.setattr("atlas.evaluacion.contenidos.ESPERA_MAXIMA_S", -1.0)
    lento = FuenteContenidos(raiz / "x", AnalizadorFijo(["en_curso"]), AlmacenFijo())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="textract_sin_terminar"):
        lento.obtener(documento)


# --- Ejecución -------------------------------------------------------------------


def test_orden_alternado_y_reintentos() -> None:
    assert orden_modelos(["haiku", "sonnet"], 1) == ["haiku", "sonnet"]
    assert orden_modelos(["haiku", "sonnet"], 2) == ["sonnet", "haiku"]
    llamadas = iter([ErrorTransitorio("t"), "ok"])

    def llamada() -> str:
        valor = next(llamadas)
        if isinstance(valor, Exception):
            raise valor
        return valor

    assert con_reintentos(llamada, lambda _: None)[:3] == ("ok", None, 2)

    def transitoria() -> str:
        raise ErrorTransitorio("bedrock_ThrottlingException")

    def permanente() -> str:
        raise ErrorPermanente("respuesta_invalida")

    assert con_reintentos(transitoria, lambda _: None)[1:3] == ("bedrock_ThrottlingException", 3)
    assert con_reintentos(permanente, lambda _: None)[1:3] == ("respuesta_invalida", 1)


def test_mediciones_intercaladas_y_reanudables(raiz: Path) -> None:
    filas = _medir(
        raiz, {"haiku": ModeloDocumentos(), "sonnet": ModeloDocumentos()}, repeticiones=2
    )
    assert [(f["repeticion"], f["modelo"]) for f in filas] == [
        (1, "haiku"), (1, "sonnet"), (1, "haiku"), (1, "sonnet"),
        (2, "sonnet"), (2, "haiku"), (2, "sonnet"), (2, "haiku"),
    ]  # fmt: skip
    assert filas[0]["tokens_clasificacion"] == [100, 10] and len(filas[0]["campos"]) == 6
    # Reanudar no repite lo registrado.
    assert len(_medir(raiz, {"haiku": ModeloDocumentos(), "sonnet": ModeloDocumentos()}, 2)) == 8


def test_fallo_definitivo_queda_registrado(raiz: Path) -> None:
    filas = _medir(raiz, {"haiku": ModeloDocumentos(falla=ErrorPermanente("respuesta_invalida"))})
    assert (
        filas[0]["clasificacion"] is None
        and filas[0]["error_clasificacion"] == "respuesta_invalida"
    )
    assert filas[0]["campos"] is None


# --- Métricas (IA-M01 a IA-M04, IA-M07) ----------------------------------------------------


def test_ia_m02_extraccion_correctos_incorrectos_omitidos_y_procedencia(raiz: Path) -> None:
    filas = _medir(raiz, {"haiku": ModeloDocumentos()})
    oraculos = cargar(raiz)
    fuente = _fuente(raiz)

    def bloques(doc_id: str) -> dict[str, str]:
        contenido = fuente.obtener(oraculos.documentos[doc_id])
        return {b.localizador: b.texto for p in contenido.paginas for b in p.bloques}

    ext = metricas.extraccion(filas, oraculos, bloques)
    contrato = ext["por_tipo"]["contrato"]
    # 5 correctos, vigencia_hasta incorrecta (FP+FN) y moneda omitida (FN).
    assert (contrato["correctos"], contrato["fp"], contrato["fn"]) == (5, 1, 2)
    assert contrato["f1"] == pytest.approx(10 / 13)
    factura = ext["por_tipo"]["factura"]
    assert factura["correctos"] == 6 and factura["f1"] == 1.0  # incluye EUR
    assert ext["exactitud_critica"]["numero"] == {"exactitud": 1.0, "correctos": 1, "esperados": 1}
    assert ext["inventados"] == {"proporcion": 0.0, "cantidad": 0}
    assert ext["procedencia_pdf"]["proporcion"] == 1.0 and ext["procedencia_pdf"]["evaluados"] == 6
    assert (
        ext["procedencia_docx"]["evaluados"] == 6 and ext["procedencia_docx"]["proporcion"] == 1.0
    )
    assert set(ext["por_formato"]) == {"docx", "pdf_digital"}


def test_ia_m01_clasificacion_y_p7_campos_omitidos_con_otro_tipo(raiz: Path) -> None:
    filas = _medir(raiz, {"haiku": ModeloDocumentos(tipo_contrato="presupuesto")})
    oraculos = cargar(raiz)
    cla = metricas.clasificacion(filas, oraculos.documentos)
    assert cla["matriz"]["contrato"] == {"presupuesto": 1}
    assert cla["por_clase"]["contrato"]["recall"] == 0.0 and cla["recall_minimo"] == 0.0
    assert cla["por_clase"]["factura"]["f1"] == 1.0
    assert cla["exactitud"] == 0.5 and cla["f1_macro"] == pytest.approx(1 / 5)
    ext = metricas.extraccion(filas, oraculos, lambda _: {})
    # El esquema de presupuesto no admite la respuesta del contrato: error técnico registrado.
    assert filas[0]["error_extraccion"] == "respuesta_invalida"
    assert ext["por_tipo"]["contrato"]["fn"] == 7 and ext["extraidos_con_otro_esquema"] == 0
    fila = {**filas[0], "campos": [{"campo": "numero", "valor": "1", "pagina": 1}]}
    assert metricas.extraccion([fila], oraculos, lambda _: {})["extraidos_con_otro_esquema"] == 1
    # El DOCX sin bloques resueltos no cuenta como procedencia correcta.
    assert ext["procedencia_docx"]["proporcion"] == 0.0


def test_ia_m02_inventado_y_pagina_ausente(raiz: Path) -> None:
    oraculos = cargar(raiz)
    fila = {
        "doc_id": "E90-A-CTR-01",
        "clasificacion": "contrato",
        "campos": [
            {"campo": "fecha_celebracion", "valor": "2026-01-11", "pagina": None, "seccion": None},
            {"campo": "monto_total", "valor": "13024464.79", "pagina": None, "seccion": None},
        ],
    }
    ext = metricas.extraccion([fila], oraculos, lambda _: {})
    assert ext["inventados"] == {"proporcion": 0.5, "cantidad": 1}
    assert ext["procedencia_pdf"]["correctos"] == 0  # localizador ausente: error (IA-M03)


def test_ia_m07_adversariales(raiz: Path) -> None:
    oraculos = cargar(raiz)
    limpio = {
        "doc_id": "E90-M-FAC-01",
        "clasificacion": "factura",
        "campos": [{"campo": "importe_total", "valor": "2242.86"}],
    }
    alterado = {
        "doc_id": "E90-M-FAC-01",
        "clasificacion": "contrato",
        "campos": [{"campo": "importe_total", "valor": "0.00"}],
    }
    otro = {"doc_id": "E90-M-CTR-01", "clasificacion": "contrato", "campos": []}
    resultado = metricas.adversariales([limpio, alterado, otro], oraculos)
    assert resultado["alterados"] == 1
    assert resultado["casos"][1]["alteraciones"] == ["clasificacion", "importe_total"]
    assert resultado["casos"][0]["sin_accion_disponible"] == ["estado_tramite"]


# --- Recuperación y respuestas (IA-M05) ------------------------------------------


def _indice(raiz: Path, embeddings: Any = None) -> recuperacion.Indice:
    oraculos = cargar(raiz)
    chunks = recuperacion.chunks_de(seleccionar(oraculos, Modo.OFICIAL), _fuente(raiz))
    return recuperacion.construir_indice(chunks, embeddings or EmbeddingsFijos())


def test_indice_congelado_busqueda_y_cobertura(raiz: Path) -> None:
    indice = _indice(raiz)
    ruta = raiz / "indice.json"
    recuperacion.guardar_indice(indice, ruta)
    assert recuperacion.cargar_indice(ruta).huella() == indice.huella()
    datos = json.loads(ruta.read_text("utf-8"))
    datos["chunks"][0]["texto"] = "alterado"
    ruta.write_text(json.dumps(datos), "utf-8")
    with pytest.raises(ValueError, match="indice_alterado"):
        recuperacion.cargar_indice(ruta)
    vector = EmbeddingsFijos().embeber(["vigente 2027"], "search_query")[0]
    ranking = recuperacion.buscar(indice, vector, ["E90-M-CTR-01"])
    assert ranking and all(c.doc_id == "E90-M-CTR-01" for c, _ in ranking)
    oraculos = cargar(raiz)
    fragmento = oraculos.fragmentos["E90-M-CTR-01-CAMPO-vigencia_hasta"]
    assert any(recuperacion.contiene(c, fragmento) for c, _ in ranking)
    otra_pagina = recuperacion.Chunk("x#1", "E90-M-CTR-01", 1, fragmento.texto, 2, "a.pdf")
    assert not recuperacion.contiene(otra_pagina, fragmento)
    otro_doc = recuperacion.Chunk("x#1", "E90-M-FAC-01", 1, fragmento.texto, None, "a.pdf")
    assert not recuperacion.contiene(otro_doc, fragmento)
    vacio = recuperacion.Chunk("x#1", "E90-M-CTR-01", 1, "texto", 1, "a.pdf")
    sin_palabras = fijo_fragmento("E90-M-CTR-01", "…")
    assert not recuperacion.contiene(vacio, sin_palabras)


def fijo_fragmento(doc_id: str, texto: str) -> Any:
    from atlas.evaluacion.oraculos import Fragmento

    return Fragmento("f", doc_id, texto, None)


def test_ia_m05_recall_at_5_y_mrr(raiz: Path) -> None:
    oraculos = cargar(raiz)
    indice = _indice(raiz)
    registro = Registro(raiz / "recuperacion.jsonl")
    nuevas = recuperacion.medir_recuperacion(
        consultas_de(oraculos, Modo.OFICIAL),
        {"cohere": indice},
        {"cohere": EmbeddingsFijos()},
        oraculos.fragmentos,
        registro,
    )
    assert nuevas == 2
    resultado = metricas.recuperacion(registro.leer())
    assert resultado["preguntas"] == 1 and resultado["recall_at_5"] == 1.0
    assert resultado["mrr"] is not None and resultado["mrr"] > 0
    manual = metricas.recuperacion(
        [
            {
                "pregunta_id": "Q1",
                "clase": "respondible",
                "relevantes": ["a", "b"],
                "ranking": [{"cubre": []}, {"cubre": ["a"]}],
            },
            {
                "pregunta_id": "Q2",
                "clase": "respondible",
                "relevantes": ["c"],
                "ranking": [{"cubre": []}],
            },
        ]
    )
    assert manual["recall_at_5"] == pytest.approx(0.25) and manual["mrr"] == pytest.approx(0.25)


def test_respuestas_planillas_y_consolidacion(raiz: Path) -> None:
    oraculos = cargar(raiz)
    consultas = consultas_de(oraculos, Modo.OFICIAL)
    indice = _indice(raiz)
    rankings = {
        q.pregunta_id: [
            c.chunk_id
            for c, _ in recuperacion.buscar(
                indice, EmbeddingsFijos().embeber([q.pregunta], "search_query")[0], q.documentos
            )
        ]
        for q in consultas
    }
    registro = Registro(raiz / "respuestas.jsonl")
    nuevas = recuperacion.medir_respuestas(
        consultas,
        indice,
        rankings,
        {
            "haiku": ModeloConsultaFijo(buscar="20/01/2027"),
            "sonnet": ModeloConsultaFijo(buscar="20/01/2027"),
        },
        registro,
        repeticiones=2,
        max_tokens=1024,
        esperar=lambda _: None,
    )
    assert nuevas == 8
    filas = registro.leer()
    assert filas[0]["suficiente"] is True and filas[0]["afirmaciones"][0]["citas"]
    # Una respuesta inválida queda como error técnico.
    errores = Registro(raiz / "respuestas_error.jsonl")
    invalido = {"haiku": ModeloConsultaFijo(entrada_cruda={"x": 1})}
    recuperacion.medir_respuestas(
        consultas[:1], indice, rankings, invalido, errores,
        repeticiones=1, max_tokens=1024, esperar=lambda _: None,
    )  # fmt: skip
    assert errores.leer()[0]["error"] == "respuesta_invalida"

    autor_a, autor_b = raiz / "a.csv", raiz / "b.csv"
    grupos = planillas.generar_planilla(filas, consultas, indice, autor_a)
    planillas.generar_planilla(filas, consultas, indice, autor_b)
    assert grupos < len(filas)  # las respuestas idénticas se agrupan
    with pytest.raises(ValueError, match="calificacion_invalida"):
        planillas.leer_planilla(autor_a)

    def completar(ruta: Path, respondible: str) -> None:
        import csv

        with ruta.open(encoding="utf-8", newline="") as archivo:
            filas_csv = list(csv.DictReader(archivo))
        for fila in filas_csv:
            si = fila["clase"] == "respondible"
            fila["calificacion"] = respondible if si else "abstencion_correcta"
            fila["afirmaciones_sustantivas"] = "1" if si else "0"
            fila["afirmaciones_respaldadas"] = "1" if si else "0"
        with ruta.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=planillas.COLUMNAS)
            escritor.writeheader()
            escritor.writerows(filas_csv)

    completar(autor_a, "correcta")
    completar(autor_b, "parcial")
    assert planillas.discrepancias(autor_a, autor_b, raiz / "disc.csv") >= 1
    with pytest.raises(ValueError, match="discrepancias_sin_consenso"):
        planillas.consolidar(autor_a, autor_b, None)
    completar(raiz / "disc.csv", "correcta")
    finales, acuerdo = planillas.consolidar(autor_a, autor_b, raiz / "disc.csv")
    assert acuerdo["acuerdos"] < acuerdo["grupos"] and acuerdo["modalidad"] == "independiente"
    rag = metricas.respuestas(finales[("haiku", 1)], consultas)
    assert (
        rag["correctas"] == 1.0 and rag["respaldo"] == 1.0 and rag["abstenciones_correctas"] == 1.0
    )
    # Una sola planilla, sin acuerdo entre evaluadores.
    conjuntas, acuerdo = planillas.consolidar_conjunta(autor_a)
    assert conjuntas == planillas.consolidar(autor_a, autor_a, None)[0]
    assert acuerdo == {
        "modalidad": "conjunta",
        "grupos": grupos,
        "acuerdos": None,
        "proporcion": None,
    }
    sin_conteos = raiz / "sin_conteos.csv"
    import csv

    with autor_a.open(encoding="utf-8", newline="") as archivo:
        filas_csv = list(csv.DictReader(archivo))
    filas_csv[0] |= {"clase": "respondible", "afirmaciones_respaldadas": ""}
    with sin_conteos.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=planillas.COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas_csv)
    with pytest.raises(ValueError, match="conteos_faltantes:1"):
        planillas.consolidar_conjunta(sin_conteos)


def test_planillas_validan_conteos_y_grupos(raiz: Path) -> None:
    import csv

    def escribir(ruta: Path, grupo: str, sustantivas: str) -> None:
        fila = dict.fromkeys(planillas.COLUMNAS, "") | {
            "grupo": grupo,
            "calificacion": "correcta",
            "afirmaciones_sustantivas": sustantivas,
        }
        with ruta.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=planillas.COLUMNAS)
            escritor.writeheader()
            escritor.writerow(fila)

    escribir(raiz / "p.csv", "g", "x")
    with pytest.raises(ValueError, match="conteo_invalido"):
        planillas.leer_planilla(raiz / "p.csv")
    escribir(raiz / "a.csv", "g", "1")
    escribir(raiz / "b.csv", "h", "1")
    with pytest.raises(ValueError, match="planillas_con_grupos_distintos"):
        planillas.discrepancias(raiz / "a.csv", raiz / "b.csv", raiz / "d.csv")


# --- Agregación y reglas de sustitución ----------------------------------------------


def test_promedios_y_reglas_de_sustitucion() -> None:
    assert metricas.resumen_repeticiones([0.8, 0.9, None, 1.0])["promedio"] == pytest.approx(0.9)
    assert metricas.resumen_repeticiones([0.5])["desvio"] is None
    base = {"clasificacion_f1_macro": False, "latencia": None, "procedencia_pdf": True}
    mejor = {"clasificacion_f1_macro": True, "latencia": None, "procedencia_pdf": True}
    assert metricas.sustituir_generativo(base, mejor, 0.80, 0.81)["sustituye"] is True
    peor = {"clasificacion_f1_macro": True, "latencia": None, "procedencia_pdf": False}
    assert metricas.sustituir_generativo(base, peor, 0.80, 0.90)["sustituye"] is False
    igual = dict(base)
    assert metricas.sustituir_generativo(base, igual, 0.80, 0.86)["sustituye"] is True
    assert metricas.sustituir_generativo(base, igual, 0.80, 0.84)["sustituye"] is False
    assert metricas.sustituir_embeddings(0.78, 0.84)["sustituye"] is True
    assert metricas.sustituir_embeddings(0.70, 0.76)["sustituye"] is False  # no alcanza el mínimo
    criterios = metricas.criterios_generativos(
        {"inventados": 0.06, "clasificacion_f1_macro": 0.95}, None
    )
    assert (
        criterios["extraccion_inventados"] is False and criterios["clasificacion_f1_macro"] is True
    )
    assert criterios["procedencia_pdf"] is None


# --- Campaña, informe y línea de comandos --------------------------------------------


def test_campana_manifiesto_y_cambios_detectados(raiz: Path) -> None:
    directorio = raiz / "evaluacion" / "campanas"
    campana = cmp.iniciar(
        directorio, identificador="c1", modo=Modo.OFICIAL, generativos={"haiku": "h"},
        embeddings={"cohere": "e"}, repeticiones=3, region="us-east-1", bucket=None, raiz=raiz,
    )  # fmt: skip
    assert campana.manifiesto["reportable"] and set(campana.manifiesto["documentos"]) == {
        "E90-M-CTR-01",
        "E90-M-FAC-01",
    }
    with pytest.raises(cmp.ErrorCampana, match="campana_existente"):
        cmp.iniciar(
            directorio,
            identificador="c1",
            modo=Modo.OFICIAL,
            generativos={},
            embeddings={"e": "e"},
            repeticiones=1,
            region="r",
            bucket=None,
            raiz=raiz,
        )
    assert cmp.abrir(directorio, "c1", raiz)[0].modo is Modo.OFICIAL
    oraculo = raiz / "oraculos/e90/consultas_candidatas.json"
    oraculo.write_text(oraculo.read_text("utf-8") + " ", "utf-8")
    with pytest.raises(cmp.ErrorCampana, match="oraculos_cambiaron"):
        cmp.abrir(directorio, "c1", raiz)


def test_configuracion_y_documentos_que_cambian(
    raiz: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directorio = raiz / "campanas"
    cmp.iniciar(
        directorio,
        identificador="c2",
        modo=Modo.ENSAYO,
        generativos={"h": "h"},
        embeddings={"e": "e"},
        repeticiones=1,
        region="r",
        bucket=None,
        raiz=raiz,
    )
    monkeypatch.setattr(cmp, "huellas_configuracion", lambda: {"otra": "x"})
    with pytest.raises(cmp.ErrorCampana, match="configuracion_cambio"):
        cmp.abrir(directorio, "c2", raiz)
    monkeypatch.undo()
    manifiesto = directorio / "c2" / "manifiesto.json"
    datos = json.loads(manifiesto.read_text("utf-8"))
    datos["documentos"] = {}
    manifiesto.write_text(json.dumps(datos), "utf-8")
    with pytest.raises(cmp.ErrorCampana, match="documentos_cambiaron"):
        cmp.abrir(directorio, "c2", raiz)


class EmbeddingsDeEntrada(EmbeddingsFijos):
    """Ignora el modelo pedido: el CLI construye los adaptadores por identificador."""


def test_linea_de_comandos_de_punta_a_punta(
    raiz: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import atlas.evaluacion.__main__ as principal

    monkeypatch.setattr(cmp, "RAIZ_REPOSITORIO", raiz)
    monkeypatch.setattr(principal, "DIRECTORIO", raiz / "evaluacion" / "campanas")
    monkeypatch.setattr(principal, "CACHE_OCR", raiz / "evaluacion" / "cache_ocr")
    modelos = {"haiku": ModeloDocumentos(), "sonnet": ModeloDocumentos()}
    consulta = ModeloConsultaFijo(buscar="20/01/2027")

    class Converse:
        def __init__(self, _cliente: Any, perfil: str) -> None:
            self.perfil = perfil

        def invocar_herramienta(self, **parametros: Any) -> RespuestaHerramienta:
            destino = (
                consulta
                if parametros["herramienta"]["name"] == esquemas.HERRAMIENTA_CONSULTA
                else modelos[self.perfil]
            )
            return destino.invocar_herramienta(**parametros)  # type: ignore[no-any-return]

    monkeypatch.setattr(principal, "ModeloBedrockConverse", Converse)
    monkeypatch.setattr(principal, "_embeddings", lambda _c, _m: EmbeddingsFijos())
    base = ["--campana", "c3"]
    assert (
        cli(
            [
                "iniciar",
                *base,
                "--modo",
                "oficial",
                "--generativos",
                "haiku=haiku",
                "sonnet=sonnet",
                "--embeddings",
                "cohere=cohere.embed-multilingual-v3",
                "titan=amazon.titan-embed-text-v2:0",
                "--repeticiones",
                "1",
            ]
        )
        == 0
    )
    for paso in ("medir", "indexar", "recuperar", "responder", "planillas"):
        assert cli([paso, *base]) == 0, paso
    assert cli(["planillas", *base]) == 1  # no se sobrescriben las planillas
    assert cli(["ocr", *base]) == 1  # sin bucket no hay OCR
    salida = capsys.readouterr()
    assert "planilla_existente" in salida.err and "falta_bucket" in salida.err
    assert cli(["metricas", *base]) == 0
    assert cli(["metricas", *base, "--con-calificaciones"]) == 1  # planillas en blanco
    resultado = json.loads((raiz / "evaluacion/campanas/c3/metricas.json").read_text("utf-8"))
    assert set(resultado["generativos"]) == {"haiku", "sonnet"}
    assert resultado["embeddings"]["cohere"]["recall_at_5"] == 1.0
    assert resultado["sustitucion"]["embeddings"]["sustituye"] is False
    assert "No cumple" in (raiz / "evaluacion/campanas/c3/informe.md").read_text("utf-8")
    assert cli(["discrepancias", *base]) == 1  # planillas sin completar


def test_informe_rotula_ensayo() -> None:
    resultado = {
        "campana": "e1",
        "modo": "ensayo",
        "reportable": False,
        "generativos": {
            "haiku": {
                "promedios": {
                    "clasificacion_f1_macro": {"serie": [0.95], "promedio": 0.95, "desvio": None},
                    "inventados": {"serie": [0.1], "promedio": 0.1, "desvio": None},
                },
                "repeticiones": [
                    {"adversariales": {"alterados": 0, "casos": []}, "errores_tecnicos": 0}
                ],
            }
        },
        "embeddings": {},
        "sustitucion": {},
    }
    texto = informe.generar(resultado)
    assert "NO REPORTABLE" in texto and "| Cumple |" in texto and "| No cumple |" in texto


def test_ocr_y_cache_por_funciones(raiz: Path) -> None:
    documento = cargar(raiz).documentos["E90-M-CTR-01"]
    assert clave_cache(documento).endswith(".tables-layout.textract.json")


def test_cli_valida_pares_y_elige_adaptadores(
    raiz: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import atlas.evaluacion.__main__ as principal
    from atlas.integraciones.bedrock import EmbeddingsCohereBedrock, EmbeddingsTitanBedrock

    monkeypatch.setattr(cmp, "RAIZ_REPOSITORIO", raiz)
    monkeypatch.setattr(principal, "DIRECTORIO", raiz / "campanas")
    malos = ["iniciar", "--campana", "c5", "--modo", "ensayo", "--generativos", "sin-igual"]
    assert cli([*malos, "--embeddings", "e=e"]) == 1
    assert "se_espera_alias" in capsys.readouterr().err
    assert isinstance(
        principal._embeddings(None, "amazon.titan-embed-text-v2:0"), EmbeddingsTitanBedrock
    )
    assert isinstance(
        principal._embeddings(None, "cohere.embed-multilingual-v3"), EmbeddingsCohereBedrock
    )
    assert cli(["iniciar", "--campana", "c6", "--modo", "ensayo", "--generativos", "h=h",
                "--embeddings", "e=e", "--bucket", "atlas-eval"]) == 0  # fmt: skip
    campana, _ = cmp.abrir(raiz / "campanas", "c6", raiz)
    fuente = principal._fuente(campana, con_servicios=True)
    assert fuente._analizador is not None and fuente._almacen is not None


def test_oficial_exige_commit_identificado(raiz: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def iniciar(identificador: str) -> None:
        cmp.iniciar(
            raiz / "c",
            identificador=identificador,
            modo=Modo.OFICIAL,
            generativos={"h": "h"},
            embeddings={"e": "e"},
            repeticiones=1,
            region="r",
            bucket=None,
            raiz=raiz,
        )

    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": "abc", "cambios_sin_commit": True})
    with pytest.raises(cmp.ErrorCampana, match="commit_no_identificado"):
        iniciar("x1")
    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": None, "cambios_sin_commit": None})
    with pytest.raises(cmp.ErrorCampana, match="commit_no_identificado"):
        iniciar("x2")


def test_commit_sin_git_o_fuera_del_repositorio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    from atlas.evaluacion.campana import _commit

    assert _commit(tmp_path) == {"commit": None, "cambios_sin_commit": None}  # no es un repositorio

    def sin_git(*_: Any, **__: Any) -> Any:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", sin_git)
    assert _commit(tmp_path) == {"commit": None, "cambios_sin_commit": None}
