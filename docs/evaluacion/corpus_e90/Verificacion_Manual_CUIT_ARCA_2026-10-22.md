# Consulta manual de los CUIT candidatos — reporte del equipo

Requisitos: DO-2026-10-22-CORPUS-CONSTRUCCION, control de identificadores fiscales sintéticos antes de generación definitiva. Fecha de consulta **22/10/2026**, confirmada expresamente por el usuario en el chat. Fuente de evidencia: resultados de consulta manual en ARCA informados por el equipo; el agente registra la declaración recibida. No se aportaron capturas ni URL del formulario exacto; no se fabrican constancias o verificaciones independientes.

El equipo informó los doce resultados siguientes y confirmó que las consultas se hicieron ese día:

| CUIT consultado, sin guiones | Resultado informado |
|---|---|
| 30986410011 | No existe |
| 30986410038 | No existe |
| 30986410046 | No existe |
| 30986410054 | No existe |
| 30986410062 | No existe |
| 30986410070 | No existe |
| 30986410089 | No existe |
| 30986410097 | No existe |
| 30986410100 | No existe |
| 30986410119 | No existe |
| 30986410127 | No existe |
| 30986410135 | No existe |

Se cotejó la coincidencia exacta de los doce números con `oraculos/e90/cuit_candidatos.json` y su dígito verificador. No se requiere reemplazar identificadores por los resultados informados. La consulta manual queda documentada con fecha, resultado y esta referencia de evidencia saneada; no se marca aceptación académica ni se atribuye una garantía de inexistencia/asignación futura.

Los números y el corpus continúan candidatos: la revisión de ambos autores y la congelación siguen pendientes. Los PDF/DOCX actuales se generaron antes de este reporte y conservan su leyenda histórica de consulta pendiente; este registro posterior no modifica sus bytes, referencias ni hashes. La leyenda se actualizará si se construye la revisión definitiva autorizada. La generación de candidatos desde cero prepara de nuevo un registro pendiente; al conservar los mismos números debe trasladarse también esta evidencia, sin simular una nueva consulta.

Tarea: registrar resultados manuales del equipo, sin nueva generación.
Requisitos cubiertos: control CUIT de DO-2026-10-22-CORPUS-CONSTRUCCION y RNF-03.
Archivos modificados: registro de CUIT, lista de consulta y esta evidencia; estado y notas vigentes de corpus/herramientas/oráculos.
Decisiones delegadas tomadas: ninguna; se registra información proporcionada por el equipo.
Diferencias con la tesis registradas: ninguna nueva; no se cambia implementación ni protocolo.
Pruebas: comparación exacta de los doce números y validación de sus dígitos tras normalizar guiones; 65 documentos y 130 auxiliares preservados por hash. Suite de raíz: **46 aprobadas y una omitida** con motivo explícito. Validador del corpus: **cero inconsistencias**; inventario válido y hashes coincidentes. `git diff --check` sin incidencias. El primer cotejo auxiliar esperaba el formato con guiones y se corrigió antes de registrar datos; no se detectó un dígito inválido. Esta es una actualización de metadatos/documentación: no se repite ni se atribuye una nueva ejecución del ensayo de CI completo del cierre ARG_A.
Pendientes o bloqueos: revisión independiente, revisión de autores y congelación. Sin resultados de modelos.
Preguntas para el equipo: ninguna.
