# Construcción y validación local del corpus E90

Decisiones: **DO-2026-10-22-CORPUS-CONSTRUCCION** y **DO-2026-10-22-CORPUS-REVISION** (diseño P0–P16) y **DO-2026-10-23-CIERRE D5** (versión **v3**: correcciones de REV-E90-16 a 19). Estado: congelado (DO-2026-10-23-E90-CONGELACION). No hay llamadas a AWS, cambios de backend/frontend, migraciones ni modificación de PD-07.

## Qué contiene

- `corpus/e90/registros_fuente.json`: 65 registros fijados antes de generar archivos (50 de medición y 15 de ajuste), con contextos de trámite, ambigüedades justificadas, adversariales y condiciones. No se obtuvieron de resultados de IA.
- `corpus/e90/medicion/` y `ajuste/`: un archivo de entrada por registro, con nombre neutro; 45 PDF y 20 DOCX. `fuentes_docx/` y `pdf_referencia/` son auxiliares, no documentos adicionales de medición.
- `oraculos/e90/`: inventario, manifiesto de artefactos, 403 campos, 745 fragmentos (727 de la v2 más 18 extractos de procedencia), 30 consultas y 18 CUIT candidatos (ver su README).
- `docs/evaluacion/corpus_e90/Cuaderno_Revision_*.md`: vistas para los autores, generadas con `cuadernos.py` a partir de los JSON.

Módulos:

| Módulo | Función |
|---|---|
| `comun.py` | Campos por tipo, perfiles de formato por familia (P4), importes en letras, patrones prohibidos (ID de inventario, pistas de construcción). |
| `preparar.py` | Registros fuente v2: sujetos por partición (P2/P3), importes y números sin relación con el ID (P5), trámites (P13), ambigüedad (P10) y adversariales (P11). |
| `generar.py` | DOCX por familia (P6/P8/P9/P12), render con LibreOffice, simulación de capturas, localizadores por etiqueta y valor, manifiesto e inventario. |
| `consultas.py` | 30 preguntas sin IDs (P14), escritas sobre lo ya construido. |
| `validar.py` | Comprobaciones estructurales y de archivos, incluidas las de P16. Nunca regenera. |
| `cuadernos.py` | Cuadernos de revisión de documentos y preguntas. |

Las familias BASE_A/BASE_B son compartidas; MED_C/MED_D se usan exclusivamente en medición, y CTR-ARG_A solo en E90-M-CTR-03. Los tres adversariales pertenecen a los 50 de medición. PD-07 permanece separado.

## Dependencias

Usar un entorno exclusivo y `pip install -r herramientas/corpus_e90/requisitos.txt`. No instalar estas dependencias en el backend ni en el paquete Lambda.

Generación: LibreOffice headless y pdftoppm locales; Pillow hace las degradaciones. La v2 y la v3 se generaron con **LibreOffice 24.2.7.2** y **pdftoppm 24.02.0** (la v1 había usado LibreOfficeDev 26.8 alpha); las versiones completas están en el manifiesto. No se promete igualdad binaria con otro renderer: inspeccionar antes de cambiar el entorno.

## Comandos

Desde la raíz del repositorio, sobre los artefactos existentes (no regeneran):

```bash
python -m herramientas.corpus_e90.validar
python herramientas/validar_inventario_e90.py --inventario oraculos/e90/inventario_candidato.csv
python -m pytest -q tests
```

`--solo-estructura` comprueba únicamente relaciones y metadatos; `--evidencia <ruta>` guarda el resultado.

Los comandos de construcción se niegan a sobrescribir registros, archivos o manifiestos existentes. Una revisión nueva se construye en una raíz limpia que contenga `docs/evaluacion/plan_diseno_corpus_e90.csv`, `docs/evaluacion/corpus_e90/fuentes/` y `herramientas/corpus_e90/`:

```bash
python -m herramientas.corpus_e90.preparar --raiz /ruta/nueva_revision
python -m herramientas.corpus_e90.generar --raiz /ruta/nueva_revision --libreoffice soffice --pdftoppm pdftoppm
python -m herramientas.corpus_e90.consultas --raiz /ruta/nueva_revision
python -m herramientas.corpus_e90.validar --raiz /ruta/nueva_revision
```

Después de revisar el resultado, se reemplazan en el repositorio `corpus/e90/{registros_fuente.json,medicion,ajuste,fuentes_docx,pdf_referencia}` y los archivos de `oraculos/e90/`, conservando antes el manifiesto anterior (como en `docs/evaluacion/corpus_e90/v1/` y `v2/`). Así se instalaron la v2 y la v3. Luego, con el commit de los datos:

```bash
python -m herramientas.corpus_e90.cuadernos --commit <commit_de_los_datos>
```

Si cambia una razón social o un CUIT por la verificación manual, se edita `preparar.py` y se regenera todo: no se corrigen archivos ni oráculos a mano. Una generación interrumpida deja archivos parciales y no acredita el conjunto: usar otra raíz limpia.

## CI e integración

La CI ejecuta `python -m pytest -q tests`, incluidas las comprobaciones del corpus ya construido. No se modifica el workflow. Las pruebas estructurales y de archivos usan biblioteca estándar y pypdf. Las pruebas de creación/render solo se habilitan localmente y se omiten con motivo explícito en la CI:

```bash
E90_PRUEBAS_RENDER=1 E90_LIBREOFFICE=soffice python -m pytest -q tests/corpus_e90
```

Los mensajes del validador contienen códigos e identificadores, sin preguntas, valores ni fragmentos. `sin_inconsistencias_estructurales` no significa aceptación académica, calidad de IA ni corpus congelado.

## Congelación (DO-2026-10-23-E90-CONGELACION)

La v3 se congeló el 23/10/2026 con `python -m herramientas.corpus_e90.congelar`, después de la revisión de ambos autores por muestreo. `oraculos/e90/congelamiento.json` guarda la revisión y las huellas de 202 archivos; el validador entra en modo congelado cuando ese registro existe (`congelado=si`) y rechaza cualquier archivo cuya huella no coincida. `comun.py` y `validar.py` se modificaron después de generar la v3 solo para agregar el modo congelado: no cambian la generación. Cualquier corrección posterior exige una revisión nueva (v4) en una raíz limpia.

## Pendientes antes de congelar (historial)

1. ~~Verificación manual de las 18 razones sociales y de los 6 CUIT de ajuste~~: completada el 23/10/2026 (`docs/evaluacion/corpus_e90/Verificacion_Manual_Ajuste_y_Razones_Sociales_2026-10-23.md`).
2. Revisión técnica de contraste de la v2 por el agente que no la construyó (P0).
3. Revisión de ambos autores con los cuadernos; no marcar oráculos como revisados desde una prueba automatizada.

ARG_A conserva licencia CC BY-NC-SA 4.0 sobre su adaptación y extractos; ver `corpus/e90/ATRIBUCIONES.md`. Las diferencias provisionales DIF-E90-* se renumerarán al integrar.
