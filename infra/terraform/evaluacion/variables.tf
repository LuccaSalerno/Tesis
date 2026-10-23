variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cuenta_id" {
  description = "Cuenta autorizada: el proveedor rechaza cualquier otra"
  type        = string
}

variable "campana" {
  description = "Identificador de la campaña de medición (etiqueta de los recursos)"
  type        = string
}

variable "nombre_bucket" {
  description = "Nombre global único, p. ej. atlas-evaluacion-<campana>-<sufijo>"
  type        = string
}
