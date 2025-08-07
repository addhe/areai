# Deployment Guide

This guide provides detailed instructions for deploying the AI-powered auto-reply system to Google Cloud Run.

## Prerequisites

Before you begin, ensure you have the following:

1.  **Google Cloud Project**: A project with billing enabled.
2.  **gcloud CLI**: The Google Cloud command-line tool, authenticated and configured to use your project.
3.  **Enabled APIs**:
    -   Cloud Build API (`cloudbuild.googleapis.com`)
    -   Cloud Run API (`run.googleapis.com`)
    -   Gmail API (`gmail.googleapis.com`)
    -   Pub/Sub API (`pubsub.googleapis.com`)
    -   Vertex AI API (`aiplatform.googleapis.com`)
    -   Secret Manager API (`secretmanager.googleapis.com`)
4.  **Project ID**: Know your Google Cloud Project ID.

## Deployment Steps

The deployment process is automated via a shell script. This script handles building the Docker container, pushing it to the Artifact Registry, and deploying it as a Cloud Run service.

1.  **Navigate to the function directory**:
    ```bash
    cd functions/auto_reply
    ```

2.  **Set Environment Variables**:
    The `deploy.sh` script requires your Google Cloud Project ID. You can set it as an environment variable:
    ```bash
    export PROJECT_ID="your-gcp-project-id"
    ```
    Replace `your-gcp-project-id` with your actual Project ID.

3.  **Run the Deployment Script**:
    Execute the script to start the deployment:
    ```bash
    ./deploy.sh
    ```

    The script will perform the following actions:
    -   Enable necessary Google Cloud services.
    -   Build the Docker image using the `Dockerfile`.
    -   Tag the image appropriately.
    -   Push the image to Google Artifact Registry.
    -   Deploy the image to Google Cloud Run, creating a new service or updating an existing one.

## Post-Deployment Verification

After the deployment script completes successfully, you should verify that the service is running correctly.

1.  **Get the Service URL**: The deployment script will output the URL of the newly deployed service.
2.  **Health Check**:
    Access the root URL (`/`) of the service in a web browser or using `curl`. It should return a `200 OK` status with a JSON payload indicating a healthy status.
    ```bash
    curl https://your-cloud-run-service-url
    ```
3.  **Test the Process Endpoint**:
    Use the `simple_test.py` or `comprehensive_test.py` scripts to send a test request to the `/process` endpoint and ensure it responds with `200 OK`.

## Important Notes

-   **Service Account**: The `deploy.sh` script configures the Cloud Run service to use the default Compute Engine service account. Ensure this service account has the necessary permissions as outlined in `setup_permissions.py`.
-   **Authentication**: The application relies on OAuth2 credentials stored in Secret Manager. Make sure you have completed the `gmail_auth.py` setup before deploying.

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Overview**

Panduan ini menjelaskan langkah-langkah lengkap untuk melakukan deployment sistem auto-reply email berbasis AI di Google Cloud Platform (GCP), mulai dari persiapan lingkungan, enable API, konfigurasi OAuth, deployment fungsi, hingga pengujian end-to-end.

---

## **2. Prerequisites**

* Akun GCP aktif dengan akses **Owner** atau **Editor**.  
* Domain Gmail (Gmail consumer atau Google Workspace).  
* **Google Cloud SDK (gcloud CLI)** terinstall.  
* Python 3.11 terinstall (untuk Cloud Functions).  
* Git & editor (VSCode atau setara).  

---

## **3. Enable Required APIs**

Jalankan perintah berikut untuk mengaktifkan API yang dibutuhkan:

```bash
gcloud services enable \
  gmail.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com
```

---

## **4. Project Setup**

### **4.1 Set Project**

```bash
gcloud config set project PROJECT_ID
```

### **4.2 Buat Service Account**

```bash
gcloud iam service-accounts create autoreply-sa \
    --description="Service Account for Auto Reply AI" \
    --display-name="Auto Reply AI SA"
```

### **4.3 Assign Roles**

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:autoreply-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:autoreply-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:autoreply-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/gmail.modify"
```

---

## **5. OAuth & Credentials Setup**

### **5.1 Create OAuth Credentials**

1. Buka [Google Cloud Console → API & Services → Credentials](https://console.cloud.google.com/apis/credentials).  
2. Buat **OAuth 2.0 Client ID** (type: Web Application).  
3. Simpan `client_id` dan `client_secret`.  

### **5.2 Authorize Gmail API**

* Jalankan script Python untuk generate `token.json` via flow OAuth:

```bash
python scripts/gmail_auth.py --project-id=PROJECT_ID --topic=new-email --save-to-secret-manager
```

### **5.3 OAuth Troubleshooting**

Jika mengalami masalah dengan redirect URI:

1. Pastikan OAuth client dikonfigurasi dengan redirect URI yang benar:
   - Buka [Google Cloud Console → API & Services → Credentials](https://console.cloud.google.com/apis/credentials)
   - Edit OAuth client ID
   - Tambahkan redirect URI: `http://localhost:4443/`

2. Jika port 8080 atau port lain sudah digunakan, script akan mendeteksi dan memberikan pesan error. Gunakan port alternatif (seperti 4443) dan pastikan redirect URI dikonfigurasi dengan benar.

3. Setelah autentikasi berhasil, token akan disimpan di:
   - File lokal: `token.json`
   - Google Secret Manager: `gmail-oauth-token`

---

## **6. Pub/Sub Setup**

### **6.1 Create Topic**

```bash
gcloud pubsub topics create new-email
```

### **6.2 Test Gmail API Integration**

Untuk memastikan integrasi Gmail API dan Pub/Sub berfungsi dengan baik:

```bash
python scripts/test_gmail_integration.py --project-id=PROJECT_ID --topic=new-email --wait-time=90
```

Script ini akan:
1. Mengirim email test ke alamat yang ditentukan
2. Membuat subscription sementara ke topic Pub/Sub
3. Menunggu notifikasi dari Gmail API watch
4. Memverifikasi bahwa notifikasi diterima dengan benar

### **6.3 Create Subscription**

```bash
gcloud pubsub subscriptions create email-subscriber \
  --topic=new-email
```

---

## **7. Gmail Watch Setup**

### **7.1 Set Watch**

Gunakan Gmail API untuk set watch ke Pub/Sub:

```bash
POST https://gmail.googleapis.com/gmail/v1/users/me/watch
Content-Type: application/json

{
  "labelIds": ["INBOX"],
  "topicName": "projects/PROJECT_ID/topics/new-email"
}
```

Respon akan mengembalikan `historyId` awal.

---

## **8. Cloud Run Service**

### **8.1 Existing Service**

Service Cloud Run `auto-reply-email` sudah ter-deploy di region `asia-southeast2` dengan URL:

```
https://auto-reply-email-361046956504.asia-southeast2.run.app
```

### **8.2 Update Service (jika diperlukan)**

Untuk mengupdate service yang sudah ada:

```bash
gcloud run deploy auto-reply-email \
  --source . \
  --region asia-southeast2 \
  --platform managed \
  --allow-unauthenticated \
  --service-account autoreply-sa@awanmasterpiece.iam.gserviceaccount.com \
  --set-env-vars PROJECT_ID=awanmasterpiece,SECRET_NAME=gmail-oauth-token,VERTEX_MODEL=gemini-1.5-pro
```

### **8.3 Verify Service**

```bash
gcloud run services describe auto-reply-email --region asia-southeast2
```

### **8.4 Configure Pub/Sub Trigger**

Pastikan Pub/Sub topic `new-email` memiliki subscription yang mengarah ke service Cloud Run:

```bash
gcloud pubsub subscriptions create auto-reply-subscription \
  --topic new-email \
  --push-endpoint=https://auto-reply-email-361046956504.asia-southeast2.run.app \
  --push-auth-service-account=autoreply-sa@awanmasterpiece.iam.gserviceaccount.com
```

### **8.5 Test Service**

Untuk menguji service:
1. Kirim email ke alamat yang terhubung dengan Gmail API watch
2. Tunggu beberapa detik untuk pemrosesan
3. Periksa inbox untuk melihat auto-reply yang dikirim
4. Periksa logs untuk memastikan service berjalan dengan benar:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email" --limit=50
```

---

## **9. Vertex AI Model Setup**

* Gunakan model `gemini-1.5-pro` langsung via API (tidak perlu deployment khusus).  
* Pastikan sudah enable Vertex AI API (lihat step 3).  

---

## **10. Secret Management**

* Simpan OAuth token & API keys ke Secret Manager:

```bash
gcloud secrets create gmail-oauth-token --replication-policy="automatic"
gcloud secrets versions add gmail-oauth-token --data-file=token.json
```

* Simpan endpoint API pelanggan ke Secret Manager:

```bash
gcloud secrets create customer-api-endpoint --replication-policy="automatic"
gcloud secrets versions add customer-api-endpoint --data-file=customer_api_endpoint.txt
```

---

## **11. Gmail Watch Maintenance**

### **11.1 Watch Duration**

Gmail API watch hanya aktif selama 7 hari dan perlu diperbarui secara berkala. Pastikan untuk menjadwalkan pembaruan watch sebelum kedaluwarsa.

### **11.2 Script untuk Aktivasi Watch**

Berikut contoh script Python untuk mengaktifkan Gmail watch:

```python
#!/usr/bin/env python3
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.cloud import secretmanager

# Konfigurasi
PROJECT_ID = "your-project-id"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/new-email"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SECRET_NAME = "gmail-oauth-token"

def get_credentials():
    """Mendapatkan credentials dari Secret Manager atau file lokal."""
    try:
        # Coba ambil dari Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token_json = response.payload.data.decode("UTF-8")
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    except Exception as e:
        print(f"Error accessing Secret Manager: {e}")
        # Fallback ke file lokal
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_info(
                json.loads(open('token.json', 'r').read()), SCOPES)
        else:
            raise Exception("No credentials available")
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Credentials invalid and cannot be refreshed")
            
    return creds

def setup_gmail_watch():
    """Setup Gmail API watch untuk notifikasi ke Pub/Sub."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    
    request = {
        'labelIds': ['INBOX'],
        'topicName': TOPIC_NAME
    }
    
    response = service.users().watch(userId='me', body=request).execute()
    print(f"Watch setup successful. History ID: {response.get('historyId')}")
    print(f"Expiration: {response.get('expiration')}")
    return response

if __name__ == "__main__":
    setup_gmail_watch()
```

### **11.3 Menjadwalkan Pembaruan Watch**

Gunakan Cloud Scheduler untuk menjadwalkan pembaruan watch setiap 6 hari:

```bash
gcloud scheduler jobs create http renew-gmail-watch \
  --schedule="0 0 */6 * *" \
  --uri="https://auto-reply-email-361046956504.asia-southeast2.run.app/renew-watch" \
  --http-method=POST \
  --oidc-service-account-email=autoreply-sa@PROJECT_ID.iam.gserviceaccount.com
```

### **11.4 Monitoring Watch Status**

Untuk memverifikasi status watch:

```python
def check_watch_status():
    """Check if Gmail API watch is active."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    
    # Get profile to check if watch is active
    profile = service.users().getProfile(userId='me').execute()
    history_id = profile.get('historyId')
    
    if history_id:
        print(f"Watch appears to be active. Current history ID: {history_id}")
        return True
    else:
        print("Watch status could not be determined")
        return False
```

### **11.5 Troubleshooting Watch Issues**

Jika notifikasi tidak diterima:

1. Verifikasi status watch dengan script di atas
2. Periksa Pub/Sub subscription metrics di Cloud Console
3. Periksa logs untuk error:
   ```bash
   gcloud logging read "resource.type=pubsub_subscription AND resource.labels.subscription_id=auto-reply-subscription" --limit=20
   ```
4. Jika diperlukan, hapus watch dan setup ulang:
   ```python
   service.users().stop(userId='me').execute()
   ```
---

## **11. Testing End-to-End**

### **11.1 Functional Test**

1. Kirim email ke inbox target.  
2. Lihat log Cloud Functions:

```bash
gcloud functions logs read auto-reply-email
```

3. Pastikan balasan otomatis terkirim ke pengirim.  

### **11.2 Load Test**

* Kirim 50-100 email serentak, pantau Pub/Sub queue & response time.  

### **11.3 Negative Test**

* Kirim email tanpa body → balasan default.  
* Simulasikan error (hapus token) → cek retry Pub/Sub.  

---

## **12. Monitoring & Alerting**

* Aktifkan **Cloud Logging** untuk semua fungsi.  
* Buat alert jika error > 1%:

```bash
gcloud monitoring policies create --notification-channels=EMAIL \
  --condition-display-name="Auto Reply Errors >1%" \
  --condition-filter='metric.type="cloudfunctions.googleapis.com/function/execution_count" AND metric.label."status"="error"'
```

---

## **13. Rollback Strategy**

* Simpan versi function sebelumnya (`--version-id`).  
* Rollback cepat:

```bash
gcloud functions versions describe FUNCTION_NAME
gcloud functions rollback FUNCTION_NAME VERSION_ID
```

---

## **14. Deployment ke Google Cloud Run**

### **14.1 Persiapan Deployment**

1. Buat file `Dockerfile` di root project:

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUSTOMER_API_ENDPOINT="https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah"
ENV CUSTOMER_API_KEY="your-api-key-here"

# Expose port untuk Cloud Run
EXPOSE 8080

# Run the application
CMD ["python", "cloud_run_server.py"]
```

2. Buat file `cloud_run_server.py` untuk endpoint HTTP:

```python
import os
import json
import base64
import logging
from flask import Flask, request, jsonify
from cloud_function.main import process_email, validate_message

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "auto-reply-email"})

@app.route("/process", methods=["POST"])
def handle_request():
    try:
        envelope = request.get_json()
        if not envelope:
            return jsonify({"error": "no Pub/Sub message received"}), 400

        if not isinstance(envelope, dict) or "message" not in envelope:
            return jsonify({"error": "invalid Pub/Sub message format"}), 400

        # Process the Pub/Sub message
        pubsub_message = envelope["message"]
        if not validate_message(pubsub_message):
            return jsonify({"error": "invalid message format"}), 400

        # Process the email
        result = process_email(pubsub_message)
        return jsonify({"success": True, "result": result})

    except Exception as e:
        logger.exception(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT, debug=False)
```

3. Buat atau perbarui `requirements.txt` untuk Cloud Run:

```
flask==2.3.3
gunicorn==21.2.0
google-cloud-pubsub==2.18.4
google-cloud-aiplatform==1.36.4
google-auth==2.23.0
google-api-python-client==2.108.0
requests==2.31.0
python-dotenv==1.0.0
```

### **14.2 Build dan Deploy ke Cloud Run**

1. Build container image dan push ke Container Registry:

```bash
# Set variabel project
export PROJECT_ID=$(gcloud config get-value project)

# Build image dengan Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/auto-reply-email .
```

2. Deploy ke Cloud Run:

```bash
gcloud run deploy auto-reply-email \
  --image gcr.io/$PROJECT_ID/auto-reply-email \
  --platform managed \
  --region asia-southeast2 \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --timeout 300s \
  --service-account autoreply-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars="CUSTOMER_API_ENDPOINT=https://nasabah-api-endpoint.example.com,CUSTOMER_API_KEY=your-api-key-here"
```

### **14.3 Konfigurasi Pub/Sub Trigger untuk Cloud Run**

1. Buat service account untuk Pub/Sub:

```bash
gcloud iam service-accounts create pubsub-cloud-run-invoker \
  --display-name "Pub/Sub Cloud Run Invoker"
```

2. Berikan izin ke service account:

```bash
gcloud run services add-iam-policy-binding auto-reply-email \
  --member="serviceAccount:pubsub-cloud-run-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

3. Buat Pub/Sub subscription dengan push ke Cloud Run:

```bash
gcloud pubsub subscriptions create cloud-run-email-subscription \
  --topic=new-email \
  --push-endpoint=$(gcloud run services describe auto-reply-email --format="value(status.url)")/process \
  --push-auth-service-account=pubsub-cloud-run-invoker@$PROJECT_ID.iam.gserviceaccount.com
```

### **14.4 Scaling dan Performance**

* Cloud Run akan otomatis scale berdasarkan load
* Konfigurasi default: 0-100 instances
* Untuk mengatur min/max instances:

```bash
gcloud run services update auto-reply-email \
  --min-instances=1 \
  --max-instances=10
```

## **15. Post-Deployment Checklist**

* [ ] API Gmail dan Pub/Sub aktif.  
* [ ] Fungsi auto-reply berhasil trigger dari email masuk.  
* [ ] Balasan AI sesuai prompt dan tone.  
* [ ] Log tercatat di Cloud Logging.  
* [ ] Monitoring alert aktif.
* [ ] Cloud Run service berjalan dan dapat menerima request.
* [ ] Pub/Sub berhasil trigger endpoint Cloud Run.
