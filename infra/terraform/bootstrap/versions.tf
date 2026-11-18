# Raíz bootstrap: estado remoto de las demás raíces. Se crea una sola vez y
# nunca se destruye. Su propio estado queda en el equipo del operador.
terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.67.0"
    }
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.cuenta_id]
  default_tags {
    tags = {
      proyecto = "atlas"
      raiz     = "bootstrap"
    }
  }
}
