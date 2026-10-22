# API Gateway HTTP API con autorizador JWT del User Pool del entorno (RC-P10-05, §2.1).
# Los permisos del dominio se verifican además en el backend.

resource "aws_apigatewayv2_api" "principal" {
  name          = "${local.prefijo}-api"
  protocol_type = "HTTP"

  # La aplicación web corre en la máquina del presentador (F7). API Gateway responde las
  # verificaciones previas de CORS sin pasar por el autorizador.
  dynamic "cors_configuration" {
    for_each = length(var.origenes_web) > 0 ? [1] : []
    content {
      allow_origins  = var.origenes_web
      allow_methods  = ["GET", "POST", "PUT", "DELETE"]
      allow_headers  = ["authorization", "content-type"]
      expose_headers = ["x-solicitud-id", "retry-after"]
      max_age        = 300
    }
  }
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.principal.id
  name             = "${local.prefijo}-cognito"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  jwt_configuration {
    issuer   = local.p.cognito_emisor
    audience = [local.p.cognito_cliente_id]
  }
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.principal.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.funcion["api"].invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "salud" {
  api_id    = aws_apigatewayv2_api.principal.id
  route_key = "GET /salud"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_route" "autenticada" {
  api_id             = aws_apigatewayv2_api.principal.id
  route_key          = "$default"
  target             = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

# Sin registro de acceso: las rutas concretas pueden contener identificadores (RNF-03).
resource "aws_apigatewayv2_stage" "predeterminada" {
  api_id      = aws_apigatewayv2_api.principal.id
  name        = "$default"
  auto_deploy = true
  default_route_settings {
    throttling_burst_limit = var.limite_rafaga_api
    throttling_rate_limit  = var.limite_tasa_api
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "api-gateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.funcion["api"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.principal.execution_arn}/*/*"
}
