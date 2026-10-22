data "aws_caller_identity" "actual" {}

# --- RDS Proxy con autenticación IAM de extremo a extremo (RC-P10-04) --------------------

data "aws_iam_policy_document" "proxy_confianza" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "proxy" {
  name               = "${local.prefijo}-rds-proxy"
  assume_role_policy = data.aws_iam_policy_document.proxy_confianza.json
}

# El proxy se conecta a la instancia (db-…, obtenido de AWS) solo como el usuario de aplicación.
data "aws_iam_policy_document" "proxy_conexion" {
  statement {
    actions = ["rds-db:connect"]
    resources = [
      "arn:aws:rds-db:${var.region}:${data.aws_caller_identity.actual.account_id}:dbuser:${local.p.rds_id_recurso}/${var.usuario_bd_aplicacion}",
    ]
  }
}

resource "aws_iam_role_policy" "proxy_conexion" {
  role   = aws_iam_role.proxy.id
  policy = data.aws_iam_policy_document.proxy_conexion.json
}

resource "aws_db_proxy" "principal" {
  name                   = "${local.prefijo}-proxy"
  engine_family          = "POSTGRESQL"
  role_arn               = aws_iam_role.proxy.arn
  vpc_subnet_ids         = local.p.subredes_datos
  vpc_security_group_ids = [local.p.sg_proxy]
  require_tls            = true
  idle_client_timeout    = 1800
  default_auth_scheme    = "IAM_AUTH"
}

resource "aws_db_proxy_default_target_group" "principal" {
  db_proxy_name = aws_db_proxy.principal.name
  connection_pool_config {
    max_connections_percent = 50
  }
}

resource "aws_db_proxy_target" "principal" {
  db_proxy_name          = aws_db_proxy.principal.name
  target_group_name      = aws_db_proxy_default_target_group.principal.name
  db_instance_identifier = local.p.rds_identificador
}

# --- Endpoints de interfaz (sin NAT): solo los que se usan (P9) --------------------------

locals {
  servicios = merge(
    {
      states          = "com.amazonaws.${var.region}.states"
      bedrock_runtime = "com.amazonaws.${var.region}.bedrock-runtime"
    },
    var.endpoint_secrets_manager ? { secretsmanager = "com.amazonaws.${var.region}.secretsmanager" } : {},
  )
}

resource "aws_vpc_endpoint" "interfaz" {
  for_each            = local.servicios
  vpc_id              = local.p.vpc_id
  service_name        = each.value
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.p.subredes_aplicacion
  security_group_ids  = [local.p.sg_endpoints]
  private_dns_enabled = true
  tags                = { Name = "${local.prefijo}-${each.key}" }
}
