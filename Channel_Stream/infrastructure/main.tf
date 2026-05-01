# Channel Stream — AWS Backend Infrastructure
#
# What this manages:
#   Network, database, cache, Go API server, Docker registry, SSL, DNS
#
# What this does NOT manage:
#   The Next.js frontend — that's static files uploaded to the portfolio's
#   existing S3 bucket under /channel-stream/ by the CI pipeline.
#
# URLs after deploy:
#   jonathanlohr.com/channel-stream  →  Next.js (portfolio S3 + CloudFront)
#   api.jonathanlohr.com             →  Go backend (this file's ALB → ECS)

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "channel-stream-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ─── Variables ─────────────────────────────────────────────────────────────────

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

variable "db_password" {
  description = "RDS master password — set in terraform.tfvars, never commit that file"
  sensitive   = true
}

# ─── Data ──────────────────────────────────────────────────────────────────────

data "aws_availability_zones" "available" {}

# Looks up the hosted zone you created in Route 53 for jonathanlohr.com
data "aws_route53_zone" "jonathanlohr" {
  name         = "jonathanlohr.com"
  private_zone = false
}

# ─── VPC + Networking ──────────────────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "channel-stream" }
}

# Public subnets — ALB and NAT gateway live here
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "channel-stream-public-${count.index}" }
}

# Private subnets — ECS, RDS, Redis live here (no direct internet access)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = { Name = "channel-stream-private-${count.index}" }
}

# Internet gateway — lets public subnets reach the internet
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT gateway — lets private subnets make outbound calls (ESPN API ingestion needs this)
resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  depends_on    = [aws_internet_gateway.main]
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ─── Security Groups ───────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name   = "channel-stream-alb"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name   = "channel-stream-ecs"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name   = "channel-stream-rds"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ─── SSL Certificate — api.jonathanlohr.com ────────────────────────────────────

resource "aws_acm_certificate" "api" {
  domain_name       = "api.jonathanlohr.com"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }
  zone_id = data.aws_route53_zone.jonathanlohr.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# ─── Load Balancer — api.jonathanlohr.com ──────────────────────────────────────

resource "aws_lb" "backend" {
  name               = "channel-stream-api"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "backend" {
  name        = "channel-stream-api"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path              = "/v1/health"
    healthy_threshold = 2
    interval          = 30
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate_validation.api.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ─── DNS — api.jonathanlohr.com → ALB ─────────────────────────────────────────

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.jonathanlohr.zone_id
  name    = "api.jonathanlohr.com"
  type    = "A"

  alias {
    name                   = aws_lb.backend.dns_name
    zone_id                = aws_lb.backend.zone_id
    evaluate_target_health = true
  }
}

# ─── RDS PostgreSQL ────────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "channel-stream"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier             = "channel-stream-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "channelstream"
  username               = "csadmin"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = true
  backup_retention_period = 7
  deletion_protection    = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "channel-stream-db-final"
  tags                   = { Environment = var.environment }
}

# ─── ElastiCache Redis ─────────────────────────────────────────────────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "channel-stream"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "channel-stream-redis"
  description                = "Channel Stream Redis"
  node_type                  = "cache.t3.micro"
  num_cache_clusters         = 2
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  automatic_failover_enabled = true
  tags                       = { Environment = var.environment }
}

# ─── ECR — Docker image registry ───────────────────────────────────────────────

resource "aws_ecr_repository" "backend" {
  name = "channel-stream-backend"
  image_scanning_configuration { scan_on_push = true }
}

# ─── Secrets Manager ───────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "db_url" {
  name = "channel-stream/database-url"
}

resource "aws_secretsmanager_secret" "redis_url" {
  name = "channel-stream/redis-url"
}

# ─── IAM — ECS execution role ──────────────────────────────────────────────────

resource "aws_iam_role" "ecs_execution" {
  name = "channel-stream-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_secrets" {
  name = "read-secrets"
  role = aws_iam_role.ecs_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.db_url.arn, aws_secretsmanager_secret.redis_url.arn]
    }]
  })
}

# ─── CloudWatch Logs ───────────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/channel-stream-backend"
  retention_in_days = 30
}

# ─── ECS Fargate — Go backend ──────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "channel-stream"
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "channel-stream-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"

    portMappings = [{ containerPort = 8080, protocol = "tcp" }]

    environment = [
      { name = "PORT",    value = "8080" },
      { name = "APP_ENV", value = "production" },
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.db_url.arn },
      { name = "REDIS_URL",    valueFrom = aws_secretsmanager_secret.redis_url.arn },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "channel-stream-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.https]
}

# ─── Outputs ───────────────────────────────────────────────────────────────────

output "api_url" {
  value = "https://api.jonathanlohr.com"
}

output "ecr_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "Push Docker images here"
}

output "rds_host" {
  value     = aws_db_instance.postgres.address  # host only, no port
  sensitive = true
}

output "redis_host" {
  value     = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive = true
}
