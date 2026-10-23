# Un solo paquete arm64 para todas las funciones, con su propio manejador (P6).

data "http" "jwks" {
  url = "${local.p.cognito_emisor}/.well-known/jwks.json"
}

locals {
  comun = {
    ATLAS_ENTORNO                           = local.p.entorno
    ATLAS_NIVEL_REGISTRO                    = "INFO"
    ATLAS_AWS_REGION                        = var.region
    ATLAS_BD_HOST                           = local.r.proxy_direccion
    ATLAS_BD_NOMBRE                         = var.base_datos
    ATLAS_BD_USUARIO                        = var.usuario_bd_aplicacion
    ATLAS_BD_AUTENTICACION                  = "iam"
    ATLAS_BD_CA_CERTIFICADOS                = "/var/task/certificados/ca-bd.pem" # RDS + Amazon Root CA (DIF-96)
    ATLAS_S3_BUCKET_DOCUMENTOS              = local.p.bucket_documentos
    ATLAS_MANTENIMIENTO_FUENTE              = "s3"
    ATLAS_BEDROCK_PERFIL_GENERATIVO         = var.perfil_generativo
    ATLAS_BEDROCK_MODELO_EMBEDDINGS         = var.modelo_embeddings
    ATLAS_VERSION_CODIGO                    = var.version_codigo
    ATLAS_PROCESAMIENTO_LIMITE_CONCURRENCIA = tostring(var.limite_concurrencia)
    # crear_cliente exige el bucket y la máquina en toda función que use AWS (validar_servicios_aws).
    ATLAS_SFN_MAQUINA_PROCESAMIENTO_ARN = local.arn_maquina
  }

  funciones = {
    api = {
      manejador = "atlas.lambda_api.manejar"
      memoria   = 1024
      tiempo    = 29 # API Gateway corta a los 30 s
      sg        = local.p.sg_lambda_aplicacion
      entorno = merge(local.comun, {
        ATLAS_JWT_EMISOR  = local.p.cognito_emisor
        ATLAS_JWT_CLIENTE = local.p.cognito_cliente_id
        ATLAS_JWT_JWKS    = data.http.jwks.response_body
        # RF-25: supresión en Cognito por la Lambda `cuentas` (DO-2026-10-23-CIERRE P7).
        ATLAS_CUENTAS_FUNCION = local.nombre_funcion_cuentas
      })
    }
    procesamiento = {
      manejador = "atlas.procesamiento.lambdas.manejar_procesamiento"
      memoria   = 1024
      tiempo    = 120
      sg        = null
      entorno   = local.comun
    }
    persistencia = {
      manejador = "atlas.procesamiento.lambdas.manejar_persistencia"
      memoria   = 512
      tiempo    = 60
      sg        = local.p.sg_lambda_aplicacion
      entorno   = local.comun
    }
    reconciliador = {
      manejador = "atlas.operacion.lambda_reconciliador.manejar"
      memoria   = 512
      tiempo    = 120
      sg        = local.p.sg_lambda_aplicacion # proxy, endpoint de Step Functions y S3
      entorno   = local.comun
    }
    # Fuera de la VPC (§5.4.2): llega a Cognito sin NAT; solo la invoca la API.
    cuentas = {
      manejador = "atlas.operacion.lambda_cuentas.manejar"
      memoria   = 256
      tiempo    = 15
      sg        = null
      entorno = {
        ATLAS_AWS_REGION             = var.region
        ATLAS_NIVEL_REGISTRO         = "INFO"
        ATLAS_COGNITO_GRUPO_USUARIOS = local.p.cognito_user_pool_id
      }
    }
    operaciones = {
      manejador = "atlas.operacion.lambda_operaciones.manejar"
      memoria   = 512
      tiempo    = 300
      sg        = local.p.sg_lambda_operaciones
      entorno = merge(local.comun, {
        ATLAS_BD_HOST_MIGRACION          = local.p.rds_direccion
        ATLAS_BD_USUARIO_MIGRACION       = var.usuario_bd_migracion
        ATLAS_OPS_SECRETO_MAESTRO_ARN    = local.p.rds_secreto_maestro_arn
        ATLAS_OPS_DIRECTORIO_MIGRACIONES = "/var/task/migraciones"
      })
    }
  }

  # Nombres conocidos de antemano: evitan los ciclos de la API con la máquina y con `cuentas`.
  nombre_funcion_cuentas = "${local.prefijo}-cuentas"
  nombre_maquina         = "${local.prefijo}-procesamiento"
  arn_maquina            = "arn:aws:states:${var.region}:${local.cuenta}:stateMachine:${local.nombre_maquina}"
}

# Grupos de registro explícitos: se retiran con la sesión y no quedan residuos.
resource "aws_cloudwatch_log_group" "funcion" {
  for_each          = local.funciones
  name              = "/aws/lambda/${local.prefijo}-${each.key}"
  retention_in_days = var.retencion_registros_dias
}

resource "aws_lambda_function" "funcion" {
  for_each         = local.funciones
  function_name    = "${local.prefijo}-${each.key}"
  role             = aws_iam_role.lambda[each.key].arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = each.value.manejador
  memory_size      = each.value.memoria
  timeout          = each.value.tiempo
  s3_bucket        = aws_s3_object.paquete.bucket
  s3_key           = aws_s3_object.paquete.key
  source_code_hash = filebase64sha256(var.paquete_lambda)

  environment {
    variables = each.value.entorno
  }

  dynamic "vpc_config" {
    for_each = each.value.sg == null ? [] : [each.value.sg]
    content {
      subnet_ids         = local.p.subredes_aplicacion
      security_group_ids = [vpc_config.value]
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.funcion,
    aws_iam_role_policy.lambda,
    aws_iam_role_policy_attachment.basica,
    aws_iam_role_policy_attachment.vpc,
  ]
}

# --- Step Functions Standard (§5.3.1): definición versionada en el backend ------------

resource "aws_sfn_state_machine" "procesamiento" {
  name     = local.nombre_maquina
  role_arn = aws_iam_role.sfn.arn
  type     = "STANDARD"
  definition = templatefile("${path.module}/../../../backend/src/atlas/procesamiento/maquina_estados.asl.json", {
    ArnLambdaProcesamiento = aws_lambda_function.funcion["procesamiento"].arn
    ArnLambdaPersistencia  = aws_lambda_function.funcion["persistencia"].arn
  })
  # Sin registro de ejecuciones: entradas y salidas ya son solo identificadores (RNF-09).
}
