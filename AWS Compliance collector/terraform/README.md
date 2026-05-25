# AWS Compliance Evidence Collector - Terraform Configuration

This directory contains a complete, production-ready Terraform configuration for the AWS Compliance Evidence Collector infrastructure. The configuration implements a secure, scalable, event-driven architecture aligned with AWS Well-Architected Framework and DVA-C02 exam best practices.

## Architecture Overview

The infrastructure consists of the following components:

### Core Services
- **DynamoDB**: Single-table design for compliance data with GSI for flexible querying
- **S3**: Secure evidence artifact storage with versioning and lifecycle management
- **Lambda**: Compliance collection and processing functions with X-Ray tracing
- **EventBridge**: Scheduled compliance scans and real-time Config change detection
- **API Gateway**: REST API with Cognito OAuth2/OIDC authentication
- **Cognito**: User pool with MFA and strong password policies
- **CloudWatch**: Monitoring dashboard and alarm configuration
- **SNS**: Alert notifications for operational events

## Directory Structure

```
terraform/
├── modules/
│   ├── dynamodb/          # DynamoDB table with GSI and encryption
│   ├── storage/           # S3 buckets with versioning and lifecycle
│   ├── lambda/            # Reusable Lambda module
│   ├── eventbridge/       # Scheduled and event-driven rules
│   ├── cognito/           # User authentication and authorization
│   ├── api_gateway/       # REST API with Cognito authorizer
│   └── monitoring/        # CloudWatch dashboard and alarms
├── environments/
│   └── dev/               # Development environment configuration
└── README.md              # This file
```

## DVA-C02 Certification Alignment

This Terraform configuration demonstrates the following DVA-C02 concepts:

### Security
- **Encryption at Rest**: KMS managed keys for DynamoDB, S3, and SNS
- **Encryption in Transit**: SSL/TLS enforcement on S3 bucket policy
- **Identity & Access**: IAM roles with least-privilege principles
- **Authentication**: Cognito User Pool with MFA and strong password policies
- **API Security**: API Gateway with Cognito authorizer

### Serverless Architecture
- **Lambda**: Event-driven functions with X-Ray tracing and CloudWatch logs
- **Event Sources**: EventBridge for scheduled and real-time event processing
- **Managed Services**: No EC2 instances, completely serverless

### Data Management
- **DynamoDB**: Single-table design pattern with GSI for flexible queries
- **DynamoDB Streams**: Event source for drift detection
- **Point-in-Time Recovery**: Disaster recovery capability
- **Versioning & Lifecycle**: S3 versioning and intelligent tiering

### Monitoring & Observability
- **CloudWatch**: Dashboard, logs, and metrics
- **X-Ray**: Distributed tracing for Lambda functions
- **Alarms**: SNS notifications for operational events
- **Access Logging**: S3 and API Gateway audit trails

## Prerequisites

1. **AWS Account**: Valid AWS account with appropriate permissions
2. **Terraform**: Version 1.0 or later
3. **AWS CLI**: Configured with credentials
4. **Python 3.11+**: For Lambda function development

## Setup Instructions

### 1. Initialize Terraform State Backend

Before deploying, ensure you have an S3 bucket and DynamoDB table for Terraform state:

```bash
# Create state bucket and lock table manually or use AWS CLI
aws s3 mb s3://compliance-collector-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket compliance-collector-terraform-state \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 2. Prepare Variables

Copy the example variables file and customize for your environment:

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values:
# - AWS account ID
# - Email for alarm notifications
# - Cognito callback URLs for your application
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform with backend configuration
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan -var-file=terraform.tfvars

# Apply configuration
terraform apply -var-file=terraform.tfvars
```

### 4. Capture Outputs

After successful deployment, outputs will be displayed automatically:

```bash
# Retrieve outputs again
terraform output

# Export specific values
export API_ENDPOINT=$(terraform output -raw api_endpoint_url)
export COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id)
export DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name)
```

## Module Details

### DynamoDB Module

**Features:**
- Single-table design with hierarchical keys
- Global Secondary Indexes (GSI) for flexible querying:
  - `ByFamily`: Query controls by compliance framework (SOC2, ISO, etc.)
  - `BySeverity`: Query controls by severity level
- DynamoDB Streams enabled for drift detection
- TTL support for automatic data cleanup
- Point-in-time recovery for disaster recovery
- AWS managed KMS encryption
- On-demand billing model

**Key Outputs:**
- `table_name`: DynamoDB table identifier
- `table_arn`: ARN for IAM policies
- `stream_arn`: Stream ARN for Lambda event source

### Storage Module

**Features:**
- S3 bucket with automatic naming (account/environment aware)
- Bucket versioning for compliance audit trail
- Server-side encryption with KMS
- Block all public access by default
- Intelligent tiering lifecycle:
  - 90 days: Standard → Infrequent Access
  - 1 year: IA → Glacier Instant Retrieval
  - 7 years: Glacier → Deep Archive
- Bucket logging for audit trail
- SSL/TLS enforcement via bucket policy

**Key Outputs:**
- `bucket_name`: S3 bucket identifier
- `bucket_arn`: ARN for IAM policies
- `kms_key_arn`: KMS key for encryption

### Lambda Module

**Features:**
- Reusable module for all compliance functions
- Automatic IAM role creation with least-privilege
- CloudWatch log group with retention policy
- X-Ray tracing enabled
- VPC support optional
- Layer support for shared dependencies
- Dead letter queue configuration
- ARM64 architecture for cost optimization

**Key Outputs:**
- `function_arn`: Lambda function identifier
- `invoke_arn`: ARN for API Gateway integration
- `role_arn`: Execution role for permission management

### EventBridge Module

**Features:**
- Scheduled rule: Every 6 hours for compliance scans
- Event rule: AWS Config compliance change detection
- Lambda permissions for EventBridge invocation
- Optional dead letter queue for failed events
- Input transformation for event enrichment

**Key Outputs:**
- `scan_schedule_rule_arn`: ARN of scheduled rule
- `config_change_rule_arn`: ARN of event rule

### Cognito Module

**Features:**
- User Pool with security best practices
- Password policy: 12+ chars, symbols, numbers, upper/lowercase
- MFA optional with TOTP support
- Email verification required
- OAuth2/OIDC support
- Resource server with scopes (read, write, admin)
- Hosted UI domain for login

**Key Outputs:**
- `user_pool_id`: User Pool identifier
- `client_id`: SPA client identifier
- `hosted_ui_domain`: Login page URL

### API Gateway Module

**Features:**
- REST API with Cognito authorization
- Resources: /controls, /posture, /reports, /scans, /drift
- Lambda proxy integration
- CORS configuration
- CloudWatch access logging
- Throttling (5000 burst, 2000 req/sec)
- v1 API stage deployment

**Key Outputs:**
- `api_endpoint`: Base URL for API calls
- `invoke_url`: Full stage invoke URL

### Monitoring Module

**Features:**
- CloudWatch dashboard with key metrics:
  - Lambda errors and duration
  - DynamoDB consumed capacity
  - S3 bucket size
  - API Gateway requests
- Alarms for operational health
- SNS topic for notifications
- KMS encryption for SNS

**Key Outputs:**
- `dashboard_name`: CloudWatch dashboard identifier
- `sns_topic_arn`: SNS topic for alarms

## Configuration Examples

### Deploy Development Environment

```bash
cd environments/dev

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
environment = "dev"
account_id = "123456789012"
alarm_email = "team@example.com"
EOF

# Deploy
terraform init
terraform plan
terraform apply
```

### Update Compliance Scan Schedule

Edit `terraform.tfvars`:

```hcl
compliance_scan_schedule = "rate(12 hours)"  # Change from 6 to 12 hours
```

Then apply:

```bash
terraform apply -var-file=terraform.tfvars
```

### Add Lambda Layers for Dependencies

Edit `terraform.tfvars`:

```hcl
lambda_layer_arns = [
  "arn:aws:lambda:us-east-1:123456789012:layer:compliance-deps:1",
  "arn:aws:lambda:us-east-1:123456789012:layer:monitoring-libs:2"
]
```

## Scaling Considerations

### DynamoDB On-Demand Pricing
Current configuration uses `PAY_PER_REQUEST` billing. For consistent high traffic, consider:

```hcl
# In modules/dynamodb/main.tf
billing_mode = "PROVISIONED"
read_capacity_units = 100
write_capacity_units = 100
```

### Lambda Memory and Timeout
Adjust for specific workloads in `environments/dev/main.tf`:

```hcl
module "compliance_collector_lambda" {
  memory_size = 1024  # Increase for CPU-intensive work
  timeout     = 120   # Increase for long-running operations
}
```

### API Gateway Rate Limiting
Modify throttling in `modules/api_gateway/main.tf`:

```hcl
throttle_settings {
  burst_limit = 10000  # Concurrent requests
  rate_limit  = 5000   # Requests per second
}
```

## State Management

Terraform state is stored in S3 with DynamoDB locking. This enables:

- **Collaboration**: Team members can work simultaneously (locking prevents conflicts)
- **Disaster Recovery**: State is versioned and backed up
- **Encryption**: State is encrypted at rest
- **Audit Trail**: All changes are logged

### Accessing State Information

```bash
# List all resources
terraform state list

# Show specific resource details
terraform state show 'module.dynamodb.aws_dynamodb_table.compliance_data'

# Display all outputs
terraform output
```

## Troubleshooting

### Cognito Domain Already Exists

The Cognito domain must be globally unique. If you get a domain conflict error:

```bash
# Modify the domain in environments/dev/main.tf or terraform.tfvars
user_pool_domain = "compliance-dashboard-${random_id.unique.hex}"
```

### Lambda Function Not Found

Ensure the Lambda function ZIP file exists:

```bash
# Build and create the deployment package
python -m pip install -r src/requirements.txt -t src/lib
cd src && zip -r ../dist/compliance-collector.zip . && cd ..

# Update terraform.tfvars
lambda_function_zip_path = "./src/dist/compliance-collector.zip"
```

### API Gateway CORS Issues

If frontend receives CORS errors, verify callback URLs match in Cognito:

```bash
# Check Cognito client configuration
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_abc123def456 \
  --client-id 1a2b3c4d5e6f7g8h
```

## Cleanup

To destroy all resources (use with caution):

```bash
terraform destroy -var-file=terraform.tfvars

# Verify everything is deleted
terraform state list  # Should be empty
```

## Security Best Practices

1. **Never commit terraform.tfvars**: Use `.gitignore`
2. **Use remote state**: Don't store state locally
3. **Enable MFA**: Require MFA for AWS console and API access
4. **Rotate credentials**: Regularly rotate AWS access keys
5. **Audit logs**: Monitor CloudTrail for all API calls
6. **Review IAM policies**: Regularly audit least-privilege permissions

## Maintenance

### Update Terraform Provider

```bash
terraform init -upgrade
```

### Update AWS Resources

Review AWS provider updates:

```bash
terraform plan -var-file=terraform.tfvars
```

### Regular Backups

DynamoDB point-in-time recovery is enabled. Test recovery procedures regularly.

## Support & Documentation

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [DVA-C02 Study Guide](https://aws.amazon.com/certification/certified-developer-associate/)
- [AWS Compliance Evidence Collector](https://github.com/jonathanlohr/compliance-collector)

## License

This Terraform configuration is part of the AWS Compliance Evidence Collector project.
