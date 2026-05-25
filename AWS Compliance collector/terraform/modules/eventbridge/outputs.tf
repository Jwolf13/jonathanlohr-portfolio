output "scan_schedule_rule_arn" {
  description = "ARN of the compliance scan schedule rule"
  value       = aws_cloudwatch_event_rule.compliance_scan_schedule.arn
}

output "scan_schedule_rule_name" {
  description = "Name of the compliance scan schedule rule"
  value       = aws_cloudwatch_event_rule.compliance_scan_schedule.name
}

output "config_change_rule_arn" {
  description = "ARN of the AWS Config change detection rule"
  value       = aws_cloudwatch_event_rule.config_change_rule.arn
}

output "config_change_rule_name" {
  description = "Name of the AWS Config change detection rule"
  value       = aws_cloudwatch_event_rule.config_change_rule.name
}

output "dlq_arn" {
  description = "ARN of the EventBridge dead letter queue (if created)"
  value       = var.create_dlq ? aws_sqs_queue.eventbridge_dlq[0].arn : null
}

output "dlq_url" {
  description = "URL of the EventBridge dead letter queue (if created)"
  value       = var.create_dlq ? aws_sqs_queue.eventbridge_dlq[0].url : null
}
