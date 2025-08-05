# **Deployment Guide**

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
python scripts/gmail_auth.py
```

---

## **6. Pub/Sub Setup**

### **6.1 Create Topic**

```bash
gcloud pubsub topics create new-email
```

### **6.2 Create Subscription**

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

## **8. Deploy Cloud Function**

### **8.1 Code Structure**

```
auto-reply/
├── main.py
├── requirements.txt
├── utils/
│   └── gmail.py
│   └── vertex_ai.py
└── config.json
```

### **8.2 Deploy Command**

```bash
gcloud functions deploy auto-reply-email \
  --runtime python311 \
  --trigger-topic new-email \
  --entry-point pubsub_trigger \
  --service-account autoreply-sa@PROJECT_ID.iam.gserviceaccount.com \
  --region us-central1 \
  --memory 256MB \
  --timeout 60s
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
