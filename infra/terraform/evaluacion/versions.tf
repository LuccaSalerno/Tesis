# Raíz evaluacion: un único bucket para que Textract asíncrono
# lea los PDF del corpus sintético E90 durante una campaña de §6.3.1. No depende de las demás
# raíces ni necesita RDS. Se crea y se retira por campaña, con el plan aprobado por el operador.
terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.67.0"
    }
  }
  backend "s3" {
    key = "evaluacion/terraform.tfstate"
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.cuenta_id]
  default_tags {
    tags = {
      proyecto = "atlas"
      entorno  = "evaluacion"
      raiz     = "evaluacion"
      campana  = var.campana
    }
  }
}
