variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "handler" {
  description = "Lambda function handler (e.g., index.handler)"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime (e.g., python3.11, nodejs18.x)"
  type        = string
}

variable "memory_size" {
  description = "Memory allocation for Lambda function in MB"
  type        = number
  default     = 256
  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 and 10240 MB."
  }
}

variable "timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "iam_policy_json" {
  description = "JSON policy document for Lambda execution role (additional permissions)"
  type        = string
  default     = null
}

variable "filename" {
  description = "Path to ZIP file for function code"
  type        = string
  default     = null
}

variable "s3_bucket" {
  description = "S3 bucket containing function code"
  type        = string
  default     = null
}

variable "s3_key" {
  description = "S3 key for function code"
  type        = string
  default     = null
}

variable "layers" {
  description = "Lambda layer ARNs to attach to function"
  type        = list(string)
  default     = []
}

variable "vpc_config" {
  description = "VPC configuration for Lambda function"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "image_config" {
  description = "Configuration for container image function"
  type = object({
    entry_point       = list(string)
    command           = list(string)
    working_directory = string
  })
  default = null
}

variable "dead_letter_queue_arn" {
  description = "ARN of SQS queue or SNS topic for failed events"
  type        = string
  default     = null
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
