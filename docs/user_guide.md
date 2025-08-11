# Sistem Balas Email Otomatis - Panduan Pengguna

This guide provides step-by-step instructions for setting up, configuring, and using the Auto Reply Email system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Authentication Setup](#authentication-setup)
5. [Deployment](#deployment)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)
10. [FAQ](#faq)

## Prerequisites

Before you begin, ensure you have the following:

- Google Cloud Platform account with billing enabled
- Google Workspace or Gmail account
- Google Cloud SDK (`gcloud`) installed and configured
- Python 3.11 or higher
- Terraform 1.5.7 or higher (for infrastructure deployment)
- Git

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/areai.git
cd areai
```

2. **Set up a virtual environment**

```bash
make setup
source .venv/bin/activate
```

3. **Install dependencies**

```bash
make install
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
CUSTOMER_API_ENDPOINT=https://nasabah-api-endpoint.example.com
CUSTOMER_API_KEY=your-api-key-here
LOGGING_LEVEL=INFO
ENABLE_CUSTOMER_VERIFICATION=true
```

### Terraform Variables

Create a `terraform.tfvars` file in the `terraform` directory:

```
project_id = "your-project-id"
region = "us-central1"
customer_api_endpoint = "https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah"
customer_api_key = "b7f2e1c4-9a3d-4e8b-8c2a-7d5e6f1a2b3c"
notification_channels = ["email:admin@example.com"]
```

## Authentication Setup

### Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Web application type)
3. Add authorized redirect URIs:
   - `http://localhost:8080`
   - `https://developers.google.com/oauthplayground`
4. Download the credentials JSON file and save it as `credentials.json` in the project root

### Generate OAuth Token

Run the authentication script:

```bash
make auth
```

This will:
1. Open a browser window for authentication
2. Request Gmail API permissions
3. Generate and save `token.json`
4. Provide instructions for uploading the token to Secret Manager

## Deployment

### Option 1: Manual Deployment

1. **Enable required APIs**

```bash
gcloud services enable \
  gmail.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com
```

2. **Deploy infrastructure with Terraform**

```bash
make deploy-infra
```

3. **Upload OAuth token to Secret Manager**

```bash
gcloud secrets versions add gmail-oauth-token --data-file=token.json
```

4. **Deploy Cloud Function**

```bash
make deploy-function
```

5. **Set up Gmail API watch**

```bash
make watch
```

### Option 2: Automated Deployment

Use the deployment script for a guided setup:

```bash
python scripts/deploy.py
```

## Testing

### Send Test Email

```bash
make test-email TO=your-email@example.com
```

### Run Comprehensive System Test

```bash
python scripts/test_system.py --to=your-email@example.com
```

### Run Unit and Integration Tests

```bash
make test
```

## Monitoring

### Set Up Monitoring Dashboard and Alerts

```bash
python scripts/setup_monitoring.py --email=admin@example.com
```

### View Cloud Function Logs

```bash
make logs
```

### Key Metrics to Monitor

1. **Response Time**: Should be < 15 seconds
2. **Error Rate**: Should be < 1%
3. **Success Rate**: Should be > 99%
4. **Email Processing Rate**: Number of emails processed per minute

## Troubleshooting

### Common Issues and Solutions

#### OAuth Token Expired

**Symptom**: Authentication errors in Cloud Function logs

**Solution**: Regenerate the OAuth token and update Secret Manager

```bash
make auth
gcloud secrets versions add gmail-oauth-token --data-file=token.json
```

#### Gmail API Watch Expired

**Symptom**: No new emails being processed

**Solution**: Renew the Gmail API watch

```bash
make watch
```

#### High Error Rate

**Symptom**: Alert notifications for error rate > 1%

**Solution**: Check Cloud Function logs for specific error messages

```bash
make logs
```

#### Slow Response Time

**Symptom**: Alert notifications for response time > 15 seconds

**Solution**: 
1. Increase Cloud Function memory allocation
2. Optimize Vertex AI prompt
3. Check for network latency issues

## Advanced Configuration

### Customizing AI Prompts

Edit the prompt templates in `cloud_function/utils/vertex_ai.py`:

```python
def create_prompt(sender, subject, body, tone, customer_info=None):
    """
    Customize the prompt structure and instructions here
    """
```

### Integrating with Custom Customer API

1. Update the `CUSTOMER_API_ENDPOINT` environment variable
2. Modify `cloud_function/utils/customer_api.py` to match your API's response format

### Adjusting Retry Parameters

Edit retry configurations in each utility module:

```python
# Example: cloud_function/utils/gmail.py
MAX_RETRIES = 5
BASE_DELAY = 1  # seconds
```

## FAQ

### How often does the Gmail API token need to be refreshed?

OAuth tokens typically expire after 7 days. The system will automatically refresh the token if a refresh token is available, but you may need to manually refresh it if authentication issues occur.

### Can the system handle attachments?

The current implementation focuses on text-based emails. Attachment handling would require additional development.

### How many emails can the system process?

The system is designed to scale with demand. The practical limit depends on:
- Gmail API quotas (1 billion units/day)
- Vertex AI quotas (varies by tier)
- Cloud Function scaling limits

### Is the system multilingual?

The current implementation works best with English emails. For other languages, you may need to customize the AI prompts and add language detection.

### How secure is the email content?

Email content is processed in-memory only and is not persistently stored. All communications use encrypted connections, and authentication is handled via OAuth 2.0.

## Support

For additional support:

- Check the [architecture documentation](architecture.md)
- Review the [API documentation](api.md)
- Submit issues via the project's issue tracker
- Contact the development team at support@example.com

## Operational Endpoints (v2.1.0)

- **GET `/check-watch-status`**: Periksa status Gmail watch (perhatikan `historyId` dan `expiration`).
- **POST `/renew-watch`**: Perbarui Gmail watch sebelum kedaluwarsa.
- **POST `/test-pubsub`**: Simulasi pesan Pub/Sub untuk menguji alur pemrosesan.

## Privacy & Isolation Notes (v2.1.0)

- **Isolasi Chat per Email**: Sistem memulai sesi chat Vertex AI baru per email menggunakan `start_chat(history=[])` agar tidak ada memori silang antar pelanggan/thread.
- **Stripping Riwayat**: Teks kutipan/riwayat dihapus dari body sebelum diproses untuk membatasi konteks.
- **Sanitasi Output**: Balasan AI disaring untuk meredaksi email selain `addhe.warman+cs@gmail.com` dan deretan digit panjang (PII).
- **Header Aman**: `From` dan `Reply-To` disetel ke `addhe.warman+cs@gmail.com` untuk memastikan balasan diteruskan ke alias +cs.
