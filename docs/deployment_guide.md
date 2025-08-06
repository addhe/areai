# Panduan Deployment untuk Sistem Balas Email Otomatis

This guide provides step-by-step instructions for deploying the Auto Reply Email system on Google Cloud Platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Authentication Configuration](#authentication-configuration)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Application Deployment](#application-deployment)
6. [Testing the Deployment](#testing-the-deployment)
7. [Post-Deployment Tasks](#post-deployment-tasks)

## Prerequisites

Before beginning the deployment, ensure you have the following:

- Google Cloud Platform account with billing enabled
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
- [Terraform](https://www.terraform.io/downloads.html) (v1.0.0+) installed
- [Python](https://www.python.org/downloads/) (v3.8+) installed
- [Git](https://git-scm.com/downloads) installed

## Project Setup

### Step 1: Create a Google Cloud Project

```bash
# Create a new GCP project
gcloud projects create auto-reply-email-system --name="Auto Reply Email System"

# Set the project as the current default
gcloud config set project auto-reply-email-system

# Enable billing for the project (replace with your billing account ID)
gcloud billing projects link auto-reply-email-system --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### Step 2: Enable Required APIs

```bash
# Enable required Google Cloud APIs
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  gmail.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### Step 3: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/auto-reply-email-system.git
cd auto-reply-email-system
```

## Authentication Configuration

### Step 1: Create OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Click **Create Credentials** > **OAuth client ID**
4. Select **Web application** as the application type
5. Set a name for the client (e.g., "Auto Reply Email OAuth Client")
6. Add authorized redirect URIs:
   - `http://localhost:8080/oauth2callback` (for local testing)
   - `https://YOUR_DOMAIN/oauth2callback` (for production)
7. Click **Create**
8. Download the client secret JSON file

### Step 2: Set Up OAuth Authentication

```bash
# Move the downloaded client secret to the project directory
mv ~/Downloads/client_secret_*.json ./client_secret.json

# Run the OAuth setup script
python scripts/gmail_auth.py --client-secret client_secret.json
```

Follow the prompts to authenticate with your Gmail account. This will:
1. Open a browser window for authentication
2. Ask you to grant permissions to the application
3. Generate and save the OAuth token

### Step 3: Store OAuth Token in Secret Manager

```bash
# Create a Secret Manager secret for the OAuth token
gcloud secrets create gmail-oauth-token --replication-policy="automatic"

# Store the token in the secret
gcloud secrets versions add gmail-oauth-token --data-file="token.json"
```

## Infrastructure Deployment

### Step 1: Configure Terraform Variables

Create a `terraform.tfvars` file in the `terraform` directory:

```bash
cd terraform
cat > terraform.tfvars << EOF
project_id      = "auto-reply-email-system"
region          = "us-central1"
pubsub_topic    = "email-notifications"
function_name   = "auto-reply-email"
oauth_secret_id = "gmail-oauth-token"
EOF
```

### Step 2: Initialize and Apply Terraform Configuration

```bash
# Initialize Terraform
terraform init

# Validate the configuration
terraform validate

# See the execution plan
terraform plan

# Apply the configuration
terraform apply
```

This will create the following resources:
- Service Account for the Cloud Function
- Pub/Sub Topic for email notifications
- Cloud Function for email processing
- IAM permissions for the service account
- Firestore database (if not already created)
- Monitoring alerts and dashboards

## Application Deployment

### Step 1: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cd ..
cat > .env << EOF
GCP_PROJECT_ID=auto-reply-email-system
GCP_REGION=us-central1
PUBSUB_TOPIC=email-notifications
FUNCTION_NAME=auto-reply-email
OAUTH_SECRET_ID=gmail-oauth-token
LOG_LEVEL=INFO
VERTEX_AI_MODEL=gemini-1.0-pro
RESPONSE_TIMEOUT=12
EOF
```

### Step 2: Deploy the Cloud Function

```bash
# Deploy the Cloud Function
gcloud functions deploy auto-reply-email \
  --runtime python310 \
  --trigger-topic email-notifications \
  --entry-point process_email \
  --source ./cloud_function \
  --service-account auto-reply-email-sa@auto-reply-email-system.iam.gserviceaccount.com \
  --env-vars-file .env.yaml \
  --memory 512MB \
  --timeout 60s
```

### Step 3: Set Up Gmail Watch

```bash
# Set up Gmail watch to receive notifications
python scripts/setup_gmail_watch.py
```

## Testing the Deployment

### Step 1: Send a Test Email

Send a test email to the Gmail account you used for authentication.

### Step 2: Check Cloud Function Logs

```bash
# View Cloud Function logs
gcloud functions logs read auto-reply-email --limit 50
```

### Step 3: Run Integration Tests

```bash
# Run integration tests
python -m pytest tests/integration -v
```

## Post-Deployment Tasks

### Step 1: Set Up Monitoring

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Monitoring** > **Dashboards**
3. Find the "Auto Reply Email System" dashboard
4. Explore the metrics and alerts

### Step 2: Configure Alerting Policies

```bash
# Deploy alerting policies
python scripts/setup_monitoring.py --create-alerts --notification-email=your-email@example.com
```

### Step 3: Schedule Regular Token Refresh

```bash
# Create a Cloud Scheduler job to refresh the OAuth token
gcloud scheduler jobs create http refresh-oauth-token \
  --schedule="0 */12 * * *" \
  --uri="https://us-central1-auto-reply-email-system.cloudfunctions.net/refresh-oauth-token" \
  --http-method=POST \
  --oidc-service-account-email=auto-reply-email-sa@auto-reply-email-system.iam.gserviceaccount.com
```

## Advanced Configuration

### Customizing AI Response Parameters

To customize the AI response parameters, modify the `.env` file:

```bash
# Edit the .env file
cat > .env << EOF
GCP_PROJECT_ID=auto-reply-email-system
GCP_REGION=us-central1
PUBSUB_TOPIC=email-notifications
FUNCTION_NAME=auto-reply-email
OAUTH_SECRET_ID=gmail-oauth-token
LOG_LEVEL=INFO
VERTEX_AI_MODEL=gemini-1.0-pro
RESPONSE_TIMEOUT=12
MAX_TOKENS=800
TEMPERATURE=0.7
TOP_P=0.95
TOP_K=40
EOF
```

Then update the Cloud Function:

```bash
# Update the Cloud Function with new environment variables
gcloud functions deploy auto-reply-email \
  --update-env-vars-file .env.yaml
```

### Setting Up Multi-User Support

For multi-user support, follow these additional steps:

1. Create a Firestore collection for users:

```python
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client()

# Create a user document
user_ref = db.collection('users').document('user@example.com')
user_ref.set({
    'email': 'user@example.com',
    'name': 'Example User',
    'created_at': firestore.SERVER_TIMESTAMP,
    'status': 'active',
    'preferences': {
        'response_tone': 'formal',
        'ai_model': 'gemini-1.0-pro',
        'max_tokens': 800
    }
})
```

2. Run the multi-user setup script:

```bash
# Set up multi-user support
python scripts/setup_multi_user.py --admin-email=admin@example.com
```

### Configuring CI/CD Pipeline

1. Create a `cloudbuild.yaml` file:

```yaml
steps:
  # Run tests
  - name: 'python:3.10'
    entrypoint: pip
    args: ['install', '-r', 'requirements-dev.txt']
  
  - name: 'python:3.10'
    entrypoint: python
    args: ['-m', 'pytest', 'tests/', '-v']
  
  # Deploy Cloud Function
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        gcloud functions deploy auto-reply-email \
          --runtime python310 \
          --trigger-topic email-notifications \
          --entry-point process_email \
          --source ./cloud_function \
          --service-account auto-reply-email-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --env-vars-file .env.yaml \
          --memory 512MB \
          --timeout 60s
```

2. Set up the Cloud Build trigger:

```bash
# Create a Cloud Build trigger
gcloud builds triggers create github \
  --repo-name=auto-reply-email-system \
  --repo-owner=yourusername \
  --branch-pattern=main \
  --build-config=cloudbuild.yaml
```

## Troubleshooting

### Common Issues

1. **OAuth Token Expired**

If you see "Token expired" errors in the logs:

```bash
# Refresh the OAuth token
python scripts/gmail_auth.py --refresh-only
```

2. **Gmail Watch Not Working**

If you're not receiving notifications:

```bash
# Check Gmail watch status
python scripts/check_gmail_watch.py

# Renew Gmail watch
python scripts/setup_gmail_watch.py --renew
```

3. **Cloud Function Deployment Failures**

If the Cloud Function fails to deploy:

```bash
# Check for errors in the deployment
gcloud functions deploy auto-reply-email \
  --runtime python310 \
  --trigger-topic email-notifications \
  --entry-point process_email \
  --source ./cloud_function \
  --verbosity=debug
```

For more troubleshooting information, refer to the [Troubleshooting Guide](troubleshooting_guide.md).

## Next Steps

After successful deployment, consider:

1. Implementing [performance optimizations](performance_optimization.md) for better response times
2. Enhancing AI responses using the [prompt engineering guide](prompt_engineering.md)
3. Implementing [security best practices](security_best_practices.md)
4. Setting up [AI model evaluation](ai_model_evaluation.md) to track response quality
5. Planning for [scaling](scaling_guide.md) as your usage grows

## Conclusion

You have successfully deployed the Auto Reply Email system on Google Cloud Platform. The system is now configured to automatically respond to incoming emails using AI-generated responses.

For ongoing maintenance and optimization, refer to the other guides in the documentation directory.
