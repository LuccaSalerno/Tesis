# language: es
@evd_01 @cadena_evidencia
Característica: Reconstrucción de la cadena de evidencia documental de ATLAS
  Como actor autorizado del trámite
  Quiero recuperar las relaciones históricas entre versiones, validaciones, controles y decisiones
  Para reconstruir la evidencia que sustentó cada intervención

  @evd_a @rn_12
  Escenario: Una versión confirmada después de la aprobación abre una nueva revisión
    Dado un trámite con un conjunto documental validado y un primer ciclo aprobado
    Cuando se confirma la incorporación de una nueva versión antes del cierre
    Entonces la decisión del primer ciclo sigue asociada a las versiones que consideró
    Y el nuevo conjunto documental requiere la revisión y decisión que correspondan
    Y la aprobación anterior no se transfiere automáticamente al nuevo ciclo

  @evd_b @rn_08 @rn_09 @rn_12
  Escenario: Una observación seguida de una corrección documental mantiene la historia
    Dado un primer ciclo con una observación motivada
    Cuando se confirma una versión corregida del documento observado
    Entonces la observación anterior conserva su contexto documental
    Y se crea el ciclo correspondiente al conjunto documental actualizado
    Y el resultado de la revisión posterior queda ligado a ese nuevo ciclo

  @evd_c @rn_13
  Escenario: La subsanación sin nuevo archivo no fabrica una versión documental
    Dado un ciclo observado con el documento vigente identificado
    Cuando se subsanan datos o metadatos sin reemplazar el contenido del archivo
    Entonces se conserva la versión documental existente
    Y el trámite regresa al estado de validación exigido por RN-13
    Y la nueva revisión no hereda automáticamente la decisión anterior

  @evd_n12 @rn_12
  Escenario: No se acepta una decisión tardía desde una tarea de ciclo desplazado
    Dado un ciclo de revisión con una tarea pendiente
    Cuando se confirma un cambio del conjunto documental que desplaza ese ciclo
    Y se intenta resolver la tarea pendiente del ciclo anterior
    Entonces la operación es rechazada por estar desactualizada
    Y no se crea una decisión válida ni se altera retroactivamente la evidencia anterior
