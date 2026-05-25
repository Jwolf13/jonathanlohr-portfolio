variable "callback_urls" {
  description = "Allowed callback URLs for OAuth2 redirects (e.g., local dev, production)"
  type        = list(string)
  default     = ["http://localhost:3000/callback"]
}

variable "logout_urls" {
  description = "Allowed logout URLs for OAuth2 logout flow"
  type        = list(string)
  default     = ["http://localhost:3000/logout"]
}

variable "user_pool_domain" {
  description = "Domain name for Cognito User Pool hosted UI"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
