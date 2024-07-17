variable "region" {
    description = "The AWS region for deployment"
    type = string
    default = "us-east-1"
}

variable "ecr_repo_name" {
  description = "The name of the ECR repository"
  type        = string
  default     = "raggie"
}

variable "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  type        = string
  default     = "raggie-streamlit-app-cluster"
}

variable "service_name" {
  description = "The name of the ECS service"
  type        = string
  default     = "raggie-ecs-service"
}

variable "container_name" {
  description = "The name of the container"
  type        = string
  default     = "raggie-container"
}

variable "container_port" {
  description = "The port on which the container listens"
  type        = number
  default     = 80
}

variable "desired_count" {
  description = "The number of tasks desired"
  type        = number
  default     = 2
}

variable "cpu" {
  description = "The number of CPU units to reserve for the container"
  type        = number
  default     = 256
}

variable "memory" {
  description = "The amount of memory (in MiB) to reserve for the container"
  type        = number
  default     = 512
}

variable "chromadb_instance_type" {
  description = "The instance type for the database"
  type        = string
  default     = "t3.micro"
}

# variable "vpc_id" {
#   description = "The ID of the VPC"
#   type        = string
#   default     = "vpc-12345678"
# }

# variable "subnet_ids" {
#   description = "The IDs of the subnets"
#   type        = list(string)
#   default     = ["subnet-12345678", "subnet-23456789"]
# }