# Launch an ebs volumn in the available zone
resource "aws_ebs_volume" "raggie_ebs_volume" {
  availability_zone = "us-east-1a"
  size              = 20 # Specify the size of the volume in GiB
  tags = {
    Name = "raggie-ebs-volume"
  }
}

# Launch an EC2 instance in the subnet to run chromadb
resource "aws_instance" "raggie-chromadb" {
  ami                    = "ami-0b72821e2f351e396"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.raggie_public_subnet.id
  vpc_security_group_ids = [aws_security_group.raggie_chromadb_sg.id]
  availability_zone      = "us-east-1a"
  tags = {
    Name = "raggie-chromadb"
  }
  user_data                   = <<-EOF
    #!/bin/bash

    # Create a directory to mount the volume
    mkdir -p /mnt/chroma-storage
    
    # Check if the volume is already formatted
    if ! file -s /dev/sdh | grep -q ext4; then
      # Format the EBS volume
      mkfs -t ext4 /dev/sdh
    fi
    
    # Mount the volume
    mount /dev/sdh /mnt/chroma-storage
    
    # Ensure the volume mounts on reboot
    if ! grep -qs '/mnt/chroma-storage' /etc/fstab; then
      echo '/dev/sdh /mnt/chroma-storage ext4 defaults,nofail 0 2' >> /etc/fstab
    fi
    
    # Install Docker
    amazon-linux-extras install docker -y
    service docker start
    usermod -a -G docker ec2-user

    # Run the Docker container
    docker run \
    -p 8000:8000 \
    -v /mnt/chroma-storage:/chroma/chroma \
    chromadb/chroma
  EOF
  user_data_replace_on_change = true
}

# Attach the EBS volume to the EC2 instance
resource "aws_volume_attachment" "raggie_ebs_attachment" {
  device_name = "/dev/sdh" # Specify the device name
  volume_id   = aws_ebs_volume.raggie_ebs_volume.id
  instance_id = aws_instance.raggie-chromadb.id
}


resource "aws_ecs_task_definition" "my_task" {
  family                   = "my-task-family"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  cpu                      = var.cpu
  memory                   = var.memory

  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = "${aws_account_id}.dkr.ecr.${var.region}.amazonaws.com/${var.ecr_repo_name}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
        }
      ]
      environment = [
        {
          name  = "DB_HOST"
          value = aws_instance.db_instance.private_ip
        },
        {
          name  = "DB_NAME"
          value = var.db_name
        },
        {
          name  = "DB_USERNAME"
          value = var.db_username
        },
        {
          name  = "DB_PASSWORD"
          value = var.db_password
        }
      ]
    }
  ])
}