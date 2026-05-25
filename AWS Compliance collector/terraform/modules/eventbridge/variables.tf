variable "collector_lambda_arn" {
  description = "ARN of the compliance collector Lambda function"
  type        = string
}

variable "collector_lambda_name" {
  description = "Name of the compliance collector Lambda function"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
}

variable "dead_letter_queue_arn" {
  description = "ARN of SQS queue for dead letter handling"
  type        = string
  default     = ""
}

variable "create_dlq" {
  description = "Whether to create a dead letter queue for EventBridge"
  type        = bool
  default     = true
}

variable "schedule_expression" {
  description = "Schedule expression for compliance scan (e.g., 'rate(6 hours)')"
  type        = string
  default     = "rate(6 hours)"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
