# Informe de actualización documental — inicio de implementación ATLAS E90

**Alcance:** preparación documental y especificaciones BDD; **sin código de producto ni resultados de evaluación ejecutados**. Esta revisión mantiene los archivos originales salvo cambios y adiciones declarados. No se utilizó AWS.

## Cambios concretos

1. Se incorporó en `docs/tesis/main.pdf` una copia **más reciente proporcionada por los autores**: SHA-256 anterior `2f0d1af82824cdead955d70f9486be95f133c455c4e1f046013608b11f1b61da` → nuevo `dd9a5ccb3f0b62b57066ac50e262a2318cd0e128c35b211e3669cf199df08fc2`. El PDF nuevo ya contempla el corpus de 50 en §6.3.1, pero **todavía no contiene la redacción última de 6.0–6.3 en Markdown**; tampoco acredita pruebas ejecutadas. Conservar la última versión de LaTeX y recompilar es tarea de los autores.
2. Se añadió el archivo Markdown `docs/tesis/ATLAS_Seccion_6_Version_Final_6_0_a_6_3.md` (copia exacta del archivo entregado). Se utiliza como referencia editorial del capítulo 6, no para reemplazar RF/RN/RNF ni resultados medidos. Las correcciones editoriales propuestas posteriormente **no se aplicaron silenciosamente**.
3. Se documentó la correspondencia **§6.2 «Verificación de la cadena de evidencia documental» ↔ EVD-01**. Los contratos EVD-01/V1–V11 no cambian de alcance.
4. Se confirmó el enfoque **BDD y escenarios Gherkin Dado–Cuando–Entonces**; se añadió un `.feature` especificativo con los cuatro recorridos; aún no hay step definitions, API, CI o ejecuciones.
5. Se incorporó el **plan de construcción** de 50 documentos de medición más **15 de ajuste propuestos**, sin falsificar un inventario construido ni modificar el rango contractual vigente 10–15. Se conservaron plantillas separadas de oráculo y registro de evidencia.
6. Se preparó el mapa de evidencias faltantes para completar §6.2–§6.6 con resultados reales, incluidos RNF-07, RNF-08/09, métricas, costos, autorizaciones para §6.4 y conclusiones.

## Compuertas pendientes, por orden de ejecución

- [ ] Confirmar el diseño propuesto de **15 de ajuste**, definir registros/plantillas y congelar corpus/oráculos tras generarlos y revisarlos (incluida validación ARCA de CUIT de PD-07).
- [ ] Implementar base local FastAPI/React/PostgreSQL pgvector/Alembic y suite pytest/BDD/Playwright, con escenarios EVD-01 y cobertura funcional real.
- [ ] Reunir evidencias oficiales de servicios/regiones/retención, cotización y aprobación presupuestaria antes de **cualquier** despliegue AWS humano/manual; conservar políticas E90A.
- [ ] Ejecutar los experimentos E90 con versiones y oráculos congelados, registrar resultados incluso si son adversos.
- [ ] Ejecutar por el equipo autorizado la validación operativa independiente §6.4, registrar únicamente resultados no sensibles.
- [ ] Incorporar en la fuente LaTeX el Markdown aprobado y completar 6.4, 6.5 y revisar 6.6 con evidencias; publicar PDF final recompilado y versionado.

**Estado del ZIP:** listo como **paquete de especificaciones para iniciar el desarrollo local**, pero **no** como aplicación desplegable, corpus congelado o tesis validada experimentalmente.


> **Adenda 22/10/2026:** este informe documenta el estado del 21/10. La posterior sincronización del PDF y Markdown se registra en [Informe_Sincronizacion_Tesis_2026-10-22.md](Informe_Sincronizacion_Tesis_2026-10-22.md).
