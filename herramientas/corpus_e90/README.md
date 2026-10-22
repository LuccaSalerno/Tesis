# Construcción y validación local del corpus E90

Decisión: **DO-2026-10-22-CORPUS-CONSTRUCCION**. Estado: candidato, no congelado, sin oráculos revisados por los autores. No hay llamadas a AWS, cambios de backend/frontend, migraciones ni modificación de PD-07.

## Qué contiene

- `corpus/e90/registros_fuente.json`: 65 registros fijados antes de generar archivos (50 de medición y 15 de ajuste). No se obtuvieron de resultados de IA.
- `corpus/e90/medicion/` y `ajuste/`: exactamente un archivo de entrada por registro; 45 PDF y 20 DOCX en total. Fuentes DOCX y PDF de referencia están separados en `fuentes_docx/` y `pdf_referencia/`: son auxiliares, no documentos adicionales de medición.
- `oraculos/e90/inventario_candidato.csv`: inventario real compatible con el validador existente, con hashes de los archivos construidos.
- `artefactos_candidatos.json`: versiones de herramientas, referencias a fuentes, tamaño/páginas, hashes y parámetros/semilla de las simulaciones. La repetibilidad binaria exige el entorno de render y las fuentes tipográficas registrados; no se promete igualdad entre versiones de LibreOffice.
- `campos_candidatos.json` y `fragmentos_candidatos.json`: 403 referencias de campos y fragmentos primarios. No son respuestas de un modelo ni revisión humana. Para campos ausentes se conserva `presente=false`, valor y localizador nulos; no se confunden con campos no aplicables.
- `consultas_candidatas.json`: 30 borradores de preguntas, referencias y abstenciones sobre documentos ya construidos; 10 directas, 8 de condiciones, 6 multidocumento y 6 sin evidencia. Evaluaciones individuales de los autores vacías. El mapeo a chunks de una indexación congelada queda pendiente.
- `cuit_candidatos.json`: 12 CUIT de dígito correcto, con consulta ARCA pendiente. La comprobación matemática no acredita que estén desasignados.

Las familias BASE_A/BASE_B son compartidas; MED_C/MED_D se usan exclusivamente en medición, por tipo. Cada registro/archivo es independiente. Los tres adversariales pertenecen a los 50 de medición. PD-07 permanece separado y sin modificaciones.

## Dependencias

Usar un entorno exclusivo y `pip install -r herramientas/corpus_e90/requisitos.txt`. No instalar estas dependencias en el backend ni en el paquete Lambda. Las versiones fijadas se corresponden con el runtime utilizado; pypdf ya es una dependencia del proyecto y se fija aquí para este entorno independiente.

Generación: LibreOffice headless y pdftoppm locales. Pillow realiza las degradaciones; ImageMagick se registra como herramienta disponible, pero no intervino en la generación. En esta sesión se usó LibreOfficeDev 26.8.0.0.alpha0 del runtime incluido, pdftoppm 26.05.0 e ImageMagick 6.9.12-98. Las versiones completas están en el manifiesto. Por ser un renderer alpha, la revisión visual y la reproducibilidad están acotadas a este entorno; comparar antes de cambiarlo.

## Comandos

Desde la raíz del repositorio:

```bash
# Sobre los artefactos existentes: no regenera ni instala herramientas.
python -m herramientas.corpus_e90.validar
python herramientas/validar_inventario_e90.py --inventario oraculos/e90/inventario_candidato.csv
python -m pytest -q tests
```

El primer comando requiere pypdf para inspeccionar PDF. `--solo-estructura` comprueba únicamente relaciones y metadatos; no sustituye la verificación de archivos/localizadores.

Para una raíz NUEVA de revisión, con una copia del plan, las plantillas aprobadas y las herramientas:

```bash
python -m herramientas.corpus_e90.preparar --raiz /ruta/nueva_revision
python -m herramientas.corpus_e90.generar --raiz /ruta/nueva_revision --libreoffice /ruta/soffice --pdftoppm /ruta/pdftoppm
python -m herramientas.corpus_e90.consultas --raiz /ruta/nueva_revision
python -m herramientas.corpus_e90.validar --raiz /ruta/nueva_revision
```

`preparar` crea candidatos por defecto: para reemplazar CUIT se editan en la raíz nueva tanto su registro como los registros fuente antes de `generar`. No copiar un inventario o unas referencias del resultado anterior como si correspondieran a los archivos nuevos. Los comandos se niegan a sobrescribir registros o generaciones existentes. Se conserva la revisión anterior. La raíz nueva debe contener `docs/evaluacion/plan_diseno_corpus_e90.csv` y `herramientas/corpus_e90/plantillas/contratos.json`; copiar solo esas referencias y herramientas, sin claves ni datos operativos.

Una generación interrumpida deja archivos parciales y no acredita el conjunto completo: utilizar otra raíz limpia de revisión. El validador informa entradas incompletas; no las rellena ni cuenta auxiliares para llegar a 65.

## CI e integración

La CI existente ejecuta `python -m pytest -q tests`, incluyendo las comprobaciones del corpus ya construido. No se modifica el workflow. Las pruebas estructurales y de archivos corren con biblioteca estándar y pypdf, que el backend ya instala. Las pruebas de creación/render solo se habilitan localmente con `E90_PRUEBAS_RENDER=1` y dependen de python-docx, Pillow y LibreOffice: se omiten con motivo explícito en la CI. Una omisión no se registra como prueba aprobada.

```bash
E90_PRUEBAS_RENDER=1 E90_LIBREOFFICE=/ruta/soffice python -m unittest discover -s tests/corpus_e90 -q
```

Los mensajes del validador contienen códigos e identificadores, sin preguntas, valores esperados ni fragmentos. El resultado `sin_inconsistencias_estructurales` no significa aceptación académica, calidad de IA ni corpus congelado.

## Revisión independiente y pendientes

1. Contrastar inventario y plan; distinguir entradas finales de sus auxiliares.
2. Revisar procedencia, avisos de licencia, traducciones y cambios de las cuatro fuentes contractuales en `plantillas/contratos.json`.
3. Inspeccionar PDFs/DOCX y cotejar el contenido de cada registro, no solo los hashes. Las imágenes degradadas son simulaciones digitales, no capturas físicas.
4. Revisar las referencias de campos y las 30 consultas; sus textos y fuentes siguen candidatos. La clasificación de casos ambiguos y la dificultad de la muestra requieren revisión de autores.
5. Resolver los CUIT con el registro manual ARCA antes de la generación definitiva. Si cambia un identificador, regenerar en una revisión nueva y verificar hashes/localizadores otra vez.
6. Conservar las revisiones de ambos autores; no marcar los oráculos como revisados desde una prueba automatizada. No medir ni congelar en este incremento.

La demo principal sigue siendo PD-07, contrato de mantenimiento y sus inconsistencias fijadas. Las cuatro familias de E90 no reemplazan esa historia ni su oráculo. Las diferencias provisionales DIF-E90-* se renumerarán al integrar.
