resource "aws_vpc" "raggie_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "Raggie VPC"
  }

}

resource "aws_internet_gateway" "raggie_internet_gateway" {
  vpc_id = aws_vpc.raggie_vpc.id

  tags = {
    Name = "Raggie IGW"
  }

}

resource "aws_subnet" "raggie_public_subnet" {
  vpc_id            = aws_vpc.raggie_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "Raggie Public Subnet"
  }

}

resource "aws_subnet" "raggie_private_subnet" {
  vpc_id            = aws_vpc.raggie_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "Raggie Private Subnet"
  }

}

resource "aws_route_table" "raggie_rt" {
  vpc_id = aws_vpc.raggie_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.raggie_internet_gateway.id
  }

  tags = {
    Name = "Raggie Route Table"
  }

}

resource "aws_route_table_association" "raggie_route_table_association" {
  subnet_id      = aws_subnet.raggie_public_subnet.id
  route_table_id = aws_route_table.raggie_rt.id
}

resource "aws_security_group" "raggie_streamlit_sg" {
  name        = "raggie_streamlit_sg"
  description = "Security group for ECS service"
  vpc_id      = aws_vpc.raggie_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.raggie_vpc.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "raggie_chromadb_sg" {
  vpc_id = aws_vpc.raggie_vpc.id

  ingress {
    protocol        = "tcp"
    from_port       = 8000
    to_port         = 8000
    cidr_blocks     = [aws_subnet.raggie_public_subnet.cidr_block]
    security_groups = [aws_security_group.raggie_streamlit_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Allow Traffic only from public subnet, on port 8000"
  }

}
