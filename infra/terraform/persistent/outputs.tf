# Solo identificadores, sin secretos. El ARN del secreto maestro no es el secreto.

output "region" {
  value = var.region
}

output "entorno" {
  value = var.entorno
}

output "sesion" {
  value = var.sesion
}

output "vpc_id" {
  value = aws_vpc.principal.id
}

output "subredes_aplicacion" {
  value = aws_subnet.aplicacion[*].id
}

output "subredes_datos" {
  value = aws_subnet.datos[*].id
}

output "sg_lambda_aplicacion" {
  value = aws_security_group.lambda_aplicacion.id
}

output "sg_lambda_operaciones" {
  value = aws_security_group.lambda_operaciones.id
}

output "sg_proxy" {
  value = aws_security_group.proxy.id
}

output "sg_endpoints" {
  value = aws_security_group.endpoints.id
}

output "rds_identificador" {
  value = aws_db_instance.principal.identifier
}

output "rds_direccion" {
  value = aws_db_instance.principal.address
}

output "rds_puerto" {
  value = aws_db_instance.principal.port
}

output "rds_id_recurso" {
  description = "DbiResourceId (db-…), obtenido de AWS"
  value       = aws_db_instance.principal.resource_id
}

output "rds_secreto_maestro_arn" {
  value = aws_db_instance.principal.master_user_secret[0].secret_arn
}

output "bucket_documentos" {
  value = aws_s3_bucket.documentos.bucket
}

output "bucket_documentos_arn" {
  value = aws_s3_bucket.documentos.arn
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.demo.id
}

output "cognito_user_pool_arn" {
  value = aws_cognito_user_pool.demo.arn
}

output "cognito_cliente_id" {
  value = aws_cognito_user_pool_client.api.id
}

output "cognito_emisor" {
  value = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.demo.id}"
}
