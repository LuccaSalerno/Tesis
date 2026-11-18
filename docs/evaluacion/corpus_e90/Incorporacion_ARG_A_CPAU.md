# Incorporación de ARG_A — CPAU

Fecha: 22/10/2026. Rama `codex/corpus-e90`, base de esta revisión `98e60f3`. **Commit de implementación: `e3337a9`**; cierre documental en el commit posterior. Decisión **DO-2026-10-22-CORPUS-ARG-A**, aprobación expresa del reemplazo recibida antes de implementar. Estado: **CANDIDATO_NO_CONGELADO**, sin mediciones de IA ni revisión de autores.

## Verificación del archivo y condiciones de reutilización

Obra: **MEPAU A-301, Contrato de proyecto y dirección**, Consejo Profesional de Arquitectura y Urbanismo (CPAU, Buenos Aires), 9.ª edición, 2023, siete páginas. La [ficha individual](https://repositorio.cpau.org/items/show/823) identifica autor/editor y asigna **CC BY-NC-SA 4.0** en su campo Licencia; su descriptor del único archivo 834 vincula `MEPAU_A-301_2023.pdf` con el [PDF concreto](https://repositorio.cpau.org/files/original/6a40a2ebfb34e5f36f1f2d8a361003ca.pdf).

SHA-256 del PDF consultado: `f033e08cf26c1d62a289e3ada3549962e8094866b087eb15cb3e6b56647c0205`, 337.927 bytes. Se leyeron y renderizaron las siete páginas. El PDF identifica CPAU/MEPAU y la edición; no imprime la licencia ni se detectó un aviso de derechos contradictorio. La asignación se respalda en la ficha específica y su vínculo al archivo, no únicamente en el pie general del sitio. `fuentes/ARG_A_CPAU_verificacion.json` y `ARG_A_CPAU_avisos.html` conservan metadatos, huellas, localizadores y extractos de evidencia. Es comprobación documental de avisos visibles, no dictamen jurídico ni garantía de titularidad.

La cláusula 7 del original trata la propiedad de planos del proyecto contratado, no la licencia de reutilización de la plantilla. La introducción anuncia diez cláusulas; el cuerpo numera 1 a 9 y cierra con espacios para acuerdos y firmas. Se adaptaron esas nueve cláusulas, sin inventar una décima ni incorporar automáticamente otros documentos referidos (A-115, C-22, etc.). El original está en español: **no hubo traducción**.

La adaptación conserva autor/organismo, obra, edición, fuente, licencia y cambios; omite logotipos, firmas, matrículas e identidades reales. Se comparte bajo [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), para uso exclusivamente no comercial y con CompartirIgual. Avisos dentro del PDF/DOCX, en el banco de fuentes y en `corpus/e90/ATRIBUCIONES.md`. La [licencia, secciones 2 y 3](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.es), permite la adaptación con esas condiciones. La [FAQ de Creative Commons sobre colecciones](https://creativecommons.org/faq/#if-i-create-a-collection-that-includes-a-work-offered-under-a-cc-license-which-licenses-may-i-choose-for-the-collection) distingue incorporar obras independientes de crear una adaptación conjunta: se mantienen licencias por pieza, sin mezclar cláusulas de otras fuentes dentro de ARG_A ni imponer NC/SA a todo el código o las otras familias. No se identificó incompatibilidad para esta incorporación académica no comercial; la pieza no queda habilitada para distribución comercial irrestricta. No hay aval del CPAU ni validación jurídica del contrato para Argentina.

## Reemplazo y condiciones metodológicas

| Familia de contratos | Medición antes | Medición actual | Ajuste actual |
|---|---:|---:|---:|
| BASE_A | 2 | 1 | 2 |
| BASE_B | 2 | 2 | 1 |
| MED_C | 3 | 3 | 0 |
| MED_D | 3 | 3 | 0 |
| ARG_A | 0 | 1 | 0 |
| **Total** | **10** | **10** | **3** |

Se cambia únicamente **E90-M-CTR-03** (PDF digital); no tiene caso difícil ni marca adversarial. BASE_A conserva un ejemplo de medición y dos de ajuste. Los extensos CTR-06/08, la ausencia CTR-05, la degradación CTR-09 y el adversarial CTR-10 permanecen intactos. En los otros cuatro tipos se conservan las cuatro familias iniciales. No cambia el protocolo, la distribución de formatos, 50 de medición + 15 de ajuste, los tres adversariales ni las 30 preguntas 10/8/6/6. ARG_A no se utiliza para ajuste; es una plantilla no vista en esa partición.

La variabilidad nueva es estructural y semántica: encabezamiento comitente/arquitecto/a, nueve cláusulas, programa de necesidades, croquis, anteproyecto, documentación, dirección diferenciada de ejecución material, honorarios, cambios de encargo y secuencia mediación/pericia arbitral. El contrato ocupa tres páginas con condiciones en párrafos y atribución en página separada. No es una variación de nombres/valores del contrato de mantenimiento. La demo PD-07 conserva su historia de mantenimiento y todas sus inconsistencias.

Para evitar ambigüedades añadidas se distingue expresamente el **total de honorarios** de un presupuesto de construcción, no se agrega un segundo monto de obra y se fijan hitos 4/9/14 días compatibles con el plazo de entrega de 14 días. La dirección se extiende durante la vigencia del instrumento. La moneda del nuevo caso es ARS. Los restantes seis valores de extracción se conservan respecto de la referencia candidata previa. Todos los sujetos, lugar de obra y operaciones son ficticios; no existe matrícula profesional. El CUIT sigue candidato y pendiente de consulta ARCA.

Un caso argentino entre diez contratos agrega cobertura, pero **no acredita representatividad nacional ni ausencia de sesgos**. La elección es deliberada y previa a medir, sin observar resultados de modelos. Los autores deberán revisar la dificultad y adecuación de la muestra; no se calculan métricas por país/familia con este único caso ni se alteran oráculos después de medir.

## Referencias, hashes y límites del cambio

Los siete campos del esquema RC-P04 están presentes en página 1 y cotejados con el registro previo al render: contraparte, CUIT, fecha de celebración, vigencia desde/hasta, monto total y moneda. Se actualizaron los hashes del PDF, DOCX fuente y PDF de referencia, sus metadatos, siete referencias de campos y nueve fragmentos primarios. El total sigue en 403 campos (398 presentes, cinco ausentes) y 534 fragmentos. Q12 conserva ID, categoría y contexto; se reconstruyeron respuesta y cita después del nuevo documento. Los otros 29 registros de preguntas son idénticos.

`Revision_ARG_A.json` conserva las 64 entradas y sus 128 auxiliares con hashes anteriores y nuevos artefactos del caso sustituido. Se compararon además los registros, artefactos, campos y fragmentos de los otros 64 documentos por igualdad de datos. El inventario y el diseño tienen una única fila cambiada. El manifiesto conserva la historia del código/entorno de la generación anterior y registra por separado la generación parcial de ARG_A. Las huellas globales de registros y banco describen el conjunto actual. Los cuatro registros de fuentes anteriores conservan su contenido y formato; solo se agrega ARG_A.

La auditoría inicial PD-07 conserva su evidencia histórica de trece hashes. De sus trece entradas, solo cambió después el hash del CSV de diseño por el reemplazo aprobado; eso no modifica los doce archivos de PD-07/generador/oráculo. La aprobación y ambas huellas del plan se conservan en `Revision_ARG_A.json`; no se reescribe la auditoría para simular que el diseño nunca cambió.

La revisión visual actual combina las 101 páginas sin cambios y las tres páginas nuevas inspeccionadas de ARG_A; no se atribuye a los autores ni equivale a validación semántica o jurídica. Se mantiene el límite de revisión independiente, ARCA y revisión de ambos autores antes de congelar.

## Informe de tarea

Tarea: Etapa 4, preparación §6.3.1, reemplazo aislado aprobado ARG_A.

Requisitos cubiertos: IA-D01/03/07/08, IA-M12, RC-P04, RC-P06.2 y RNF-03/RNF-09; preparación y comprobaciones estructurales, sin marcar aceptación como Cumple.

Archivos modificados: diseño de una fila; registro y tres artefactos de E90-M-CTR-03; banco/generador/preparación/validación y pruebas; inventario, campos, fragmentos, Q12 y manifiesto; procedencia/atribuciones, evidencia y documentación dependiente. Lista exacta de esta revisión en `Archivos_ARG_A.txt`. Sin backend/frontend, infraestructura, dependencias nuevas ni originales PD-07.

Decisiones delegadas tomadas: ninguna. DO-2026-10-22-CORPUS-ARG-A registra la aprobación del equipo.

Diferencias con la tesis registradas: **DIF-E90-08**, provisional para integrar.

Pruebas: raíz **46 aprobadas y una omitida** con motivo explícito; corpus local con render **44 aprobadas**; ambos validadores sin inconsistencias; Ruff check/format conformes. Ensayo limpio: lint/mypy correctos, backend **677 aprobadas, cuatro omitidas, 31 advertencias, 98 % de cobertura total y los 73 módulos ≥90 %**; raíz **46 aprobadas y una omitida**. Las omisiones se conservan y no se cuentan como aprobadas. La cobertura corresponde al backend y no se extrapola a herramientas ni a requisitos. Ver `Revision_ARG_A.json` y salida real en `Ensayo_CI_ARG_A.txt`. El CSV del diseño conserva sus CRLF originales; el chequeo predeterminado de whitespace señala ese CR en la única fila nueva y se verificó con la opción temporal cr-at-eol, sin introducir otro cambio de formato.

Pendientes o bloqueos: consulta manual ARCA, revisión independiente y de ambos autores; sin congelación ni resultados experimentales. Conciliar registros compartidos al integrar. No se hizo push ni merge.

Preguntas para el equipo: ninguna nueva para este alcance.

No hubo pruebas fallidas durante esta revisión. La inspección visual inicial detectó un párrafo de licencia partido entre páginas; se separó su sección en una página y se volvió a renderizar/verificar. Las generaciones previas y la instantánea anterior del corpus se conservan temporalmente en `/tmp`; los commits previos conservan el estado recuperable. No se cambiaron umbrales ni oráculos tras observar modelos: no se ejecutaron modelos.
