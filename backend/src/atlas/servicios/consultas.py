"""Consulta asistida con recuperación autorizada (RF-13, RN-04, §5.3.4, DO-2026-10-22-RAG).

1. El alcance lo fija el backend: fragmentos del intento vigente de archivos incorporados
   que son la versión vigente de un documento del trámite (P1). Nada del cliente lo amplía.
2. Búsqueda exacta por distancia coseno (RC-P07.3) de los k fragmentos más cercanos.
3. El modelo responde con afirmaciones y sus citas, o se abstiene (P3). El backend descarta
   las afirmaciones sin cita válida; si no queda ninguna, la respuesta es una abstención.
4. Cada consulta se conserva con su evidencia (P2); los registros técnicos solo llevan
   identificadores, duración y códigos.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from atlas.dominio.enumeraciones import MotivoAbstencion
from atlas.persistencia.modelos import ConsultaAsistida, ConsultaFragmento, Tramite
from atlas.persistencia.vector import a_texto
from atlas.procesamiento import esquemas
from atlas.procesamiento.contenido import neutralizar
from atlas.procesamiento.embeddings import ModeloEmbeddings
from atlas.procesamiento.errores import ErrorPermanente
from atlas.procesamiento.modelo import ModeloGenerativo
from atlas.registro import registrar_evento

_registrador = logging.getLogger("atlas.consultas")

_ALCANCE = text(
    """
    SELECT f.id, f.contenido, f.embedding <=> CAST(:vector AS vector) AS distancia,
           d.id AS documento_id, d.nombre AS documento_nombre,
           v.id AS version_id, v.numero AS version_numero,
           rf.pagina, rf.seccion
    FROM atlas.fragmento f
    JOIN atlas.archivo a ON a.id = f.archivo_id AND a.estado_incorporacion = 'incorporado'
    JOIN atlas.version_documental v ON v.archivo_id = a.id
    JOIN atlas.documento d ON d.version_vigente_id = v.id AND d.tramite_id = :tramite
    JOIN atlas.trabajo_procesamiento t
      ON t.id = f.trabajo_id AND t.intento = f.intento AND t.estado = 'completado'
    LEFT JOIN atlas.referencia_fuente rf ON rf.id = f.fuente_id
    WHERE CAST(:versiones AS bigint[]) IS NULL OR v.id = ANY(CAST(:versiones AS bigint[]))
    ORDER BY distancia, f.id
    LIMIT :limite
    """
)


@dataclass(frozen=True)
class FragmentoRecuperado:
    etiqueta: str
    fragmento_id: int
    contenido: str
    distancia: float
    documento_id: int
    documento_nombre: str
    version_id: int
    version_numero: int
    pagina: int | None
    seccion: str | None


@dataclass(frozen=True)
class Afirmacion:
    texto: str
    referencias: tuple[FragmentoRecuperado, ...]


@dataclass(frozen=True)
class Resultado:
    consulta: ConsultaAsistida
    afirmaciones: tuple[Afirmacion, ...]
    recuperados: tuple[FragmentoRecuperado, ...]


def recuperar(
    sesion: Session,
    tramite_id: int,
    vector: list[float],
    limite: int,
    versiones: frozenset[int] | None = None,
) -> list[FragmentoRecuperado]:
    """`versiones`: None para el responsable; para el revisor, las de sus ciclos (P8)."""
    filas = sesion.execute(
        _ALCANCE,
        {
            "vector": a_texto(vector),
            "tramite": tramite_id,
            "limite": limite,
            "versiones": None if versiones is None else sorted(versiones),
        },
    ).mappings()
    return [
        FragmentoRecuperado(
            etiqueta=f"F{posicion}",
            fragmento_id=fila["id"],
            contenido=fila["contenido"],
            distancia=float(fila["distancia"]),
            documento_id=fila["documento_id"],
            documento_nombre=fila["documento_nombre"],
            version_id=fila["version_id"],
            version_numero=fila["version_numero"],
            pagina=fila["pagina"],
            seccion=fila["seccion"],
        )
        for posicion, fila in enumerate(filas, start=1)
    ]


def renderizar(pregunta: str, recuperados: list[FragmentoRecuperado]) -> str:
    """Pregunta y fragmentos delimitados como datos; ninguno puede cerrar su etiqueta."""
    partes = [f"<pregunta>{neutralizar(pregunta)}</pregunta>", "<fragmentos>"]
    for f in recuperados:
        pagina = f' pagina="{f.pagina}"' if f.pagina is not None else ""
        partes.append(
            f'<fragmento id="{f.etiqueta}" documento="{neutralizar(f.documento_nombre)}"'
            f' version="{f.version_numero}"{pagina}>\n{neutralizar(f.contenido)}\n</fragmento>'
        )
    partes.append("</fragmentos>")
    return "\n".join(partes)


def _validar(entrada: Any) -> tuple[bool, list[tuple[str, list[str]]]]:
    if not isinstance(entrada, dict) or set(entrada) != {"suficiente", "afirmaciones"}:
        raise ErrorPermanente("respuesta_invalida")
    suficiente, afirmaciones = entrada["suficiente"], entrada["afirmaciones"]
    if not isinstance(suficiente, bool) or not isinstance(afirmaciones, list):
        raise ErrorPermanente("respuesta_invalida")
    validadas = []
    for afirmacion in afirmaciones:
        if (
            not isinstance(afirmacion, dict)
            or set(afirmacion) != {"texto", "fragmentos"}
            or not isinstance(afirmacion["texto"], str)
            or not isinstance(afirmacion["fragmentos"], list)
            or not all(isinstance(e, str) for e in afirmacion["fragmentos"])
        ):
            raise ErrorPermanente("respuesta_invalida")
        validadas.append((afirmacion["texto"].strip(), afirmacion["fragmentos"]))
    return suficiente, validadas


def consultar(
    sesion: Session,
    *,
    tramite: Tramite,
    usuario_id: int,
    pregunta: str,
    embeddings: ModeloEmbeddings,
    modelo: ModeloGenerativo,
    limite: int,
    max_tokens: int,
    versiones: frozenset[int] | None = None,
) -> Resultado:
    inicio = time.perf_counter()
    vector = embeddings.embeber([pregunta], "search_query")[0]
    recuperados = recuperar(sesion, tramite.id, vector, limite, versiones)
    por_etiqueta = {f.etiqueta: f for f in recuperados}

    afirmaciones: list[Afirmacion] = []
    motivo: MotivoAbstencion | None = None
    uso: tuple[str | None, str | None, int | None, int | None] = (None, None, None, None)
    if not recuperados:
        motivo = MotivoAbstencion.SIN_FRAGMENTOS  # sin evidencia autorizada: no se invoca
    else:
        respuesta = modelo.invocar_herramienta(
            instrucciones=esquemas.instrucciones(esquemas.VERSION_INSTRUCCIONES_CONSULTA),
            contenido=renderizar(pregunta, recuperados),
            herramienta=esquemas.herramienta_consulta(),
            max_tokens=max_tokens,
        )
        uso = (
            respuesta.modelo,
            esquemas.VERSION_INSTRUCCIONES_CONSULTA,
            respuesta.tokens_entrada,
            respuesta.tokens_salida,
        )
        suficiente, propuestas = _validar(respuesta.entrada)
        if not suficiente:
            motivo = MotivoAbstencion.EVIDENCIA_INSUFICIENTE
        else:
            for texto_afirmacion, etiquetas in propuestas:
                citas = tuple(
                    dict.fromkeys(por_etiqueta[e] for e in etiquetas if e in por_etiqueta)
                )
                if texto_afirmacion and citas:  # P3: sin cita válida, se descarta
                    afirmaciones.append(Afirmacion(texto_afirmacion, citas))
            if not afirmaciones:
                motivo = MotivoAbstencion.SIN_CITAS_VALIDAS

    citados = {f.fragmento_id for a in afirmaciones for f in a.referencias}
    consulta = ConsultaAsistida(
        tramite_id=tramite.id,
        usuario_id=usuario_id,
        pregunta=pregunta,
        suficiente=motivo is None,
        respuesta=" ".join(a.texto for a in afirmaciones) if motivo is None else None,
        afirmaciones=[
            {"texto": a.texto, "fragmentos": [f.fragmento_id for f in a.referencias]}
            for a in afirmaciones
        ],
        motivo_abstencion=motivo,
        modelo_generacion=uso[0],
        version_instrucciones=uso[1],
        modelo_embeddings=embeddings.identificador,
        tokens_entrada=uso[2],
        tokens_salida=uso[3],
        duracion_ms=round((time.perf_counter() - inicio) * 1000),
    )
    sesion.add(consulta)
    sesion.flush()
    for posicion, fragmento in enumerate(recuperados, start=1):
        sesion.add(
            ConsultaFragmento(
                consulta_id=consulta.id,
                posicion=posicion,
                fragmento_id=fragmento.fragmento_id,
                distancia=fragmento.distancia,
                citado=fragmento.fragmento_id in citados,
            )
        )
    sesion.flush()
    registrar_evento(
        _registrador,
        "consulta_asistida",
        tramite_id=tramite.id,
        usuario_id=usuario_id,
        duracion_ms=consulta.duracion_ms,
        codigo_error=motivo.value if motivo else None,
    )
    return Resultado(
        consulta=consulta, afirmaciones=tuple(afirmaciones), recuperados=tuple(recuperados)
    )


# --- Historial propio (DO-2026-10-22-WEB F6) --------------------------------------------

_CITADOS = text(
    """
    SELECT f.id, f.contenido, d.id AS documento_id, d.nombre AS documento_nombre,
           v.id AS version_id, v.numero AS version_numero, rf.pagina, rf.seccion
    FROM atlas.fragmento f
    JOIN atlas.version_documental v ON v.archivo_id = f.archivo_id
    JOIN atlas.documento d ON d.id = v.documento_id AND d.tramite_id = :tramite
    LEFT JOIN atlas.referencia_fuente rf ON rf.id = f.fuente_id
    WHERE f.id = ANY(CAST(:ids AS bigint[]))
    """
)


def _citas(afirmacion: dict[str, object]) -> list[int]:
    ids = afirmacion.get("fragmentos")
    return [int(i) for i in ids] if isinstance(ids, list) else []


@dataclass(frozen=True)
class ConsultaRegistrada:
    consulta: ConsultaAsistida
    afirmaciones: tuple[Afirmacion, ...]
    recuperados: int


def historial(sesion: Session, tramite_id: int, usuario_id: int) -> list[ConsultaRegistrada]:
    """Consultas propias del trámite, de la más reciente a la más antigua, con las citas
    reconstruidas desde los fragmentos guardados (DO-2026-10-22-RAG P2)."""
    consultas = list(
        sesion.scalars(
            select(ConsultaAsistida)
            .where(
                ConsultaAsistida.tramite_id == tramite_id,
                ConsultaAsistida.usuario_id == usuario_id,
            )
            .order_by(ConsultaAsistida.id.desc())
        )
    )
    ids = sorted({i for c in consultas for a in c.afirmaciones for i in _citas(a)})
    fragmentos = {
        fila["id"]: FragmentoRecuperado(
            etiqueta="",
            fragmento_id=fila["id"],
            contenido=fila["contenido"],
            distancia=0.0,
            documento_id=fila["documento_id"],
            documento_nombre=fila["documento_nombre"],
            version_id=fila["version_id"],
            version_numero=fila["version_numero"],
            pagina=fila["pagina"],
            seccion=fila["seccion"],
        )
        for fila in sesion.execute(_CITADOS, {"tramite": tramite_id, "ids": ids}).mappings()
    }
    recuperados = dict(
        sesion.execute(
            select(ConsultaFragmento.consulta_id, func.count())
            .where(ConsultaFragmento.consulta_id.in_([c.id for c in consultas]))
            .group_by(ConsultaFragmento.consulta_id)
        ).all()
    )
    return [
        ConsultaRegistrada(
            consulta=c,
            afirmaciones=tuple(
                Afirmacion(
                    str(a["texto"]),
                    tuple(fragmentos[i] for i in _citas(a) if i in fragmentos),
                )
                for a in c.afirmaciones
            ),
            recuperados=int(recuperados.get(c.id, 0)),
        )
        for c in consultas
    ]
