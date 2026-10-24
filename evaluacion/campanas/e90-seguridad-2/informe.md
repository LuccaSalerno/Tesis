# Verificación de seguridad e90-seguridad-2 (§6.3.3)

## SEG-02 — configuración

| Verificación | Resultado | Detalle |
|---|---|---|
| s3_cifrado | Cumple | AES256 |
| s3_solo_tls | Cumple | Deny sin aws:SecureTransport |
| s3_bloqueo_publico | Cumple | BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets |
| rds_cifrado | Cumple | StorageEncrypted |
| rds_sin_acceso_publico | Cumple | PubliclyAccessible |
| rds_force_ssl | Cumple | atlas-demo-postgres16: rds.force_ssl=1, in-sync |
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
