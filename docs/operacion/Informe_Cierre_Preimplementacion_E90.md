# Informe de cierre de preparación para desarrollo E90

**Fecha:** 21/10/2026 · **Estado:** documental y de herramientas locales; **no** cierre de implementación.

## Decisiones vigentes verificadas en el paquete

- AWS solo por operadores humanos autorizados, sin GitHub OIDC, sin CI/CD cloud y con costos aprobados previamente.
- E90A: demo AWS sintética descartable; eliminar manualmente los recursos de sesión incluida RDS; conservar control/estado `bootstrap`; no promete recuperación de los mismos registros entre despliegues.
- E90-CORPUS: 50 sintéticos de medición (10 por cada tipo; 3 adversariales internos), 10–15 documentos **de ajuste separados**, 30 preguntas RAG; métricas originales sin cambios. Sin 16 casos extra ni conjunto público/contraste.
- La validación operativa real (§6.4) está separada de la medición cuantitativa; sus archivos auténticos **no** entran en este repositorio ni herramientas de desarrollo; solo resultados/evidencias saneados y autorizados.

## Modificaciones concretas

1. `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md`: RC-P05 y RC-P06 actualizadas, DO-2026-10-21-E90-CORPUS agregada y selección A/B retirada.
2. `docs/aceptacion/Contrato_Aceptacion_Integral_Reconstruccion_PFI_2026-10-20_v1_1.md`: IA-D01..D08 alineadas, manteniendo IDs históricos retirados D05/D06 y métricas de §5.2 sin cambios.
3. `AGENTS.md`: la excepción acotada al corpus y la protección absoluta de documentos operativos reales frente al agente, la CI y la demo.
4. `docs/plan/Plan_Implementacion_por_Etapas.md`: etapa experimental de 50 y validación operativa independiente.
5. `docs/evaluacion/`: protocolo, plantilla de inventario y validador local de estructura/huellas.
6. `README.md`, `README_PRIMERO.md`, `INICIO_CODEx_E90.md`, `.gitignore`, especificación de seed: instrucciones unificadas.

## Pendientes que no bloquean desarrollar localmente

- Los autores deben actualizar la **fuente académica** y reemplazar `docs/tesis/main.pdf` con la versión aprobada; el PDF distribuido aquí sigue conteniendo referencias antiguas de §6.3.1. No fingir modificación.
- El corpus de medición de 50, ajuste de 10–15 y oráculos **no están generados**. La plantilla CSV no representa documentos existentes ni tests aprobados.
- La consulta ARCA del CUIT candidato y el congelamiento de PD-07 están pendientes.
- La cotización AWS de modalidad descartable no es oficial ni está aprobada; Terraform/seed remoto/runbooks no están probados. No desplegar hasta verificar costos, identidad, segregación, creación y destrucción.
- La validación operativa necesita permisos, controles y resultados auténticos ejecutados por el equipo. Nada de esos documentos fue incorporado.
- El ZIP conserva `.git` y sus *untracked* del archivo entregado; no se hizo `push`, merge ni commit en nombre del equipo.

## Validaciones realizadas para este cierre

- **24 archivos Markdown**, enlaces relativos verificados: **0 rotos**.
- Compilación sintáctica de scripts Python y `bash -n` del script de auditoría: **sin errores**.
- `python -m unittest discover -s tests -p 'test*.py' -q`: **3 pruebas pasan** (inventario válido, detección de adversariales faltantes, rechazo de rutas fuera de `corpus/`).
- `python herramientas/preparar_seed_demo_e90.py --output /tmp/atlas_ultima_manifest_demo.json`: **manifiesto local de 5 PDF producido**, sin conexiones a AWS.
- `docs/tesis/main.pdf` conservado byte a byte, SHA-256: `2f0d1af82824cdead955d70f9486be95f133c455c4e1f046013608b11f1b61da`.
- Contra el ZIP E90A anterior: **6 archivos nuevos, 9 modificados, 0 eliminados**, sin contar `.git` ni archivos generados de cache.
- El CSV de inventario se distribuye **vacío a propósito**: ejecutar su verificador ahora devuelve «INCOMPLETO», lo esperable porque todavía no existen los 50/10–15 documentos. No falsificar estado validado.

Estas comprobaciones **no** demuestran funcionalidad de ATLAS, cumplen evaluación E90 ni sustituyen la cotización económica, las pruebas reales o la revisión humana de los documentos sintéticos.
