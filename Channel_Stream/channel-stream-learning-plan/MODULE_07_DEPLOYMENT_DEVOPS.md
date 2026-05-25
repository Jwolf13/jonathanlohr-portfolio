# Module 7 — Deployment & DevOps

## What you're deploying

This guide deploys the **complete Channel Stream application** — every piece of it — to AWS so it runs live on your domain. That means:

| Piece | What it is | Where it ends up |
|---|---|---|
| **Next.js frontend** | The React UI — dashboard, sports, schedule, providers pages | `jonathanlohr.com/channel-stream` |
| **Go API server** | The HTTP backend serving `/v1/sports/live`, `/v1/sports/schedule`, etc. | `api.jonathanlohr.com` |
| **ESPN ingestion worker** | The background goroutine that polls ESPN every 60s and writes game data to the DB | Runs inside the same Go server on ECS |
| **PostgreSQL database** | Stores sports events, profiles, broadcast mappings | AWS RDS (private, not publicly accessible) |
| **Redis cache** | Caches API responses — 90s for live scores, 5min for schedule | AWS ElastiCache (private) |

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

## Before you start — collect these 4 values from AWS

You'll paste these into commands below. Get them now.

| Value | Where to find it | Example |
|---|---|---|
| **S3 bucket name** | S3 → Buckets — the one your portfolio uses | `jonathanlohr-portfolio` |
| **CloudFront Distribution ID** | CloudFront → Distributions → your distro → top of page | `EABC1234DEFGHI` |
| **Route 53 Hosted Zone ID** | Route 53 → Hosted zones → jonathanlohr.com → details panel | `Z1ABC2DEF3GHI4` |
| **Your AWS Account ID** | Top-right menu in AWS Console → account number | `123456789012` |

---

## Step 1 — Install tools (if not already done)

```powershell
# Run in PowerShell as Administrator
winget install Amazon.AWSCLI
winget install Hashicorp.Terraform

# Close and reopen your terminal, then verify both work
aws --version
terraform --version
```

---

## Step 2 — Create an IAM deploy user

This gives GitHub Actions (and your terminal) permission to deploy.

1. AWS Console → **IAM** → **Users** → **Create user**
2. Name: `channel-stream-deploy`
3. **Attach policies directly** — add these:
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
4. After creating the user: **Security credentials** tab → **Create access key** → CLI use case → **Download CSV**

Now configure your terminal to use these credentials:

```bash
aws configure
# AWS Access Key ID:     (paste from CSV)
# AWS Secret Access Key: (paste from CSV)
# Default region:        us-east-1
# Default output format: json

# Verify it works — should print your account ID
aws sts get-caller-identity
```

---

## Step 3 — Deploy backend infrastructure with Terraform (one time)

This is where you provision all the AWS resources needed to run the Go backend. Terraform creates everything in one command:

- **VPC + networking** — private network for your servers, NAT gateway so the ESPN ingestion worker can make outbound HTTP calls
- **RDS PostgreSQL** — the database (sports events, profiles, broadcast mappings)
- **ElastiCache Redis** — the cache layer in front of the database
- **ECS Fargate cluster** — where the Go server and ingestion goroutine actually run (2 containers for redundancy)
- **ECR repository** — where Docker images are stored before ECS pulls them
- **Application Load Balancer** — receives traffic at `api.jonathanlohr.com` and routes it to the ECS containers
- **ACM SSL certificate** — free HTTPS for `api.jonathanlohr.com`, auto-renewing
- **Route 53 DNS record** — points `api.jonathanlohr.com` at the load balancer
- **Secrets Manager** — stores DATABASE_URL and REDIS_URL so they're never hardcoded

### Create the Terraform state bucket first

Terraform needs an S3 bucket to store its state. Create it manually (Terraform can't create its own):

```bash
aws s3 mb s3://channel-stream-terraform-state --region us-east-1
```

### Set your database password

Create the file `infrastructure/terraform.tfvars` — **do not commit this file**:

```hcl
db_password = "PickAStrongPasswordHere123!"
```

### Run Terraform

```bash
cd infrastructure/

terraform init
terraform plan      # shows everything it will create — read it over
terraform apply     # type "yes" to confirm — takes about 10 minutes
```

When it finishes you'll see:

```
Apply complete!

Outputs:
api_url    = "https://api.jonathanlohr.com"
ecr_url    = "123456789012.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend"
 "435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend"
rds_host   = <sensitive>
redis_host = <sensitive>
```

Save the `ecr_url` — you need it in Step 5.

---

## Step 4 — Store secrets (one time)

Get the database and Redis host addresses Terraform just created:

```bash
# From inside the infrastructure/ directory
RDS_HOST=$(terraform output -raw rds_host)
REDIS_HOST=$(terraform output -raw redis_host)

# Store them in AWS Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id "channel-stream/database-url" \
  --secret-string "postgresql://csadmin:PickAStrongPasswordHere123!@${RDS_HOST}:5432/channelstream"

aws secretsmanager put-secret-value \
  --secret-id "channel-stream/redis-url" \
  --secret-string "redis://${REDIS_HOST}:6379"
```

---

## Step 5 — Run database migrations (one time)

```bash
# Set the connection string (same password you used in Step 4)
RDS_HOST=$(terraform output -raw rds_host)
export DATABASE_URL="postgresql://csadmin:PickAStrongPasswordHere123!@${RDS_HOST}:5432/channelstream"

# Go back to the Channel_Stream root
cd ..

# Apply every migration file in order
for f in supabase/migrations/*.sql; do
  echo "Running $f..."
  psql "$DATABASE_URL" -f "$f"
done

# Load the seed data (demo profile, followed teams, broadcast mappings)
psql "$DATABASE_URL" -f supabase/seed.sql
```

> If `psql` isn't installed: `winget install PostgreSQL.psql` or download from postgresql.org

---

## Step 6 — Push the first Docker image (one time)

```bash
# Paste your ecr_url from Step 3
ECR_URL="435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend"

# Log in to ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "$ECR_URL"

# Build and push (run from the Channel_Stream root directory)
docker build -t channel-stream-backend .
docker tag channel-stream-backend:latest "$ECR_URL:latest"
docker push "$ECR_URL:latest"
```

ECS will automatically pull this image and start 2 tasks. Wait ~2 minutes then verify:

```bash
curl https://api.jonathanlohr.com/v1/health
# Expected: {"status":"ok","version":"1.0.0"}
```

---

## Step 7 — Upload the frontend (one time)

Build and push the Next.js static export into your existing S3 bucket:

```bash
# Paste your actual bucket name and CloudFront ID from the "Before you start" table
PORTFOLIO_BUCKET="jonathanlohr-portfolio"    # ← replace with yours
CF_ID="EABC1234DEFGHI"                       # ← replace with yours

 PORTFOLIO_BUCKET = jonathanlohrwebsite                                                                                                                                                                                                                                                                                                                                                                                    #cloudfront ID                   
  - CF_ID = EK4OIENDNNXAG  
# Build with the /channel-stream base path
NEXT_PUBLIC_BASE_PATH=/channel-stream \
NEXT_PUBLIC_API_URL=https://api.jonathanlohr.com \
npm run build



# Upload hashed assets — long cache (filenames change when content changes)
aws s3 sync out/ "s3://${PORTFOLIO_BUCKET}/channel-stream/" \
  --delete \
  --exclude "*.html" \
  --cache-control "public,max-age=31536000,immutable"

# Upload HTML — no cache (always serve latest version)
aws s3 sync out/ "s3://${PORTFOLIO_BUCKET}/channel-stream/" \
  --delete \
  --exclude "*" --include "*.html" \
  --cache-control "public,max-age=0,must-revalidate"

# Clear CloudFront so visitors see the new files immediately
aws cloudfront create-invalidation \
  --distribution-id "$CF_ID" \
  --paths "/channel-stream/*"
```

Open **https://jonathanlohr.com/channel-stream** — the dashboard should load.

---

## Step 8 — Set up GitHub Actions (automates all future deploys)

After this, every push to `main` automatically deploys both the backend and frontend.

### Add secrets to GitHub

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each of these:

| Secret name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | From the CSV you downloaded in Step 2 |
| `AWS_SECRET_ACCESS_KEY` | From the CSV you downloaded in Step 2 |
| `PORTFOLIO_S3_BUCKET` | Your S3 bucket name (e.g. `jonathanlohr-portfolio`) |
| `PORTFOLIO_CF_ID` | Your CloudFront Distribution ID (e.g. `EABC1234DEFGHI`) |

### The workflow file is already in the repo

It lives at `.github/workflows/deploy.yml`. When you push to `main` it will:

1. Build the Go backend into a Docker image
2. Push the image to ECR
3. Tell ECS to deploy the new image (zero-downtime rolling update)
4. Build the Next.js static export with `NEXT_PUBLIC_BASE_PATH=/channel-stream`
5. Upload the build to `s3://your-bucket/channel-stream/`
6. Invalidate the CloudFront cache

### Test it

```bash
# Make a small change, commit, and push
git add .
git commit -m "test deployment pipeline"
git push origin main
```

Go to your GitHub repo → **Actions** tab — you'll see the workflow running.
When it turns green, visit `https://jonathanlohr.com/channel-stream`.

---

## How it works going forward

After Step 8, a single `git push` deploys the entire application — both frontend and backend:

```
git push origin main
       ↓
GitHub Actions (.github/workflows/deploy.yml)
       │
       ├── BACKEND
       │     Build Go server into Docker image
       │     Push image to ECR (AWS Docker registry)
       │     Tell ECS to deploy new image
       │     ECS starts new containers, health-checks them,
       │     shifts traffic over, removes old containers
       │     → api.jonathanlohr.com serving new Go code
       │
       └── FRONTEND
             npm run build  (with basePath=/channel-stream)
             Upload /out files to S3 bucket /channel-stream/
             Invalidate CloudFront cache
             → jonathanlohr.com/channel-stream serving new UI
```

The database (RDS) and cache (ElastiCache) are not redeployed on every push — they're persistent infrastructure managed by Terraform. Only redeploy Terraform if you change `infrastructure/main.tf`.

---

## Troubleshooting

**`aws configure` says command not found**
→ Close your terminal completely and reopen it after the `winget install` commands.

**`terraform apply` fails on the Route 53 data source**
→ Your hosted zone name in Route 53 must be exactly `jonathanlohr.com` (no trailing dot).
   Check: AWS Console → Route 53 → Hosted zones.

**`curl https://api.jonathanlohr.com/v1/health` times out**
→ ACM certificate validation can take up to 5 minutes after `terraform apply`.
   Check: AWS Console → Certificate Manager → your cert → status.

**The dashboard loads but API calls fail (CORS error in browser console)**
→ The Go server needs to allow `jonathanlohr.com` as an origin.
   Add `CORS_ORIGIN=https://jonathanlohr.com` to the ECS task definition environment variables.

**S3 upload succeeds but CloudFront still shows old version**
→ The invalidation takes ~30 seconds. Hard-refresh the browser (`Ctrl+Shift+R`).

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

To pause: `terraform destroy` stops all billing. `terraform apply` brings it back in ~10 minutes.

---

## Checklist

- [ ] `aws sts get-caller-identity` works
- [ ] `terraform apply` completed without errors
- [ ] `curl https://api.jonathanlohr.com/v1/health` returns `{"status":"ok"}`
- [ ] `https://jonathanlohr.com/channel-stream` loads the dashboard
- [ ] GitHub secrets are set (4 values)
- [ ] Pushed to `main` and Actions workflow turned green
- [ ] Second push deploys automatically without any manual steps

---

**Next**: [Module 8 → Presenting Like a Real Business](./MODULE_08_PRESENTATION.md)
