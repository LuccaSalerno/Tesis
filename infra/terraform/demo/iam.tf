# Roles de ejecución mínimos por función (RC-P10, AGENTS.md §3). Ninguno administra
# infraestructura: solo el procesamiento funcional de la tesis.

data "aws_iam_policy_document" "confianza_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

locals {
  bucket_arn = local.p.bucket_documentos_arn
  roles      = toset(["api", "procesamiento", "persistencia", "operaciones", "reconciliador"])
  en_vpc     = toset(["api", "persistencia", "operaciones", "reconciliador"])

  bedrock_generativo = concat(
    ["arn:aws:bedrock:${var.region}:${local.cuenta}:inference-profile/${var.perfil_generativo}"],
    [for r in var.regiones_destino_perfil : "arn:aws:bedrock:${r}::foundation-model/${var.modelo_generativo}"],
  )
  bedrock_embeddings = ["arn:aws:bedrock:${var.region}::foundation-model/${var.modelo_embeddings}"]

  usuario_proxy_app = "arn:aws:rds-db:${var.region}:${local.cuenta}:dbuser:${local.r.proxy_id_recurso}/${var.usuario_bd_aplicacion}"
  usuario_rds_migr  = "arn:aws:rds-db:${var.region}:${local.cuenta}:dbuser:${local.p.rds_id_recurso}/${var.usuario_bd_migracion}"
}

resource "aws_iam_role" "lambda" {
  for_each           = local.roles
  name               = "${local.prefijo}-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.confianza_lambda.json
}

resource "aws_iam_role_policy_attachment" "basica" {
  for_each   = setsubtract(local.roles, local.en_vpc)
  role       = aws_iam_role.lambda[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "vpc" {
  for_each   = local.en_vpc
  role       = aws_iam_role.lambda[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# --- API: cargas prefirmadas, incorporación, mantenimiento, Step Functions y RAG --------

data "aws_iam_policy_document" "api" {
  statement {
    sid     = "CargasEIncorporacion"
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = [
      "${local.bucket_arn}/cargas-temporales/*",
      "${local.bucket_arn}/documentos/*",
    ]
  }
  statement {
    sid       = "LeerMantenimiento" # solo lectura: nunca lo modifica (RC-P10-09)
    actions   = ["s3:GetObject"]
    resources = ["${local.bucket_arn}/control/mantenimiento.json"]
  }
  statement {
    sid       = "ListarParaHead" # sin esto, un objeto ausente responde 403 y no 404
    actions   = ["s3:ListBucket"]
    resources = [local.bucket_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["cargas-temporales/*", "documentos/*"]
    }
  }
  statement {
    actions   = ["states:StartExecution"]
    resources = [local.arn_maquina]
  }
  statement {
    sid       = "ConsultaAsistida"
    actions   = ["bedrock:InvokeModel"]
    resources = concat(local.bedrock_generativo, local.bedrock_embeddings)
  }
  statement {
    actions   = ["rds-db:connect"]
    resources = [local.usuario_proxy_app]
  }
}

# --- Procesamiento (fuera de la VPC): Textract, Bedrock y resultados en S3 --------------

data "aws_iam_policy_document" "procesamiento" {
  statement {
    actions = ["s3:GetObject"]
    resources = [
      "${local.bucket_arn}/cargas-temporales/*",
      "${local.bucket_arn}/documentos/*",
    ]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${local.bucket_arn}/resultados/*"]
  }
  statement {
    actions   = ["textract:StartDocumentAnalysis", "textract:GetDocumentAnalysis"]
    resources = ["*"] # Textract no admite permisos a nivel de recurso
  }
  statement {
    actions   = ["bedrock:InvokeModel"]
    resources = concat(local.bedrock_generativo, local.bedrock_embeddings)
  }
}

# --- Persistencia (en la VPC): resultados y PostgreSQL por el proxy ---------------------

data "aws_iam_policy_document" "persistencia" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${local.bucket_arn}/resultados/*"]
  }
  statement {
    actions   = ["rds-db:connect"]
    resources = [local.usuario_proxy_app]
  }
}

# --- Operaciones privadas: credencial maestra, migración directa y drenaje -------------

data "aws_iam_policy_document" "operaciones" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [local.p.rds_secreto_maestro_arn]
  }
  statement {
    actions   = ["rds-db:connect"]
    resources = [local.usuario_rds_migr]
  }
  statement {
    actions   = ["states:ListExecutions"]
    resources = [local.arn_maquina]
  }
}

# --- Reconciliador (en la VPC): estado real de las ejecuciones e inicio idempotente -------

data "aws_iam_policy_document" "reconciliador" {
  statement {
    sid       = "IniciarEjecucion" # nombre determinista por intento: nunca una segunda
    actions   = ["states:StartExecution"]
    resources = [local.arn_maquina]
  }
  statement {
    sid       = "ConsultarEjecucion"
    actions   = ["states:DescribeExecution"]
    resources = ["${replace(local.arn_maquina, ":stateMachine:", ":execution:")}:*"]
  }
  statement {
    sid       = "LeerMantenimiento" # no actúa fuera de `active` (RC-P08.12)
    actions   = ["s3:GetObject"]
    resources = ["${local.bucket_arn}/control/mantenimiento.json"]
  }
  statement {
    actions   = ["rds-db:connect"]
    resources = [local.usuario_proxy_app]
  }
}

locals {
  politicas = {
    api           = data.aws_iam_policy_document.api.json
    procesamiento = data.aws_iam_policy_document.procesamiento.json
    persistencia  = data.aws_iam_policy_document.persistencia.json
    operaciones   = data.aws_iam_policy_document.operaciones.json
    reconciliador = data.aws_iam_policy_document.reconciliador.json
  }
}

resource "aws_iam_role_policy" "lambda" {
  for_each = local.roles
  name     = "${local.prefijo}-${each.key}"
  role     = aws_iam_role.lambda[each.key].id
  policy   = local.politicas[each.key]
}

# --- Step Functions: solo invoca las dos funciones de su entorno (RC-P10-05) -----------

data "aws_iam_policy_document" "confianza_sfn" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "${local.prefijo}-procesamiento-sfn"
  assume_role_policy = data.aws_iam_policy_document.confianza_sfn.json
}

data "aws_iam_policy_document" "sfn" {
  statement {
    actions = ["lambda:InvokeFunction"]
    resources = flatten([
      for f in ["procesamiento", "persistencia"] : [
        aws_lambda_function.funcion[f].arn,
        "${aws_lambda_function.funcion[f].arn}:*",
      ]
    ])
  }
}

resource "aws_iam_role_policy" "sfn" {
  name   = "${local.prefijo}-procesamiento-sfn"
  role   = aws_iam_role.sfn.id
  policy = data.aws_iam_policy_document.sfn.json
}
