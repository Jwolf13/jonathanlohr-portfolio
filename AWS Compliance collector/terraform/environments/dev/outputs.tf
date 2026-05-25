output "api_endpoint_url" {
  description = "Base URL for the Compliance API"
  value       = module.api_gateway.invoke_url
  sensitive   = false
}

output "api_id" {
  description = "API Gateway REST API ID"
  value       = module.api_gateway.api_id
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for compliance evidence storage"
  value       = module.storage.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for compliance evidence"
  value       = module.storage.bucket_arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for compliance data"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.dynamodb.table_arn
}

output "dynamodb_stream_arn" {
  description = "ARN of the DynamoDB Streams for drift detection"
  value       = module.dynamodb.stream_arn
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = module.cognito.user_pool_arn
}

output "cognito_client_id" {
  description = "Client ID for the Compliance Dashboard SPA"
  value       = module.cognito.client_id
  sensitive   = false
}

output "cognito_hosted_ui_domain" {
  description = "Domain URL for Cognito Hosted UI (login page)"
  value       = module.cognito.hosted_ui_domain
}

output "lambda_function_arn" {
  description = "ARN of the compliance collector Lambda function"
  value       = module.compliance_collector_lambda.function_arn
}

output "lambda_function_name" {
  description = "Name of the compliance collector Lambda function"
  value       = module.compliance_collector_lambda.function_name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.compliance_collector_lambda.role_arn
}

output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard for monitoring"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${module.monitoring.dashboard_name}"
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = module.monitoring.sns_topic_arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic"
  value       = module.monitoring.sns_topic_name
}

output "eventbridge_scan_schedule_arn" {
  description = "ARN of the scheduled compliance scan EventBridge rule"
  value       = module.eventbridge.scan_schedule_rule_arn
}

output "eventbridge_config_change_rule_arn" {
  description = "ARN of the AWS Config change detection EventBridge rule"
  value       = module.eventbridge.config_change_rule_arn
}

output "deployment_summary" {
  description = "Summary of deployment endpoints and credentials"
  value = {
    api_endpoint          = module.api_gateway.invoke_url
    cognito_pool_id       = module.cognito.user_pool_id
    cognito_client_id     = module.cognito.client_id
    login_page            = module.cognito.hosted_ui_domain
    dynamodb_table        = module.dynamodb.table_name
    s3_bucket             = module.storage.bucket_name
    cloudwatch_dashboard  = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${module.monitoring.dashboard_name}"
    region                = var.aws_region
    environment           = var.environment
  }
}
