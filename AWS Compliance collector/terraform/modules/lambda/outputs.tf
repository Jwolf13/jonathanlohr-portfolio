output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.compliance_function.arn
}

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.compliance_function.function_name
}

output "role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_role.name
}

output "log_group_name" {
  description = "Name of the CloudWatch log group for Lambda"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "invoke_arn" {
  description = "ARN to invoke the Lambda function (for use with EventBridge, API Gateway, etc.)"
  value       = aws_lambda_function.compliance_function.invoke_arn
}
