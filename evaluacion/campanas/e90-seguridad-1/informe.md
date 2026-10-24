# Verificación de seguridad e90-seguridad-1 (§6.3.3)

## SEG-01, SEG-03 y RNF-08: Cumple

237 de 237 casos con el resultado esperado.
No implementadas (no se cuentan como cumplidas): ninguna.


## SEG-02 — configuración

| Verificación | Resultado | Detalle |
|---|---|---|
| s3_cifrado | Cumple | AES256 |
| s3_solo_tls | Cumple | Deny sin aws:SecureTransport |
| s3_bloqueo_publico | Cumple | BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets |
| rds_cifrado | Cumple | StorageEncrypted |
| rds_sin_acceso_publico | Cumple | PubliclyAccessible |
| rds_force_ssl | No cumple | atlas-demo-postgres16 |
| lambda_api_sin_secretos | Cumple | ninguna |
| logs_api_retencion | Cumple | 7 días |
| lambda_procesamiento_sin_secretos | Cumple | ninguna |
| logs_procesamiento_retencion | Cumple | 7 días |
| lambda_persistencia_sin_secretos | Cumple | ninguna |
| logs_persistencia_retencion | Cumple | 7 días |
| lambda_operaciones_sin_secretos | Cumple | ninguna |
| logs_operaciones_retencion | Cumple | 7 días |
| bedrock_sin_registro_de_invocaciones | Cumple | loggingConfig |
| sin_endpoint_secrets_manager | Cumple | bedrock-runtime,lambda,s3,states |

## SEG-04 — registros

| Verificación | Resultado | Detalle |
|---|---|---|
| logs_api_sin_SEGMARCAA17969 | Cumple | 0 eventos |
| logs_api_sin_SEGMARCAB17969 | Cumple | 0 eventos |
| logs_api_sin_SEGMARCATITULO | Cumple | 0 eventos |
| logs_api_sin_SEGMARCAARCHIV | Cumple | 0 eventos |
| logs_api_sin_SEGMARCAPREGUN | Cumple | 0 eventos |
| logs_api_sin_SEGMARCAFALLO1 | Cumple | 0 eventos |
| logs_procesamiento_sin_SEGMARCAA17969 | Cumple | 0 eventos |
| logs_procesamiento_sin_SEGMARCAB17969 | Cumple | 0 eventos |
| logs_procesamiento_sin_SEGMARCATITULO | Cumple | 0 eventos |
| logs_procesamiento_sin_SEGMARCAARCHIV | Cumple | 0 eventos |
| logs_procesamiento_sin_SEGMARCAPREGUN | Cumple | 0 eventos |
| logs_procesamiento_sin_SEGMARCAFALLO1 | Cumple | 0 eventos |
| logs_persistencia_sin_SEGMARCAA17969 | Cumple | 0 eventos |
| logs_persistencia_sin_SEGMARCAB17969 | Cumple | 0 eventos |
| logs_persistencia_sin_SEGMARCATITULO | Cumple | 0 eventos |
| logs_persistencia_sin_SEGMARCAARCHIV | Cumple | 0 eventos |
| logs_persistencia_sin_SEGMARCAPREGUN | Cumple | 0 eventos |
| logs_persistencia_sin_SEGMARCAFALLO1 | Cumple | 0 eventos |
| logs_operaciones_sin_SEGMARCAA17969 | Cumple | 0 eventos |
| logs_operaciones_sin_SEGMARCAB17969 | Cumple | 0 eventos |
| logs_operaciones_sin_SEGMARCATITULO | Cumple | 0 eventos |
| logs_operaciones_sin_SEGMARCAARCHIV | Cumple | 0 eventos |
| logs_operaciones_sin_SEGMARCAPREGUN | Cumple | 0 eventos |
| logs_operaciones_sin_SEGMARCAFALLO1 | Cumple | 0 eventos |
| logs_api_con_correlacion | Cumple | 4922 solicitudes |
| logs_persistencia_con_trabajo_id | Cumple | 10 eventos |
| stepfunctions_sin_marcadores | Cumple | 10 ejecuciones, 0 con marcador |
| camino_de_error_ejercitado | Cumple | 1 ejecuciones fallidas |
