# Raíz web: la aplicación web servida con S3 y CloudFront (§5.4.2).
# Independiente de las demás y persistente entre sesiones, como bootstrap: la URL queda estable.
# Solo guarda archivos estáticos compilados, sin contenido documental. Se retira al cerrar el
# proyecto, con un plan de retiro revisado por el operador.
terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.67.0"
    }
  }
  backend "s3" {
    key = "web/terraform.tfstate"
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.cuenta_id]
  default_tags {
    tags = {
      proyecto = "atlas"
      entorno  = "web"
      raiz     = "web"
    }
  }
}
