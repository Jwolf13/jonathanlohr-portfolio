# DVA-C02: S3 bucket for storing compliance evidence artifacts
# Implements defense-in-depth with encryption, versioning, and access controls

resource "aws_s3_bucket" "compliance_evidence" {
  bucket = "compliance-evidence-${var.account_id}-${var.environment}"

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-evidence-${var.environment}"
      Module     = "storage"
      Component  = "evidence-storage"
    }
  )
}

# DVA-C02: Block all public access to prevent unauthorized exposure
resource "aws_s3_bucket_public_access_block" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DVA-C02: Enable versioning for compliance audit trail
# Maintains version history for drift detection and forensics
resource "aws_s3_bucket_versioning" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  versioning_configuration {
    status = "Enabled"
  }
}

# DVA-C02: Server-side encryption with KMS
# Protects data at rest with customer-managed keys
resource "aws_s3_bucket_server_side_encryption_configuration" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true  # DVA-C02: Reduces KMS API calls and costs
  }
}

# DVA-C02: KMS key for S3 bucket encryption
resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 compliance evidence bucket encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true  # DVA-C02: Automatic key rotation

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow S3 to use the key"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name    = "compliance-s3-kms-key"
      Purpose = "s3-encryption"
    }
  )
}

resource "aws_kms_alias" "s3" {
  name          = "alias/compliance-evidence-key"
  target_key_id = aws_kms_key.s3.key_id
}

# DVA-C02: Bucket policy enforcing SSL/TLS for data in transit
resource "aws_s3_bucket_policy" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.compliance_evidence.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      },
      {
        Sid    = "DenyInsecureTransport"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.compliance_evidence.arn,
          "${aws_s3_bucket.compliance_evidence.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# DVA-C02: Lifecycle rules for cost optimization
# Tiered storage: Standard -> Intelligent Tiering -> Glacier -> Deep Archive
resource "aws_s3_bucket_lifecycle_configuration" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  rule {
    id     = "archive-old-evidence"
    status = "Enabled"

    filter {
      prefix = "evidence/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"  # Move to Infrequent Access after 90 days
    }

    transition {
      days          = 365
      storage_class = "GLACIER_IR"  # Move to Glacier Instant Retrieval after 1 year
    }

    transition {
      days          = 2555  # ~7 years
      storage_class = "DEEP_ARCHIVE"  # Move to Deep Archive after 7 years
    }

    # Keep non-current versions for compliance audit trail
    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 365
      storage_class   = "GLACIER_IR"
    }

    noncurrent_version_expiration {
      noncurrent_days = 2555  # Delete non-current versions after 7 years
    }
  }
}

# DVA-C02: Enable bucket logging for audit trail
resource "aws_s3_bucket_logging" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "compliance-evidence-logs/"
}

# Logging bucket
resource "aws_s3_bucket" "access_logs" {
  bucket = "compliance-evidence-logs-${var.account_id}-${var.environment}"

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-evidence-logs-${var.environment}"
      Module     = "storage"
      Component  = "logging"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle for logs to reduce storage costs
resource "aws_s3_bucket_lifecycle_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    id     = "delete-old-logs"
    status = "Enabled"

    expiration {
      days = 90  # Delete logs after 90 days
    }
  }
}
