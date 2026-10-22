# Cierre del incremento de corpus E90 candidato

Fecha: 22/10/2026. Rama `codex/corpus-e90`, desde `1e2a6c6`. **Estado: generación candidata y validadores completados; sin congelación, revisión de autores ni mediciones de modelos.** Commit de implementación: `5970ebe`; ajuste no funcional de finales de línea CSV y cierre documental en el commit siguiente.

Tarea: preparación de Etapa 4 (§6.3.1) hasta el límite aprobado en DO-2026-10-22-CORPUS-CONSTRUCCION, más auditoría PD-07 en lectura.

Requisitos cubiertos: preparación y comprobaciones estructurales trazadas a IA-D01 a IA-D08, IA-M12, RC-P04, RC-P06.2, PD-07 y RNF-03/RNF-09. No se marca ningún contrato de aceptación como Cumple ni se atribuyen resultados de OCR/IA.

Archivos modificados: `corpus/e90/`, `oraculos/e90/`, `herramientas/corpus_e90/`, `tests/corpus_e90/`, `docs/evaluacion/corpus_e90/`; anexos en los cuatro registros compartidos de decisiones técnicas, diferencias con la tesis, estado de implementación y destinos/retención. La lista completa está en `Archivos_Incremento.txt`. No hay cambios en backend, frontend, migraciones, Terraform, workflows ni originales PD-07.

Decisiones delegadas tomadas: ninguna. Las elecciones de construcción y las cuatro fuentes contractuales fueron aprobadas expresamente por el equipo y registradas en DO-2026-10-22-CORPUS-CONSTRUCCION.

Diferencias con la tesis registradas: DIF-E90-01 a DIF-E90-07, IDs provisionales para renumerar al integrar. Incluyen simulaciones digitales, concreción de 15 de ajuste, separación de CI y generación, referencias a PDF previos a rasterización, fuentes contractuales/bilingüismo y pendientes de validación humana.

Pruebas:

| Comprobación ejecutada | Resultado observado |
|---|---|
| `ruff check --no-cache herramientas/corpus_e90 tests/corpus_e90` y `ruff format --check --no-cache ...` | Sin errores; ocho archivos de código conformes |
| Validador existente con el inventario real E90 | 50 medición, 15 ajuste, tres adversariales y hashes coincidentes |
| `python -m herramientas.corpus_e90.validar` | Cero inconsistencias estructurales/de archivos/localizadores/referencias; sigue candidato |
| Suite de la raíz sobre el resultado final | 38 aprobadas, una omitida (creación/render explícitamente local) |
| Suite propia local con python-docx/Pillow/LibreOffice y render habilitado | 36 pruebas aprobadas, incluidas creación/conversión local para los cinco tipos |
| Ensayo de CI limpia final en contenedores locales sin AWS | Lint y mypy correctos; backend: 677 aprobadas, cuatro omitidas, 31 advertencias, 98 % de cobertura total y los 73 módulos ≥90 %; raíz: 38 aprobadas y una omitida |
| Preservación de entradas previas de PD-07 y del plan | Los 13 hashes de la auditoría inicial se conservan; sin modificar sus documentos ni oráculo |
| Preservación de registros fuente durante iteraciones de formato | SHA-256 sin cambios desde su preparación previa a generar |
| Revisión visual preliminar por el agente | 65 documentos/104 páginas inspeccionadas en paneles; sin recortes/superposiciones detectados; algunos contratos tienen páginas finales poco densas. No equivale a revisión semántica/jurídica ni de los autores |

La cobertura informada corresponde al backend (`atlas`), no se extrapola a las herramientas del corpus ni a cobertura de requisitos. Las omisiones no se cuentan como pruebas aprobadas: EVD-A/EVD-B y dos pruebas AWS en backend; creación/render en CI de corpus. La verificación local del corpus no contacta AWS.

El lint inicial del código nuevo detectó importaciones, estilo y llamadas mejorables, corregidos antes de las comprobaciones finales. La revisión visual motivó una iteración de formato para quitar bordes heredados y saltos artificiales; una primera edición no se aplicó y se corrigió antes de la generación entregada. El chequeo de Git al incorporar el CSV detectó sus finales CRLF; se normalizaron a LF y se fijó el generador, sin cambiar campos ni documentos. El ensayo limpio se ejecutó antes de esa normalización no funcional; después se repitieron los validadores, el lint y las pruebas de la raíz (38 aprobadas, una omitida), y se comprobó por parseo que el CSV conserva todos sus datos. Las generaciones previas se preservaron temporalmente en `/tmp`; no se cambiaron registros fuente, umbrales ni datos tras observar modelos, porque no se ejecutaron modelos. Se reforzó el verificador para distinguir campos con valores iguales por sus etiquetas.

Pendientes o bloqueos:

- Consultas manuales ARCA de los 12 CUIT candidatos, antes de generación definitiva. Lista preparada y registro editable con resultados todavía pendientes.
- Revisión técnica independiente del otro agente y revisión de fuentes, traducciones, registros, casos ambiguos, dificultad de las simulaciones, campos y preguntas por los autores. `revisado_por_autores` permanece falso; evaluaciones de respuestas y consenso vacíos.
- Mapear referencias primarias a chunks de cada indexación congelada antes de evaluar recuperación. No hay embeddings, resultados de clasificación/extracción/RAG, latencias ni métricas experimentales en este incremento.
- Reemplazar y regenerar en una revisión nueva cualquier identificador o contenido que cambie, conservando hashes/localizadores/oráculos correspondientes.
- PD-07: ocho campos y localizadores faltantes en su oráculo; DIF-84 sigue abierta. Este incremento no lo modifica ni habilita EVD-01.
- Conciliar los cuatro registros documentales compartidos con otras ramas y renumerar DIF-E90-* al integrar. No se probó ni ejecutó un merge con la rama de frontend en curso; puede haber conflictos documentales. No se hizo push ni merge a main.

Preguntas para el equipo: ninguna nueva para completar este alcance. Las revisiones y consultas pendientes son las compuertas ya acordadas para la siguiente etapa.

## Inventario construido

65 archivos de entrada: 50 de medición y 15 de ajuste; 45 PDF y 20 DOCX. Hay cuatro familias por cada uno de los cinco tipos. BASE_A/BASE_B compartidas; MED_C/MED_D exclusivas de medición. Exactamente tres documentos adversariales dentro de medición. Dos contratos extensos de 10 y 11 páginas; el resto de los contratos tiene entre dos y tres páginas. Se conservan 65 DOCX fuente y 65 PDF digitales de referencia como auxiliares, no como documentos extra. El directorio de corpus ocupa aproximadamente 14 MiB en esta sesión.

Referencias: 403 campos (398 presentes y cinco ausentes) y 534 fragmentos primarios; 30 preguntas candidatas (10 directas, ocho condiciones, seis multidocumento y seis sin evidencia). No están revisadas por los autores ni congeladas. Las preguntas se prepararon después de construir los archivos y antes de cualquier ejecución de modelos.

Fuentes contractuales: GOV.UK Short Form 1.5A, Bonterms 1.2, Common Paper 1.1 y GOV.UK Mid-Tier Core Terms 1.3A. Atribución, licencias, URLs, hashes, extractos y traducciones/modificaciones en el banco de plantillas. Son modelos públicos en blanco, no documentación privada. Las adaptaciones no son modelos jurídicamente validados para Argentina. Los contratos extensos incluyen extractos originales atribuidos; su contenido bilingüe está declarado como composición de muestra candidata.

## Evidencia y revisión

- `Ensayo_CI_Limpio.txt`: salida real resumida del ensayo final.
- `Verificacion_Candidatos.json`: alcance y resultado estructural del validador; sin aceptación académica.
- `Revision_Visual_Preliminar.json`: índice de páginas/paneles y sus hashes, ligado al manifiesto final. Los previews están en `/tmp` y son temporales; los documentos y manifiestos quedan conservados.
- `Entorno_y_Codigo_Verificacion.json`: runtime y huellas del código final. La instantánea del código al generar se conserva aparte en el manifiesto; no se reescribió su historia al mejorar el validador.
- `Auditoria_PD07.md` y su JSON de evidencia: auditoría estática parcial, sin cambiar originales.
- `Revision_Independiente.md`: comandos y criterios para que otro agente revise sin regenerar ni acceder a AWS.
- `CUIT_Candidatos_Para_ARCA.md`: lista para la consulta manual del equipo.
