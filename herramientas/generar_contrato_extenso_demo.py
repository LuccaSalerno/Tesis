#!/usr/bin/env python3
"""Contrato extenso de la demo (DO-2026-10-24-DEMO-EXTENSO): C-v1 con anexos operativos.

Solo para la demo en vivo: no forma parte de PD-07, EVD-01 ni E90, y no cambia C-v1 ni su
oráculo. Las diez páginas iniciales son las de C-v1, generadas con el mismo código de
`generar_corpus.py` (que no se modifica ni se guarda); después siguen anexos operativos
sintéticos. Los datos del contrato (partes, CUIT, celebración, monto, moneda y vigencia) son
los de C-v1, para que la demo use la misma orden y la misma factura. Los anexos no agregan
otros importes totales, fechas de vigencia ni identificaciones tributarias.

Ejecución (entorno de herramientas/corpus_e90/requisitos.txt y LibreOffice local):

    python herramientas/generar_contrato_extenso_demo.py
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GENERADOR = RAIZ / "herramientas" / "generar_corpus.py"
SALIDA = RAIZ / "operaciones" / "demo" / "documentos_a_cargar"
NOMBRE = "0_Contrato_extenso_C-v1-EXT"
CODIGO = "CTR-ATLAS-2026-001 / C-v1-EXT"


def contrato_c_v1() -> dict:
    """Ejecuta el armado de C-v1 de `generar_corpus.py` sin guardarlo."""
    fuente = GENERADOR.read_text(encoding="utf-8")
    corte = fuente.index("d.save(OUT/'C-v1_Contrato_Mantenimiento_ATLAS.docx')")
    espacio: dict = {"__file__": str(GENERADOR)}
    exec(compile(fuente[:corte], str(GENERADOR), "exec"), espacio)  # noqa: S102
    return espacio


def reemplazar(d, inicio: str, texto: str) -> None:
    [parrafo] = [p for p in d.paragraphs if p.text.startswith(inicio)]
    for run in parrafo.runs[1:]:
        run._r.getparent().remove(run._r)
    parrafo.runs[0].text = texto


def anexos(g: dict) -> None:
    d, P, H2, bullet, page, tbl = (g[k] for k in ("d", "P", "H2", "bullet", "page", "tbl"))

    page(d, "Anexo B. Niveles de servicio")
    P(d, "Este anexo describe los niveles de servicio de referencia para la atención de incidentes del parque de ensayo. Los tiempos se cuentan en horas hábiles desde el registro del requerimiento por el referente operativo, y se informan en el reporte mensual. Ninguno de estos valores modifica el monto total, la moneda ni la vigencia establecidos en el cuerpo del contrato.")
    tbl(d, [("Prioridad 1 (crítica)", "Respuesta en 2 horas hábiles; restablecimiento objetivo en 8 horas hábiles"),
            ("Prioridad 2 (alta)", "Respuesta en 4 horas hábiles; restablecimiento objetivo en 16 horas hábiles"),
            ("Prioridad 3 (media)", "Respuesta en 8 horas hábiles; restablecimiento objetivo en 3 días hábiles"),
            ("Prioridad 4 (baja)", "Respuesta en 2 días hábiles; atención planificada en la siguiente visita"),
            ("Horario de atención", "Lunes a viernes de 9 a 18 horas, excepto feriados nacionales")])
    H2(d, "B.1. Criterios de asignación de prioridad")
    P(d, "La prioridad la propone la prestadora a partir del síntoma informado y la confirma el referente de la parte requirente. Un incidente es crítico cuando impide el trabajo de más de un tercio de las estaciones o afecta el repositorio documental compartido. Un incidente es alto cuando afecta una estación de uso exclusivo o un recurso compartido sin alternativa disponible.")
    P(d, "Los incidentes de prioridad media o baja comprenden fallas con alternativa de trabajo, consultas de uso, ajustes de configuración y pedidos de instalación de software autorizado. La reclasificación de un incidente queda registrada con su motivo, la persona que la propuso y la persona que la confirmó.")
    H2(d, "B.2. Medición y exclusiones")
    P(d, "Los tiempos se suspenden mientras el incidente espera una acción de la parte requirente, por ejemplo el acceso físico a un equipo o la aprobación de un cambio. Tampoco se computan las demoras atribuibles a proveedores de terceros, cortes de energía del edificio o casos de fuerza mayor documentados.")
    P(d, "El reporte mensual informa, para cada prioridad, la cantidad de incidentes, el porcentaje atendido dentro del objetivo y los casos fuera de objetivo con su explicación. Un objetivo incumplido se trata conforme al Anexo G; no habilita por sí mismo tareas adicionales ni modifica las condiciones económicas.")

    page(d, "Anexo B (continuación). Indicadores del reporte mensual")
    for t in ["Cantidad de incidentes abiertos, cerrados y pendientes al cierre del mes, por prioridad.",
              "Tiempo medio de respuesta y de restablecimiento, por prioridad, en horas hábiles.",
              "Porcentaje de incidentes atendidos dentro del objetivo de cada prioridad.",
              "Incidentes reabiertos dentro de los cinco días hábiles posteriores a su cierre.",
              "Tareas preventivas planificadas, realizadas y reprogramadas en el mes.",
              "Hallazgos de las revisiones preventivas y recomendaciones sujetas a aprobación humana.",
              "Cambios de configuración realizados, con su referencia al requerimiento que los originó."]:
        bullet(d, t)
    P(d, "Los indicadores se calculan sobre los registros de la herramienta de gestión de solicitudes. Cuando un registro se corrige después del cierre del mes, el reporte siguiente informa la corrección, el valor anterior y el motivo, sin reescribir el reporte ya entregado.")
    P(d, "La parte requirente puede pedir el detalle de cualquier indicador. La prestadora entrega el listado de incidentes que lo sustenta con su identificador, fechas, prioridad y estado, sin incluir el contenido de los documentos o archivos de los usuarios.")

    trimestres = [
        ("Primer trimestre operativo", "marzo, abril y mayo de 2026",
         "relevamiento inicial completo, inventario técnico y verificación de respaldos"),
        ("Segundo trimestre operativo", "junio, julio y agosto de 2026",
         "limpieza interna de equipos, revisión de ventilación y actualización de controladores"),
        ("Tercer trimestre operativo", "septiembre, octubre y noviembre de 2026",
         "revisión de discos, pruebas de restauración y depuración de cuentas locales"),
        ("Cuarto trimestre operativo", "diciembre de 2026, enero y febrero de 2027",
         "revisión general, informe anual de estado y propuesta de renovación del parque"),
    ]
    for i, (nombre, meses, foco) in enumerate(trimestres, start=1):
        page(d, f"Anexo C. Plan de mantenimiento preventivo — {nombre}")
        P(d, f"El {nombre.lower()} comprende {meses}. La visita preventiva se agenda con al menos diez días hábiles de anticipación y se coordina con el referente para no interrumpir actividades del laboratorio. El foco del trimestre es: {foco}.")
        H2(d, f"C.{i}.1. Tareas por estación de trabajo")
        for t in ["Verificación del estado físico, conexiones y periféricos.",
                  "Revisión de actualizaciones pendientes del sistema operativo autorizado.",
                  "Control del espacio libre en disco y de los registros de errores del equipo.",
                  "Verificación del antivirus institucional y de su última actualización.",
                  "Prueba de acceso al repositorio documental simulado con una cuenta de prueba."]:
            bullet(d, t)
        H2(d, f"C.{i}.2. Tareas sobre recursos compartidos")
        P(d, "En cada visita se revisan las dos impresoras de red (estado de consumibles, cola de impresión y configuración) y el repositorio documental simulado (espacio disponible, permisos de las carpetas de ensayo y resultado de la última copia de respaldo). Los hallazgos se registran como observaciones con su prioridad propuesta.")
        H2(d, f"C.{i}.3. Entregables del trimestre")
        P(d, "Al finalizar la visita se entrega un acta de mantenimiento preventivo con las estaciones revisadas, los hallazgos, las tareas pendientes y las recomendaciones. El acta se incorpora al registro de la prestación y requiere la conformidad del referente; las recomendaciones que implican compras o cambios se tratan conforme al Anexo I.")

    page(d, "Anexo D. Inventario técnico del parque de ensayo")
    P(d, "El inventario identifica las estaciones de trabajo ficticias con un código interno. No contiene números de serie, direcciones ni datos de usuarios reales. Se actualiza en cada visita preventiva y cualquier alta o baja queda registrada con su motivo.")
    sectores = ["Recepción de muestras", "Análisis", "Calidad", "Administración", "Dirección técnica"]
    filas = [("Código", "Sector / tipo / estado de ensayo")]
    for n in range(1, 31):
        sector = sectores[(n - 1) % len(sectores)]
        tipo = "estación de escritorio" if n % 3 else "estación portátil"
        filas.append((f"EST-{n:02d}", f"{sector} / {tipo} / operativa"))
    tbl(d, filas)
    H2(d, "D.1. Recursos compartidos")
    tbl(d, [("IMP-01", "Impresora de red, sector Análisis"),
            ("IMP-02", "Impresora de red, sector Administración"),
            ("REP-01", "Repositorio documental simulado, carpetas de ensayo")])
    P(d, "Las estaciones portátiles se revisan en el laboratorio durante la visita. Si una estación no está disponible, la revisión se reprograma y la reprogramación se informa en el acta del trimestre.")

    page(d, "Anexo E. Procedimiento de gestión de incidentes")
    P(d, "El procedimiento describe el ciclo de un incidente desde su registro hasta su cierre. Su propósito es que cada intervención pueda reconstruirse: quién la pidió, qué se hizo, con qué autorización y con qué resultado.")
    H2(d, "E.1. Registro")
    P(d, "El referente registra el incidente en la herramienta de gestión de solicitudes con la estación o el recurso afectado, el síntoma, el momento en que se detectó y la prioridad sugerida. La herramienta asigna un identificador único que se usa en todas las comunicaciones posteriores.")
    H2(d, "E.2. Diagnóstico")
    P(d, "La prestadora confirma la recepción, valida la prioridad y realiza el diagnóstico remoto cuando es posible. Si el diagnóstico requiere acceso físico, coordina la visita con el referente. Las pruebas realizadas y sus resultados se registran en el incidente.")
    H2(d, "E.3. Intervención")
    P(d, "La intervención se ejecuta dentro del alcance del Anexo A y de las tareas del objeto. Si la solución requiere un cambio de configuración, una compra o una tarea fuera del alcance, la prestadora lo propone y espera la autorización correspondiente antes de ejecutarlo.")

    page(d, "Anexo E (continuación). Cierre y reapertura")
    H2(d, "E.4. Cierre")
    P(d, "El incidente se cierra cuando el referente confirma el restablecimiento. La prestadora registra la causa identificada, la solución aplicada y, si corresponde, la recomendación para evitar la repetición. Un incidente sin confirmación del referente permanece en estado resuelto pendiente de conformidad.")
    H2(d, "E.5. Reapertura")
    P(d, "Si el síntoma reaparece dentro de los cinco días hábiles posteriores al cierre, el incidente se reabre con el mismo identificador y se conserva el historial anterior. La reapertura se informa en el reporte mensual como indicador de calidad de la atención.")
    H2(d, "E.6. Comunicación")
    for t in ["Toda comunicación sobre un incidente cita su identificador.",
              "Los cambios de estado se notifican al referente por el canal acordado.",
              "Las comunicaciones no incluyen contraseñas, claves ni contenido de documentos de los usuarios.",
              "Las decisiones que requieren autorización se documentan con el nombre de quien autoriza."]:
        bullet(d, t)

    page(d, "Anexo F. Matriz de escalamiento")
    P(d, "La matriz identifica los roles de cada parte ficticia que intervienen cuando un incidente no se resuelve dentro del objetivo o cuando hay un desacuerdo sobre la prestación. Los roles no corresponden a personas reales y no incluyen datos de contacto.")
    tbl(d, [("Nivel 1", "Técnico de soporte asignado / referente operativo del laboratorio"),
            ("Nivel 2", "Responsable técnico de coordinación / responsable del área usuaria"),
            ("Nivel 3", "Gerencia de servicios de la prestadora / dirección técnica del laboratorio"),
            ("Disparador del nivel 2", "Objetivo de restablecimiento vencido o reapertura reiterada"),
            ("Disparador del nivel 3", "Desacuerdo no resuelto en el nivel 2 en cinco días hábiles")])
    H2(d, "F.1. Registro del escalamiento")
    P(d, "Cada escalamiento se registra en el incidente con su motivo, el nivel alcanzado, la fecha y el resultado. Un escalamiento no suspende la atención del incidente ni modifica su prioridad, salvo que el referente lo confirme expresamente.")
    P(d, "Las reuniones de seguimiento de nivel 3 se documentan con un acta que enumera los temas tratados, las decisiones y los responsables de cada acción. El acta se incorpora al registro de la prestación como cualquier otro documento vinculado.")

    page(d, "Anexo G. Créditos de servicio por incumplimiento de objetivos")
    P(d, "Este anexo describe, a título ilustrativo, el tratamiento de los objetivos de servicio no cumplidos. Los créditos se expresan como porcentaje del abono mensual de referencia y no modifican el monto total del contrato establecido en el cuerpo principal.")
    tbl(d, [("Cumplimiento mensual de prioridad 1 entre 90 % y 95 %", "Crédito del 2 % del abono mensual"),
            ("Cumplimiento mensual de prioridad 1 menor al 90 %", "Crédito del 5 % del abono mensual"),
            ("Cumplimiento mensual de prioridad 2 menor al 90 %", "Crédito del 2 % del abono mensual"),
            ("Visita preventiva no realizada sin reprogramación acordada", "Crédito del 3 % del abono mensual"),
            ("Tope mensual de créditos", "10 % del abono mensual")])
    H2(d, "G.1. Procedimiento")
    P(d, "La prestadora informa en el reporte mensual los objetivos no cumplidos y el crédito que corresponde. El referente revisa el cálculo y lo confirma o lo observa con motivo. Un crédito confirmado se descuenta en la liquidación siguiente; la decisión no se toma de manera automática.")
    P(d, "Los créditos no se aplican a los incumplimientos causados por demoras de la parte requirente, por cambios no autorizados realizados por los usuarios ni por los casos de fuerza mayor del Anexo B.")

    page(d, "Anexo H. Seguridad de la información y respaldos")
    P(d, "La prestadora accede a los equipos del parque de ensayo solo con las cuentas técnicas asignadas para cada intervención. Las cuentas se habilitan para la visita o el incidente y se deshabilitan al finalizar. Las credenciales no se comparten por correo ni se anotan en las actas.")
    H2(d, "H.1. Respaldos")
    P(d, "El repositorio documental simulado tiene una copia de respaldo diaria. En cada visita preventiva se verifica el resultado de las copias del período y, una vez por trimestre, se realiza una prueba de restauración de una carpeta de ensayo, cuyo resultado se registra en el acta.")
    H2(d, "H.2. Equipos que se retiran")
    P(d, "Una estación que se retira del laboratorio para su reparación se entrega sin datos de usuarios o con su disco cifrado. La salida y el regreso del equipo se registran con su código de inventario, la fecha y la persona que autoriza el traslado.")

    page(d, "Anexo H (continuación). Incidentes de seguridad")
    P(d, "Un incidente de seguridad se registra con prioridad crítica. La prestadora contiene el incidente dentro del alcance autorizado, conserva la evidencia técnica disponible y comunica los hechos al referente. Las acciones posteriores, como la notificación a terceros, dependen de la decisión de la parte requirente.")
    for t in ["Acceso no autorizado a una estación o al repositorio documental simulado.",
              "Pérdida o robo de una estación portátil del parque de ensayo.",
              "Detección de software malicioso que el antivirus no pudo contener.",
              "Uso indebido de una cuenta técnica de la prestadora."]:
        bullet(d, t)
    P(d, "Después del cierre, la prestadora entrega un informe del incidente con la cronología, la causa identificada, las acciones tomadas y las recomendaciones. El informe no incluye el contenido de los documentos afectados.")

    page(d, "Anexo I. Gestión de cambios")
    P(d, "Un cambio es cualquier modificación de la configuración de las estaciones o de los recursos compartidos que exceda la intervención de un incidente: instalación de software nuevo, cambio de permisos, actualización mayor del sistema operativo o reemplazo de componentes.")
    H2(d, "I.1. Solicitud y autorización")
    P(d, "La prestadora presenta la solicitud de cambio con su motivo, el alcance, el plan de ejecución, el plan de reversión y el impacto previsto. El referente la aprueba, la observa o la rechaza con motivo. Un cambio aprobado se agenda; un cambio observado vuelve a la prestadora para su corrección.")
    H2(d, "I.2. Ejecución y registro")
    P(d, "El cambio se ejecuta en la fecha acordada y su resultado se registra. Si el cambio falla, se aplica el plan de reversión y se informa. Los cambios realizados se listan en el reporte mensual con su referencia a la solicitud aprobada.")
    P(d, "Los cambios urgentes necesarios para contener un incidente crítico pueden ejecutarse con la autorización verbal del referente, que se documenta en el incidente dentro de las veinticuatro horas siguientes.")

    page(d, "Anexo J. Modelos de reporte y de acta")
    H2(d, "J.1. Reporte mensual de actividades")
    tbl(d, [("Período", "Mes informado"),
            ("Resumen", "Indicadores del Anexo B por prioridad"),
            ("Incidentes fuera de objetivo", "Identificador, prioridad, causa y explicación"),
            ("Mantenimiento preventivo", "Tareas planificadas, realizadas y reprogramadas"),
            ("Cambios", "Cambios ejecutados con su solicitud aprobada"),
            ("Créditos de servicio", "Cálculo propuesto conforme al Anexo G"),
            ("Recomendaciones", "Propuestas sujetas a aprobación humana")])
    H2(d, "J.2. Acta de mantenimiento preventivo")
    tbl(d, [("Trimestre y fecha de visita", "Según el plan del Anexo C"),
            ("Estaciones revisadas", "Códigos del inventario del Anexo D"),
            ("Hallazgos", "Descripción, prioridad propuesta y estado"),
            ("Pendientes", "Tareas no realizadas y fecha de reprogramación"),
            ("Conformidad", "Nombre del referente y fecha de conformidad")])

    page(d, "Anexo J (continuación). Acta de cierre de la prestación")
    P(d, "Al finalizar la vigencia, las partes ficticias labran un acta de cierre que resume la prestación del período: incidentes atendidos, cumplimiento de los objetivos, visitas preventivas realizadas, cambios ejecutados y créditos aplicados. El acta enumera también los pendientes y su tratamiento.")
    tbl(d, [("Período informado", "El de la vigencia del contrato"),
            ("Incidentes del período", "Totales por prioridad y porcentaje dentro del objetivo"),
            ("Mantenimiento preventivo", "Visitas realizadas sobre las cuatro planificadas"),
            ("Pendientes al cierre", "Descripción y responsable de cada uno"),
            ("Conformidad final", "Firmas simuladas de ambas partes ficticias")])
    P(d, "El acta de cierre no reemplaza la conformidad de cada prestación ni la revisión de los documentos vinculados. Se incorpora como un documento más del registro, con su propia versión.")

    page(d, "Anexo K. Glosario")
    for termino, definicion in [
        ("Abono mensual de referencia", "Fracción mensual del monto total del contrato, usada solo para calcular créditos de servicio."),
        ("Acta", "Documento que registra una visita, una reunión o el cierre de la prestación, con la conformidad del referente."),
        ("Cambio", "Modificación de configuración que excede la intervención de un incidente (Anexo I)."),
        ("Crédito de servicio", "Descuento porcentual por objetivos no cumplidos, confirmado por el referente (Anexo G)."),
        ("Escalamiento", "Elevación de un incidente o desacuerdo a un nivel superior de cada parte (Anexo F)."),
        ("Incidente", "Falla o pedido registrado por el referente con un identificador único (Anexo E)."),
        ("Parque de ensayo", "Conjunto de estaciones y recursos compartidos ficticios del inventario (Anexo D)."),
        ("Prioridad", "Clasificación de un incidente según su impacto, que determina sus objetivos (Anexo B)."),
        ("Referente operativo", "Persona designada por la parte requirente para registrar, confirmar y dar conformidad."),
        ("Reporte mensual", "Informe de actividades e indicadores del mes (Anexo J)."),
    ]:
        P(d, f"{termino}: {definicion}")

    page(d, "Anexo L. Cuadro resumen de condiciones")
    P(d, "El cuadro resume las condiciones principales establecidas en el cuerpo del contrato. Ante cualquier diferencia prevalece el texto de las cláusulas 4 y 5.")
    tbl(d, [("Número de contrato", "CTR-ATLAS-2026-001"),
            ("Parte requirente", g["CLIENTE"]),
            ("Contraparte", g["PROVEEDOR"]),
            ("CUIT de la contraparte (dato de prueba)", g["CUIT"]),
            ("Fecha de celebración", "20/02/2026"),
            ("Monto total", "ARS 1.250.000,00 (IVA incluido)"),
            ("Moneda", "ARS - pesos argentinos"),
            ("Vigencia", "Del 01/03/2026 al 28/02/2027, ambas fechas inclusive")])
    P(d, "Fin del documento C-v1-EXT. Versión extensa de C-v1 para la demostración en vivo: material sintético de prueba, sin firmas, sin efecto comercial y sin validez fiscal.")


def main() -> None:
    g = contrato_c_v1()
    d = g["d"]
    # Identificación propia: no es C-v1 ni forma parte del corpus congelado.
    d.sections[0].header.paragraphs[0].text = f"ATLAS | CORPUS SINTÉTICO | {CODIGO} (demo)"
    reemplazar(d, "Identificador documental:", f"Identificador documental: {CODIGO}  |  Versión: 1.0  |  Uso exclusivo: demostración en vivo.")
    reemplazar(d, "Código de corpus: C-v1.", "Código de corpus: C-v1-EXT (versión extensa de C-v1 para la demo). Número de referencia: CTR-ATLAS-2026-001. Estado del documento: material sintético de prueba, sin firmas, sin efecto comercial y sin validez fiscal. Los anexos B a L detallan la operación del servicio.")
    [fin] = [p for p in d.paragraphs if p.text.startswith("Fin del documento C-v1.")]
    fin._p.getparent().remove(fin._p)
    anexos(g)
    with tempfile.TemporaryDirectory() as tmp:
        docx = Path(tmp) / f"{NOMBRE}.docx"
        d.save(docx)
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx)],
            check=True,
            capture_output=True,
        )
        SALIDA.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(tmp) / f"{NOMBRE}.pdf", SALIDA / f"{NOMBRE}.pdf")
    print(f"Generado {SALIDA / (NOMBRE + '.pdf')}")


if __name__ == "__main__":
    main()
