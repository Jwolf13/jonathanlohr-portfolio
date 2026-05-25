output "api_endpoint" {
  description = "Base URL of the API Gateway endpoint"
  value       = "${aws_api_gateway_rest_api.compliance_api.execution_arn}/v1"
}

output "api_id" {
  description = "REST API ID"
  value       = aws_api_gateway_rest_api.compliance_api.id
}

output "stage_name" {
  description = "API Gateway stage name"
  value       = aws_api_gateway_stage.v1.stage_name
}

output "invoke_url" {
  description = "Invoke URL for the API stage"
  value       = aws_api_gateway_stage.v1.invoke_url
}

output "authorizer_id" {
  description = "ID of the Cognito authorizer"
  value       = aws_api_gateway_authorizer.cognito.id
}
