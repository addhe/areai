/**
 * Auto Reply Email with AI (Vertex AI Gemini)
 * Terraform infrastructure as code for GCP resources
 */

# Pub/Sub Topic for Gmail API notifications
resource "google_pubsub_topic" "email_topic" {
  name = "new-email"
  
  labels = {
    app = "auto-reply-email"
  }
}

# Pub/Sub Subscription for Cloud Function
resource "google_pubsub_subscription" "email_subscription" {
  name  = "email-subscriber"
  topic = google_pubsub_topic.email_topic.name
  
  ack_deadline_seconds = 20
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  expiration_policy {
    ttl = ""  # Never expire
  }
  
  labels = {
    app = "auto-reply-email"
  }
}

# Service Account for Auto Reply Email
resource "google_service_account" "autoreply_sa" {
  account_id   = "autoreply-sa"
  display_name = "Auto Reply Email Service Account"
  description  = "Service Account for Auto Reply Email with AI"
}

# IAM binding for Pub/Sub subscriber role
resource "google_project_iam_binding" "sa_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  
  members = [
    "serviceAccount:${google_service_account.autoreply_sa.email}"
  ]
}

# IAM binding for Vertex AI user role
resource "google_project_iam_binding" "sa_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  
  members = [
    "serviceAccount:${google_service_account.autoreply_sa.email}"
  ]
}

# IAM binding for Gmail modify role
resource "google_project_iam_binding" "sa_gmail_modify" {
  project = var.project_id
  role    = "roles/gmail.modify"
  
  members = [
    "serviceAccount:${google_service_account.autoreply_sa.email}"
  ]
}

# IAM binding for Secret Manager accessor role
resource "google_project_iam_binding" "sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.autoreply_sa.email}"
  ]
}

# Storage bucket for Cloud Function source code
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-functions"
  location = var.region
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 30  # days
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud Function for auto-reply email
resource "google_cloudfunctions_function" "auto_reply_function" {
  name        = "auto-reply-email"
  description = "Auto Reply Email with Vertex AI Gemini"
  runtime     = "python311"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_source.name
  
  entry_point = "pubsub_trigger"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.email_topic.name
  }
  
  environment_variables = {
    GCP_PROJECT_ID          = var.project_id
    GCP_REGION              = var.region
    CUSTOMER_API_ENDPOINT   = var.customer_api_endpoint
    LOG_LEVEL               = "INFO"
  }
  
  service_account_email = google_service_account.autoreply_sa.email
  
  timeout               = 60
  max_instances         = 100
  
  labels = {
    app = "auto-reply-email"
  }
  
  depends_on = [
    google_project_iam_binding.sa_pubsub_subscriber,
    google_project_iam_binding.sa_vertex_ai_user,
    google_project_iam_binding.sa_gmail_modify,
    google_project_iam_binding.sa_secret_accessor
  ]
}

# Zip the Cloud Function source code
data "archive_file" "function_source" {
  type        = "zip"
  source_dir  = "${path.module}/../cloud_function"
  output_path = "${path.module}/function.zip"
}

# Upload the Cloud Function source code to the bucket
resource "google_storage_bucket_object" "function_source" {
  name   = "function-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_source.output_path
}

# Secret Manager for Gmail OAuth token
resource "google_secret_manager_secret" "gmail_oauth_token" {
  secret_id = "gmail-oauth-token"
  
  replication {
    automatic = true
  }
  
  labels = {
    app = "auto-reply-email"
  }
}

# Secret Manager for Customer API key
resource "google_secret_manager_secret" "customer_api_key" {
  secret_id = "customer-api-key"
  
  replication {
    automatic = true
  }
  
  labels = {
    app = "auto-reply-email"
  }
}

# Cloud Monitoring alert policy for error rate
resource "google_monitoring_alert_policy" "error_alert" {
  display_name = "Auto Reply Email Error Rate > 1%"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate exceeds 1%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_function\" AND resource.labels.function_name=\"${google_cloudfunctions_function.auto_reply_function.name}\" AND severity>=ERROR"
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.01
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  documentation {
    content   = "Error rate for Auto Reply Email function exceeds 1%. Check Cloud Logging for details."
    mime_type = "text/markdown"
  }
}
