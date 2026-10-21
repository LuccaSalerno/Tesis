# ATLAS — Especificación de seed de demo descartable E90A

**Fecha:** 21/10/2026. **Estado:** especificación; **NO existe aún una implementación que pueble AWS**. La API/backend, Terraform y modelo físico todavía no están construidos. El script `herramientas/preparar_seed_demo_e90.py` genera solamente un **manifiesto local** de archivos/huellas: no se conecta a AWS ni crea trámites.

**Distinción E90-CORPUS:** esta semilla PD-07 prepara el **recorrido funcional de demo/EVD**, no la muestra de 50 archivos usada para medir extracción y clasificación. Los documentos de medición y ajuste tienen manifiestos y oráculos propios; nunca se usan documentos de una validación operativa real para poblar la demo.

## Objetivo

Dejar cada despliegue E90A con un escenario **nuevo, sintético, reproducible y evaluable**, sin mantener RDS ni snapshots entre sesiones. El script real de seed debe ser **manual**, invocado por operador autorizado después del despliegue y migraciones, usando APIs con identidades ficticias y permisos reales. Nunca crear directamente decisiones/eventos de auditoría falsos con SQL ni escribir fixtures sensibles en logs.

## Entradas versionadas

- `corpus/C-v1_Contrato_Mantenimiento_ATLAS.pdf` (contrato C-v1).
- `corpus/O-v1_Orden_Compra.pdf` y `corpus/O-v2_Orden_Compra.pdf`.
- `corpus/F-v1_Factura.pdf` y `corpus/F-v2_Factura.pdf`.
- Archivos DOCX equivalentes si se necesita probar formato; no duplicar incorporaciones sin caso de prueba específico.
- `oraculos/oraculo_PD07_preliminar.json` es todavía **preliminar**: validar CUIT ficticio conforme a ARCA, consistencia documental, escenarios y congelar oráculo antes de usarlo como fuente de aceptación.

## Secuencia esperada del seed real (a implementar con API existente)

1. Verificar cuenta, región, `demo` recién creado, corpus y hashes. Rechazar ejecución en un entorno no aprobado o con datos existentes que puedan perderse; no adivinar credenciales/IDs.
2. Crear usuarios ficticios en Cognito con roles Responsable, Revisor/Aprobador y Administrador operativo, cada uno con permisos mínimos y autenticación real; secretos fuera del repositorio.
3. Crear un trámite y registrar mapeo de ID dinámico de esta sesión (las IDs pueden cambiar entre ejecuciones).
4. Incorporar C-v1 como nueva versión documental mediante flujo de carga/confirmación y trabajo técnico, no creando directamente una fila en base. Validar clasificación y siete campos con procedencia según implementación disponible.
5. Incorporar O-v1/F-v1 y, según los hitos implementados, O-v2/F-v2 para recorrer asociación, reglas de consistencia, cambios de ciclo, observación y aprobaciones; cada acción se realiza por usuario ficticio habilitado. Si alguna capacidad falta, marcarla **NO IMPLEMENTADA**, no inventar su evidencia.
6. Verificar por API respuestas y relaciones (versiones, validaciones, tareas, decisiones, ejecuciones de reglas consideradas y auditoría) comparando contra oráculo aprobado; no asumir orden de eventos ni IDs fijos.
7. Validar pruebas negativas de permisos y comportamiento RN-12/EVD-N12 según los hitos realmente disponibles. Ejecutar la IA real solo con habilitación explícita de costo y cantidad de documentos.
8. Guardar fuera de AWS un resultado saneado (IDs correlacionables, hashes, código, corpus, oráculo, resultados pass/fail, errores). Nunca exportar contraseñas/tokens. Toda nueva sesión crea un escenario nuevo, no restaura eventos o huellas de una sesión destruida.

## Propiedades del seed

- **Reproducibilidad lógica**: misma versión de corpus, roles, secuencia de acciones y resultados esperados; las fechas, IDs y respuestas IA no se falsifican.
- **Seguridad**: por API autenticada con separación de funciones; no elude validación humana real ni autoriza decisiones automáticas de IA.
- **Reentrancia segura**: no reiniciar un seed incompleto sobre datos sin auditar. Comprobar precondiciones y detenerse o reanudar bajo un manifiesto verificable por sesión, según la API que se implemente.
- **Métricas**: duración de seed y tokens/páginas de inferencia facturados se registran aparte; los resultados del seed no son pruebas de calidad experimental por sí mismos.
- **Sin datos persistentes entre sesiones**: la destrucción de la demo elimina también su auditoría AWS. Los reportes/evidencias saneadas de las campañas se conservan externamente.

## Línea de comandos preparatoria (sin AWS)

```bash
python3 herramientas/preparar_seed_demo_e90.py --output /tmp/atlas_e90_seed_manifest.json
```

La salida solo lista los 5 PDFs, sus hashes SHA-256 y metadatos de la propuesta. **No carga archivos a AWS**. No autorizar un seed remoto hasta que el backend y los endpoints estén implementados y auditados.
