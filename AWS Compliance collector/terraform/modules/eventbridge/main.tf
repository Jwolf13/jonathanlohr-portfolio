# DVA-C02: EventBridge rules for compliance collector event-driven architecture
# Enables automated compliance scanning and real-time drift detection

# DVA-C02: Scheduled rule for periodic compliance scans
# Runs every 6 hours to collect compliance evidence across AWS environment
resource "aws_cloudwatch_event_rule" "compliance_scan_schedule" {
  name                = "compliance-scan-schedule"
  description         = "Scheduled rule to trigger compliance evidence collection every 6 hours"
  schedule_expression = "rate(6 hours)"
  is_enabled          = true

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-scan-schedule"
      Module     = "eventbridge"
      Component  = "scheduling"
    }
  )
}

# DVA-C02: EventBridge target for scheduled compliance scans
resource "aws_cloudwatch_event_target" "compliance_scan_lambda" {
  rule      = aws_cloudwatch_event_rule.compliance_scan_schedule.name
  target_id = "ComplianceScanCollector"
  arn       = var.collector_lambda_arn

  # DVA-C02: Pass custom event data to Lambda
  input = jsonencode({
    source      = "eventbridge"
    trigger     = "scheduled-scan"
    timestamp   = "$.time"
    region      = var.aws_region
  })
}

# DVA-C02: Lambda permission to allow EventBridge invocation
resource "aws_lambda_permission" "allow_eventbridge_scan" {
  statement_id  = "AllowExecutionFromEventBridgeScan"
  action        = "lambda:InvokeFunction"
  function_name = var.collector_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.compliance_scan_schedule.arn
}

# DVA-C02: Event rule for AWS Config compliance changes
# Triggers real-time response to compliance state changes
resource "aws_cloudwatch_event_rule" "config_change_rule" {
  name        = "config-change-rule"
  description = "Event rule to detect AWS Config compliance changes"
  is_enabled  = true

  # DVA-C02: Match Config compliance change events
  event_pattern = jsonencode({
    source      = ["aws.config"]
    detail-type = ["Config Rules – Compliance Change", "Config Rules – State Change"]
    detail = {
      newEvaluationResult = {
        complianceType = [
          "NON_COMPLIANT",
          "COMPLIANT"
        ]
      }
    }
  })

  tags = merge(
    var.common_tags,
    {
      Name       = "config-change-rule"
      Module     = "eventbridge"
      Component  = "event-matching"
    }
  )
}

# DVA-C02: EventBridge target for Config compliance changes
resource "aws_cloudwatch_event_target" "config_change_lambda" {
  rule      = aws_cloudwatch_event_rule.config_change_rule.name
  target_id = "ComplianceChangeHandler"
  arn       = var.collector_lambda_arn

  # DVA-C02: Enrich event with metadata for Lambda processing
  input_transformer {
    input_paths = {
      rule          = "$.detail.configRuleName"
      compliance    = "$.detail.newEvaluationResult.complianceType"
      resource      = "$.detail.configRuleInvokingEvent.configurationItem.resourceId"
      resource_type = "$.detail.configRuleInvokingEvent.configurationItem.resourceType"
    }
    input_template = jsonencode({
      source        = "aws.config"
      trigger       = "compliance-change"
      configRule    = "<rule>"
      compliance    = "<compliance>"
      resourceId    = "<resource>"
      resourceType  = "<resource_type>"
      timestamp     = "$.time"
      region        = var.aws_region
    })
  }

  dead_letter_config {
    arn = var.dead_letter_queue_arn
  }
}

# DVA-C02: Lambda permission to allow EventBridge Config invocation
resource "aws_lambda_permission" "allow_eventbridge_config" {
  statement_id  = "AllowExecutionFromEventBridgeConfig"
  action        = "lambda:InvokeFunction"
  function_name = var.collector_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.config_change_rule.arn
}

# DVA-C02: Dead letter queue for failed events (optional SQS queue)
resource "aws_sqs_queue" "eventbridge_dlq" {
  count                    = var.create_dlq ? 1 : 0
  name                     = "${var.collector_lambda_name}-eventbridge-dlq"
  message_retention_period = 86400  # 24 hours

  tags = merge(
    var.common_tags,
    {
      Name       = "${var.collector_lambda_name}-dlq"
      Module     = "eventbridge"
      Component  = "dlq"
    }
  )
}
