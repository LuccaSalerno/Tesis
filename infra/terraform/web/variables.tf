variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cuenta_id" {
  description = "Cuenta autorizada: el proveedor rechaza cualquier otra"
  type        = string
}

variable "nombre_bucket" {
  description = "Bucket privado de los archivos estáticos, p. ej. atlas-web-<sufijo>"
  type        = string
}
