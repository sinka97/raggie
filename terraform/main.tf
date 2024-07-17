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

# ECS Resources
resource "aws_ecs_cluster" "raggie_cluster" {
  name = var.ecs_cluster_name
}

resource "aws_ecs_task_definition" "raggie_ecs_task" {
  family                   = "raggie-task-family"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_agent.arn
  cpu                      = var.cpu
  memory                   = var.memory

  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = "021041863094.dkr.ecr.us-east-1.amazonaws.com/raggie:latest"
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
          value = aws_instance.raggie-chromadb.private_ip
        }
      ]
    }
  ])
}

resource "aws_lb" "raggie_alb" {
  name               = "raggie-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.raggie_ecs_sg.id]
  subnets            = [aws_subnet.raggie_public_subnet.id,aws_subnet.raggie_public_subnet_b.id]
}

resource "aws_lb_target_group" "raggie_target_group" {
  name     = "raggie-target-group"
  port     = var.container_port
  protocol = "HTTP"
  vpc_id   = aws_vpc.raggie_vpc.id
  target_type = "ip"

  health_check {
    path                = "/"
    protocol            = "HTTP"
    timeout             = 5
    interval            = 30
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = "200-399"
  }
}

resource "aws_lb_listener" "raggie_listener" {
  load_balancer_arn = aws_lb.raggie_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.raggie_target_group.arn
  }
}

resource "aws_ecs_service" "raggie_ecs_service" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.raggie_cluster.id
  task_definition = aws_ecs_task_definition.raggie_ecs_task.arn
  desired_count   = 2         # Number of tasks to run
  launch_type     = "FARGATE" # Or "EC2" if using EC2

  network_configuration {
    subnets          = [aws_subnet.raggie_public_subnet.id,aws_subnet.raggie_public_subnet_b.id]
    security_groups  = [aws_security_group.raggie_ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.raggie_target_group.arn
    container_name   = var.container_name
    container_port   = var.container_port
  }

}