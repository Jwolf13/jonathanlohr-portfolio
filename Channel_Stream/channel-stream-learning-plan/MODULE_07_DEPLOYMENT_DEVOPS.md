# Module 7 — Deployment & DevOps

## What you're deploying

This guide deploys the **complete Channel Stream application** to AWS so it runs live on your domain. That means:

| Piece | What it is | Where it ends up |
|---|---|---|
| **Next.js frontend** | The React UI — dashboard, sports, schedule, providers pages | `jonathanlohr.com/channel-stream` |
| **Go API server** | The HTTP backend serving `/v1/sports/live`, `/v1/sports/schedule`, etc. | `api.jonathanlohr.com` |
| **ESPN ingestion worker** | Background goroutine polling ESPN every 60s, writing game data to the DB | Runs inside the same Go server on ECS |
| **PostgreSQL database** | Stores sports events, profiles, broadcast mappings | AWS RDS (private subnet — not reachable from internet) |
| **Redis cache** | Caches API responses — 90s for live scores, 5min for schedule | AWS ElastiCache (private subnet) |

After following these steps, a real user visiting `jonathanlohr.com/channel-stream` on any device will see live sports data served by your Go backend running on AWS. Nothing is running on your laptop anymore.

```
Browser → jonathanlohr.com/channel-stream  →  S3 + CloudFront (Next.js UI)
                    ↕ API calls
         api.jonathanlohr.com              →  ALB → ECS Fargate (Go server)
                                                          ↕
                                               RDS PostgreSQL + ElastiCache Redis
                                                          ↕
                                               ESPN API (ingestion goroutine)
```

**Your existing CloudFront + S3** already serves `jonathanlohr.com` for your portfolio. The frontend just adds a `/channel-stream/` folder to that same bucket — no new CDN needed. The backend is a live server so it gets its own subdomain and AWS infrastructure.

---

## Key concepts before you start

**IAM (Identity and Access Management)** — AWS's permission system. Every action in AWS (creating a bucket, starting a server, writing a file) requires the actor to have explicit permission. You create an IAM *user* with an *access key* that your terminal and CI pipeline use to authenticate. Permissions are granted via *policies* — either AWS-managed (pre-built lists of permissions) or *inline* (custom JSON you write yourself). AWS limits you to 10 managed policies per user; inline policies have no limit.

**VPC (Virtual Private Cloud)** — A private network inside AWS where your servers live. Think of it like your own section of the internet, walled off from everyone else. Inside the VPC you have *public subnets* (reachable from the internet — where the load balancer lives) and *private subnets* (not reachable from the internet — where the database, cache, and app servers live). A *NAT gateway* in the public subnet lets private-subnet servers make outbound calls (like hitting the ESPN API) without being reachable inbound.

**Terraform** — Infrastructure-as-code. Instead of clicking around the AWS console to create 20 different resources, you write a config file (`infrastructure/main.tf`) and run one command. Terraform figures out what needs to be created, updated, or deleted. It stores the current state of your infrastructure in an S3 bucket so it can track changes over time.

**ECS Fargate** — AWS's managed container platform. You give it a Docker image; it runs 2 copies of your Go server on hardware AWS manages. No EC2 instances to patch or resize. The *Application Load Balancer (ALB)* sits in front and distributes traffic between the 2 containers.

**ECR (Elastic Container Registry)** — AWS's private Docker registry. Your CI pipeline builds the Go server into a Docker image and pushes it here. ECS pulls from here when deploying.

**Secrets Manager** — Stores sensitive values (database passwords, connection strings) encrypted at rest. ECS tasks pull these at startup — the password is never in your code or config files.

---

## Your actual AWS values

These are the real values for this deployment — use these everywhere the guide references them:

| Value | This project |
|---|---|
| **S3 bucket (portfolio)** | `jonathanlohrwebsite` |
| **CloudFront Distribution ID** | `EK4OIENDNNXAG` |
| **AWS Account ID** | `435204302991` |
| **ECR URL** | `435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend` |
| **RDS host** | `channel-stream-db.c2vugkacqzdw.us-east-1.rds.amazonaws.com` |
| **Redis host** | `channel-stream-redis.llfliw.ng.0001.use1.cache.amazonaws.com` |
| **IAM deploy user** | `channel-stream-deploy` |

---

## Step 1 — Install tools (if not already done)

Run in PowerShell as Administrator:

```powershell
winget install Amazon.AWSCLI
winget install Hashicorp.Terraform
```

Close and reopen your terminal, then verify:

```powershell
aws --version
terraform --version
```

---

## Step 2 — Create an IAM deploy user

**Why:** Your terminal needs credentials to talk to AWS. Rather than using your root account (dangerous), you create a dedicated user with only the permissions this project needs.

### Create the user in the AWS Console

1. Go to **AWS Console → IAM → Users → Create user**
2. Name: `channel-stream-deploy`
3. Choose **Attach policies directly** and add these 10 managed policies:
   - `AmazonECS_FullAccess`
   - `AmazonEC2FullAccess`
   - `AmazonRDSFullAccess`
   - `AmazonElastiCacheFullAccess`
   - `AmazonRoute53FullAccess`
   - `SecretsManagerReadWrite`
   - `CloudWatchFullAccess`
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AWSCloudFormationFullAccess`
   - `IAMFullAccess`

> **Important:** AWS limits each user to 10 managed policies. You are exactly at that limit. Any additional permissions must be added as *inline policies* (custom JSON attached directly to the user, not counted against the limit). You will need to do this for S3 and other resources this project touches — see Troubleshooting below.

4. After creating the user: click into the user → **Security credentials** tab → **Create access key** → select "Command Line Interface (CLI)" → **Download CSV**

### Configure your terminal

```powershell
aws configure
# AWS Access Key ID:     (paste from CSV)
# AWS Secret Access Key: (paste from CSV)
# Default region:        us-east-1
# Default output format: json
```

Verify it works:

```powershell
aws sts get-caller-identity
# Should print your account ID: 435204302991
```

---

## Step 3 — Deploy backend infrastructure with Terraform (one time)

**Why Terraform:** This single command creates 20+ AWS resources in the right order with the right connections between them. Doing this manually in the AWS console would take hours and be error-prone.

**What it creates:**
- VPC with public and private subnets across 2 availability zones
- NAT gateway (lets the ESPN ingestion worker call the ESPN API from a private subnet)
- RDS PostgreSQL in the private subnet
- ElastiCache Redis in the private subnet
- ECS Fargate cluster + task definition + service (2 running containers)
- ECR repository for Docker images
- Application Load Balancer in the public subnet
- ACM SSL certificate for `api.jonathanlohr.com` (auto-renewing, free)
- Route 53 DNS record pointing `api.jonathanlohr.com` at the load balancer
- Secrets Manager secrets for DATABASE_URL and REDIS_URL
- IAM roles so ECS can read those secrets

### Before you run Terraform: check your VPC limit

AWS defaults to 5 VPCs per region. If you hit this limit, `terraform apply` will fail. Check how many you have:

```powershell
aws ec2 describe-vpcs --query "Vpcs[*].{ID:VpcId,Name:Tags[?Key=='Name']|[0].Value,Default:IsDefault}" --output table
```

If you have 5 VPCs, delete the default one (it's created automatically by AWS and most accounts never use it):

```powershell
# List subnets in the default VPC (replace vpc-XXXXXXXX with the default VPC's ID)
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-XXXXXXXX" --query "Subnets[*].SubnetId" --output text

# Detach and delete the internet gateway
aws ec2 detach-internet-gateway --internet-gateway-id igw-XXXXXXXX --vpc-id vpc-XXXXXXXX
aws ec2 delete-internet-gateway --internet-gateway-id igw-XXXXXXXX

# Delete each subnet
aws ec2 delete-subnet --subnet-id subnet-XXXXXXXX

# Delete any non-default security groups, then delete the VPC
aws ec2 delete-vpc --vpc-id vpc-XXXXXXXX
```

### Create the Terraform state bucket

Terraform stores what it has created in an S3 bucket so it can track changes. Create this bucket once before running Terraform:

```powershell
aws s3 mb s3://channel-stream-terraform-state --region us-east-1
```

> If you get `AccessDenied`, the deploy user is missing `s3:CreateBucket`. Add it as an inline policy — see Troubleshooting.

### Set your database password

Create the file `infrastructure/terraform.tfvars`. This file is in `.gitignore` and must never be committed:

```hcl
db_password = "YourStrongPasswordHere123"
```

**Password rules for RDS:** Do not use `/`, `@`, `"`, or spaces. The `@` character breaks the connection URL format (`user:password@host`) — if you need special characters, stick to `!`, `#`, `$`. If your password contains `#`, you must URL-encode it as `%23` in the connection string stored in Secrets Manager (not in terraform.tfvars — just in the secret value).

### Run Terraform

```powershell
cd infrastructure
terraform init
terraform plan      # shows everything it will create — read it
terraform apply     # type "yes" — takes about 10 minutes
```

When it finishes you'll see outputs including `ecr_url` and sensitive `rds_host` / `redis_host`. Get them with:

```powershell
terraform output -raw ecr_url
terraform output -raw rds_host
terraform output -raw redis_host
```

> **If `terraform apply` times out on RDS:** The RDS instance may have actually finished creating — AWS is slow and Terraform's internal timer gives up before AWS signals completion. Check the instance status:
> ```powershell
> aws rds describe-db-instances --db-instance-identifier channel-stream-db --query "DBInstances[0].DBInstanceStatus" --output text
> ```
> If it says `available`, remove the taint and re-apply:
> ```powershell
> terraform untaint aws_db_instance.postgres
> terraform apply
> ```

---

## Step 4 — Store secrets in AWS Secrets Manager (one time)

**Why Secrets Manager:** Your Go server needs the database password and Redis URL at runtime. Hardcoding them in environment variables or code is a security risk. Instead, ECS pulls them from Secrets Manager at startup — they're encrypted at rest and never appear in logs or config files.

Run from the `infrastructure/` directory:

```powershell
aws secretsmanager put-secret-value --secret-id "channel-stream/database-url" --secret-string "postgresql://csadmin:YourPassword@channel-stream-db.c2vugkacqzdw.us-east-1.rds.amazonaws.com:5432/channelstream"

aws secretsmanager put-secret-value --secret-id "channel-stream/redis-url" --secret-string "redis://channel-stream-redis.llfliw.ng.0001.use1.cache.amazonaws.com:6379"
```

> Replace `YourPassword` with the actual password from `terraform.tfvars`. If it contains `#`, write it as `%23` in this command (but not in tfvars — only in the URL string).

---

## Step 5 — Run database migrations (one time)

**Why:** The RDS database was just created empty. Your migration files in `supabase/migrations/` define the tables the Go server expects. You need to run them once to create those tables and load seed data.

**The challenge:** RDS lives in a *private subnet* — there is no route from the internet to it. You cannot run `psql` from your laptop directly. The security group only allows connections from inside the VPC.

**The solution:** Launch a temporary EC2 instance inside the VPC, use AWS SSM (a secure shell-like service that works without opening any ports) to run commands on it, then terminate it.

### Option A — EC2 bastion via SSM (what we actually did)

This is the right approach. It keeps RDS fully locked down.

**1. Grant the deploy user SSM permissions (inline policy):**

```powershell
aws iam put-user-policy --user-name channel-stream-deploy --policy-name ssm-send-command --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"ssm:SendCommand\",\"ssm:GetCommandInvocation\",\"ssm:ListCommandInvocations\"],\"Resource\":\"*\"}]}"
```

**2. Create an IAM role for the bastion EC2 (so SSM can connect to it):**

```powershell
aws iam create-role --role-name channel-stream-ssm-bastion --assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"ec2.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}" --query "Role.RoleName" --output text
aws iam attach-role-policy --role-name channel-stream-ssm-bastion --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam attach-role-policy --role-name channel-stream-ssm-bastion --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam create-instance-profile --instance-profile-name channel-stream-ssm-bastion --query "InstanceProfile.InstanceProfileName" --output text
aws iam add-role-to-instance-profile --instance-profile-name channel-stream-ssm-bastion --role-name channel-stream-ssm-bastion
```

**3. Upload migrations to S3 (so the bastion can download them):**

```powershell
aws s3 cp supabase/migrations/ s3://channel-stream-terraform-state/migrations/ --recursive
aws s3 cp supabase/seed.sql s3://channel-stream-terraform-state/migrations/seed.sql
```

**4. Launch the bastion in the public subnet with the ECS security group (which has RDS access):**

Get the public subnet and ECS security group IDs:
```powershell
aws ec2 describe-subnets --filters "Name=tag:Name,Values=channel-stream-public-0" --query "Subnets[0].SubnetId" --output text
aws ec2 describe-security-groups --filters "Name=group-name,Values=channel-stream-ecs" --query "SecurityGroups[0].GroupId" --output text
```

Launch the instance (replace the subnet and SG IDs with your output above):
```powershell
aws ec2 run-instances --image-id ami-0c1e21d82fe9c9336 --instance-type t3.micro --subnet-id subnet-XXXXXXXX --security-group-ids sg-XXXXXXXX --iam-instance-profile Name=channel-stream-ssm-bastion --associate-public-ip-address --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=channel-stream-migration-bastion}]" --query "Instances[0].InstanceId" --output text
```

Wait ~60 seconds for it to start and the SSM agent to connect.

**5. Run the migrations via SSM:**

```powershell
aws ssm send-command --instance-ids i-XXXXXXXXXXXXXXX --document-name "AWS-RunShellScript" --parameters "commands=[\"dnf install -y postgresql15\",\"aws s3 cp s3://channel-stream-terraform-state/migrations/ /tmp/migrations/ --recursive\",\"for f in \$(ls /tmp/migrations/*.sql | grep -v seed.sql | sort); do echo Running \$f; PGPASSWORD=YourPassword psql postgresql://csadmin@channel-stream-db.c2vugkacqzdw.us-east-1.rds.amazonaws.com:5432/channelstream -f \$f; done\",\"PGPASSWORD=YourPassword psql postgresql://csadmin@channel-stream-db.c2vugkacqzdw.us-east-1.rds.amazonaws.com:5432/channelstream -f /tmp/migrations/seed.sql\",\"echo MIGRATIONS_COMPLETE\"]" --query "Command.CommandId" --output text
```

Check the output (replace COMMAND_ID with the ID returned above):
```powershell
aws ssm get-command-invocation --command-id COMMAND_ID --instance-id i-XXXXXXXXXXXXXXX --query "{Status:Status,Output:StandardOutputContent}" --output json
```

**6. Clean up:**

```powershell
# Terminate the bastion
aws ec2 terminate-instances --instance-ids i-XXXXXXXXXXXXXXX

# Remove migration files from S3
aws s3 rm s3://channel-stream-terraform-state/migrations/ --recursive
```

> **Expected:** The first migration file (`20260427205435_remote_schema.sql`) will show errors about missing roles (`anon`, `postgres`, `authenticated`) and a missing extension (`supabase_vault`). These are Supabase-specific and don't exist on standard RDS. **These errors are safe to ignore.** The important migrations run clean — you'll see `CREATE TABLE`, `ALTER TABLE`, `INSERT` lines for the later files.

---

## Step 6 — Push the first Docker image (one time)

**Why Docker:** ECS runs your Go server as a container. A container is a self-contained package with the compiled binary and everything it needs to run. ECR (Elastic Container Registry) is AWS's private storage for Docker images — like GitHub but for containers.

### The Dockerfile

The repo includes a `Dockerfile` at the root. It uses a two-stage build:
- **Stage 1 (builder):** Uses the full Go toolchain to compile the binary
- **Stage 2 (runtime):** Copies only the compiled binary into a tiny Alpine Linux image (~10MB vs ~1GB)

### Log in to ECR

In PowerShell, piping the ECR password directly to `docker login` sometimes corrupts the token. Capture it in a variable first:

```powershell
$TOKEN = aws ecr get-login-password --region us-east-1
docker login --username AWS --password $TOKEN 435204302991.dkr.ecr.us-east-1.amazonaws.com
```

### Build and push

Run from the `Channel_Stream` root directory:

```powershell
docker build -t channel-stream-backend .
docker tag channel-stream-backend:latest 435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend:latest
docker push 435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend:latest
```

### Verify ECS picks it up

ECS will pull the image and start 2 tasks. Wait ~2 minutes, then:

```powershell
curl https://api.jonathanlohr.com/v1/health
# Expected: {"status":"ok","version":"1.0.0"}
```

If you get 503 or 504, check ECS task logs:
```powershell
aws ecs describe-services --cluster channel-stream --services channel-stream-backend --query "services[0].events[:3]" --output json
```

If tasks stopped, check CloudWatch for the reason:
```powershell
# Get the most recent log stream name
aws logs describe-log-streams --log-group-name "/ecs/channel-stream-backend" --order-by LastEventTime --descending --query "logStreams[0].logStreamName" --output text
```

If ECS is stuck from a failed earlier attempt, force a new deployment:
```powershell
aws ecs update-service --cluster channel-stream --service channel-stream-backend --force-new-deployment
```

---

## Step 7 — Upload the frontend (one time)

**Why two sync commands:** Browsers cache files aggressively. For JS/CSS files, the filename changes every build (contains a content hash), so we tell the browser to cache them forever (`max-age=31536000`). For HTML files, the filename never changes (`index.html`), so we tell the browser never to cache them (`max-age=0`) — otherwise users get stale HTML pointing at old JS files.

Run from the `Channel_Stream` root directory:

```powershell
# Build with the /channel-stream base path
$env:NEXT_PUBLIC_BASE_PATH = "/channel-stream"
$env:NEXT_PUBLIC_API_URL = "https://api.jonathanlohr.com"
npm run build

# Upload hashed assets — long cache (filenames change when content changes)
aws s3 sync out/ "s3://jonathanlohrwebsite/channel-stream/" --delete --exclude "*.html" --cache-control "public,max-age=31536000,immutable"

# Upload HTML — no cache (always serve latest version)
aws s3 sync out/ "s3://jonathanlohrwebsite/channel-stream/" --delete --exclude "*" --include "*.html" --cache-control "public,max-age=0,must-revalidate"

# Clear CloudFront so visitors see the new files immediately
aws cloudfront create-invalidation --distribution-id EK4OIENDNNXAG --paths "/channel-stream/*"
```

Open **https://jonathanlohr.com/channel-stream** — the dashboard should load.

---

## Step 8 — Set up GitHub Actions (automates all future deploys)

After this, every push to `main` automatically deploys both the backend and frontend. **This step is optional** — the site is already live. Set this up when you want hands-free deployments.

### Add secrets to GitHub

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each:

| Secret name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | From the CSV you downloaded in Step 2 |
| `AWS_SECRET_ACCESS_KEY` | From the CSV you downloaded in Step 2 |
| `PORTFOLIO_S3_BUCKET` | `jonathanlohrwebsite` |
| `PORTFOLIO_CF_ID` | `EK4OIENDNNXAG` |

### The workflow file is already in the repo

It lives at `.github/workflows/deploy.yml`. When you push to `main` it will:

1. Build the Go backend into a Docker image
2. Push the image to ECR
3. Tell ECS to deploy the new image (zero-downtime rolling update)
4. Build the Next.js static export with `NEXT_PUBLIC_BASE_PATH=/channel-stream`
5. Upload the build to `s3://jonathanlohrwebsite/channel-stream/`
6. Invalidate the CloudFront cache

### Test it

```powershell
git add .
git commit -m "test deployment pipeline"
git push origin main
```

Go to your GitHub repo → **Actions** tab — you'll see the workflow running. When it turns green, visit `https://jonathanlohr.com/channel-stream`.

---

## How it works going forward

After Step 8, a single `git push` deploys the entire application:

```
git push origin main
       ↓
GitHub Actions (.github/workflows/deploy.yml)
       │
       ├── BACKEND
       │     Build Go server into Docker image
       │     Push image to ECR
       │     Tell ECS to deploy new image
       │     ECS starts new containers, health-checks them,
       │     shifts traffic over, removes old containers
       │     → api.jonathanlohr.com serving new Go code
       │
       └── FRONTEND
             npm run build  (with basePath=/channel-stream)
             Upload /out files to S3 /channel-stream/
             Invalidate CloudFront cache
             → jonathanlohr.com/channel-stream serving new UI
```

The database (RDS) and cache (ElastiCache) are persistent — they are not redeployed on every push. Only re-run Terraform if you change `infrastructure/main.tf`.

---

## Troubleshooting

### IAM: `AccessDenied` on `s3:CreateBucket` (Terraform state bucket)

The deploy user is missing S3 permissions. Add an inline policy (inline policies don't count against the 10-policy limit):

Save this to `infrastructure/s3-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:CreateBucket","s3:DeleteBucket","s3:GetBucketLocation","s3:GetBucketVersioning","s3:PutBucketVersioning","s3:GetEncryptionConfiguration","s3:PutEncryptionConfiguration","s3:ListBucket","s3:GetObject","s3:PutObject","s3:DeleteObject"],
    "Resource": ["arn:aws:s3:::channel-stream-terraform-state","arn:aws:s3:::channel-stream-terraform-state/*"]
  }]
}
```

Then:
```powershell
aws iam put-user-policy --user-name channel-stream-deploy --policy-name s3-terraform-state --policy-document file://infrastructure/s3-policy.json
```

### IAM: `LimitExceeded — Cannot exceed quota for PoliciesPerUser: 10`

You've hit the 10 managed-policy limit. Use `put-user-policy` (inline policy) instead of `attach-user-policy`. Inline policies don't count against the limit.

### PowerShell: backslash line continuation doesn't work

In bash you can break long commands with `\`. In PowerShell, `\` is not a line-continuation character — it causes a parse error. Either:
- Put the entire command on one line, or
- Use the backtick `` ` `` as the line-continuation character

### PowerShell: JSON in `--policy-document` causes parse errors

PowerShell mangles escaped quotes in inline JSON strings. Write the JSON to a file and reference it with `file://`:

```powershell
# Write JSON to a file, then:
aws iam put-user-policy --user-name channel-stream-deploy --policy-name my-policy --policy-document file://path/to/policy.json
```

### Terraform: `VpcLimitExceeded`

AWS defaults to 5 VPCs per region. Check how many you have:
```powershell
aws ec2 describe-vpcs --query "Vpcs[*].{ID:VpcId,Name:Tags[?Key=='Name']|[0].Value,Default:IsDefault}" --output table
```

Delete the default VPC if you have 5 (it's safe to delete — AWS never uses it for anything you create):
1. Find and detach its internet gateway
2. Delete its subnets
3. Delete any non-default security groups inside it
4. Delete the VPC

### Terraform: `Invalid character` in security group blocks

HCL (Terraform's language) does not support semicolons to separate arguments on one line. Each argument must be on its own line:

```hcl
# Wrong:
ingress { from_port = 80; to_port = 80; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }

# Correct:
ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}
```

### Terraform: `terraform.tfvars` — `Invalid character` or `This character is not used`

String values in HCL must be in double quotes:
```hcl
# Wrong:
db_password = MyPassword123

# Correct:
db_password = "MyPassword123"
```

### Terraform: RDS timeout (`waiting for state to become 'available'`)

The RDS instance may have actually finished — Terraform's internal waiter just gave up. Check:
```powershell
aws rds describe-db-instances --db-instance-identifier channel-stream-db --query "DBInstances[0].DBInstanceStatus" --output text
```
If it says `available`, Terraform marked the resource as tainted (broken). Remove the taint and re-apply:
```powershell
cd infrastructure
terraform untaint aws_db_instance.postgres
terraform apply
```

### Terraform: `final_snapshot_identifier is required`

When `skip_final_snapshot = false`, Terraform requires a snapshot name before it destroys an RDS instance. This is already set in `main.tf` (`final_snapshot_identifier = "channel-stream-db-final"`). If you see this error, make sure you saved the file before running `terraform apply`.

### Terraform: ACM `AccessDeniedException`

The deploy user is missing ACM permissions. Add an inline policy:
```powershell
aws iam put-user-policy --user-name channel-stream-deploy --policy-name acm-certificate --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"acm:RequestCertificate\",\"acm:DescribeCertificate\",\"acm:DeleteCertificate\",\"acm:ListCertificates\",\"acm:AddTagsToCertificate\",\"acm:ListTagsForCertificate\"],\"Resource\":\"*\"}]}"
```

### RDS password: `not a valid password` / URL parse errors

Two separate issues:

**In `terraform.tfvars`:** RDS forbids `/`, `@`, `"`, and spaces in the master password. Use only letters, numbers, and `!`, `#`, `$`.

**In the connection URL (Secrets Manager):** The `@` character separates `user:password` from the hostname in a URL. If your password contains `@`, the URL parser gets confused. If your password contains `#`, it gets treated as a URL fragment. URL-encode these: `@` → `%40`, `#` → `%23`.

Example: password `MyPass#51` → connection string `postgresql://csadmin:MyPass%2351@hostname:5432/db`

### RDS: cannot connect from laptop (`psql` times out)

RDS is in a private subnet — there is no internet route to it. This is intentional. Use the EC2 SSM bastion approach in Step 5, or temporarily add your IP to the RDS security group for the duration of your connection:

```powershell
# Get your IP
curl https://checkip.amazonaws.com

# Get the RDS security group ID
aws ec2 describe-security-groups --filters "Name=group-name,Values=channel-stream-rds" --query "SecurityGroups[0].GroupId" --output text

# Add a temporary rule
aws ec2 authorize-security-group-ingress --group-id sg-XXXXXXXX --protocol tcp --port 5432 --cidr YOUR.IP.HERE/32

# ... run your psql commands ...

# Remove the rule when done (use the rule ID from the authorize output)
aws ec2 revoke-security-group-ingress --group-id sg-XXXXXXXX --security-group-rule-ids sgr-XXXXXXXX
```

Note: even with a security group rule, RDS in a private subnet is not routable from the internet. You also need to either make the RDS publicly accessible or use the bastion approach.

### Docker: `no such file or directory` — Dockerfile

The Dockerfile must exist at `Channel_Stream/Dockerfile`. Check that it's there:
```powershell
ls Dockerfile
```

### Docker: `go.mod requires go >= 1.X.X (running go 1.Y.Y)`

The Go version in `go.mod` must match the Docker image. Update `Dockerfile`:
```
FROM golang:1.25-alpine AS builder
```
And update `go.mod`:
```
go 1.25
```
Then run `go mod tidy` locally before building.

### Docker: `go mod tidy` needed

If you change the Go version in `go.mod`, run `go mod tidy` locally before building the Docker image. This updates `go.sum` to match. Without it, the Docker build will fail.

### Docker ECR login: `400 Bad Request`

Piping the ECR token through PowerShell's `|` can corrupt it. Capture the token first:
```powershell
$TOKEN = aws ecr get-login-password --region us-east-1
docker login --username AWS --password $TOKEN 435204302991.dkr.ecr.us-east-1.amazonaws.com
```

### ECS: 503 Service Unavailable

The load balancer has no healthy targets — ECS tasks aren't running yet. Check:
```powershell
aws ecs describe-services --cluster channel-stream --services channel-stream-backend --query "services[0].events[:3]" --output json
```

Common causes:
- Image not in ECR yet (push it first, then force a new deployment)
- Tasks crashing on startup (check CloudWatch logs)

### ECS: 504 Gateway Timeout

The load balancer can reach the tasks but they're not responding. Check CloudWatch logs for startup errors — usually a bad DATABASE_URL or missing environment variable.

### ECS: tasks fail with `CannotPullContainerError: not found`

The image wasn't in ECR when ECS tried to start. Push the image, then force ECS to retry:
```powershell
aws ecs update-service --cluster channel-stream --service channel-stream-backend --force-new-deployment
```

### ECS: `Failed to connect to database: invalid port ":YourPassword"`

The `#` character in the password is being treated as a URL fragment, cutting off the hostname. The password must be URL-encoded in the secret value. Update the secret:
```powershell
aws secretsmanager put-secret-value --secret-id "channel-stream/database-url" --secret-string "postgresql://csadmin:YourPass%2351@channel-stream-db.c2vugkacqzdw.us-east-1.rds.amazonaws.com:5432/channelstream"
```
Then force a new ECS deployment so the tasks pick up the updated secret.

### S3 sync: `AccessDenied` on `PutObject` to portfolio bucket

The deploy user needs write access to the portfolio bucket (`jonathanlohrwebsite`). Add an inline policy:
```powershell
aws iam put-user-policy --user-name channel-stream-deploy --policy-name portfolio-s3-frontend --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:PutObject\",\"s3:DeleteObject\",\"s3:GetObject\",\"s3:ListBucket\"],\"Resource\":[\"arn:aws:s3:::jonathanlohrwebsite\",\"arn:aws:s3:::jonathanlohrwebsite/*\"]},{\"Effect\":\"Allow\",\"Action\":[\"cloudfront:CreateInvalidation\"],\"Resource\":\"arn:aws:cloudfront::435204302991:distribution/EK4OIENDNNXAG\"}]}"
```

### Build error: `Export getSportsSchedule doesn't exist`

`getSportsSchedule` was missing from `lib/api.ts`. It's now added — the function calls `/v1/sports/schedule` on the Go backend.

### CloudFront still shows old version after sync

The invalidation takes 30–60 seconds. Hard-refresh your browser with `Ctrl+Shift+R`. If it still shows the old version after a minute, check the invalidation status:
```powershell
aws cloudfront list-invalidations --distribution-id EK4OIENDNNXAG --query "InvalidationList.Items[0].{ID:Id,Status:Status}" --output json
```

### `curl https://api.jonathanlohr.com/v1/health` times out

ACM certificate validation can take up to 5 minutes after `terraform apply`. Check: **AWS Console → Certificate Manager → your cert → Status**. Wait until it says "Issued".

---

## Monthly cost

| Service | ~Cost |
|---|---|
| ECS Fargate (2 tasks) | $30 |
| RDS PostgreSQL | $30 |
| ElastiCache Redis | $25 |
| Load Balancer | $20 |
| NAT Gateway | $35 |
| Everything else | $2 |
| Frontend (S3 + CloudFront) | $0 — shared with portfolio |
| **Total** | **~$142/month** |

To pause all billing: `terraform destroy`. To bring it back: `terraform apply` (~10 minutes).

---

## Checklist

- [ ] `aws sts get-caller-identity` returns account ID `435204302991`
- [ ] `terraform apply` completed without errors
- [ ] Secrets stored in Secrets Manager (database-url, redis-url)
- [ ] Database migrations ran successfully (tables created, seed data loaded)
- [ ] Docker image pushed to ECR
- [ ] `curl https://api.jonathanlohr.com/v1/health` returns `{"status":"ok","version":"1.0.0"}`
- [ ] `https://jonathanlohr.com/channel-stream` loads the dashboard
- [ ] GitHub secrets are set (4 values) — optional, for CI/CD
- [ ] Pushed to `main` and Actions workflow turned green — optional

---

**Next**: [Module 8 → Presenting Like a Real Business](./MODULE_08_PRESENTATION.md)
