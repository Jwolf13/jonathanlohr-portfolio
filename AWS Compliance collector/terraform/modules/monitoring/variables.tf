variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "alarm_email" {
  description = "Email address for SNS alarm notifications"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB compliance data table"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 compliance evidence bucket"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
