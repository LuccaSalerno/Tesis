# EventBridge Scheduler invoca el reconciliador cada 5 minutos.
# Con `reconciliador_habilitado = false` la programación queda pausada; la función misma no
# actúa fuera de `active`.

data "aws_iam_policy_document" "confianza_scheduler" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.cuenta]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${local.prefijo}-reconciliador-scheduler"
  assume_role_policy = data.aws_iam_policy_document.confianza_scheduler.json
}

data "aws_iam_policy_document" "scheduler" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.funcion["reconciliador"].arn]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "${local.prefijo}-reconciliador-scheduler"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler.json
}

resource "aws_scheduler_schedule" "reconciliador" {
  name                = "${local.prefijo}-reconciliador"
  schedule_expression = "rate(5 minutes)"
  state               = var.reconciliador_habilitado ? "ENABLED" : "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.funcion["reconciliador"].arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ origen = "scheduler" })
    retry_policy {
      maximum_retry_attempts = 0 # la próxima ejecución, en 5 minutos, retoma lo pendiente
    }
  }
}
