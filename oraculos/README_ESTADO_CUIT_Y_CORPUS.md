# Estado del CUIT y de la versión candidata del corpus ATLAS

**Fecha:** 21/10/2026.

- CUIT candidato: `30-96472518-3`, representado sin guiones `30964725183`.
- Longitud y prefijo de sociedad: sí (dos dígitos de tipo + ocho internos + dígito).
- Algoritmo de módulo 11: **correcto** (coeficientes `5,4,3,2,7,6,5,4,3,2` sobre los diez primeros dígitos).
- Búsqueda web informativa de coincidencia exacta: no se obtuvo prueba de una identidad tributaria coincidente; **no es equivalente a la consulta oficial**.
- **Consulta pública ARCA:** PENDIENTE. El asistente no interactuó con su formulario ni obtuvo respuesta oficial para ese CUIT.
- **Conclusión:** CUIT de prueba sintácticamente válido; no declarar inexistente o desasignado. Documentación de corpus en estado **candidato / no congelado**.

## Pasos antes de marcarlo validado

1. Abrir https://arca.gob.ar/buscador-consultas-publicas/ . Buscar “Constancia de inscripción” y/o “Estados administrativos de la CUIT”.
2. Consultar CUIT `30964725183`, sin aportar datos privados de terceros.
3. Conservar fecha y resultado comprobable de la consulta oficial, especificando si se obtuvo “sin resultados”, error de sistema, coincidencia o resultado de otra naturaleza.
4. Si aparece cualquier entidad real asociada o no se puede determinar el estado, no marcarlo como verificado ni afirmar que no está asignado.
5. Si cambia el CUIT, regenerar **todos** los PDF desde la fuente reproducible `herramientas/generar_corpus.py`, cotejar el oráculo, volver a verificar páginas y calcular nuevos SHA-256.
6. Solo entonces congelar el corpus y registrar su versión y fecha en `oraculos/oraculo_PD07_v2_preliminar.json` (v2 del 23/10/2026: número estable en O y F, DO-2026-10-23-CIERRE D4; la v1 queda como antecedente).

> El control de colisiones nunca garantiza al 100 % la inexistencia de asignación, como ya advierte PD-07.
