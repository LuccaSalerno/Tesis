# language: es
@rf_14 @rf_15 @rf_16 @rn_05 @rn_06 @punto_demo_c
Característica: Vínculos documentales y reglas de consistencia
  Como responsable del trámite
  Quiero vincular el contrato, la orden de compra y la factura y ver los controles R1 a R4
  Para detectar inconsistencias explicables sobre los valores validados, sin que decidan por mí

  Antecedentes:
    Dado un responsable del trámite autenticado
    Y un trámite con el contrato C-v1 validado

  Escenario: El sistema sugiere el vínculo y no lo aplica hasta que se confirma
    Cuando incorpora y valida la orden de compra "O-v1"
    Entonces se sugiere un vínculo pendiente entre la orden y el contrato
    Y no hay controles ejecutados
    Cuando confirma el vínculo sugerido
    Entonces el vínculo rige y los controles se ejecutan

  Escenario: Advertencia de orden de compra fuera de la vigencia del contrato
    Cuando incorpora, valida y vincula la orden de compra "O-v1" y la factura "F-v2"
    Entonces R3 advierte que la fecha de la orden 2027-03-15 está fuera de la vigencia
    Y R1, R2 y R4 se cumplen
    Y el control R3 muestra la regla, las versiones y los valores validados comparados
    Y el trámite sigue en Borrador

  Escenario: Corregir la fecha validada deja un control nuevo y conserva el anterior
    Cuando incorpora, valida y vincula la orden de compra "O-v1" y la factura "F-v2"
    Y corrige la fecha validada de la orden a "2026-09-15"
    Entonces R3 se cumple con una ejecución nueva
    Y la ejecución con la advertencia sigue en el historial sin cambios
