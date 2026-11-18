output "proxy_direccion" {
  description = "Endpoint predeterminado del proxy (puede cambiar al recrearlo)"
  value       = aws_db_proxy.principal.endpoint
}

output "proxy_id_recurso" {
  description = "Identificador prx-…, obtenido del ARN del proxy"
  value       = element(split(":", aws_db_proxy.principal.arn), 6)
}

output "endpoints_interfaz" {
  value = sort(keys(aws_vpc_endpoint.interfaz))
}
