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

# Cloud Scheduler variables
variable "cloud_run_url_base" {
  description = "Base URL of the Cloud Run service (e.g., https://auto-reply-email-<proj>.run.app)"
  type        = string
  default     = "https://auto-reply-email-361046956504.us-central1.run.app"
}

variable "scheduler_timezone" {
  description = "Timezone for Cloud Scheduler jobs"
  type        = string
  default     = "Asia/Jakarta"
}

# Toggle to deploy legacy Cloud Function (disabled by default since we use Cloud Run)
variable "enable_cloud_function" {
  description = "Whether to deploy the legacy Cloud Function and its packaging artifacts"
  type        = bool
  default     = false
}

# Cloud Run service name for IAM bindings (must match the deployed service)
variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service to grant run.invoker to"
  type        = string
  default     = "auto-reply-email"
}

# Numeric GCP project number, used for service agent identities
variable "project_number" {
  description = "Numeric GCP project number (e.g., 361046956504)"
  type        = string
  validation {
    condition     = can(regex("^[0-9]+$", var.project_number))
    error_message = "project_number must be the numeric project number."
  }
}
