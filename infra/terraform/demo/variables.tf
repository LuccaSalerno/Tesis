variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cuenta_id" {
  type = string
}

variable "bucket_estado" {
  type = string
}

variable "nombre_bucket_artefactos" {
  description = "Bucket de la sesión para el paquete Lambda"
  type        = string
}

variable "paquete_lambda" {
  description = "Zip construido con infra/empaquetado/construir_lambda.sh"
  type        = string
  default     = "../../../dist/atlas-lambda.zip"
}

variable "version_codigo" {
  description = "Commit desplegado (RC-P10-11: versión identificable)"
  type        = string
}

variable "base_datos" {
  type    = string
  default = "pfi_demo"
}

variable "usuario_bd_aplicacion" {
  type    = string
  default = "atlas_demo_app"
}

variable "usuario_bd_migracion" {
  type    = string
  default = "atlas_demo_migracion"
}

variable "perfil_generativo" {
  description = "Perfil geográfico de EE. UU. de Claude Haiku 4.5 (RC-P09)"
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "modelo_generativo" {
  type    = string
  default = "anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "regiones_destino_perfil" {
  description = "Regiones de destino del perfil (Registro de destinos)"
  type        = list(string)
  default     = ["us-east-1", "us-east-2", "us-west-2"]
}

variable "modelo_embeddings" {
  type    = string
  default = "cohere.embed-multilingual-v3"
}

variable "origenes_web" {
  description = "Orígenes de la aplicación web (CORS de API Gateway), p. ej. http://localhost:4173; vacío: sin CORS (DO-2026-10-22-WEB F7)"
  type        = list(string)
  default     = []
}

variable "limite_rafaga_api" {
  description = "Límite de ráfaga de API Gateway: acota el consumo accidental"
  type        = number
  default     = 20
}

variable "limite_tasa_api" {
  type    = number
  default = 10
}

variable "retencion_registros_dias" {
  type    = number
  default = 7
}

variable "limite_concurrencia" {
  description = "Trabajos de procesamiento simultáneos (RC-P08.5: 10 en demo, 5 en tests)"
  type        = number
  default     = 10
}

variable "reconciliador_habilitado" {
  description = "Programación del reconciliador cada 5 minutos (RC-P08.3); false la pausa"
  type        = bool
  default     = true
}
