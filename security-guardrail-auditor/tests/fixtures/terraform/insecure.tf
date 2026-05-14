resource "aws_s3_bucket" "wide" {
  bucket = "wide-open"
  acl    = "public-read"
}

resource "aws_security_group" "bad" {
  name = "bad-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "db" {
  identifier          = "demo-db"
  publicly_accessible = true
  storage_encrypted   = false
}

resource "aws_instance" "web" {
  ami                         = "ami-12345"
  instance_type               = "t3.micro"
  associate_public_ip_address = true
}

resource "aws_iam_policy" "admin" {
  name = "too-open"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

# Intentional insecure pattern for scanner tests
variable "db_password" {
  default = "not-used"
}

resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 10
  encrypted         = false
}
