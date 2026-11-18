# Bucket documental de la sesión: originales, cargas temporales, resultados por
# trabajo e intento y el objeto de control de mantenimiento. Nunca force_destroy: se vacía
# con `python -m atlas.herramientas.vaciar_bucket_versionado` antes del plan de retiro.

resource "aws_s3_bucket" "documentos" {
  bucket = var.nombre_bucket_documentos
}

resource "aws_s3_bucket_versioning" "documentos" {
  bucket = aws_s3_bucket.documentos.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documentos" {
  bucket = aws_s3_bucket.documentos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256" # SSE-S3
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documentos" {
  bucket                  = aws_s3_bucket.documentos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "documentos" {
  bucket = aws_s3_bucket.documentos.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

data "aws_iam_policy_document" "documentos_solo_tls" {
  statement {
    sid     = "SoloTLS"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.documentos.arn,
      "${aws_s3_bucket.documentos.arn}/*",
    ]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "documentos" {
  bucket = aws_s3_bucket.documentos.id
  policy = data.aws_iam_policy_document.documentos_solo_tls.json
}

# Réplica literal de atlas.integraciones.ciclo_vida_s3.REGLAS_CICLO_VIDA.
resource "aws_s3_bucket_lifecycle_configuration" "documentos" {
  bucket = aws_s3_bucket.documentos.id
  rule {
    id     = "atlas-cargas-temporales-respaldo"
    status = "Enabled"
    filter {
      prefix = "cargas-temporales/"
    }
    expiration {
      days = 2
    }
    noncurrent_version_expiration {
      noncurrent_days = 2
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 2
    }
  }
  rule {
    id     = "atlas-cargas-temporales-marcadores"
    status = "Enabled"
    filter {
      prefix = "cargas-temporales/"
    }
    expiration {
      expired_object_delete_marker = true
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "documentos" {
  count  = length(var.origenes_cors) > 0 ? 1 : 0
  bucket = aws_s3_bucket.documentos.id
  cors_rule {
    allowed_methods = ["PUT", "GET"]
    allowed_origins = var.origenes_cors
    allowed_headers = ["content-type", "range"]
    expose_headers  = ["content-length", "content-range", "accept-ranges"]
    max_age_seconds = 300
  }
}

# La sesión nace en offline. Solo el operador cambia el estado
# (aws s3 cp); Terraform no vuelve a escribirlo.
resource "aws_s3_object" "control_mantenimiento" {
  bucket       = aws_s3_bucket.documentos.id
  key          = "control/mantenimiento.json"
  content      = jsonencode({ estado = "offline" })
  content_type = "application/json"
  lifecycle {
    ignore_changes = [content, etag]
  }
  depends_on = [aws_s3_bucket_versioning.documentos]
}
