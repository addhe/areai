/**
 * Auto Reply Email with AI (Vertex AI Gemini)
 * Terraform variables
 */

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "customer_api_endpoint" {
  description = "Customer API endpoint URL"
  type        = string
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}
