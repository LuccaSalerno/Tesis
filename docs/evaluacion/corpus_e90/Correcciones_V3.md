# Candidata v3 del corpus E90: correcciones de REV-E90-16 a 19

**Fecha:** 23/10/2026. **Decisión:** DO-2026-10-23-CIERRE (D5). **Estado:** candidata, **no congelada** y **sin revisión de los autores**. No cambia cantidades (50 de medición, 15 de ajuste, 3 adversariales internos, 30 consultas), particiones, plantillas ni umbrales.

Se regeneró el conjunto completo en una raíz limpia con el entorno aprobado del corpus (`herramientas/corpus_e90/requisitos.txt`, LibreOffice y pdftoppm locales), según el procedimiento de `herramientas/corpus_e90/README.md`. El validador informa `errores=0`. El manifiesto y el inventario v2 quedan en `v2/`; Git conserva los binarios v2.

| Hallazgo | Corrección en v3 | Dónde | Comprobación |
|---|---|---|---|
| **REV-E90-16** — IVA residual de un centavo en PRE-05 y PRE-09 | El IVA se calcula como el 21 % del neto redondeado a centavos (mitad hacia arriba). Si neto + IVA no alcanza el total de referencia, se imprime una línea separada «Ajuste por redondeo ± 0,01». Los totales de referencia y el oráculo no cambian | `generar.py` (`montos` y el bloque de importes) | `test_rev_e90_16_iva_y_ajuste_cuadran_en_cada_docx`: lee el texto impreso de cada DOCX con desglose y comprueba IVA = 21 % del neto, neto + IVA + ajuste = total y \|ajuste\| ≤ 0,01. Hay exactamente dos ajustes |
| **REV-E90-17** — condiciones de pago no conciliadas en T1, T2 y T4 | En cada trámite con orden y factura, la condición de pago de la orden y la forma de pago del presupuesto se derivan del vencimiento de la factura, contadas desde la recepción conforme o, sin constancia, desde la entrega comprometida. T1: 18 días desde la recepción; T2: 14 días desde la entrega; T3: 14 días desde la entrega; T4: 2 días desde la recepción. No se infiere precedencia entre documentos: los tres dicen lo mismo. La respuesta de Q16 (forma de pago de la oferta de T3) se recalcula desde los registros | `preparar.py` (`conciliar_pagos`) | `test_rev_e90_17_condiciones_de_pago_conciliadas` |
| **REV-E90-18** — el ambiguo OC-07 conserva el prefijo OC | Número neutro `55372/2026` solo en OC-07. Su clasificación esperada no cambia; la justificación de la ambigüedad lo menciona | `preparar.py` | `test_rev_e90_18_el_ambiguo_oc_07_tiene_numero_neutro` |
| **REV-E90-19** — alcance de los extractos en inglés en Q11/Q12 | El extracto de procedencia es un fragmento propio (`ORIGEN-n`, 18 fragmentos nuevos: 745 en total) y forma parte del conjunto relevante de Q11 y Q12. Cada consulta declara `variantes_admitidas`: se aceptan los plazos y supuestos más específicos del extracto, con cita a él, si no contradicen la adaptación; no se exigen. No se crea una prioridad jurídica ni se amplía la fuente documental | `generar.py`, `consultas.py` | `test_rev_e90_19_extracto_de_procedencia_relevante_y_admitido` |

## Pendientes del equipo antes de congelar

1. Revisión de ambos autores de la v3 con los cuadernos regenerados (los cuatro cambios anteriores y la muestra de documentos).
2. ~~Verificaciones manuales de las 18 razones sociales y de los 6 CUIT de ajuste~~: completadas el 23/10/2026 ([registro](Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md)); no hubo que reemplazar ninguna.
3. Congelación del corpus y de los oráculos, con la tolerancia del 80 % confirmada (D6, DIF-110).
