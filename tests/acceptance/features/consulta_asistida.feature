# language: es
@rf_13 @rn_04 @punto_demo_b
Característica: Consulta asistida sobre la documentación autorizada del trámite
  Como responsable del trámite
  Quiero preguntar sobre los documentos incorporados y ver de dónde sale cada respuesta
  Para contrastar cada afirmación con su fuente sin recurrir a información externa

  Antecedentes:
    Dado un responsable del trámite autenticado
    Y el contrato sintético C-v1 procesado e incorporado a su trámite

  Escenario: Pregunta por la vigencia con cita a la página de origen
    Cuando pregunta "¿Hasta cuándo está vigente el contrato?"
    Entonces la respuesta afirma que está vigente hasta el 28/02/2027
    Y cita el documento "Contrato C-v1", versión 1, página 6

  Escenario: Sin evidencia suficiente el sistema se abstiene
    Dado que el modelo indica que los fragmentos no alcanzan
    Cuando pregunta "¿Cuál es el número de cuenta bancaria del proveedor?"
    Entonces la respuesta informa que la evidencia es insuficiente y no afirma nada
