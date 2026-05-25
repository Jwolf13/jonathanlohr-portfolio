# DVA-C02: CloudWatch monitoring for compliance collector
# Provides visibility into system health, performance, and security posture

# DVA-C02: SNS topic for alarm notifications
resource "aws_sns_topic" "compliance_alarms" {
  name              = "compliance-collector-alarms"
  kms_master_key_id = aws_kms_key.sns.id  # DVA-C02: Encrypt topic at rest

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-alarms"
      Module     = "monitoring"
      Component  = "notifications"
    }
  )
}

# DVA-C02: SNS topic subscription (replace with actual email)
resource "aws_sns_topic_subscription" "compliance_alarms_email" {
  topic_arn = aws_sns_topic.compliance_alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email

  # Confirmation required from email address
}

# DVA-C02: KMS key for SNS encryption
resource "aws_kms_key" "sns" {
  description             = "KMS key for SNS topic encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch to use the key"
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
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
      Name    = "compliance-sns-kms-key"
      Purpose = "sns-encryption"
    }
  )
}

resource "aws_kms_alias" "sns" {
  name          = "alias/compliance-sns-key"
  target_key_id = aws_kms_key.sns.key_id
}

# DVA-C02: CloudWatch Dashboard for compliance metrics
resource "aws_cloudwatch_dashboard" "compliance_collector" {
  dashboard_name = "compliance-collector"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", { stat = "Sum", label = "Lambda Errors" }],
            [".", "Invocations", { stat = "Sum", label = "Lambda Invocations" }],
            [".", "Duration", { stat = "Average", label = "Avg Duration (ms)" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Performance"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        x = 0
        y = 0
        width = 12
        height = 6
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", { stat = "Sum", dimensions = { TableName = var.dynamodb_table_name } }],
            [".", "ConsumedReadCapacityUnits", { stat = "Sum", dimensions = { TableName = var.dynamodb_table_name } }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "DynamoDB Consumed Capacity"
        }
        x = 12
        y = 0
        width = 12
        height = 6
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/S3", "BucketSizeBytes", { stat = "Average", dimensions = { BucketName = var.s3_bucket_name, StorageType = "StandardStorage" } }]
          ]
          period = 86400
          stat   = "Average"
          region = var.aws_region
          title  = "S3 Bucket Size"
        }
        x = 0
        y = 6
        width = 12
        height = 6
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", { stat = "Sum", dimensions = { ApiName = "compliance-api" } }],
            [".", "4XXError", { stat = "Sum", dimensions = { ApiName = "compliance-api" } }],
            [".", "5XXError", { stat = "Sum", dimensions = { ApiName = "compliance-api" } }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "API Gateway Requests"
        }
        x = 12
        y = 6
        width = 12
        height = 6
      }
    ]
  })
}

# DVA-C02: Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "compliance-lambda-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when Lambda function errors exceed 5 in 5 minutes"
  alarm_actions       = [aws_sns_topic.compliance_alarms.arn]
  treat_missing_data  = "notBreaching"

  tags = merge(
    var.common_tags,
    {
      Name       = "lambda-errors-alarm"
      Component  = "monitoring"
    }
  )
}

# DVA-C02: Alarm for Lambda duration (60% of timeout)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "compliance-lambda-duration"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 36000  # 60% of 60 second timeout
  alarm_description   = "Alert when Lambda duration exceeds 60% of timeout"
  alarm_actions       = [aws_sns_topic.compliance_alarms.arn]
  treat_missing_data  = "notBreaching"

  tags = merge(
    var.common_tags,
    {
      Name       = "lambda-duration-alarm"
      Component  = "monitoring"
    }
  )
}

# DVA-C02: Alarm for DynamoDB throttling
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttling" {
  alarm_name          = "compliance-dynamodb-throttling"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alert on DynamoDB throttling"
  alarm_actions       = [aws_sns_topic.compliance_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  tags = merge(
    var.common_tags,
    {
      Name       = "dynamodb-throttling-alarm"
      Component  = "monitoring"
    }
  )
}

# DVA-C02: Alarm for API Gateway 5XX errors
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "compliance-api-5xx-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert on API Gateway 5XX errors"
  alarm_actions       = [aws_sns_topic.compliance_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = "compliance-api"
  }

  tags = merge(
    var.common_tags,
    {
      Name       = "api-5xx-errors-alarm"
      Component  = "monitoring"
    }
  )
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}
