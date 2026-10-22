# language: es
@rf_09 @rf_12 @rn_02 @rn_03 @punto_demo_a
Característica: Validación humana de la clasificación y de los datos extraídos
  Como responsable del trámite
  Quiero confirmar o corregir las sugerencias con su página de origen a la vista
  Para que solo los valores validados alimenten los controles y decisiones del trámite

  Antecedentes:
    Dado un responsable del trámite autenticado
    Y el contrato sintético C-v1 procesado e incorporado a su trámite

  Escenario: Las sugerencias muestran la página de origen y esperan validación
    Entonces la clasificación sugerida es "contrato" y no está validada
    Y el monto total sugerido es "1250000.00" en la página 5

  Escenario: Confirmar la clasificación y un dato conserva la evidencia de la sugerencia
    Cuando confirma la clasificación sugerida
    Y confirma el monto total sugerido
    Entonces el documento queda clasificado como "contrato"
    Y el monto total validado conserva la sugerencia, el actor, la fecha, la versión y la página 5

  Escenario: Corregir un dato conserva la sugerencia original
    Cuando confirma la clasificación sugerida
    Y corrige la moneda a "USD"
    Entonces la moneda vigente es "USD" como corrección
    Y la sugerencia original de la moneda sigue siendo "ARS"

  Escenario: Un dato no se valida antes que la clasificación
    Cuando intenta validar el monto total sin validar la clasificación
    Entonces la validación se rechaza pidiendo validar primero la clasificación
