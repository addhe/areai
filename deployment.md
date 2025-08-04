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

## **14. Post-Deployment Checklist**

* [ ] API Gmail dan Pub/Sub aktif.  
* [ ] Fungsi auto-reply berhasil trigger dari email masuk.  
* [ ] Balasan AI sesuai prompt dan tone.  
* [ ] Log tercatat di Cloud Logging.  
* [ ] Monitoring alert aktif.
