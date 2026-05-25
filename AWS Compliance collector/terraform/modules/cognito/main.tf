# DVA-C02: Cognito User Pool for API Gateway authentication
# Provides secure identity management for compliance dashboard access

# DVA-C02: Cognito User Pool with security best practices
resource "aws_cognito_user_pool" "compliance_dashboard" {
  name = "compliance-dashboard-users"

  # DVA-C02: Password policy enforces strong credentials
  password_policy {
    minimum_length    = 12  # DVA-C02: Minimum 12 characters
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  # DVA-C02: MFA for additional security layer
  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true  # DVA-C02: TOTP-based MFA support
  }

  # DVA-C02: Email verification for account validation
  auto_verified_attributes = ["email"]

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"  # DVA-C02: Use AWS managed email sending
  }

  # DVA-C02: User account recovery options
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # DVA-C02: Username attributes for flexible sign-in
  username_attributes = ["email"]
  case_sensitive      = false

  # DVA-C02: Enable user deletion protection
  deletion_protection = "ACTIVE"

  # DVA-C02: User pool security settings
  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  # DVA-C02: Sign-in requirements
  sign_in_policy {
    authentication_flow_policy_type = "RECOMMENDED"
  }

  # DVA-C02: Token configuration
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  access_token_validity   = 60  # 1 hour
  id_token_validity       = 60  # 1 hour
  refresh_token_validity  = 30  # 30 days

  # DVA-C02: Device tracking for compliance audit
  device_configuration {
    challenge_required_on_new_device = false
    device_only_remembered_on_user_prompt = false
  }

  tags = merge(
    var.common_tags,
    {
      Name       = "compliance-dashboard-users"
      Module     = "cognito"
      Component  = "identity"
    }
  )
}

# DVA-C02: Cognito User Pool Client for SPA applications
# Implements OAuth2/OIDC for secure API access
resource "aws_cognito_user_pool_client" "dashboard_spa" {
  user_pool_id = aws_cognito_user_pool.compliance_dashboard.id
  client_name  = "compliance-dashboard-spa"

  # DVA-C02: Prevent client secret generation for SPAs
  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"  # DVA-C02: For secure backend flows
  ]

  # DVA-C02: OAuth2 configuration for API access
  allowed_oauth_flows = [
    "code",
    "implicit"
  ]
  allowed_oauth_scopes = [
    "email",
    "openid",
    "profile",
    "aws.cognito.signin.user.admin"
  ]
  allowed_oauth_flows_user_pool_client = true

  # DVA-C02: Callback URLs for OAuth redirects
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  # DVA-C02: Token validity for secure sessions
  access_token_validity  = 60  # minutes
  id_token_validity      = 60  # minutes
  refresh_token_validity = 30  # days

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  # DVA-C02: Prevent insecure auth flows
  prevent_user_existence_errors = "ENABLED"

  # DVA-C02: Read attributes for dashboard
  read_attributes = [
    "email",
    "email_verified",
    "name",
    "given_name",
    "family_name"
  ]

  # DVA-C02: Allow attribute write for user management
  write_attributes = [
    "name",
    "given_name",
    "family_name"
  ]

  depends_on = [aws_cognito_user_pool.compliance_dashboard]
}

# DVA-C02: Resource Server for API authorization scopes
resource "aws_cognito_resource_server" "compliance_api" {
  identifier   = "compliance-api"
  name         = "Compliance API"
  user_pool_id = aws_cognito_user_pool.compliance_dashboard.id

  scope {
    scope_name        = "read"
    scope_description = "Read access to compliance data"
  }

  scope {
    scope_name        = "write"
    scope_description = "Write access to compliance data"
  }

  scope {
    scope_name        = "admin"
    scope_description = "Administrative access to compliance system"
  }
}

# DVA-C02: User Pool Domain for hosted UI
resource "aws_cognito_user_pool_domain" "compliance" {
  domain       = var.user_pool_domain
  user_pool_id = aws_cognito_user_pool.compliance_dashboard.id
}
