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

locals {
  buckets = {
    "cg-prod-app-data"   = { sse = "aws:kms", env = "production", lifecycle = true,  has_object = true }
    "cg-prod-logs"       = { sse = "aws:kms", env = "production", lifecycle = true,  has_object = true }
    "cg-dev-scratch"     = { sse = "AES256",  env = "dev",        lifecycle = false, has_object = true }
    "cg-untagged-legacy" = { sse = "AES256",  env = null,         lifecycle = false, has_object = true }
    "cg-orphan-empty"    = { sse = "AES256",  env = "staging",    lifecycle = true,  has_object = false }
  }

  roles = {
    "cg-admin-legacy" = { action = "*",             resource = "*" }
    "cg-app-reader"   = { action = "s3:GetObject",  resource = "arn:aws:s3:::cg-prod-app-data/*" }
    "cg-log-writer"   = { action = "s3:PutObject",  resource = "arn:aws:s3:::cg-prod-logs/*" }
  }
}

resource "aws_s3_bucket" "this" {
  for_each = local.buckets
  bucket   = each.key
  tags     = each.value.env == null ? {} : { Environment = each.value.env }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.this[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = each.value.sse
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  for_each = { for k, v in local.buckets : k => v if v.lifecycle }
  bucket   = aws_s3_bucket.this[each.key].id

  rule {
    id     = "expire-old-data"
    status = "Enabled"
    filter {}
    expiration {
      days = 90
    }
  }
}

resource "aws_s3_object" "sample" {
  for_each = { for k, v in local.buckets : k => v if v.has_object }
  bucket   = aws_s3_bucket.this[each.key].id
  key      = "sample.txt"
  content  = "demo data"
}

resource "aws_iam_role" "this" {
  for_each = local.roles
  name     = each.key

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "this" {
  for_each = local.roles
  name     = "inline-policy"
  role     = aws_iam_role.this[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = each.value.action
      Resource = each.value.resource
    }]
  })
}