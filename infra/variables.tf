variable "localstack_endpoint" {
  type        = string
  description = "LocalStack edge endpoint"
}

variable "aws_access_key" {
  type      = string
  sensitive = true
}

variable "aws_secret_key" {
  type      = string
  sensitive = true
}