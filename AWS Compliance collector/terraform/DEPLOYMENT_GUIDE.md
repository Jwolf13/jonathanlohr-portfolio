# Terraform Deployment Quick Reference

## 5-Minute Quick Start

### Step 1: Prepare AWS Account
```bash
# Ensure AWS CLI is configured
aws sts get-caller-identity

# Save your account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $AWS_ACCOUNT_ID"
```

### Step 2: Create State Backend (One-time)
```bash
# Create S3 bucket for state
aws s3 mb s3://compliance-collector-terraform-state-${AWS_ACCOUNT_ID} --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket compliance-collector-terraform-state-${AWS_ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Step 3: Configure Terraform Variables
```bash
cd environments/dev

# Create variables file
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
environment = "dev"
account_id = "${AWS_ACCOUNT_ID}"
alarm_email = "your-email@example.com"
cognito_callback_urls = ["http://localhost:3000/callback"]
cognito_logout_urls = ["http://localhost:3000"]
EOF
```

### Step 4: Deploy
```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply
```

### Step 5: Capture Outputs
```bash
# Display all outputs
terraform output

# Export key values
export API_ENDPOINT=$(terraform output -raw api_endpoint_url)
export COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id)
export DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name)

echo "API: $API_ENDPOINT"
echo "Cognito Client: $COGNITO_CLIENT_ID"
echo "DynamoDB: $DYNAMODB_TABLE"
```

## Common Operations

### View Current Infrastructure State
```bash
terraform show
```

### Check What Will Change
```bash
terraform plan -var-file=terraform.tfvars
```

### Update Single Module
```bash
# Re-deploy only Lambda function after code changes
terraform apply -target=module.compliance_collector_lambda

# Re-deploy only monitoring
terraform apply -target=module.monitoring
```

### View Specific Outputs
```bash
# Get API endpoint
terraform output api_endpoint_url

# Get all Cognito details
terraform output -json | jq '.cognito_*'

# Get DynamoDB table name
terraform output dynamodb_table_name
```

### Check Resource Details
```bash
# List all resources
terraform state list

# Show specific resource
terraform state show 'module.dynamodb.aws_dynamodb_table.compliance_data'

# Show Lambda role details
terraform state show 'module.compliance_collector_lambda.aws_iam_role.lambda_role'
```

### Destroy Everything
```bash
terraform destroy -var-file=terraform.tfvars

# Confirm when prompted
# Note: S3 bucket and DynamoDB table must be empty or will fail
```

## Post-Deployment Checklist

- [ ] Verify API Gateway endpoint is accessible
- [ ] Confirm Cognito user pool is created
- [ ] Check DynamoDB table exists and has GSIs
- [ ] Verify S3 bucket is created and encrypted
- [ ] Confirm Lambda function is deployed
- [ ] Check CloudWatch dashboard is visible
- [ ] Test SNS topic subscription (check email)

## Architecture Components Map

| Component | Module | Key Resource |
|-----------|--------|--------------|
| Data Storage | dynamodb | `aws_dynamodb_table.compliance_data` |
| Evidence Storage | storage | `aws_s3_bucket.compliance_evidence` |
| Compute | lambda | `aws_lambda_function.compliance_function` |
| Scheduling | eventbridge | `aws_cloudwatch_event_rule.compliance_scan_schedule` |
| API | api_gateway | `aws_api_gateway_rest_api.compliance_api` |
| Auth | cognito | `aws_cognito_user_pool.compliance_dashboard` |
| Monitoring | monitoring | `aws_cloudwatch_dashboard.compliance_collector` |

## Environment Variables for Scripts

After deployment, set these for testing:

```bash
# Export from Terraform outputs
export TF_API_ENDPOINT=$(cd environments/dev && terraform output -raw api_endpoint_url)
export TF_COGNITO_POOL=$(cd environments/dev && terraform output -raw cognito_user_pool_id)
export TF_COGNITO_CLIENT=$(cd environments/dev && terraform output -raw cognito_client_id)
export TF_DYNAMODB_TABLE=$(cd environments/dev && terraform output -raw dynamodb_table_name)
export TF_S3_BUCKET=$(cd environments/dev && terraform output -raw s3_bucket_name)
export TF_REGION="us-east-1"
```

## Troubleshooting Commands

### Check Terraform Plan for Errors
```bash
terraform plan -var-file=terraform.tfvars 2>&1 | head -50
```

### View Provider Configuration
```bash
terraform providers
```

### Validate All Modules
```bash
terraform validate
```

### Check Specific Module Variables
```bash
# Check what variables the cognito module expects
grep "variable" modules/cognito/variables.tf
```

### View Remote State
```bash
# List resources in remote state
terraform state list

# Show resource details from remote state
terraform state show module.dynamodb.aws_dynamodb_table.compliance_data
```

## Cost Estimation

Run before deployment:

```bash
terraform plan -var-file=terraform.tfvars -out=plan.tfplan

# Use tfcost or similar tool for cost analysis
# terraform plan -json | jq . > plan.json
```

## Network Diagram (Text)

```
Internet → API Gateway (HTTPS) → Lambda
                                   ↓
                            DynamoDB + S3
                                   ↓
                            EventBridge
                                   ↓
                            Lambda (scheduled)
```

## Key AWS Resources Created

1. **DynamoDB Table**: `ComplianceData` with 2 GSIs
2. **S3 Bucket**: `compliance-evidence-{account}-dev`
3. **S3 Bucket**: `compliance-evidence-logs-{account}-dev`
4. **Lambda Function**: `compliance-collector`
5. **Lambda Role**: `compliance-collector-execution-role`
6. **API Gateway**: `compliance-api` with v1 stage
7. **Cognito User Pool**: `compliance-dashboard-users`
8. **EventBridge Rules**: 2 (scheduled + config change)
9. **CloudWatch Dashboard**: `compliance-collector`
10. **SNS Topic**: `compliance-collector-alarms`
11. **KMS Keys**: 3 (DynamoDB, S3, SNS)
12. **IAM Roles**: Multiple for least-privilege access

## Integration Points

### For Frontend Application
```javascript
const config = {
  apiEndpoint: "https://your-api-id.execute-api.us-east-1.amazonaws.com/v1",
  cognitoUserPoolId: "us-east-1_xxxxxxxxxxxx",
  cognitoClientId: "1a2b3c4d5e6f7g8h9i0j",
  region: "us-east-1"
};
```

### For Lambda Functions
```python
import boto3

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
```

### For EventBridge
- Scheduled every 6 hours for compliance scans
- Triggered by AWS Config compliance changes
- Both invoke the same Lambda function

## Monitoring & Alerts

### View Dashboard
```bash
# Open in browser
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=compliance-collector"
```

### Check Alarms
```bash
aws cloudwatch describe-alarms --region us-east-1
```

### View Lambda Logs
```bash
aws logs tail /aws/lambda/compliance-collector --follow
```

### Check DynamoDB Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=ComplianceData \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Updating Configuration

### Change Alarm Email
```bash
# Edit terraform.tfvars
alarm_email = "new-email@example.com"

# Apply changes
terraform apply -target=module.monitoring
```

### Increase Lambda Memory
```bash
# Edit environments/dev/main.tf
memory_size = 1024  # from 512

# Apply changes
terraform apply -target=module.compliance_collector_lambda
```

### Modify EventBridge Schedule
```bash
# Edit terraform.tfvars
compliance_scan_schedule = "rate(12 hours)"  # from rate(6 hours)

# Apply changes
terraform apply -target=module.eventbridge
```

## Reference Links

- Architecture: See parent README.md
- AWS Docs: https://docs.aws.amazon.com/
- Terraform AWS: https://registry.terraform.io/providers/hashicorp/aws/latest
- DVA-C02: https://aws.amazon.com/certification/certified-developer-associate/

## Next Steps

1. Verify deployment succeeded
2. Deploy Lambda function code
3. Test API endpoints with Cognito auth
4. Configure SNS email subscriptions
5. Set up CloudWatch log monitoring
6. Document custom policies in your organization
