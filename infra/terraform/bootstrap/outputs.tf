output "bucket_estado" {
  description = "Bucket para -backend-config de las demás raíces"
  value       = aws_s3_bucket.estado.bucket
}
