/**
 * Auto Reply Email with AI (Vertex AI Gemini)
 * Terraform outputs
 */

output "pubsub_topic" {
  description = "The Pub/Sub topic for Gmail API notifications"
  value       = google_pubsub_topic.email_topic.name
}

output "function_name" {
  description = "The name of the deployed Cloud Function"
  value       = google_cloudfunctions_function.auto_reply_function.name
}

output "function_url" {
  description = "The URL of the deployed Cloud Function"
  value       = google_cloudfunctions_function.auto_reply_function.https_trigger_url
}

output "service_account" {
  description = "The service account used by the Cloud Function"
  value       = google_service_account.autoreply_sa.email
}

output "storage_bucket" {
  description = "The storage bucket for Cloud Function source code"
  value       = google_storage_bucket.function_bucket.name
}
