terraform {
  backend "s3" {
    bucket         = "raggie-tf"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "raggie-tf-state-lock"
    encrypt        = true
  }
}


provider "aws" {
  region = "us-east-1" # Update with your desired AWS region
}

# Create VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "raggie-vpc"
  }
}

# Create an internet gateway for the VPC
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "raggie-igw"
  }
}

# Create a route table for public subnet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "raggie-public-rt"
  }
}

# Create a subnet within the VPC
resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a" # Update with an available AZ in your region

  tags = {
    Name = "raggie-public-subnet"
  }
}

# Associate the route table with the subnet
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Create a security group
resource "aws_security_group" "instance_sg" {
  name        = "raggie-instance-sg"
  description = "Allow SSH and HTTP inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Launch an EC2 instance in the subnet
resource "aws_instance" "raggie-test" {
  ami                    = "ami-0b72821e2f351e396"
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.instance_sg.id]

  tags = {
    Name = "raggie-test"
  }
}
