variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "account_id" {
  description = "AWS account ID for resource naming and permissions"
  type        = string
  validation {
    condition     = can(regex("^\\d{12}$", var.account_id))
    error_message = "Account ID must be a 12-digit number"
  }
}

variable "cognito_callback_urls" {
  description = "Allowed callback URLs for Cognito OAuth redirects"
  type        = list(string)
  default     = ["http://localhost:3000/callback"]
}

variable "cognito_logout_urls" {
  description = "Allowed logout URLs for Cognito OAuth logout flow"
  type        = list(string)
  default     = ["http://localhost:3000/logout"]
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alarm_email))
    error_message = "Alarm email must be a valid email address"
  }
}

variable "compliance_scan_schedule" {
  description = "EventBridge schedule expression for compliance scans"
  type        = string
  default     = "rate(6 hours)"
}

variable "lambda_function_zip_path" {
  description = "Path to the Lambda function ZIP file or S3 location"
  type        = string
  default     = null
}

variable "lambda_layer_arns" {
  description = "ARNs of Lambda layers to attach to functions"
  type        = list(string)
  default     = []
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "compliance-collector"
    CreatedBy = "terraform"
  }
}
