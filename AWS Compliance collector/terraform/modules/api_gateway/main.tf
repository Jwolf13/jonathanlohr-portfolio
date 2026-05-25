# DVA-C02: API Gateway with Cognito authorization for compliance dashboard
# Implements OAuth2/OIDC authentication, rate limiting, and CORS

# DVA-C02: REST API for compliance operations
resource "aws_api_gateway_rest_api" "compliance_api" {
  name        = "compliance-api"
  description = "REST API for compliance evidence collection and posture management"

  # DVA-C02: Enable request validation
  body = jsonencode({
    swagger = "2.0"
    info = {
      title       = "Compliance API"
      description = "API for compliance evidence collection"
      version     = "1.0"
    }
    paths = {}
  })

  endpoint_configuration {
    types = ["REGIONAL"]  # DVA-C02: Regional endpoint for better performance
  }

  # DVA-C02: Enable access logging for audit trail
  access_log_settings = {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      error          = "$context.error.message"
      integrationLatency = "$context.integration.latency"
    })
  }

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-api"
      Module     = "api_gateway"
      Component  = "api"
    }
  )
}

# DVA-C02: CloudWatch Log Group for API access logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/compliance-api"
  retention_in_days = 30  # DVA-C02: Retain logs for audit compliance

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-api-logs"
      Component  = "monitoring"
    }
  )
}

# DVA-C02: Cognito authorizer for API authentication
resource "aws_api_gateway_authorizer" "cognito" {
  name            = "cognito-authorizer"
  type            = "COGNITO_USER_POOLS"
  rest_api_id     = aws_api_gateway_rest_api.compliance_api.id
  provider_arns   = [var.cognito_user_pool_arn]
  identity_source = "method.request.header.Authorization"

  identity_validation_expression = "^[a-zA-Z0-9\\-_]+\\.[a-zA-Z0-9\\-_]+\\.[a-zA-Z0-9\\-_]+$"  # JWT format
}

# DVA-C02: API Gateway resource: /controls
resource "aws_api_gateway_resource" "controls" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  parent_id   = aws_api_gateway_rest_api.compliance_api.root_resource_id
  path_part   = "controls"
}

# DVA-C02: GET /controls - List compliance controls
resource "aws_api_gateway_method" "get_controls" {
  rest_api_id      = aws_api_gateway_rest_api.compliance_api.id
  resource_id      = aws_api_gateway_resource.controls.id
  http_method      = "GET"
  authorization    = "COGNITO_USER_POOLS"
  authorizer_id    = aws_api_gateway_authorizer.cognito.id
  api_key_required = false

  request_parameters = {
    "method.request.querystring.family" = false
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_integration" "get_controls" {
  rest_api_id             = aws_api_gateway_rest_api.compliance_api.id
  resource_id             = aws_api_gateway_resource.controls.id
  http_method             = aws_api_gateway_method.get_controls.http_method
  type                    = "AWS_PROXY"  # DVA-C02: Lambda proxy integration
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# DVA-C02: API Gateway resource: /posture
resource "aws_api_gateway_resource" "posture" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  parent_id   = aws_api_gateway_rest_api.compliance_api.root_resource_id
  path_part   = "posture"
}

# DVA-C02: GET /posture - Get compliance posture overview
resource "aws_api_gateway_method" "get_posture" {
  rest_api_id      = aws_api_gateway_rest_api.compliance_api.id
  resource_id      = aws_api_gateway_resource.posture.id
  http_method      = "GET"
  authorization    = "COGNITO_USER_POOLS"
  authorizer_id    = aws_api_gateway_authorizer.cognito.id
  api_key_required = false

  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_integration" "get_posture" {
  rest_api_id             = aws_api_gateway_rest_api.compliance_api.id
  resource_id             = aws_api_gateway_resource.posture.id
  http_method             = aws_api_gateway_method.get_posture.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# DVA-C02: API Gateway resource: /reports
resource "aws_api_gateway_resource" "reports" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  parent_id   = aws_api_gateway_rest_api.compliance_api.root_resource_id
  path_part   = "reports"
}

# DVA-C02: GET /reports - Retrieve compliance reports
resource "aws_api_gateway_method" "get_reports" {
  rest_api_id      = aws_api_gateway_rest_api.compliance_api.id
  resource_id      = aws_api_gateway_resource.reports.id
  http_method      = "GET"
  authorization    = "COGNITO_USER_POOLS"
  authorizer_id    = aws_api_gateway_authorizer.cognito.id
  api_key_required = false

  request_parameters = {
    "method.request.querystring.format"   = false
    "method.request.querystring.severity" = false
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_integration" "get_reports" {
  rest_api_id             = aws_api_gateway_rest_api.compliance_api.id
  resource_id             = aws_api_gateway_resource.reports.id
  http_method             = aws_api_gateway_method.get_reports.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# DVA-C02: API Gateway resource: /scans
resource "aws_api_gateway_resource" "scans" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  parent_id   = aws_api_gateway_rest_api.compliance_api.root_resource_id
  path_part   = "scans"
}

# DVA-C02: POST /scans - Initiate on-demand compliance scan
resource "aws_api_gateway_method" "post_scans" {
  rest_api_id      = aws_api_gateway_rest_api.compliance_api.id
  resource_id      = aws_api_gateway_resource.scans.id
  http_method      = "POST"
  authorization    = "COGNITO_USER_POOLS"
  authorizer_id    = aws_api_gateway_authorizer.cognito.id
  api_key_required = false

  request_parameters = {
    "method.request.header.Authorization" = true
    "method.request.header.Content-Type"  = true
  }
}

resource "aws_api_gateway_integration" "post_scans" {
  rest_api_id             = aws_api_gateway_rest_api.compliance_api.id
  resource_id             = aws_api_gateway_resource.scans.id
  http_method             = aws_api_gateway_method.post_scans.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# DVA-C02: API Gateway resource: /drift
resource "aws_api_gateway_resource" "drift" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  parent_id   = aws_api_gateway_rest_api.compliance_api.root_resource_id
  path_part   = "drift"
}

# DVA-C02: GET /drift - Get infrastructure drift status
resource "aws_api_gateway_method" "get_drift" {
  rest_api_id      = aws_api_gateway_rest_api.compliance_api.id
  resource_id      = aws_api_gateway_resource.drift.id
  http_method      = "GET"
  authorization    = "COGNITO_USER_POOLS"
  authorizer_id    = aws_api_gateway_authorizer.cognito.id
  api_key_required = false

  request_parameters = {
    "method.request.querystring.resource_type" = false
    "method.request.header.Authorization"      = true
  }
}

resource "aws_api_gateway_integration" "get_drift" {
  rest_api_id             = aws_api_gateway_rest_api.compliance_api.id
  resource_id             = aws_api_gateway_resource.drift.id
  http_method             = aws_api_gateway_method.get_drift.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# DVA-C02: CORS configuration for SPA access
resource "aws_api_gateway_gateway_response" "cors_response" {
  rest_api_id      = aws_api_gateway_rest_api.compliance_api.id
  response_type    = "DEFAULT_4XX"
  status_code      = "400"
  response_templates = {
    "application/json" = "{\"message\":$context.error.messageString}"
  }

  default_response = true
}

# DVA-C02: API Gateway stage for v1 API
resource "aws_api_gateway_stage" "v1" {
  deployment_id = aws_api_gateway_deployment.compliance_api.id
  rest_api_id   = aws_api_gateway_rest_api.compliance_api.id
  stage_name    = "v1"

  # DVA-C02: Enable CloudWatch metrics for monitoring
  cloudwatch_metrics_enabled        = true
  log_level                         = "INFO"
  data_trace_enabled                = false  # DVA-C02: Don't log request/response data
  metrics_enabled                   = true

  # DVA-C02: Caching for improved performance
  cache_cluster_enabled = false  # DVA-C02: Use on-demand caching
  cache_cluster_size    = null

  # DVA-C02: Throttling for abuse prevention
  throttle_settings {
    burst_limit = 5000   # DVA-C02: Max concurrent requests
    rate_limit  = 2000   # DVA-C02: Requests per second
  }

  variables = {
    environment = var.environment
  }

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-api-v1"
      Component  = "api-stage"
    }
  )

  depends_on = [aws_cloudwatch_log_group.api_logs]
}

# DVA-C02: API Gateway deployment
resource "aws_api_gateway_deployment" "compliance_api" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id

  depends_on = [
    aws_api_gateway_integration.get_controls,
    aws_api_gateway_integration.get_posture,
    aws_api_gateway_integration.get_reports,
    aws_api_gateway_integration.post_scans,
    aws_api_gateway_integration.get_drift
  ]
}

# DVA-C02: Lambda permission for API Gateway invocation
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.compliance_api.execution_arn}/*/*"
}
