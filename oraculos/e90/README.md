# Referencias candidatas del corpus E90 (v2)

Borradores de referencia y metadatos de generación de la versión **e90-candidato-v2** (DO-2026-10-22-CORPUS-REVISION). No contienen resultados experimentales ni calificaciones de los autores. El estado es CANDIDATO_NO_CONGELADO y `revisado_por_autores` permanece falso.

- `inventario_candidato.csv`: los 65 archivos de entrada, con su ID de inventario y su ruta neutra.
- `artefactos_candidatos.json`: originales y auxiliares con hashes, herramientas y transformaciones simuladas.
- `campos_candidatos.json`: 403 campos con valor normalizado, representación impresa, etiqueta impresa, modo de localización y localizador; distingue presencia y ausencia.
- `fragmentos_candidatos.json`: 727 fragmentos primarios (campos, condiciones, cláusulas, objeto, referencias y adversariales). Los chunks técnicos se mapearán después para cada indexación.
- `consultas_candidatas.json`: 30 preguntas previas a ejecutar modelos, con afirmaciones atómicas limitadas a lo preguntado.
- `cuit_candidatos.json`: 18 CUIT; los 12 de medición con el reporte manual ARCA del equipo («No existe», 22/10/2026) y los 6 de ajuste pendientes.

Una comprobación estructural exitosa no acredita calidad de OCR/IA, adecuación semántica de las referencias, inexistencia de un CUIT o razón social, revisión de autores ni aceptación de IA-D/IA-M. PD-07 no se modifica ni se importa a estas particiones.
