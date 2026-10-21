# Informe de cambio — E90, modalidad A descartable

**Fecha:** 21/10/2026. **Estado:** modificación documental preparada; AWS no fue modificado.

## Decisión del equipo

En vez de suspender RDS y conservar datos entre sesiones, desplegar manualmente una **demo nueva** con infraestructura AWS real, crear esquema con migraciones, generar el escenario sintético mediante seed y destruir los recursos de la sesión al terminar. Conservar únicamente `bootstrap`, configuraciones administrativas/costos/privacidad y corpus/evidencias académicas exportados localmente. Sin OIDC ni CD AWS.

## Archivos y alcance de los cambios

- `AGENTS.md`: autorización humana específica para destruir recursos de demo; mantiene la prohibición absoluta de tocar `bootstrap`/otras cuentas y de borrar auditoría funcional.
- `docs/decisiones/Decisiones_Tecnicas_Reconstruccion_PFI_2026.md`: DO-2026-10-21-E90A formal; reemplazos de RC-P10-08/09, criterios B-E90, E y V-TF; antecedente del runbook antiguo marcado como supersedido.
- `docs/diseno/RC-P10_Diseno_Infraestructura.md`: distinción entre estado `bootstrap` persistente y raíces de sesión (`persistent`, `runtime`, `demo`), recreación de recursos, seed y eliminación manual selectiva.
- `docs/plan/Plan_Implementacion_por_Etapas.md`: condiciones de despliegue, verificación dentro de sesión y eliminación completa, sin falsa recuperación entre sesiones.
- `operaciones/aws/README_OPERACION_MANUAL.md`: nuevo runbook E90A de crear/migrar/seed/probar/drenar/evidenciar/destruir, manteniendo supervisión humana.
- `docs/operacion/Seed_Demo_E90_Especificacion.md`: contrato futuro del seed real por API, corpus/oráculo y criterios de seguridad.
- `herramientas/preparar_seed_demo_e90.py`: script **local**, real y verificable que genera SHA-256/manifiesto; **no** carga datos a AWS (el backend/API aún no existe).
- `docs/operacion/Politica_Costos_AWS.md`, informes y `README_PRIMERO.md`: advierten que la cotización histórica basada en RDS detenido ya no es válida para E90A.
- `docs/operacion/Runbook_RDS_Detenido_HISTORICO_2026-10-21.md`: antecedente archivado para conservar trazabilidad; **no ejecutar**.

## Riesgos académicos y operativos que permanecen

1. **Criterio B original de RC-P10:** recuperar la **misma evidencia** tras apagar y encender **no se puede demostrar** si se destruyen la base y los objetos. B-E90 solo demuestra persistencia, auditoría y trazabilidad *durante* una sesión. No afirmar equivalencia con el criterio original ni modificar RF/RN/RNF. Confirmar con el equipo si la tesis E90/100 exige recuperación intersesión.
2. **RNF-04/RN-10:** la aplicación jamás incorpora un endpoint para borrar versiones/trámites/auditoría; el descarte total se realiza solo por operador como destrucción autorizada del **entorno técnico efímero**.
3. **Sin aplicación/API ni Terraform aún:** no existe un script funcional que pueda poblar PostgreSQL/Cognito/S3 por API, ni un procedimiento probado de destrucción en AWS. El script de manifiesto local **no** valida el seed remoto.
4. **Costo:** retirar RDS evita el reinicio de siete días y almacenamiento residual de la instancia, pero hay cargos por cada ciclo, mínimos, backups, S3 versiones, logs, CloudFront y secretos diferidos. RC-P10-13 requiere cotización nueva de la modalidad A antes del primer despliegue. Los presupuestos AWS no evitan cargos.
5. **Protección contra destrucción:** Terraform aún no implementado; resolver cómo mantener `prevent_destroy`/`deletion_protection` sin imposibilitar la eliminación manual **solo** de demo; no deshabilitar controles globalmente ni tocar `bootstrap`.
6. **Cuidado con el corpus:** los CUIT siguen pendientes de consulta en ARCA. No proclamar cumplimiento del oráculo hasta congelarlo y verificarlo.

## Criterio de finalización de la modalidad A

Un operador autorizado crea los recursos aprobados, ejecuta migraciones y seed, verifica funciones y trazabilidad por API, exporta evidencia saneada y realiza retirada manual selectiva hasta comprobar ausencia de recursos de demo facturables, conservando únicamente administración y registro de evidencias. Para E90 todas estas verificaciones siguen **PENDIENTES** de implementación y ejecución.

**Fuentes oficiales:** https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DeleteDBInstance.html ; https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.Retaining.html ; https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html .
