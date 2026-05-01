# ─── Cognito User Pool ────────────────────────────────────────────────────────

variable "google_client_id" {
  description = "Google OAuth client ID — set in terraform.tfvars"
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret — set in terraform.tfvars"
  sensitive   = true
}

resource "aws_cognito_user_pool" "main" {
  name = "channel-stream-users"

  auto_verified_attributes = ["email"]
  username_attributes      = ["email"]

  username_configuration {
    case_sensitive = false
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = { Environment = var.environment }
}

# Google as Social Identity Provider
resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id             = var.google_client_id
    client_secret         = var.google_client_secret
    authorize_scopes      = "email openid profile"
    oidc_issuer           = "https://accounts.google.com"
    token_request_method  = "POST"
    token_url             = "https://www.googleapis.com/oauth2/v4/token"
    attributes_url        = "https://people.googleapis.com/v1/people/me?personFields="
    attributes_url_add_attributes = "true"
    authorize_url         = "https://accounts.google.com/o/oauth2/v2/auth"
  }

  attribute_mapping = {
    email    = "email"
    username = "sub"
    name     = "name"
    picture  = "picture"
  }
}

# App client — PKCE, no secret (required for browser-based SPA)
resource "aws_cognito_user_pool_client" "spa" {
  name         = "channel-stream-spa"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false

  callback_urls = [
    "https://jonathanlohr.com/channel-stream/auth/callback",
    "http://localhost:3000/auth/callback",
  ]
  logout_urls = [
    "https://jonathanlohr.com/channel-stream",
    "http://localhost:3000",
  ]

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["openid", "email", "profile"]

  supported_identity_providers = ["Google"]

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]

  depends_on = [aws_cognito_identity_provider.google]
}

# Hosted UI domain — gives us the /oauth2/authorize endpoint
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "channel-stream-jl"
  user_pool_id = aws_cognito_user_pool.main.id
}

# ─── Outputs ──────────────────────────────────────────────────────────────────

output "cognito_user_pool_id" {
  value       = aws_cognito_user_pool.main.id
  description = "Set as COGNITO_POOL_ID env var in ECS"
}

output "cognito_client_id" {
  value       = aws_cognito_user_pool_client.spa.id
  description = "Set as NEXT_PUBLIC_COGNITO_CLIENT_ID in Next.js build"
}

output "cognito_domain" {
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
  description = "Set as NEXT_PUBLIC_COGNITO_DOMAIN in Next.js build"
}
