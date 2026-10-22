# Raíz runtime (RC-P10-07): RDS Proxy, su rol y los endpoints de interfaz. Se crea y se
# retira por sesión. Recrearla obliga a reaplicar demo antes de habilitar (RC-P10-04).
terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.67.0"
    }
  }
  backend "s3" {
    key = "runtime/terraform.tfstate"
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.cuenta_id]
  default_tags {
    tags = {
      proyecto = "atlas"
      entorno  = local.p.entorno
      raiz     = "runtime"
      sesion   = local.p.sesion
    }
  }
}

data "terraform_remote_state" "persistent" {
  backend = "s3"
  config = {
    bucket = var.bucket_estado
    key    = "persistent/terraform.tfstate"
    region = var.region
  }
}

locals {
  p       = data.terraform_remote_state.persistent.outputs
  prefijo = "atlas-${local.p.entorno}"
}
