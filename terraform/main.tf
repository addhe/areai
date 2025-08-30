/**
 * Auto Reply Email with AI (Vertex AI Gemini)
 * Terraform infrastructure as code for GCP resources
 */

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
    archive = {
      source = "hashicorp/archive"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required GCP APIs
resource "google_project_service" "apis" {
  for_each           = toset([
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Pub/Sub Topic for Gmail API notifications
resource "google_pubsub_topic" "email_topic" {
  name = "new-email"
  
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

# Allow Cloud Scheduler service agent to mint OIDC tokens for this service account
resource "google_service_account_iam_binding" "scheduler_token_creator" {
  service_account_id = google_service_account.autoreply_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"

  members = [
    "serviceAccount:service-${var.project_number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
  ]
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


# IAM binding for Secret Manager accessor role
resource "google_project_iam_binding" "sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.autoreply_sa.email}"
  ]
}

# Allow the service account to invoke the Cloud Run service
resource "google_cloud_run_service_iam_member" "run_invoker_autoreply_sa" {
  project  = var.project_id
  location = var.region
  service  = var.cloud_run_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.autoreply_sa.email}"
}

# Storage bucket for Cloud Function source code (optional)
resource "google_storage_bucket" "function_bucket" {
  count    = var.enable_cloud_function ? 1 : 0
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

# Cloud Function for auto-reply email (optional)
resource "google_cloudfunctions_function" "auto_reply_function" {
  count       = var.enable_cloud_function ? 1 : 0
  name        = "auto-reply-email"
  description = "Auto Reply Email with Vertex AI Gemini"
  runtime     = "python311"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket[0].name
  source_archive_object = google_storage_bucket_object.function_source[0].name
  
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
    google_project_iam_binding.sa_secret_accessor
  ]
}

# Zip the Cloud Function source code
data "archive_file" "function_source" {
  count       = var.enable_cloud_function ? 1 : 0
  type        = "zip"
  source_dir  = "${path.module}/../cloud_function"
  output_path = "${path.module}/function.zip"
}

# Upload the Cloud Function source code to the bucket
resource "google_storage_bucket_object" "function_source" {
  count  = var.enable_cloud_function ? 1 : 0
  name   = "function-${data.archive_file.function_source[0].output_md5}.zip"
  bucket = google_storage_bucket.function_bucket[0].name
  source = data.archive_file.function_source[0].output_path
}

# Secret Manager for Gmail OAuth token
resource "google_secret_manager_secret" "gmail_oauth_token" {
  secret_id = "gmail-oauth-token"
  
  replication {
    auto {}
  }
  
  labels = {
    app = "auto-reply-email"
  }
}

# Secret Manager for Customer API key
resource "google_secret_manager_secret" "customer_api_key" {
  secret_id = "customer-api-key"
  
  replication {
    auto {}
  }
  
  labels = {
    app = "auto-reply-email"
  }
}

# Cloud Monitoring alert policy for error rate
resource "google_monitoring_alert_policy" "error_alert" {
  count       = var.enable_cloud_function ? 1 : 0
  display_name = "Auto Reply Email Error Rate > 1%"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate exceeds 1%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_function\" AND resource.labels.function_name=\"auto-reply-email\" AND severity>=ERROR"
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

# ---------------------------------------------
# Cloud Scheduler jobs (call Cloud Run endpoints)
# ---------------------------------------------

# Hourly health/watch status check (GET /check-watch-status)
resource "google_cloud_scheduler_job" "check_watch_status_hourly" {
  name        = "check-watch-status-hourly"
  description = "Checks Gmail watch status via Cloud Run endpoint every hour"
  schedule    = "0 * * * *" # at minute 0 every hour
  time_zone   = var.scheduler_timezone

  http_target {
    http_method = "GET"
    uri         = "${var.cloud_run_url_base}/check-watch-status"

    headers = {
      Content-Type = "application/json"
    }

    oidc_token {
      service_account_email = google_service_account.autoreply_sa.email
      audience              = var.cloud_run_url_base
    }
  }

  attempt_deadline = "320s"

  retry_config {
    retry_count          = 3
    min_backoff_duration = "30s"
    max_backoff_duration = "300s"
    max_doublings        = 3
  }
}

# Daily Gmail watch renewal (POST /renew-watch)
resource "google_cloud_scheduler_job" "renew_watch_daily" {
  name        = "renew-gmail-watch-daily"
  description = "Renews Gmail API watch daily to prevent expiration"
  schedule    = "0 3 * * *" # 03:00 local time daily
  time_zone   = var.scheduler_timezone

  http_target {
    http_method = "POST"
    uri         = "${var.cloud_run_url_base}/renew-watch"

    headers = {
      Content-Type = "application/json"
    }

    body = base64encode("{}")

    oidc_token {
      service_account_email = google_service_account.autoreply_sa.email
      audience              = var.cloud_run_url_base
    }
  }

  attempt_deadline = "320s"

  retry_config {
    retry_count          = 5
    min_backoff_duration = "60s"
    max_backoff_duration = "600s"
    max_doublings        = 3
  }
}
