resource "aws_iam_role" "ec2_instance_role" {
  name = "raggie_ec2_instance_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "ecr_access_policy" {
  name        = "raggie_ecr_access_policy"
  description = "Policy to allow access to ECR"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_ecr_policy" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = aws_iam_policy.ecr_access_policy.arn

  depends_on = [
    aws_iam_role.ec2_instance_role,
    aws_iam_policy.ecr_access_policy
  ]
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "raggie_ec2_instance_profile"
  role = aws_iam_role.ec2_instance_role.name

  depends_on = [
    aws_iam_role.ec2_instance_role,
    aws_iam_role_policy_attachment.attach_ecr_policy
  ]
}