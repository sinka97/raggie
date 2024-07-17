terraform {
  backend "s3" {
    bucket         = "raggie-tf"
    key            = "terraform.tfstate"
    region         = var.region
    dynamodb_table = "raggie-tf-state-lock"
    encrypt        = true
  }
}