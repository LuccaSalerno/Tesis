variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cuenta_id" {
  type = string
}

variable "bucket_estado" {
  description = "Bucket de estado remoto (salida de bootstrap)"
  type        = string
}

variable "usuario_bd_aplicacion" {
  description = "Usuario PostgreSQL de aplicación del entorno (RC-P10-03)"
  type        = string
  default     = "atlas_demo_app"
}

variable "endpoint_secrets_manager" {
  description = "Endpoint temporal: solo durante la inicialización privilegiada (RC-P10-15)"
  type        = bool
  default     = true
}
