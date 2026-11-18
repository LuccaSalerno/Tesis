# Raíz demo: API Gateway, Lambda, Step Functions, roles y artefactos del
# entorno demo. Se crea y se retira por sesión (E90A). Sin frontend, Scheduler ni Lambda
# de Cognito en el primer despliegue.
terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.67.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "3.6.2"
    }
  }
  backend "s3" {
    key = "demo/terraform.tfstate"
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.cuenta_id]
  default_tags {
    tags = {
      proyecto = "atlas"
      entorno  = local.p.entorno
      raiz     = "demo"
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

data "terraform_remote_state" "runtime" {
  backend = "s3"
  config = {
    bucket = var.bucket_estado
    key    = "runtime/terraform.tfstate"
    region = var.region
  }
}

data "aws_caller_identity" "actual" {}

locals {
  p       = data.terraform_remote_state.persistent.outputs
  r       = data.terraform_remote_state.runtime.outputs
  prefijo = "atlas-${local.p.entorno}"
  cuenta  = data.aws_caller_identity.actual.account_id
}
