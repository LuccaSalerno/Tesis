# Correspondencia entre el capítulo 6, EVD-01 y BDD/Gherkin

**Decisión de implementación del equipo (21/10/2026).** Este documento aclara los nombres y el enfoque de pruebas. **No agrega ni elimina RF, RN, RNF, umbrales, entidades o escenarios obligatorios; no acredita ejecución.**

## Un mismo alcance con nombres en dos niveles

| En el PFI (redacción académica) | En aceptación y repositorio | Alcance idéntico |
|---|---|---|
| §6.2 «Verificación de la cadena de evidencia documental» | **EVD-01**, contrato interno de aceptación | Los cuatro recorridos y todas las propiedades verificables de la cadena |
| Aprobación seguida de incorporación confirmada de una nueva versión | EVD-A / RN-12 | Decisión y conjunto anterior conservados; nuevo ciclo requiere nueva decisión |
| Observación y corrección documental | EVD-B / RN-08, RN-09, RN-12 | Motivo e historia conservados; versión corregida y nuevo ciclo |
| Subsanación sin sustituir el archivo | EVD-C / RN-13 | No se fabrica una versión nueva; revalidación en el mismo contenido documental |
| Intento de decisión en tarea de ciclo anterior | EVD-N12 / RN-12 | Rechazo de decisión tardía tras cambio del conjunto confirmado |

**Regla para implementación:** EVD-01 no fue descartado, rebautizado en el código ni sustituido por una demostración visual. Solo se simplificó **su presentación en la tesis**. Los identificadores EVD-A/B/C/N12, V1–V11 y las verificaciones complementarias, negativas y de carreras siguen vigentes en los contratos y las pruebas. **V4 exige recuperar desde una decisión los controles que efectivamente consideró**, no el último estado de las reglas.

La cadena se verifica mediante API autenticada/autorizada y aserciones sobre estados **y relaciones persistentes recuperables por la propia API**. La consulta directa a SQL puede ayudar a depurar, pero no reemplaza el oráculo funcional. RNF-07 y los recorridos visuales requieren además pruebas de interfaz; una captura no reemplaza la suite API ni los ensayos cuantitativos.

## Decisión BDD confirmada

- Los **criterios de aceptación de comportamiento** se expresan mediante archivos Gherkin en español `Dado–Cuando–Entonces`, sin introducir requisitos adicionales.
- **BDD** organiza los escenarios y sus expectativas; **Gherkin** es el formato legible, no evidencia de ejecución por sí mismo.
- La automatización obligatoria de EVD-01 se realiza contra API autenticada/autorizada. Los recorridos UI con Playwright verifican interacción, permisos visibles y RNF-07; se vinculan a los mismos RF/RN/RNF, sin confundir UI con la API.
- Se propone integrar los `.feature` con `pytest-bdd` (compatible con pytest acordado), sujeto a aprobación del equipo para la biblioteca concreta; los ejemplos incluidos son **especificaciones, no pruebas ejecutables implementadas**. Cualquier runner alternativo debe preservar el mismo contrato.
- Localización sugerida: `tests/acceptance/features/*.feature`, implementación en `tests/acceptance/steps/` y pruebas UI en la estructura frontend/Playwright que se establezca. Los nombres y fixtures efectivos se fijan al desarrollar, sin crear endpoints imaginarios.
- Asociar cada escenario con los IDs de aceptación en etiquetas o metadatos y conservar esperado/observado, commit, entorno, datos sintéticos y resultado de cada ejecución. No marcar un caso «Cumple» por tener el archivo `.feature`.

## Relación con fuentes de la tesis

- `docs/tesis/main.pdf`: PDF actualizado el 22/10/2026 con la redacción consolidada del capítulo 6; sirve de referencia para RF/RN/RNF, dominio, arquitectura y método de validación.
- `docs/tesis/ATLAS_Seccion_6_Version_Final_6_0_a_6_3.md`: copia Markdown sincronizada con el método de 6.0–6.3 del PDF actualizado; no es un reporte de pruebas ejecutadas.
- Si aparece diferencia editorial entre el PDF y el Markdown sobre 6.2, mantener la referencia al PDF vigente, aplicar la equivalencia de esta nota y preservar los requisitos contractuales. Si hay diferencia sustantiva, elevarla al equipo en vez de elegir silenciosamente.
