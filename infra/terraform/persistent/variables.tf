variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cuenta_id" {
  description = "Cuenta AWS autorizada"
  type        = string
}

variable "entorno" {
  description = "Solo demo en E90 (tests requiere aprobación separada)"
  type        = string
  default     = "demo"
  validation {
    condition     = var.entorno == "demo"
    error_message = "En E90 solo se despliega demo."
  }
}

variable "sesion" {
  description = "Identificador de la sesión E90A (etiqueta de inventario), p. ej. e90-2026-10-24"
  type        = string
}

variable "retiro_autorizado" {
  description = "Solo true en el plan de retiro aprobado: quita la protección de borrado de RDS y Cognito"
  type        = bool
  default     = false
}

variable "cidr_vpc" {
  type    = string
  default = "10.40.0.0/16"
}

variable "rds_clase" {
  description = "Hipótesis inicial de RC-P10-13, sujeta a medición"
  type        = string
  default     = "db.t4g.medium"
}

variable "rds_version_motor" {
  description = "PostgreSQL 16, igual que en local y CI; RDS elige la versión menor vigente"
  type        = string
  default     = "16"
}

variable "rds_almacenamiento_gib" {
  type    = number
  default = 20
}

variable "nombre_bucket_documentos" {
  description = "Nombre global único del bucket documental de la sesión"
  type        = string
}

variable "origenes_cors" {
  description = "Orígenes de la aplicación web autorizados a cargar (PUT) y leer (GET) con URL prefirmada; p. ej. http://localhost:4173 (DO-2026-10-22-WEB F7)"
  type        = list(string)
  default     = []
}
