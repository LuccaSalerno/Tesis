# Revisión independiente del incremento E90

Rama `codex/corpus-e90`, base `1e2a6c6`. Alcance autorizado: corpus candidato y validadores. No ejecutar AWS, no regenerar PD-07, no congelar ni marcar revisiones de autores.

## Reproducir las comprobaciones

Desde esta rama y su worktree, con el entorno del backend ya disponible o un entorno de pruebas propio:

```bash
python -m pytest -q tests
python -m herramientas.corpus_e90.validar
python herramientas/validar_inventario_e90.py --inventario oraculos/e90/inventario_candidato.csv
```

Los comandos inspeccionan lo construido: no generan documentos ni necesitan LibreOffice. La prueba de render se omite explícitamente en CI; su ejecución local está documentada en `herramientas/corpus_e90/README.md`.

Verificar especialmente:

- Inventario de 50 + 15, exactamente 10 + 3 por tipo, tres adversariales internos. Los 130 archivos auxiliares DOCX/PDF no se cuentan como documentos extra de medición.
- BASE_A/BASE_B compartidas; MED_C/MED_D exclusivas de medición. Las cuatro fuentes contractuales aprobadas deben conservar sus diferencias de cláusulas y complejidad, no solo nombres y valores distintos.
- Correspondencia de cada campo con el archivo final. Cuando dos campos tienen igual valor, la igualdad textual por sí sola no demuestra que el párrafo correcto corresponda al campo esperado.
- Las páginas esperadas de PDF de imágenes proceden del PDF digital previo, ligado por hash. El cotejo visual de la imagen final y la revisión semántica son necesarios; el verificador no realiza OCR.
- Las 30 preguntas usan únicamente documentos de medición ya construidos; las seis multidocumento citan al menos dos archivos dentro del contexto autorizado. Los fragmentos primarios todavía deben mapearse a chunks de cada indexación congelada.
- Los casos ambiguos tienen etiqueta candidata fijada antes de cualquier consulta a modelos. Revisar su justificación semántica; no inferir calidad de la dificultad a partir de la etiqueta del plan.
- Las evaluaciones de los autores están vacías, `revisado_por_autores` sigue falso y todos los registros permanecen candidatos. Los CUIT requieren la consulta manual ARCA indicada en su lista; su dígito no prueba inexistencia.
- Los anexos bilingües de los contratos extensos y las simulaciones digitales están declarados en las diferencias. Su representatividad académica queda pendiente de revisión.
- No existen cambios en backend/frontend, migraciones, workflows, Terraform ni los originales de PD-07 en esta rama. Los únicos archivos previos editados son cuatro registros documentales compartidos.

## Comprobar procedencia de los modelos

El banco `herramientas/corpus_e90/plantillas/contratos.json` conserva la URL de publicación y del archivo exacto, versión, SHA-256 del original y del texto extraído, extractos originales, localizadores, atribución y traducciones/adaptaciones. Los archivos originales en blanco se descargaron a `/tmp/e90_fuentes` para comprobarlos; son referencias públicas autorizadas, no documentos de una operación real ni entradas de la muestra. No se incorporaron los binarios originales al corpus final.

Método de numeración para los extractos:

- GOV.UK DOCX: se abrió `word/document.xml` como ZIP/XML y se enumeraron todos los elementos `w:p` en orden de documento, concatenando los textos `w:t`; se conservaron los párrafos vacíos. Índices 1-based.
- Bonterms/Common Paper HTML: extracción con `html.parser.HTMLParser` de la biblioteca estándar, ignorando `script/style`. Se agregaron separadores de línea al abrir/cerrar `p`, `li`, `h1`–`h4`, `div`, y al abrir `br`. Cada línea no vacía se normalizó uniendo sus palabras con un espacio. Los rangos del banco son 1-based respecto de ese texto. Un cambio de HTML puede alterar la numeración; contrastar siempre también el extracto y los hashes.

El SHA del código presente durante la generación está en el manifiesto como instantánea histórica; el validador se reforzó después para distinguir etiquetas de campos con el mismo valor y el escritor CSV se fijó a LF. El inventario anterior y el normalizado se compararon por parseo, sin cambios de datos. La evidencia final registra por separado las huellas del código de verificación. No cambiar las huellas de la generación histórica para simular que no hubo iteraciones.

## Integración posterior

Los IDs DIF-E90-* son provisionales. Conciliar las cuatro actualizaciones de documentos compartidos con las de otras ramas y renumerar donde corresponda. Revisar diff y ejecutar verificaciones en la rama integrada antes de aceptar. Este incremento no hace push ni merge a main. Una revisión técnica de agente no reemplaza las revisiones humanas ni la congelación del equipo.

## Adenda ARG_A — revisión del reemplazo aprobado

Ver `Incorporacion_ARG_A_CPAU.md` y `Revision_ARG_A.json`: solo E90-M-CTR-03 cambia de BASE_A a CPAU. Ahora hay cinco familias de contratos y cuatro por cada otro tipo; cantidades, formatos y dificultades siguen iguales. El CSV del diseño tiene una única fila cambiada respecto del incremento inicial. Revisar las siete referencias de campos, los nueve fragmentos primarios del nuevo documento y Q12; los otros 29 registros de preguntas se conservan.

La ficha específica CPAU vincula el único archivo 834, MEPAU_A-301_2023.pdf, con CC BY-NC-SA 4.0. `fuentes/ARG_A_CPAU_verificacion.json` registra SHA-256 y revisión de las siete páginas; `ARG_A_CPAU_avisos.html` conserva extractos de la ficha. El original en blanco se descargó a `/tmp/e90_cpau_A301_2023.pdf`, no se agrega como entrada del corpus. Los extractos originales españoles del banco se localizan por cláusula y página de PDF, no por los índices de párrafo de las otras fuentes. No se confundió la cláusula de propiedad intelectual de planos con la licencia del modelo. La introducción menciona diez cláusulas, pero el cuerpo numera nueve; se adaptaron esas nueve, sin inventar un original adicional.

Comparar los 64 documentos y 128 auxiliares con las huellas anteriores preservadas en `Revision_ARG_A.json`. La revisión parcial del manifiesto identifica el código y entorno usados para ARG_A; los campos superiores históricos de código no fueron sustituidos por los del generador nuevo. La revisión visual actual conserva las 101 páginas sin cambios y sustituye la inspección de las tres páginas de ARG_A, sin atribuir una nueva revisión humana al resto.

La licencia no comercial y CompartirIgual se identifica dentro de la pieza y por fuente en el banco; no se mezclan cláusulas con las familias OGL/CC BY. Revisar los permisos de cada pieza al distribuir la colección. Ninguna verificación de agente equivale a dictamen jurídico ni a revisión de autores.
