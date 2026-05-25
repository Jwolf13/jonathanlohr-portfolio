# DVA-C02: Reusable Lambda module for compliance collector functions
# Implements least-privilege IAM, encryption, monitoring, and X-Ray tracing

# DVA-C02: Lambda execution role with least-privilege permissions
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name       = "${var.function_name}-role"
      Component  = "iam-role"
    }
  )
}

# DVA-C02: CloudWatch Logs policy - required for all Lambda functions
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "${var.function_name}-cloudwatch-logs"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CreateLogGroup"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.function_name}:*"
      }
    ]
  })
}

# DVA-C02: X-Ray write access for distributed tracing
resource "aws_iam_role_policy" "xray_write" {
  name = "${var.function_name}-xray-write"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "WriteXRayTrace"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# DVA-C02: Custom IAM policy for function-specific permissions
# Passed as variable to maintain modularity
resource "aws_iam_role_policy" "lambda_custom" {
  count = var.iam_policy_json != null ? 1 : 0
  name  = "${var.function_name}-custom-policy"
  role  = aws_iam_role.lambda_role.id

  policy = var.iam_policy_json
}

# DVA-C02: CloudWatch Log Group with retention policy
# Prevents log storage costs from growing indefinitely
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14  # DVA-C02: Balance between retention and cost

  tags = merge(
    var.common_tags,
    {
      Name       = "${var.function_name}-logs"
      Component  = "monitoring"
    }
  )
}

# DVA-C02: Lambda function with security best practices
resource "aws_lambda_function" "compliance_function" {
  filename         = var.filename != null ? var.filename : null
  s3_bucket        = var.s3_bucket != null ? var.s3_bucket : null
  s3_key           = var.s3_key != null ? var.s3_key : null
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = var.handler
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size
  architectures    = ["arm64"]  # DVA-C02: Graviton for cost optimization

  # DVA-C02: Environment variables for configuration
  environment {
    variables = var.environment_variables
  }

  # DVA-C02: X-Ray tracing enabled for observability
  tracing_config {
    mode = "Active"
  }

  # DVA-C02: Lambda with VPC support for private resource access
  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  # DVA-C02: Container image support as alternative to ZIP
  dynamic "image_config" {
    for_each = var.image_config != null ? [var.image_config] : []
    content {
      entry_point       = image_config.value.entry_point
      command           = image_config.value.command
      working_directory = image_config.value.working_directory
    }
  }

  # DVA-C02: Specify layers for shared code
  dynamic "layers" {
    for_each = var.layers != null ? var.layers : []
    content {
      arn = layers.value
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
    aws_iam_role_policy.cloudwatch_logs,
    aws_iam_role_policy.xray_write
  ]

  tags = merge(
    var.common_tags,
    {
      Name       = var.function_name
      Module     = "lambda"
      Component  = "compute"
    }
  )
}

# DVA-C02: Lambda version for deployment safety
resource "aws_lambda_function_event_invoke_config" "compliance_function" {
  function_name       = aws_lambda_function.compliance_function.function_name
  maximum_event_age   = 3600  # DVA-C02: Reject events older than 1 hour
  maximum_retry_attempts = 0  # DVA-C02: No retries for event processing

  dead_letter_config {
    target_arn = var.dead_letter_queue_arn != null ? var.dead_letter_queue_arn : null
  }
}
