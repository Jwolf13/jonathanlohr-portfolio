# Apex Benchmark AWS Deployment — May 26, 2026
## Plain English SOP: How to Deploy a FastAPI App on AWS ECS with RDS

---

## The Big Picture

We took a FastAPI Python app that lived on your laptop and put it on the internet using AWS. Here's the final architecture:

```
You (Browser)
      |
      | HTTP port 80 (public internet)
      v
+------------------+
| Load Balancer    |  <-- The "front door". Only thing exposed to internet.
| (ALB)            |      Lives in PUBLIC subnets.
+------------------+
      |
      | port 8000 (private network only)
      v
+------------------+
| ECS Fargate Task |  <-- Your Docker container running FastAPI.
| (apex-benchmark) |      Lives in PRIVATE subnets.
+------------------+
      |
      | port 5432 (private network only)
      v
+------------------+
| Aurora RDS       |  <-- Your PostgreSQL database.
| (apex-benchmark) |      Lives in PRIVATE subnets.
+------------------+

All of the above lives inside:
+-----------------------------------------------+
|  VPC: channel-stream (vpc-0dbbdd0e9db5cb430)  |
|                                               |
|  PUBLIC subnets:   channel-stream-public-0    |
|                    channel-stream-public-1    |
|                    (have internet access)     |
|                                               |
|  PRIVATE subnets:  channel-stream-private-0   |
|                    channel-stream-private-1   |
|                    (no direct internet)       |
+-----------------------------------------------+
```

---

## Key Concepts (Plain English)

**VPC** — A private bubble of networking inside AWS. Think of it like your own private office building. Nothing gets in or out unless you explicitly open a door.

**Subnets** — Rooms inside that building. Public rooms have windows to the street (internet). Private rooms don't — you can only reach them from inside the building.

**Security Group** — A firewall rule on each resource. Like a bouncer at each door: "only let in traffic from this specific place on this specific port."

**Load Balancer (ALB)** — The public-facing receptionist. Takes internet traffic on port 80 and routes it to your app container. Also runs health checks to make sure your app is alive.

**ECS Fargate** — Runs your Docker container without you needing to manage any servers. You give it a Docker image, it runs it.

**ECR** — AWS's private Docker Hub. Where you store your Docker images before ECS pulls them.

**RDS Aurora** — Managed PostgreSQL. AWS handles backups, patching, and uptime. You just connect to it.

**Task Definition** — A config file that tells ECS: what Docker image to run, how much CPU/memory to give it, what environment variables to inject, and where to send logs.

**ECS Service** — Keeps your task running. If it crashes, the service restarts it. Also connects it to the load balancer.

---

## Security Group Wiring

Each resource has a firewall. Here's what each one allows:

```
apex-benchmark-ecs (ECS tasks)
  INBOUND:
    - port 80  from 0.0.0.0/0     (ALB sends health checks here)
    - port 8000 from 0.0.0.0/0    (ALB forwards app traffic here)

apex-benchmark-rds (RDS database)
  INBOUND:
    - port 5432 from apex-benchmark-ecs  (only ECS can talk to DB)
```

---

## What We Did Step by Step

### Step 1 — Figured Out the VPC
We already had a working VPC from the Channel Stream project (`channel-stream`, `10.0.0.0/16`). Rather than create a new one, we reused it. The correct VPC is always the one with **Default: No** but named after your project, with your subnets inside it.

**How to identify your VPC:** Go to EC2 → Load Balancers → click any working resource → it shows the VPC ID.

---

### Step 2 — Created RDS (Database)
We had to do this manually in the console because Terraform permissions weren't set up yet.

**What we set:**
- Engine: PostgreSQL (Aurora)
- DB identifier: `apex-benchmark`
- Username: `apexadmin`
- VPC: the channel-stream VPC
- Subnet group: `channel-stream` (private subnets only)
- Public access: No
- Security group: `apex-benchmark-rds` (new, empty inbound rules for now)

**Why Aurora and not regular RDS?** Aurora is AWS's enhanced PostgreSQL — it's faster and has automatic failover. The connection works the same way from your app.

**The gotcha:** Aurora doesn't create the database inside the cluster automatically. You have to either specify it on creation OR create it in code. We handled this in the startup script.

---

### Step 3 — Added IAM Permissions
Your IAM user didn't have enough permissions to run Terraform or do much in AWS.

**Fix:** IAM → Users → your user → Add permissions → Attach `AdministratorAccess`

For a personal project this is fine. In a company you'd use more specific policies.

---

### Step 4 — Pushed Docker Image to ECR
ECR is AWS's private container registry. ECS pulls your image from here.

```
Your Machine
     |
     | docker build
     v
Docker Image (local)
     |
     | docker tag + docker push
     v
ECR Repository (435204302991.dkr.ecr.us-east-1.amazonaws.com/apex-benchmark)
     |
     | ECS pulls on deploy
     v
Running Container
```

**Commands to push a new image:**
```bash
# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 435204302991.dkr.ecr.us-east-1.amazonaws.com

# Build, tag, push
docker build -t apex-benchmark ./apex_benchmark
docker tag apex-benchmark:latest 435204302991.dkr.ecr.us-east-1.amazonaws.com/apex-benchmark:latest
docker push 435204302991.dkr.ecr.us-east-1.amazonaws.com/apex-benchmark:latest
```

---

### Step 5 — Created ECS Cluster
Just a logical grouping for your tasks and services. Name: `apex-benchmark`, type: Fargate.

---

### Step 6 — Created Task Definition
This is the config that tells ECS how to run your container.

**Key fields:**
- Image: your ECR URI
- CPU: 256 (0.25 vCPU)
- Memory: 512 MB
- Port: 8000
- Environment variable: `DATABASE_URL` (the full PostgreSQL connection string)
- Execution Role: `ecsTaskExecutionRole` (lets ECS pull from ECR and write logs)
- Task Role: `ecsTaskRole` (lets the running container call AWS APIs)

**The two roles explained:**
```
ecsTaskExecutionRole  — used by ECS ITSELF to set up the container
                        (pull image from ECR, create CloudWatch log group)

ecsTaskRole           — used by YOUR APP while it's running
                        (call other AWS services if needed)
```

---

### Step 7 — Created ECS Service + Load Balancer
The service keeps your task running and wires it to the load balancer.

**Critical mistake to avoid:** When the wizard asks for subnets, put:
- **Load Balancer** → PUBLIC subnets (`channel-stream-public-0`, `channel-stream-public-1`)
- **ECS Tasks** → PRIVATE subnets (`channel-stream-private-0`, `channel-stream-private-1`)

We originally put the ALB in private subnets and the site was unreachable. Private subnets have no internet gateway route — the internet can't reach them.

---

### Step 8 — Fixed Security Groups

**Problem 1:** ECS tasks couldn't receive traffic from the ALB.
- Fix: Add inbound rule to `apex-benchmark-ecs` → TCP port 8000 from `0.0.0.0/0`

**Problem 2:** ECS tasks couldn't connect to RDS.
- Fix: Add inbound rule to `apex-benchmark-rds` → PostgreSQL port 5432 from `apex-benchmark-ecs` security group

**Problem 3:** CloudWatch couldn't create log groups.
- Fix: IAM → Roles → `ecsTaskExecutionRole` → attach `CloudWatchLogsFullAccess`

---

### Step 9 — Fixed Database Migrations

**Problem 1:** Alembic was connecting to `localhost` instead of RDS.
- Root cause: `alembic/env.py` was reading from `alembic.ini` which had `localhost` hardcoded.
- Fix: Updated `env.py` to read `DATABASE_URL` from environment variables first.

```python
# In alembic/env.py — run_migrations_online()
import os
url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
```

**Problem 2:** The database `apexbenchmark` didn't exist inside Aurora.
- Root cause: Aurora creates the cluster but not the database inside it unless you explicitly create it.
- Fix: Added a `start.sh` script that creates the DB if it doesn't exist, then runs migrations, then seeds data, then starts the server.

```
Container starts
      |
      v
start.sh runs:
  1. CREATE DATABASE apexbenchmark (if not exists)
  2. alembic upgrade head  (creates tables)
  3. python -m app.db.seed (inserts benchmark data, skips if already seeded)
  4. uvicorn starts (app is live)
```

---

## SOP: How to Deploy This Again From Scratch

### Prerequisites
- AWS CLI installed and configured (`aws configure`)
- Docker Desktop running
- AWS account with AdministratorAccess

### Step-by-Step

**1. Create ECR repository**
```
AWS Console → ECR → Create repository → name: apex-benchmark → Private
```

**2. Push Docker image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
docker build -t apex-benchmark ./apex_benchmark
docker tag apex-benchmark:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/apex-benchmark:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/apex-benchmark:latest
```

**3. Create RDS Aurora PostgreSQL**
- VPC: your project VPC
- Subnet group: private subnets only
- Public access: No
- Note the writer endpoint URL

**4. Create ECS Cluster**
- Type: Fargate

**5. Register Task Definition**
```bash
aws ecs register-task-definition --cli-input-json file://apex_benchmark/task-definition.json --region us-east-1
```

**6. Create ECS Service**
- ALB subnets: PUBLIC
- Task subnets: PRIVATE
- Health check path: `/health`

**7. Fix IAM roles**
- `ecsTaskExecutionRole` needs: `CloudWatchLogsFullAccess`, `AmazonECS_FullAccess`, ECR pull permissions
- `ecsTaskRole` needs: `AmazonSSMManagedInstanceCore`

**8. Fix Security Groups**
- ECS SG inbound: port 8000 from ALB
- RDS SG inbound: port 5432 from ECS security group

**9. Verify**
- ECS task shows RUNNING
- Target group shows healthy
- Hit the ALB DNS name in browser

---

## How to Deploy a Code Update

```bash
# 1. Build and push new image
docker build -t apex-benchmark ./apex_benchmark
docker tag apex-benchmark:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# 2. Force ECS to pull the new image
aws ecs update-service \
  --cluster apex-benchmark \
  --service <service-name> \
  --force-new-deployment \
  --region us-east-1
```

ECS will pull the new image, start a new task, wait for it to pass health checks, then stop the old task. Zero downtime.

---

## Useful AWS Console Shortcuts

| What you want to check | Where to go |
|---|---|
| Is my app running? | ECS → Clusters → apex-benchmark → Tasks |
| Why did my task crash? | ECS → Tasks → click task → Logs tab |
| Is the ALB routing traffic? | EC2 → Target Groups → Targets tab |
| What's my app's URL? | EC2 → Load Balancers → DNS name |
| Database connection issues? | Check Security Groups → RDS inbound rules |
| App can't reach internet? | Check if ECS is in PUBLIC vs PRIVATE subnet |
