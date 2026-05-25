output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.compliance_collector.dashboard_name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = aws_sns_topic.compliance_alarms.arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic"
  value       = aws_sns_topic.compliance_alarms.name
}

output "lambda_errors_alarm_arn" {
  description = "ARN of the Lambda errors alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_errors.arn
}

output "lambda_duration_alarm_arn" {
  description = "ARN of the Lambda duration alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_duration.arn
}

output "dynamodb_throttling_alarm_arn" {
  description = "ARN of the DynamoDB throttling alarm"
  value       = aws_cloudwatch_metric_alarm.dynamodb_throttling.arn
}

output "api_5xx_errors_alarm_arn" {
  description = "ARN of the API Gateway 5XX errors alarm"
  value       = aws_cloudwatch_metric_alarm.api_5xx_errors.arn
}

output "kms_key_id" {
  description = "ID of the KMS key for SNS encryption"
  value       = aws_kms_key.sns.id
}
