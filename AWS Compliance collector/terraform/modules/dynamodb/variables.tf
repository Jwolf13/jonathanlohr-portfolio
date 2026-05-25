variable "table_name" {
  description = "Name of the DynamoDB table for compliance data storage"
  type        = string
  default     = "ComplianceData"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
