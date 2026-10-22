# VPC privada en dos zonas, sin NAT ni salida a Internet (RC-P10-02, tesis §5.4).

data "aws_availability_zones" "disponibles" {
  state = "available"
}

locals {
  zonas = slice(data.aws_availability_zones.disponibles.names, 0, 2)
}

resource "aws_vpc" "principal" {
  cidr_block           = var.cidr_vpc
  enable_dns_support   = true
  enable_dns_hostnames = true # necesario para el DNS privado de los endpoints de interfaz
  tags                 = { Name = "${local.prefijo}-vpc" }
}

resource "aws_subnet" "aplicacion" {
  count             = 2
  vpc_id            = aws_vpc.principal.id
  availability_zone = local.zonas[count.index]
  cidr_block        = cidrsubnet(var.cidr_vpc, 8, 1 + count.index)
  tags              = { Name = "${local.prefijo}-aplicacion-${count.index}" }
}

resource "aws_subnet" "datos" {
  count             = 2
  vpc_id            = aws_vpc.principal.id
  availability_zone = local.zonas[count.index]
  cidr_block        = cidrsubnet(var.cidr_vpc, 8, 11 + count.index)
  tags              = { Name = "${local.prefijo}-datos-${count.index}" }
}

resource "aws_route_table" "privada" {
  vpc_id = aws_vpc.principal.id
  tags   = { Name = "${local.prefijo}-privada" }
}

resource "aws_route_table_association" "aplicacion" {
  count          = 2
  subnet_id      = aws_subnet.aplicacion[count.index].id
  route_table_id = aws_route_table.privada.id
}

resource "aws_route_table_association" "datos" {
  count          = 2
  subnet_id      = aws_subnet.datos[count.index].id
  route_table_id = aws_route_table.privada.id
}

# Endpoint gateway de S3 (sin cargo): originales y resultados desde las Lambda privadas.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.principal.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.privada.id]
  tags              = { Name = "${local.prefijo}-s3" }
}

# --- Grupos de seguridad estables (RC-P10-07): reglas mínimas por puerto y origen --------

resource "aws_security_group" "lambda_aplicacion" {
  name        = "${local.prefijo}-lambda-aplicacion"
  description = "API y persistencia: solo proxy, endpoints y S3"
  vpc_id      = aws_vpc.principal.id
}

resource "aws_security_group" "lambda_operaciones" {
  name        = "${local.prefijo}-lambda-operaciones"
  description = "Operaciones privadas: RDS directo, endpoints y S3"
  vpc_id      = aws_vpc.principal.id
}

resource "aws_security_group" "proxy" {
  name        = "${local.prefijo}-proxy"
  description = "RDS Proxy"
  vpc_id      = aws_vpc.principal.id
}

resource "aws_security_group" "rds" {
  name        = "${local.prefijo}-rds"
  description = "Instancia PostgreSQL"
  vpc_id      = aws_vpc.principal.id
}

resource "aws_security_group" "endpoints" {
  name        = "${local.prefijo}-endpoints"
  description = "Endpoints de interfaz"
  vpc_id      = aws_vpc.principal.id
}

resource "aws_vpc_security_group_egress_rule" "aplicacion_a_proxy" {
  security_group_id            = aws_security_group.lambda_aplicacion.id
  referenced_security_group_id = aws_security_group.proxy.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "aplicacion_a_endpoints" {
  security_group_id            = aws_security_group.lambda_aplicacion.id
  referenced_security_group_id = aws_security_group.endpoints.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_egress_rule" "aplicacion_a_s3" {
  security_group_id = aws_security_group.lambda_aplicacion.id
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "operaciones_a_rds" {
  security_group_id            = aws_security_group.lambda_operaciones.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "operaciones_a_endpoints" {
  security_group_id            = aws_security_group.lambda_operaciones.id
  referenced_security_group_id = aws_security_group.endpoints.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_egress_rule" "operaciones_a_s3" {
  security_group_id = aws_security_group.lambda_operaciones.id
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "proxy_desde_aplicacion" {
  security_group_id            = aws_security_group.proxy.id
  referenced_security_group_id = aws_security_group.lambda_aplicacion.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "proxy_a_rds" {
  security_group_id            = aws_security_group.proxy.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_ingress_rule" "rds_desde_proxy" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.proxy.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_ingress_rule" "rds_desde_operaciones" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.lambda_operaciones.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_desde_aplicacion" {
  security_group_id            = aws_security_group.endpoints.id
  referenced_security_group_id = aws_security_group.lambda_aplicacion.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_desde_operaciones" {
  security_group_id            = aws_security_group.endpoints.id
  referenced_security_group_id = aws_security_group.lambda_operaciones.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}
