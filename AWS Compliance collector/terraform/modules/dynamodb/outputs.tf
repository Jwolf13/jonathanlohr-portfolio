output "table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.compliance_data.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.compliance_data.arn
}

output "stream_arn" {
  description = "ARN of the DynamoDB Streams"
  value       = aws_dynamodb_table.compliance_data.stream_arn
}

output "kms_key_id" {
  description = "ID of the KMS key used for table encryption"
  value       = aws_kms_key.dynamodb.id
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for table encryption"
  value       = aws_kms_key.dynamodb.arn
}
