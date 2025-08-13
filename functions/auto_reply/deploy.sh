#!/bin/bash
# Deployment script for auto-reply service to Cloud Run

set -e  # Exit on error

# Validate required environment variables
if [ -z "${NASABAH_API_KEY}" ]; then
  echo "Error: Environment variable NASABAH_API_KEY tidak diset." >&2
  echo "Gunakan: export NASABAH_API_KEY=\"your-api-key-here\"" >&2
  exit 1
fi

# Configuration
PROJECT_ID="awanmasterpiece"
REGION="us-central1"
SERVICE_NAME="auto-reply-email"
SERVICE_ACCOUNT="autoreply-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Deploying ${SERVICE_NAME} to Cloud Run in ${REGION}..."
echo "Using NASABAH API Key: ${NASABAH_API_KEY:0:10}..."

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},SECRET_NAME=gmail-oauth-token,VERTEX_MODEL=gemini-2.5-flash-lite,USE_PRIMARY_FROM=true,PRIMARY_FROM=addhe.warman@gmail.com,NASABAH_API_URL=https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah,NASABAH_API_KEY=${NASABAH_API_KEY}" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s \
  --max-instances 3

echo "Deployment completed!"
echo "To view logs, run:"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND severity>=INFO\" --limit=20 --project=${PROJECT_ID}"
