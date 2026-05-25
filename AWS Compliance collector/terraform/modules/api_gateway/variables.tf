variable "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function for proxy integration"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function for permission configuration"
  type        = string
}

variable "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool for authorization"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
