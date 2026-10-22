resource "aws_s3_bucket" "artefactos" {
  bucket = var.nombre_bucket_artefactos
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artefactos" {
  bucket = aws_s3_bucket.artefactos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artefactos" {
  bucket                  = aws_s3_bucket.artefactos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "artefactos" {
  bucket = aws_s3_bucket.artefactos.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_object" "paquete" {
  bucket      = aws_s3_bucket.artefactos.id
  key         = "lambda/atlas-${var.version_codigo}.zip"
  source      = var.paquete_lambda
  source_hash = filemd5(var.paquete_lambda)
}
