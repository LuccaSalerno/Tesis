output "url_api" {
  value = aws_apigatewayv2_stage.predeterminada.invoke_url
}

output "funcion_operaciones" {
  description = "Nombre de la Lambda privada que invoca el operador (RC-P10-15)"
  value       = aws_lambda_function.funcion["operaciones"].function_name
}

output "maquina_procesamiento" {
  value = aws_sfn_state_machine.procesamiento.arn
}

output "version_codigo" {
  value = var.version_codigo
}
