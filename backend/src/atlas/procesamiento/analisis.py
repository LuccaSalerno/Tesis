"""Clasificación y extracción sobre el contenido normalizado (RF-08, RF-10, RF-11, §5.3).

El modelo solo propone. Toda respuesta se valida contra su esquema; cada valor
conserva su procedencia únicamente si el fragmento citado aparece de verdad en la
página indicada. Si no, la sugerencia queda sin localizador y se informa el motivo
(RF-11). Nada de esto modifica estados, versiones ni permisos (§5.4.3).
"""

from dataclasses import asdict, dataclass
from typing import Any

from atlas.dominio.enumeraciones import MotivoSinFuente, TipoDocumental
from atlas.procesamiento import esquemas
from atlas.procesamiento.contenido import ContenidoNormalizado, comparable, renderizar
from atlas.procesamiento.errores import ErrorPermanente
from atlas.procesamiento.modelo import ModeloGenerativo
from atlas.procesamiento.valores import normalizar


@dataclass(frozen=True)
class Uso:
    modelo: str
    tokens_entrada: int
    tokens_salida: int


@dataclass(frozen=True)
class Clasificacion:
    tipo: TipoDocumental
    version_instrucciones: str
    version_esquema: str
    uso: Uso


@dataclass(frozen=True)
class CampoExtraido:
    campo: str
    valor: str
    valor_original: str
    pagina: int | None
    seccion: str | None
    fragmento: str | None
    motivo_sin_fuente: MotivoSinFuente | None


@dataclass(frozen=True)
class Extraccion:
    tipo: TipoDocumental
    campos: tuple[CampoExtraido, ...]
    version_instrucciones: str
    version_esquema: str
    uso: Uso


def _exigir_dentro_de_limite(contenido: ContenidoNormalizado, caracteres_maximos: int) -> None:
    # Nunca se trunca en silencio: un documento que no entra es un fallo técnico.
    if contenido.caracteres() > caracteres_maximos:
        raise ErrorPermanente("contenido_excede_limite")


def clasificar(
    contenido: ContenidoNormalizado,
    modelo: ModeloGenerativo,
    *,
    max_tokens: int,
    caracteres_maximos: int,
) -> Clasificacion:
    _exigir_dentro_de_limite(contenido, caracteres_maximos)
    respuesta = modelo.invocar_herramienta(
        instrucciones=esquemas.instrucciones(esquemas.VERSION_INSTRUCCIONES_CLASIFICACION),
        contenido=renderizar(contenido),
        herramienta=esquemas.herramienta_clasificacion(),
        max_tokens=max_tokens,
    )
    entrada = respuesta.entrada
    if not isinstance(entrada, dict) or set(entrada) != {"tipo"}:
        raise ErrorPermanente("respuesta_invalida")
    try:
        tipo = TipoDocumental(entrada["tipo"])
    except ValueError as error:
        raise ErrorPermanente("respuesta_invalida") from error
    return Clasificacion(
        tipo=tipo,
        version_instrucciones=esquemas.VERSION_INSTRUCCIONES_CLASIFICACION,
        version_esquema=esquemas.VERSION_ESQUEMA_CLASIFICACION,
        uso=Uso(respuesta.modelo, respuesta.tokens_entrada, respuesta.tokens_salida),
    )


def extraer(
    contenido: ContenidoNormalizado,
    tipo: TipoDocumental,
    modelo: ModeloGenerativo,
    *,
    max_tokens: int,
    caracteres_maximos: int,
) -> Extraccion:
    """Aplica el esquema del tipo sugerido (§5.3.2). Los datos ausentes no generan
    sugerencia (§5.3.3)."""
    _exigir_dentro_de_limite(contenido, caracteres_maximos)
    respuesta = modelo.invocar_herramienta(
        instrucciones=esquemas.instrucciones(esquemas.VERSION_INSTRUCCIONES_EXTRACCION),
        contenido=renderizar(contenido),
        herramienta=esquemas.herramienta_extraccion(tipo),
        max_tokens=max_tokens,
    )
    campos_esperados = esquemas.CAMPOS[tipo]
    entrada = respuesta.entrada
    if not isinstance(entrada, dict) or set(entrada) != {c.nombre for c in campos_esperados}:
        raise ErrorPermanente("respuesta_invalida")
    extraidos = []
    for campo in campos_esperados:
        dato = _validar_dato(entrada[campo.nombre])
        if dato["valor"] is None or not dato["valor"].strip():
            continue
        pagina, seccion, fragmento, motivo = _procedencia(contenido, dato["pagina"], dato["cita"])
        extraidos.append(
            CampoExtraido(
                campo=campo.nombre,
                valor=normalizar(dato["valor"], campo.clase),
                valor_original=dato["valor"],
                pagina=pagina,
                seccion=seccion,
                fragmento=fragmento,
                motivo_sin_fuente=motivo,
            )
        )
    return Extraccion(
        tipo=tipo,
        campos=tuple(extraidos),
        version_instrucciones=esquemas.VERSION_INSTRUCCIONES_EXTRACCION,
        version_esquema=esquemas.version_esquema_extraccion(tipo),
        uso=Uso(respuesta.modelo, respuesta.tokens_entrada, respuesta.tokens_salida),
    )


def _validar_dato(dato: Any) -> dict[str, Any]:
    if not isinstance(dato, dict) or set(dato) != {"valor", "pagina", "cita"}:
        raise ErrorPermanente("respuesta_invalida")
    valor, pagina, cita = dato["valor"], dato["pagina"], dato["cita"]
    if valor is not None and not isinstance(valor, str):
        raise ErrorPermanente("respuesta_invalida")
    if pagina is not None and (isinstance(pagina, bool) or not isinstance(pagina, int)):
        raise ErrorPermanente("respuesta_invalida")
    if cita is not None and not isinstance(cita, str):
        raise ErrorPermanente("respuesta_invalida")
    return {"valor": valor, "pagina": pagina, "cita": cita}


def _procedencia(
    contenido: ContenidoNormalizado, pagina: int | None, cita: str | None
) -> tuple[int | None, str | None, str | None, MotivoSinFuente | None]:
    """Devuelve (página, sección, fragmento, motivo_sin_fuente) verificados (RF-11)."""
    if cita is None or len(comparable(cita)) < 3:
        if pagina is None:
            return None, None, None, MotivoSinFuente.NO_INFORMADA
        return None, None, None, MotivoSinFuente.NO_VERIFICADA
    buscada = comparable(cita)
    if contenido.paginado:
        objetivo = contenido.pagina(pagina) if pagina is not None else None
        if objetivo is None or buscada not in comparable(objetivo.texto()):
            return None, None, None, MotivoSinFuente.NO_VERIFICADA
        paginas = [objetivo]
    else:
        paginas = [p for p in contenido.paginas if buscada in comparable(p.texto())]
        if not paginas or pagina is not None:
            # Un DOCX no tiene páginas: una página informada no puede verificarse.
            return None, None, None, MotivoSinFuente.NO_VERIFICADA
    bloque = next((b for p in paginas for b in p.bloques if buscada in comparable(b.texto)), None)
    if bloque is None:
        # La cita abarca más de un bloque: se conserva la página, sin sección.
        return paginas[0].numero, None, cita.strip()[:500], None
    seccion = (
        bloque.seccion
        if contenido.paginado
        else (f"{bloque.seccion} ({bloque.localizador})" if bloque.seccion else bloque.localizador)
    )
    return paginas[0].numero, seccion[:255] if seccion else None, cita.strip()[:500], None


def a_dict(resultado: Clasificacion | Extraccion) -> dict[str, Any]:
    return asdict(resultado)


def clasificacion_desde_dict(datos: dict[str, Any]) -> Clasificacion:
    return Clasificacion(
        tipo=TipoDocumental(datos["tipo"]),
        version_instrucciones=datos["version_instrucciones"],
        version_esquema=datos["version_esquema"],
        uso=Uso(**datos["uso"]),
    )


def extraccion_desde_dict(datos: dict[str, Any]) -> Extraccion:
    return Extraccion(
        tipo=TipoDocumental(datos["tipo"]),
        campos=tuple(
            CampoExtraido(
                **{
                    **c,
                    "motivo_sin_fuente": (
                        None
                        if c["motivo_sin_fuente"] is None
                        else MotivoSinFuente(c["motivo_sin_fuente"])
                    ),
                }
            )
            for c in datos["campos"]
        ),
        version_instrucciones=datos["version_instrucciones"],
        version_esquema=datos["version_esquema"],
        uso=Uso(**datos["uso"]),
    )
