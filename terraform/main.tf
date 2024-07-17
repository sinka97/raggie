# Launch an ebs volumn in the available zone
resource "aws_ebs_volume" "raggie_ebs_volume" {
  availability_zone = "us-east-1a"
  size              = 20 # Specify the size of the volume in GiB
  tags = {
    Name = "raggie-ebs-volume"
  }
}

# Launch an EC2 instance in the subnet to run chromadb
resource "aws_instance" "raggie_chromadb" {
  ami                         = "ami-0b72821e2f351e396"
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.raggie_private_subnet.id
  vpc_security_group_ids      = [aws_security_group.raggie_chromadb_sg.id]
  availability_zone           = "us-east-1a"
  ebs_block_device {
    device_name = "/dev/sdh"
    volume_size = 30
  }
  user_data                   = <<-EOF
    #!/bin/bash

    # Create a directory to mount the volume
    sudo mkdir -p /mnt/chroma-storage
    
    # Check if the volume is already formatted
    if ! file -s /dev/sdh | grep -q ext4; then
      # Format the EBS volume
      sudo mkfs -t ext4 /dev/sdh
    fi
    
    # Mount the volume
    sudo mount /dev/sdh /mnt/chroma-storage

    # Install docker
    sudo yum update -y
    sudo yum install docker -y
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ec2-user
    newgrp docker

    # Run the Docker container
    docker run \
    -p 8000:8000 \
    -v /mnt/chroma-storage:/chroma/chroma \
    chromadb/chroma
  EOF
  user_data_replace_on_change = true
  tags = {
    Name = "Raggie_ChromaDB_Instance"
  }
}


resource "aws_instance" "raggie_streamlit" {
  ami                  = "ami-0b72821e2f351e396"
  instance_type        = "m5.xlarge"
  subnet_id            = aws_subnet.raggie_public_subnet.id
  iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name
  security_groups      = [aws_security_group.raggie_streamlit_sg.id]
  availability_zone    = "us-east-1a"
  ebs_block_device {
    device_name = "/dev/sdg"
    volume_size = 20
  }
  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install docker -y
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -a -G docker ec2-user
              newgrp docker
              aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 021041863094.dkr.ecr.us-east-1.amazonaws.com
              docker image pull 021041863094.dkr.ecr.us-east-1.amazonaws.com/raggie:latest
              docker run -p 8501:8501 -d 021041863094.dkr.ecr.us-east-1.amazonaws.com/raggie:latest
              EOF
  user_data_replace_on_change = true
  tags = {
    Name = "Raggie_Streamlit_Instance"
  }
  depends_on = [
    aws_instance.raggie_chromadb,
    aws_security_group.raggie_streamlit_sg,
    aws_iam_instance_profile.ec2_instance_profile
  ]
}

resource "aws_eip" "raggie_streamlit_eip" {
  instance = aws_instance.raggie_streamlit.id
  domain   = "vpc"

  depends_on = [
    aws_internet_gateway.raggie_internet_gateway
  ]

}