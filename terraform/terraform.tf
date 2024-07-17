terraform {
  backend "s3" {
    bucket         = "raggie-tf"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "raggie-tf-state-lock"
    encrypt        = true
  }
}