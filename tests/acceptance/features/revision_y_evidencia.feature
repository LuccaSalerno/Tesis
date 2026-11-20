# language: es
@rf_17 @rf_18 @rf_19 @rf_20 @rf_22 @rn_08 @punto_demo_d
Característica: Flujo de revisión, decisión y evidencia de la decisión
  Como responsable del trámite y como revisores/aprobadores asignados
  Queremos revisar el conjunto documental con un flujo confirmado
  Para que cada decisión quede ligada a las versiones, validaciones y controles que la sustentaron

  Antecedentes:
    Dado una plantilla de contratos con revisión legal y aprobación final
    Y un trámite con el contrato C-v1, la orden O-v1 y la factura F-v1 validados y vinculados

  Escenario: El flujo sugerido queda inactivo hasta que el responsable lo confirma
    Cuando el responsable envía el trámite a validación
    Entonces se sugiere la plantilla de contratos sin crear tareas
    Cuando el responsable confirma el flujo sugerido
    Entonces el trámite queda Pendiente de aprobación con la revisión legal habilitada
    Y el ciclo 1 considera las versiones vigentes de los tres documentos

  Escenario: Recorrido completo hasta la evidencia de la decisión
    Cuando el responsable envía el trámite a validación y confirma el flujo sugerido
    Y el revisor legal aprueba su tarea con las advertencias a la vista
    Y el aprobador final observa su tarea con el motivo "La orden excede la vigencia del contrato"
    Entonces el trámite queda Observado
    Y la evidencia de la observación muestra el ciclo, las versiones, los valores validados y los controles considerados
    Y la línea de tiempo registra la confirmación del flujo, las decisiones y el cambio de estado
