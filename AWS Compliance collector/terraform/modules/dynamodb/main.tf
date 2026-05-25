# DVA-C02: DynamoDB single-table design for compliance evidence storage
# Single table pattern reduces complexity and improves query performance
# All entities use hierarchical partition and sort keys for flexible querying

resource "aws_dynamodb_table" "compliance_data" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"  # DVA-C02: Pay-per-request for unpredictable workloads
  hash_key       = "PK"
  range_key      = "SK"

  stream_specification {
    stream_view_type = "NEW_AND_OLD_IMAGES"  # DVA-C02: Required for drift detection
  }

  # DVA-C02: Primary key design for single-table pattern
  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # DVA-C02: GSI1 for querying by control family
  # Example: PK=FAMILY#SOC2, SK=CONTROL#ID#version
  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  global_secondary_index {
    name            = "ByFamily"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"  # DVA-C02: Include all attributes to avoid additional queries
  }

  # DVA-C02: GSI2 for querying by severity level
  # Example: PK=SEVERITY#CRITICAL, SK=CONTROL#ID#timestamp
  attribute {
    name = "GSI2PK"
    type = "S"
  }

  attribute {
    name = "GSI2SK"
    type = "S"
  }

  global_secondary_index {
    name            = "BySeverity"
    hash_key        = "GSI2PK"
    range_key       = "GSI2SK"
    projection_type = "ALL"
  }

  # DVA-C02: TTL for automatic cleanup of expired compliance data
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # DVA-C02: KMS encryption at rest using AWS managed keys
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  # DVA-C02: Point-in-time recovery for disaster recovery capability
  point_in_time_recovery_specification {
    point_in_time_recovery_enabled = true
  }

  tags = merge(
    var.common_tags,
    {
      Name       = var.table_name
      Module     = "dynamodb"
      Component  = "data-store"
    }
  )
}

# DVA-C02: KMS key for DynamoDB encryption
# Separate key allows granular access control and rotation policies
resource "aws_kms_key" "dynamodb" {
  description             = "KMS key for DynamoDB ComplianceData table encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true  # DVA-C02: Automatic key rotation

  tags = merge(
    var.common_tags,
    {
      Name      = "${var.table_name}-kms-key"
      Purpose   = "dynamodb-encryption"
    }
  )
}

resource "aws_kms_alias" "dynamodb" {
  name          = "alias/${var.table_name}-key"
  target_key_id = aws_kms_key.dynamodb.key_id
}
