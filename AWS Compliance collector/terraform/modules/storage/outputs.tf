output "bucket_name" {
  description = "Name of the S3 compliance evidence bucket"
  value       = aws_s3_bucket.compliance_evidence.id
}

output "bucket_arn" {
  description = "ARN of the S3 compliance evidence bucket"
  value       = aws_s3_bucket.compliance_evidence.arn
}

output "bucket_region" {
  description = "AWS region where the bucket is located"
  value       = aws_s3_bucket.compliance_evidence.region
}

output "logs_bucket_name" {
  description = "Name of the S3 access logs bucket"
  value       = aws_s3_bucket.access_logs.id
}

output "kms_key_id" {
  description = "ID of the KMS key used for S3 encryption"
  value       = aws_kms_key.s3.id
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for S3 encryption"
  value       = aws_kms_key.s3.arn
}
