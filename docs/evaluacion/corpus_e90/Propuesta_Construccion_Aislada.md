> Actualización posterior del equipo: aprobación expresa recibida el 22/10/2026 para P1–P6, 15 de ajuste, dependencias aisladas, 12 CUIT candidatos, simulaciones declaradas e IDs provisionales. También se aprobaron las cuatro fuentes contractuales públicas (GOV.UK Short Form 1.5A, Bonterms 1.2, Common Paper 1.1 y GOV.UK Mid-Tier Core Terms 1.3A), con atribución y comprobación de excepciones. Las menciones a aprobaciones pendientes en la propuesta original se conservan como antecedentes de diseño; el estado vigente y los límites están en el README del corpus y la DO registrada al cierre.

# Propuesta de construcción aislada del corpus E90

Fecha: 22/10/2026. Revisión 2. Estado: **aprobada por DO-2026-10-22-CORPUS-CONSTRUCCION, incluida generación candidata; congelación y revisión humana fuera del alcance**.

La revisión recibida recomienda 15 documentos de ajuste y respetar las familias de plantillas del plan. Las opciones pendientes se presentan en preguntas explícitas al equipo, sin interpretar una recomendación como autorización técnica.
Rama: `codex/corpus-e90`, desde `1e2a6c6` de `fundacion/local-backend`.

## Tarea y contrato

Preparación de Etapa 4 (§6.3.1), con auditoría separada del corpus funcional PD-07 de Etapa 2.
Referencias: tesis vigente; RC-P04, RC-P05, RC-P06.2, PD-07; DO-2026-10-21-E90-CORPUS;
contrato de aceptación IA-D01 a IA-D08 e IA-M12; protocolo y plan de corpus E90.
La auditoría de PD-07 no lo convierte en parte de la muestra cuantitativa.

## Decisiones propuestas para revisión (P1–P9)

| ID | Opción recomendada | Alternativa | Requisito / motivo |
|---|---|---|---|
| P1 | Primero auditar los cinco PDF/DOCX de PD-07 y su oráculo en modo lectura; documentar discrepancias sin regenerar ni modificar los archivos actuales | Dejar PD-07 para otra tarea y comenzar por los registros de medición | PD-07, DIF-84: proteger las entradas que pueden usar la demo y el frontend |
| P2 | Concretar en 50 documentos de medición y 15 de ajuste (3 por tipo), conforme a la recomendación recibida; mantener las 65 filas como diseño hasta producir archivos verificables | 10 de ajuste solo si el equipo cambia expresamente esta elección antes de generar | IA-D03/04/07: confirmar junto con la configuración de dependencias; no agregar los antiguos 16 extra ni un conjunto de contraste |
| P3 | Seguir exactamente las familias previstas por tipo: BASE_A y BASE_B compartidas, MED_C y MED_D exclusivas de medición, con sus prefijos de tipo y reparto del CSV existente; registros y documentos independientes entre particiones; 3 adversariales dentro de los 50 | Cualquier redistribución exige propuesta expresa y revisión previa del equipo | IA-D01/02/03/04 y Plan_Diseno_Corpus_E90.md: no reducir el diseño existente al mínimo contractual de una plantilla exclusiva |
| P4 | Aprobar python-docx y Pillow como dependencias exclusivas del corpus, en manifiesto propio y sin tocar backend ni workflow; CI ejecuta comprobaciones estructurales sin estas dependencias y omite explícitamente solo integraciones si faltan paquetes o herramientas | Proponer en otro cambio una CI completa con generación/render y sus dependencias de sistema | AGENTS.md §4, RC-P02: aprobación pendiente; disponibilidad en el runtime de Codex no equivale a dependencia reproducible del proyecto |
| P5 | Aplicar la distribución ya aprobada de RC-P06.2, punto 2: 10 directas, 8 de condiciones/cláusulas, 6 multidocumento y 6 sin evidencia suficiente, sobre los documentos de medición construidos | Diferir su elaboración a otro incremento, sin cambiar el reparto aprobado | RC-P06.2, puntos 2/3/9, IA-D08: el CSV solo tiene la clase general; el JSON del oráculo registra también la categoría; no es una decisión nueva |
| P6 | Revisión técnica independiente del otro agente y revisión de oráculos por ambos autores antes de congelar; el equipo decide la integración a su rama objetivo | Revisar por lotes pequeños manteniendo el conjunto en estado candidato hasta completar todas las comprobaciones | IA-M12, AGENTS.md §7: ejecución con oráculo y evidencia; una revisión de agente no reemplaza la calificación de ambos autores |
| P7 | Reutilizar un grupo pequeño de CUIT candidatos de dígito válido, evitando nuevos números por documento; mantener todo en estado candidato hasta documentar las consultas ARCA exigidas, antes de generación definitiva/congelación | Esperar un grupo de CUIT comprobados por el equipo antes de incorporar identificadores | Pendiente de aprobación; no usar dígitos inválidos como solución general ni declarar inexistencia por algoritmo o búsqueda web |
| P8 | Crear degradaciones digitales reproducibles, identificadas como simulaciones y candidatas; registrar rasterización, resolución, ruido/rotación y semilla; exigir conformidad metodológica antes de computarlas como capturas de los estratos finales | Reservar las filas para impresión y escaneo/fotografía física del equipo | Pendiente de aprobación; una simulación no acredita una captura física ni permite modificar la tesis o el significado de sus estratos |
| P9 | Investigar modelos contractuales públicos y sus permisos; presentar candidatos y trazabilidad; adaptar solo los que el equipo apruebe | El equipo entrega modelos públicos expresamente autorizados | IA-D01 y AGENTS.md: acceso público no prueba permiso específico; no copiar contratos operativos ni redactar todo el contrato mediante LLM |

## Dependencias y pruebas en CI

Hechos comprobados el 22/10/2026:

- El Python del shell no tiene python-docx, Pillow, pypdf ni pytest; el runtime de Codex sí dispone de python-docx 1.2.0, Pillow 12.3.0 y pypdf 6.10.0. No se instaló nada.
- El backend declara pypdf, pero no python-docx ni Pillow. No se propone añadir bibliotecas del corpus al paquete Lambda.
- LibreOffice, pdftoppm y convert se encuentran en la máquina; magick no se encuentra en PATH. La mera presencia de herramientas de escritorio no acredita un entorno de generación reproducible aprobado.
- El workflow usa ubuntu-24.04; quien usa python:3.12-slim es el ensayo local de CI limpia, que instala postgresql-client, pero no las herramientas de render. Ambos ejecutan las pruebas de la raíz.

Diseño propuesto: dependencias del corpus en manifiesto separado con versiones fijadas después de aprobar P4. No importar bibliotecas opcionales al recolectar pruebas estructurales. Las integraciones comprueban de forma explícita paquete y herramienta necesarios y registran skip con el motivo concreto si faltan; con el entorno de corpus provisionado deben ejecutarse y fallar si el generador o el render falla. No omitir errores de programación ni declarar que una prueba omitida pasó. Las pruebas estructurales de manifiestos, referencias, cantidades, particiones, rutas y hashes corren siempre, usando biblioteca estándar.

No es obligatorio usar ImageMagick si Pillow y pdftoppm cubren las transformaciones aprobadas. Para render de documentos se emplearán las herramientas admitidas por las habilidades aplicables y se verificará el entorno antes de generar. Cualquier instalación adicional se consulta conforme a AGENTS.md.

## Archivos y límites del trabajo

Ubicaciones nuevas propuestas:

- `corpus/e90/`: registros fuente, plantillas y documentos de ajuste/medición separados.
- `oraculos/e90/`: referencias de campos, clasificación, procedencia, consultas y manifiestos.
- `herramientas/corpus_e90/`: generación y comprobaciones del corpus.
- `tests/corpus_e90/`: pruebas propias de estas herramientas.
- `docs/evaluacion/corpus_e90/`: auditoría PD-07, diseño, revisión y evidencias locales.

No editar frontend, backend, migraciones, infraestructura, workflows ni los archivos actuales de
PD-07 durante este alcance. Si se detecta una necesidad de cambiar alguno, documentarla y coordinar
antes de hacerlo. El validador actual del inventario se reutiliza en lectura; si necesita cambios,
proponerlos por separado. No renombrar ni regenerar automáticamente los documentos de demo.

Los registros compartidos de decisiones, diferencias y estado se actualizan coordinadamente al
aprobar/cerrar el incremento, en el mismo cambio que corresponda según AGENTS.md. No se omiten
por evitar conflictos: se integran contra su versión más reciente y sin reemplazar entradas ajenas.
Las propuestas de registro usan IDs provisionales `CORPUS-E90-PROP-*` en `Entradas_Provisionales_Integracion.md`, sin reservar números DIF-NN ni modificar los registros compartidos. Al aprobar/cerrar cada incremento se asignan los IDs definitivos coordinadamente; las entradas obligatorias se integran en el mismo cambio que introduzca las diferencias. No existe todavía una DO aprobada de construcción del corpus.

## Modelo físico, rutas y destinos

Modelo físico de la aplicación: sin cambios; no hay migraciones. Rutas API: sin cambios.
La propuesta reutiliza las columnas de inventario y oráculo existentes; cualquier estructura
adicional del dataset se documentará antes de implementarla. No hay procesamiento externo ni
invocaciones AWS. Revisar el registro de destinos al cierre; no añadir servicios ficticios.

## Incrementos y verificación prevista

1. Auditoría PD-07: cotejar campos de RC-P04, archivos reales y hashes, texto, páginas/localizadores,
   fuentes DOCX, coherencia de importes y resultados de R1–R4, y marca de documento ficticio.
   Informar la consulta ARCA pendiente sin convertir el dígito verificador en prueba de inexistencia.
2. Registros y plantillas: revisar particiones y casos difíciles; inventariar procedencia/licencia
   de modelos públicos antes de adaptarlos. No usar documentación operativa real.
3. Generación por lotes: tras aprobar dependencias, CUIT, fuentes contractuales y modalidad, comprobar formato real, apertura, límites RC-P04, contenido y diseño visual de PDF/DOCX; registrar método, páginas y SHA-256. Las simulaciones se identifican expresamente y no se hacen pasar por escaneos/fotografías físicos.
4. Oráculos: el agente prepara borradores de referencias cotejadas con el documento final y el registro previo, con localizadores PDF/DOCX y distinción entre ausente y no aplicable. Se conservan discrepancias y estado pendiente de revisión de ambos autores. Esta preparación no acredita validación humana ni resultados de modelos.
5. Validadores: pruebas negativas de recuentos, particiones, plantillas, duplicados, hashes,
   localizadores y referencias de consultas. Ejecutar pruebas pertinentes y el ensayo de CI limpio
   antes del commit del hito; reportar resultados observados, no supuestos.
6. Congelación: inventario de 50 + ajuste aprobado, 3 adversariales internos, 30 consultas y revisión
   humana documentada. No medir modelos, ajustar umbrales ni atribuir resultados de §6.3/§6.4.

## Integración y riesgo de conflictos

El worktree separado evita compartir archivos de trabajo con el agente de frontend. La rama
conserva cambios y commits independientes, pero no garantiza ausencia de conflictos de merge:
ambas ramas comparten historia y pueden editar archivos comunes o introducir incompatibilidades.
La integración se revisará con diff y pruebas sobre la rama destino actualizada; no se hará push
ni merge a main. Las actualizaciones de documentos compartidos requieren conciliación manual.

## Pendientes antes de implementar

Aprobar conjuntamente la configuración de 15 de ajuste y P4, elegir P7 y P8, y revisar los modelos candidatos de P9 antes de usarlos. P3 se alinea al plan vigente y P5 conserva la decisión ya aprobada.

El trabajo independiente ya realizado comprende auditoría estática y revisión de esta propuesta. El trabajo autónomo posterior puede preparar registros, plantillas autorizadas, validadores, generación candidata y borradores de referencias. La consulta ARCA pendiente, el visto bueno de las fuentes, la conformidad metodológica de capturas y la revisión humana no se sustituyen con autonomía técnica. La calificación de respuestas reales por ambos autores ocurre después de ejecutar los modelos; no se inventa aquí. La congelación final queda pendiente del equipo.

La revisión técnica del otro agente se prepara con instrucciones reproducibles; no se le envían mensajes ni se delega trabajo desde esta propuesta.
