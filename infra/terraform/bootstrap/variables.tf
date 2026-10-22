variable "region" {
  description = "Región principal (RC-P10-01)"
  type        = string
  default     = "us-east-1"
}

variable "cuenta_id" {
  description = "Cuenta AWS autorizada: el proveedor se niega a operar en otra"
  type        = string
}

variable "nombre_bucket_estado" {
  description = "Nombre global único del bucket de estado remoto"
  type        = string
}
