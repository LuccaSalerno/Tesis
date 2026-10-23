output "bucket" {
  value = aws_s3_bucket.web.id
}

output "distribucion_id" {
  value = aws_cloudfront_distribution.web.id
}

output "origen" {
  description = "Origen para el CORS de persistent (origenes_cors) y demo (origenes_web)"
  value       = "https://${aws_cloudfront_distribution.web.domain_name}"
}
