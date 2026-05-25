# Terraform Configuration - Complete Manifest

## Overview
This manifest documents all Terraform files created for the AWS Compliance Evidence Collector infrastructure. The configuration is production-ready and fully implements the architecture with DVA-C02 best practices.

## File Structure

### Root Directory
```
terraform/
├── README.md                          # Comprehensive documentation
├── DEPLOYMENT_GUIDE.md               # Quick start and operational guide
├── MANIFEST.md                       # This file
└── modules/                          # Reusable infrastructure modules
└── environments/                     # Environment-specific configurations
```

## Module Files (terraform/modules/)

### DynamoDB Module
**Location**: `modules/dynamodb/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | DynamoDB table, KMS encryption, streams, PITR | Single-table design, encryption at rest, PITR, TTL |
| `variables.tf` | Input variables | Table naming, tagging |
| `outputs.tf` | Output values | Table ARN, stream ARN, KMS key ID |

**Key Resources**:
- `aws_dynamodb_table.compliance_data` - Single table with PK/SK and 2 GSIs
- `aws_kms_key.dynamodb` - Encryption key with rotation
- `aws_kms_alias.dynamodb` - Alias for key management

**Architecture Notes**:
- Uses PAY_PER_REQUEST billing for variable workloads
- ByFamily GSI for control family queries (SOC2, ISO, PCI)
- BySeverity GSI for severity-level queries (CRITICAL, HIGH, MEDIUM)
- Streams enabled with NEW_AND_OLD_IMAGES for drift detection
- Point-in-time recovery enabled for disaster recovery

---

### Storage Module
**Location**: `modules/storage/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | S3 buckets, versioning, encryption, lifecycle, logging | Encryption at rest, lifecycle, versioning, SSL enforcement |
| `variables.tf` | Input variables | Account ID, environment, tags |
| `outputs.tf` | Output values | Bucket name, ARN, KMS key details |

**Key Resources**:
- `aws_s3_bucket.compliance_evidence` - Primary evidence bucket
- `aws_s3_bucket.access_logs` - Logging bucket
- `aws_s3_bucket_server_side_encryption_configuration` - KMS encryption
- `aws_s3_bucket_lifecycle_configuration` - Tiered storage (Standard → IA → Glacier → Deep Archive)
- `aws_s3_bucket_policy` - SSL/TLS enforcement

**Architecture Notes**:
- Automatic tiering: 90d (IA), 1yr (Glacier), 7yr (Deep Archive)
- Versioning enabled for audit trail
- Public access blocked via bucket policy
- KMS encryption with customer-managed keys
- Logging to separate bucket with 90-day retention

---

### Lambda Module
**Location**: `modules/lambda/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | Lambda function, IAM role, CloudWatch logs, X-Ray tracing | Serverless, least-privilege IAM, execution role, X-Ray tracing |
| `variables.tf` | Input variables | Handler, runtime, memory, timeout, environment variables, IAM policy |
| `outputs.tf` | Output values | Function ARN, role ARN, invoke ARN, log group |

**Key Resources**:
- `aws_lambda_function.compliance_function` - Compliance collector function
- `aws_iam_role.lambda_role` - Execution role with least-privilege
- `aws_iam_role_policy.cloudwatch_logs` - CloudWatch logs permission
- `aws_iam_role_policy.xray_write` - X-Ray tracing permission
- `aws_iam_role_policy.lambda_custom` - Custom IAM policy
- `aws_cloudwatch_log_group.lambda_logs` - 14-day log retention

**Architecture Notes**:
- Reusable module for any Lambda function
- ARM64 architecture (Graviton) for cost optimization
- X-Ray tracing enabled by default
- Custom IAM policies passed as JSON variable
- VPC support optional
- Lambda layers support for shared dependencies
- Event invoke config with dead letter queue

---

### EventBridge Module
**Location**: `modules/eventbridge/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | EventBridge rules, targets, permissions, DLQ | Event-driven architecture, scheduled events, real-time events |
| `variables.tf` | Input variables | Lambda ARN/name, schedule expression, DLQ configuration |
| `outputs.tf` | Output values | Rule ARNs, DLQ URL |

**Key Resources**:
- `aws_cloudwatch_event_rule.compliance_scan_schedule` - Scheduled rule (every 6 hours)
- `aws_cloudwatch_event_rule.config_change_rule` - AWS Config change detection
- `aws_cloudwatch_event_target.*` - Lambda integration
- `aws_lambda_permission.allow_eventbridge_*` - Invocation permissions
- `aws_sqs_queue.eventbridge_dlq` - Dead letter queue

**Architecture Notes**:
- Scheduled scans every 6 hours (configurable)
- Config compliance change detection (real-time)
- Input transformation for event enrichment
- DLQ for failed event handling
- Both rules invoke same Lambda with different payloads

---

### Cognito Module
**Location**: `modules/cognito/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | Cognito User Pool, Client, domain, resource server | Authentication, OAuth2/OIDC, MFA, password policies |
| `variables.tf` | Input variables | Callback URLs, logout URLs, domain name |
| `outputs.tf` | Output values | User Pool ID, Client ID, hosted UI domain |

**Key Resources**:
- `aws_cognito_user_pool.compliance_dashboard` - User Pool with security policies
- `aws_cognito_user_pool_client.dashboard_spa` - SPA client
- `aws_cognito_resource_server.compliance_api` - OAuth scopes
- `aws_cognito_user_pool_domain.compliance` - Hosted UI domain

**Architecture Notes**:
- Password policy: 12+ chars, symbols, numbers, upper/lowercase
- MFA optional with TOTP support
- Email verification required
- OAuth2/OIDC for SPA and mobile apps
- Resource scopes: read, write, admin
- Deletion protection enabled
- Device tracking for security

---

### API Gateway Module
**Location**: `modules/api_gateway/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | REST API, authorizer, resources, methods, integration, stage | REST API, OAuth2 authorizer, proxy integration, CORS |
| `variables.tf` | Input variables | Lambda ARN/name, Cognito User Pool ARN, environment |
| `outputs.tf` | Output values | API endpoint, stage invoke URL, authorizer ID |

**Key Resources**:
- `aws_api_gateway_rest_api.compliance_api` - REST API
- `aws_api_gateway_authorizer.cognito` - Cognito OAuth2 authorizer
- `aws_api_gateway_resource.*` - /controls, /posture, /reports, /scans, /drift
- `aws_api_gateway_method.*` - GET/POST methods
- `aws_api_gateway_integration.*` - Lambda proxy integration
- `aws_api_gateway_stage.v1` - v1 stage deployment
- `aws_cloudwatch_log_group.api_logs` - 30-day access logs

**Architecture Notes**:
- Cognito OAuth2 authorization on all methods
- Lambda proxy integration for flexible routing
- CloudWatch access logging for audit
- Throttling: 5000 burst, 2000 req/sec
- Regional endpoint for security
- Caching disabled (on-demand)
- CORS configuration

**API Endpoints**:
- `GET /controls` - List compliance controls
- `GET /posture` - Compliance posture overview
- `GET /reports` - Retrieve reports
- `POST /scans` - On-demand compliance scan
- `GET /drift` - Infrastructure drift status

---

### Monitoring Module
**Location**: `modules/monitoring/`

| File | Purpose | DVA-C02 Concepts |
|------|---------|-----------------|
| `main.tf` | CloudWatch dashboard, alarms, SNS topic, KMS encryption | Monitoring, alerting, CloudWatch metrics, SNS notifications |
| `variables.tf` | Input variables | Region, email, resource names |
| `outputs.tf` | Output values | Dashboard name, SNS topic ARN, alarm ARNs |

**Key Resources**:
- `aws_cloudwatch_dashboard.compliance_collector` - Monitoring dashboard
- `aws_sns_topic.compliance_alarms` - Alarm notification topic
- `aws_cloudwatch_metric_alarm.*` - Multiple alarms
- `aws_kms_key.sns` - SNS encryption key

**Alarms Configured**:
1. Lambda Errors > 5 in 5 minutes
2. Lambda Duration > 60% of timeout (36 seconds)
3. DynamoDB Throttling > 0
4. API Gateway 5XX Errors > 10 in 5 minutes

**Dashboard Metrics**:
- Lambda: Errors, Invocations, Duration
- DynamoDB: Read/Write capacity
- S3: Bucket size
- API Gateway: Requests, 4XX/5XX errors

---

## Environment Configuration Files

### Development Environment
**Location**: `environments/dev/`

| File | Purpose | Content |
|------|---------|---------|
| `main.tf` | Environment orchestration | Module composition, provider config, backend setup |
| `variables.tf` | Input variables | AWS region, account ID, email, schedule, tags |
| `outputs.tf` | Output values | All deployment endpoints and credentials |
| `terraform.tfvars.example` | Example configuration | Template for user customization |

**main.tf Details**:
- Terraform version requirement (>=1.0)
- AWS provider with default tags
- S3 backend for state management
- DynamoDB locking for concurrent access
- Module instantiation for all 7 modules
- Module dependencies and cross-references
- Deployment info locals

**Key Modules Composed**:
1. DynamoDB (storage)
2. Storage (S3)
3. Cognito (authentication)
4. Compliance Collector Lambda (compute)
5. EventBridge (scheduling)
6. API Gateway (API)
7. Monitoring (observability)

---

## Configuration Examples

### Example: terraform.tfvars
```hcl
aws_region = "us-east-1"
environment = "dev"
account_id = "123456789012"
cognito_callback_urls = ["http://localhost:3000/callback"]
cognito_logout_urls = ["http://localhost:3000"]
alarm_email = "team@example.com"
compliance_scan_schedule = "rate(6 hours)"
lambda_function_zip_path = "./src/dist/compliance-collector.zip"
lambda_layer_arns = []
common_tags = {
  Project = "compliance-collector"
  Team = "platform-engineering"
}
```

---

## DVA-C02 Alignment Matrix

### Security Best Practices
| Requirement | Implementation | File |
|-------------|----------------|------|
| Encryption at Rest | KMS keys for DynamoDB, S3, SNS | dynamodb/main.tf, storage/main.tf, monitoring/main.tf |
| Encryption in Transit | SSL/TLS enforcement on S3, API Gateway | storage/main.tf, api_gateway/main.tf |
| Least Privilege IAM | Role policies with specific permissions | lambda/main.tf |
| Authentication | Cognito User Pool with OAuth2 | cognito/main.tf, api_gateway/main.tf |
| Audit Logging | S3 versioning, API Gateway logs, CloudTrail | storage/main.tf, api_gateway/main.tf |

### Serverless Architecture
| Concept | Implementation | File |
|---------|----------------|------|
| Lambda Functions | Compliance collector function | lambda/main.tf, environments/dev/main.tf |
| Event Sources | EventBridge scheduled and event rules | eventbridge/main.tf |
| Managed Services | DynamoDB, S3, API Gateway, Cognito | All modules |
| X-Ray Tracing | Enabled on Lambda | lambda/main.tf |
| CloudWatch Logs | Log groups with retention | lambda/main.tf, api_gateway/main.tf |

### Data Management
| Concept | Implementation | File |
|---------|----------------|------|
| Single-Table Design | DynamoDB with 2 GSIs | dynamodb/main.tf |
| Streams | DynamoDB Streams for drift detection | dynamodb/main.tf |
| PITR | Point-in-time recovery enabled | dynamodb/main.tf |
| Versioning | S3 versioning enabled | storage/main.tf |
| Lifecycle | Intelligent tiering with 7-year retention | storage/main.tf |

### Monitoring & Observability
| Concept | Implementation | File |
|---------|----------------|------|
| CloudWatch Dashboard | Multi-metric dashboard | monitoring/main.tf |
| Metric Alarms | 4 alarms for operational health | monitoring/main.tf |
| SNS Notifications | Email notifications for alerts | monitoring/main.tf |
| Access Logging | S3 and API Gateway logs | storage/main.tf, api_gateway/main.tf |
| X-Ray Tracing | Distributed tracing for Lambda | lambda/main.tf |

---

## Total Files Created

**Count by Type**:
- `main.tf` files: 9 (7 modules + 1 environment + 1 README reference)
- `variables.tf` files: 8 (7 modules + 1 environment)
- `outputs.tf` files: 8 (7 modules + 1 environment)
- Documentation files: 3 (README, DEPLOYMENT_GUIDE, MANIFEST)
- Example files: 1 (terraform.tfvars.example)

**Total Lines of Code**: ~2,500+ lines
**Total Documentation**: ~1,500+ lines

---

## Deployment Flow

```
1. User prepares terraform.tfvars
   ↓
2. terraform init (backend setup)
   ↓
3. terraform plan (dry-run)
   ↓
4. terraform apply (create infrastructure)
   ↓
5. Capture outputs (endpoints, credentials)
   ↓
6. Deploy Lambda function code
   ↓
7. Test API endpoints
   ↓
8. Confirm SNS subscriptions
```

---

## Resource Naming Convention

All resources follow AWS naming best practices:

```
Format: <service>-<component>-<environment>

Examples:
- compliance-collector (Lambda function)
- compliance-api (API Gateway)
- compliance-evidence-123456789012-dev (S3 bucket)
- ComplianceData (DynamoDB table)
- compliance-dashboard-users (Cognito User Pool)
- compliance-collector-alarms (SNS topic)
```

---

## State Management

Terraform state is stored in:
- **Bucket**: `compliance-collector-terraform-state`
- **Key**: `dev/terraform.tfstate`
- **Locking**: DynamoDB table `terraform-state-lock`
- **Encryption**: Enabled on S3 bucket
- **Versioning**: Enabled for recovery

---

## Customization Points

Users can customize:
1. **AWS Region**: Change `aws_region` in terraform.tfvars
2. **Alarm Email**: Update `alarm_email` for notifications
3. **Lambda Memory**: Adjust `memory_size` in environments/dev/main.tf
4. **EventBridge Schedule**: Change `compliance_scan_schedule` in terraform.tfvars
5. **Cognito URLs**: Update callback/logout URLs for production
6. **Tagging**: Add custom tags in common_tags variable

---

## Testing Recommendations

After deployment:
1. Verify all resources exist in AWS Console
2. Test API endpoints with curl or Postman
3. Create test user in Cognito
4. Verify Lambda function is triggered by EventBridge
5. Check CloudWatch logs for errors
6. Confirm SNS subscription email
7. Monitor CloudWatch dashboard

---

## Maintenance & Updates

Regular maintenance tasks:
- Review and rotate KMS keys (automatic with enable_key_rotation)
- Monitor CloudWatch alarms
- Review IAM policies quarterly
- Update Terraform provider versions
- Backup DynamoDB data
- Test disaster recovery (PITR)

---

## References

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **AWS Well-Architected**: https://aws.amazon.com/architecture/well-architected/
- **DVA-C02 Certification**: https://aws.amazon.com/certification/certified-developer-associate/

---

## Version Control

Recommended .gitignore:
```
# Terraform
*.tfstate
*.tfstate.*
*.tfvars
!terraform.tfvars.example
.terraform/
.terraform.lock.hcl
*.tfplan

# IDE
.vscode/
*.swp
*.swo
*.DS_Store
```

---

**Last Updated**: 2024
**Configuration Status**: Production Ready
**DVA-C02 Alignment**: Complete
