#!/bin/bash
# Script untuk deploy Auto Reply Email ke Google Cloud Run

set -e  # Exit on error

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Auto Reply Email - Cloud Run Deployment =====${NC}"

# Mendapatkan Project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Project ID tidak ditemukan. Silakan set project dengan:${NC}"
    echo "gcloud config set project PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"

# Konfirmasi dari user
read -p "Lanjutkan deployment? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Deployment dibatalkan."
    exit 0
fi

# 1. Enable API yang diperlukan
echo -e "\n${GREEN}1. Mengaktifkan API yang diperlukan...${NC}"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  gmail.googleapis.com \
  pubsub.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com

# 2. Buat service account jika belum ada
echo -e "\n${GREEN}2. Menyiapkan service account...${NC}"
if ! gcloud iam service-accounts describe autoreply-sa@$PROJECT_ID.iam.gserviceaccount.com &> /dev/null; then
    echo "Membuat service account autoreply-sa..."
    gcloud iam service-accounts create autoreply-sa \
        --description="Service Account for Auto Reply AI" \
        --display-name="Auto Reply AI SA"
    
    # Assign roles
    echo "Memberikan izin ke service account..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:autoreply-sa@$PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/pubsub.subscriber"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:autoreply-sa@$PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:autoreply-sa@$PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/gmail.modify"
else
    echo "Service account autoreply-sa sudah ada."
fi

# 3. Buat service account untuk Pub/Sub invoker jika belum ada
echo -e "\n${GREEN}3. Menyiapkan service account untuk Pub/Sub...${NC}"
if ! gcloud iam service-accounts describe pubsub-cloud-run-invoker@$PROJECT_ID.iam.gserviceaccount.com &> /dev/null; then
    echo "Membuat service account pubsub-cloud-run-invoker..."
    gcloud iam service-accounts create pubsub-cloud-run-invoker \
      --display-name "Pub/Sub Cloud Run Invoker"
else
    echo "Service account pubsub-cloud-run-invoker sudah ada."
fi

# 4. Create Artifact Registry repository if it doesn't exist
echo -e "\n${GREEN}4. Setting up Artifact Registry...${NC}"
if ! gcloud artifacts repositories describe auto-reply-repo --location=asia-southeast2 &> /dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create auto-reply-repo \
        --repository-format=docker \
        --location=asia-southeast2 \
        --description="Repository for Auto Reply Email images"
else
    echo "Artifact Registry repository already exists."
fi

# 5. Build dan push container image
echo -e "\n${GREEN}5. Building container image...${NC}"
gcloud builds submit --tag asia-southeast2-docker.pkg.dev/$PROJECT_ID/auto-reply-repo/auto-reply-email:latest .

# 6. Deploy ke Cloud Run
echo -e "\n${GREEN}6. Deploying ke Cloud Run...${NC}"
gcloud run deploy auto-reply-email \
  --image asia-southeast2-docker.pkg.dev/$PROJECT_ID/auto-reply-repo/auto-reply-email:latest \
  --platform managed \
  --region asia-southeast2 \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --timeout 300s \
  --service-account autoreply-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars="CUSTOMER_API_ENDPOINT=${CUSTOMER_API_ENDPOINT:-https://nasabah-api-endpoint.example.com},CUSTOMER_API_KEY=${CUSTOMER_API_KEY:-your-api-key},DESTINATION_EMAIL=${DESTINATION_EMAIL:-addhe.warman+cs@gmail.com}"

# 6. Dapatkan URL Cloud Run service
SERVICE_URL=$(gcloud run services describe auto-reply-email --format="value(status.url)")
echo -e "\n${GREEN}Cloud Run service URL: ${SERVICE_URL}${NC}"

# 7. Berikan izin ke service account Pub/Sub
echo -e "\n${GREEN}6. Memberikan izin ke service account Pub/Sub...${NC}"
gcloud run services add-iam-policy-binding auto-reply-email \
  --member="serviceAccount:pubsub-cloud-run-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# 8. Buat atau update Pub/Sub topic
echo -e "\n${GREEN}7. Menyiapkan Pub/Sub topic...${NC}"
if ! gcloud pubsub topics describe new-email &> /dev/null; then
    echo "Membuat Pub/Sub topic new-email..."
    gcloud pubsub topics create new-email
else
    echo "Pub/Sub topic new-email sudah ada."
fi

# 9. Buat Pub/Sub subscription dengan push ke Cloud Run
echo -e "\n${GREEN}8. Membuat Pub/Sub subscription untuk Cloud Run...${NC}"
if ! gcloud pubsub subscriptions describe cloud-run-email-subscription &> /dev/null; then
    echo "Membuat subscription cloud-run-email-subscription..."
    gcloud pubsub subscriptions create cloud-run-email-subscription \
      --topic=new-email \
      --push-endpoint=$SERVICE_URL/process \
      --push-auth-service-account=pubsub-cloud-run-invoker@$PROJECT_ID.iam.gserviceaccount.com
else
    echo "Memperbarui subscription cloud-run-email-subscription..."
    gcloud pubsub subscriptions update cloud-run-email-subscription \
      --push-endpoint=$SERVICE_URL/process
fi

# 10. Set min/max instances untuk scaling
echo -e "\n${GREEN}9. Mengkonfigurasi scaling...${NC}"
gcloud run services update auto-reply-email \
  --min-instances=1 \
  --max-instances=10

echo -e "\n${GREEN}===== Deployment selesai! =====${NC}"
echo -e "Cloud Run service URL: ${SERVICE_URL}"
echo -e "Health check: ${SERVICE_URL}"
echo -e "Pub/Sub endpoint: ${SERVICE_URL}/process"
echo -e "\nUntuk melihat logs:"
echo -e "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email' --limit=10"
