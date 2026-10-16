terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  # LocalStack has no real AWS account, so skip checks that
  # would try to contact real AWS
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3  = var.localstack_endpoint
    iam = var.localstack_endpoint
    sts = var.localstack_endpoint
  }
}

# Deliberately misconfigured test bucket: AWS-managed encryption (not KMS)
# and no Environment tag, so the scanner has real findings to detect.
resource "aws_s3_bucket" "test" {
  bucket = "cloudguard-test-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "test" {
  bucket = aws_s3_bucket.test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Deliberately over-permissive test role so the scanner has an IAM finding
resource "aws_iam_role" "test" {
  name = "cloudguard-test-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "wildcard" {
  name = "wildcard-policy"
  role = aws_iam_role.test.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}