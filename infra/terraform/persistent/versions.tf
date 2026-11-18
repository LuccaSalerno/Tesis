# Raíz persistent. En E90A se crea y se retira en cada sesión: el nombre es
# histórico y no implica conservación de datos.
terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.67.0"
    }
  }
  backend "s3" {
    key = "persistent/terraform.tfstate"
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.cuenta_id]
  default_tags {
    tags = local.etiquetas
  }
}

locals {
  prefijo = "atlas-${var.entorno}"
  etiquetas = {
    proyecto = "atlas"
    entorno  = var.entorno
    raiz     = "persistent"
    sesion   = var.sesion
  }
}
