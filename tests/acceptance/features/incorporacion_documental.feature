# language: es
@rf_04 @rf_07 @do_2026_10_22_cargas
Característica: Incorporación documental de un archivo cargado
  Como responsable del trámite
  Quiero cargar un archivo y confirmar su incorporación como documento nuevo
  Para que forme parte del conjunto documental con su versión inicial vigente

  Antecedentes:
    Dado un responsable del trámite autenticado
    Y un trámite en Borrador a su cargo

  @rf_04
  Escenario: La carga confirmada queda pendiente sin modificar el trámite
    Cuando carga el documento sintético "C-v1_Contrato_Mantenimiento_ATLAS.pdf"
    Entonces el archivo queda pendiente de incorporación con su huella SHA-256
    Y el trámite sigue en Borrador sin documentos

  @rf_05 @rf_07
  Escenario: La incorporación crea un documento con su versión inicial vigente
    Dado que cargó el documento sintético "C-v1_Contrato_Mantenimiento_ATLAS.pdf"
    Cuando confirma su incorporación como documento nuevo
    Entonces el trámite tiene un documento cuya versión vigente es la número 1
    Y la incorporación queda registrada en la auditoría con su versión

  @do_2026_10_22_cargas
  Escenario: Una carga pendiente vencida no puede incorporarse
    Dado que cargó el documento sintético "C-v1_Contrato_Mantenimiento_ATLAS.pdf"
    Y pasaron más de 24 horas sin incorporarlo
    Cuando confirma su incorporación como documento nuevo
    Entonces la incorporación se rechaza por vencimiento
    Y el trámite sigue en Borrador sin documentos

  @rnf_01
  Escenario: Otro responsable no puede incorporar archivos de un trámite ajeno
    Dado que cargó el documento sintético "C-v1_Contrato_Mantenimiento_ATLAS.pdf"
    Cuando otro responsable intenta incorporarlo
    Entonces la operación se rechaza sin revelar el trámite
    Y el trámite sigue en Borrador sin documentos
