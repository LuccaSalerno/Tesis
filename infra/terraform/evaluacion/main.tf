# Solo recibe copias del corpus sintético E90 (AGENTS.md §2.4): ningún documento real. Por
# eso, a diferencia del bucket documental, admite force_destroy: el retiro de esta raíz no
# requiere vaciado manual. El ciclo de vida borra las copias al día siguiente.

resource "aws_s3_bucket" "evaluacion" {
  bucket        = var.nombre_bucket
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evaluacion" {
  bucket = aws_s3_bucket.evaluacion.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "evaluacion" {
  bucket                  = aws_s3_bucket.evaluacion.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "evaluacion" {
  bucket = aws_s3_bucket.evaluacion.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

data "aws_iam_policy_document" "solo_tls" {
  statement {
    sid     = "SoloTLS"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.evaluacion.arn,
      "${aws_s3_bucket.evaluacion.arn}/*",
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

resource "aws_s3_bucket_policy" "evaluacion" {
  bucket = aws_s3_bucket.evaluacion.id
  policy = data.aws_iam_policy_document.solo_tls.json
}

resource "aws_s3_bucket_lifecycle_configuration" "evaluacion" {
  bucket = aws_s3_bucket.evaluacion.id
  rule {
    id     = "atlas-evaluacion-copias"
    status = "Enabled"
    filter {}
    expiration {
      days = 1
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}
