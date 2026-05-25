# DVA-C02: Compliance Collector Infrastructure for Development Environment
# Orchestrates all modules with proper cross-module dependencies

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # DVA-C02: Remote state management with locking for team collaboration
  backend "s3" {
    bucket         = "compliance-collector-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# DVA-C02: AWS provider configuration for dev environment
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "compliance-collector"
      ManagedBy   = "terraform"
      CreatedAt   = timestamp()
    }
  }
}

# DVA-C02: DynamoDB module for compliance data storage
module "dynamodb" {
  source = "../../modules/dynamodb"

  table_name = "ComplianceData"

  common_tags = var.common_tags
}

# DVA-C02: Storage module for evidence artifacts
module "storage" {
  source = "../../modules/storage"

  account_id  = var.account_id
  environment = var.environment

  common_tags = var.common_tags
}

# DVA-C02: Cognito authentication module
module "cognito" {
  source = "../../modules/cognito"

  user_pool_domain = "compliance-dashboard-${var.account_id}"
  callback_urls    = var.cognito_callback_urls
  logout_urls      = var.cognito_logout_urls

  common_tags = var.common_tags
}

# DVA-C02: Core Lambda function for compliance collection and processing
module "compliance_collector_lambda" {
  source = "../../modules/lambda"

  function_name = "compliance-collector"
  handler       = "src.handlers.collector.lambda_handler"
  runtime       = "python3.11"
  memory_size   = 512
  timeout       = 60

  environment_variables = {
    DYNAMODB_TABLE_NAME = module.dynamodb.table_name
    S3_BUCKET_NAME      = module.storage.bucket_name
    LOG_LEVEL           = "INFO"
    ENVIRONMENT         = var.environment
  }

  # DVA-C02: Inline policy for DynamoDB and S3 access
  iam_policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.dynamodb.table_arn,
          "${module.dynamodb.table_arn}/index/*"
        ]
      },
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${module.storage.bucket_arn}/*"
      },
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          module.dynamodb.kms_key_arn,
          module.storage.kms_key_arn
        ]
      },
      {
        Sid    = "DescribeServices"
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "s3:GetBucketVersioning"
        ]
        Resource = "*"
      }
    ]
  })

  # DVA-C02: Use Lambda function from local ZIP or S3
  filename = var.lambda_function_zip_path
  layers   = var.lambda_layer_arns

  common_tags = var.common_tags
}

# DVA-C02: EventBridge rules for event-driven compliance collection
module "eventbridge" {
  source = "../../modules/eventbridge"

  collector_lambda_arn  = module.compliance_collector_lambda.function_arn
  collector_lambda_name = module.compliance_collector_lambda.function_name
  aws_region            = var.aws_region

  schedule_expression = var.compliance_scan_schedule

  create_dlq            = true
  dead_letter_queue_arn = ""

  common_tags = var.common_tags
}

# DVA-C02: API Gateway for dashboard access
module "api_gateway" {
  source = "../../modules/api_gateway"

  lambda_invoke_arn     = module.compliance_collector_lambda.invoke_arn
  lambda_function_name  = module.compliance_collector_lambda.function_name
  cognito_user_pool_arn = module.cognito.user_pool_arn
  environment           = var.environment

  common_tags = var.common_tags
}

# DVA-C02: CloudWatch monitoring and alarms
module "monitoring" {
  source = "../../modules/monitoring"

  aws_region            = var.aws_region
  alarm_email           = var.alarm_email
  dynamodb_table_name   = module.dynamodb.table_name
  s3_bucket_name        = module.storage.bucket_name

  common_tags = var.common_tags
}

# DVA-C02: Output values for dashboard access and management
locals {
  deployment_info = {
    api_endpoint        = module.api_gateway.invoke_url
    cognito_pool_id     = module.cognito.user_pool_id
    cognito_client_id   = module.cognito.client_id
    cognito_domain      = module.cognito.hosted_ui_domain
    dynamodb_table      = module.dynamodb.table_name
    s3_bucket           = module.storage.bucket_name
    cloudwatch_dashboard = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=compliance-collector"
  }
}
