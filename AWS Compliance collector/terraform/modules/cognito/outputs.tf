output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.compliance_dashboard.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.compliance_dashboard.arn
}

output "client_id" {
  description = "ID of the Cognito User Pool Client (SPA)"
  value       = aws_cognito_user_pool_client.dashboard_spa.client_id
}

output "user_pool_domain" {
  description = "Domain of the Cognito User Pool"
  value       = aws_cognito_user_pool_domain.compliance.domain
}

output "hosted_ui_domain" {
  description = "Full domain URL for Cognito Hosted UI"
  value       = "https://${aws_cognito_user_pool_domain.compliance.domain}.auth.${data.aws_caller_identity.current.region}.amazoncognito.com"
}

output "resource_server_id" {
  description = "ID of the Compliance API resource server"
  value       = aws_cognito_resource_server.compliance_api.identifier
}

# Data source to get current AWS region
data "aws_caller_identity" "current" {}
