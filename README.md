# AI-Powered Email Auto-Reply System

This repository contains the source code for an intelligent email auto-reply system built on Google Cloud Platform. It uses Vertex AI's Gemini model to generate context-aware replies to incoming emails, providing a fully automated and smart communication assistant.

## Overview

The core of this project is a serverless function (`functions/auto_reply`) that is triggered by new emails via Gmail API and Pub/Sub. It includes robust security features, comprehensive testing, and automated deployment scripts.

## Key Documentation

For detailed information, please refer to the following documents:

-   **[Architecture Overview](docs/architecture.md)**: A high-level look at the system design and components.
-   **[Deployment Guide](docs/deployment_guide.md)**: Step-by-step instructions for deploying the application to Google Cloud Run.
-   **[Auto-Reply Function README](functions/auto_reply/README.md)**: Detailed documentation for the core auto-reply service, including its specific setup and testing procedures.

## Getting Started

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    ```
2.  **Navigate to the function directory**:
    ```bash
    cd functions/auto_reply
    ```
3.  **Follow the setup instructions** in the `functions/auto_reply/README.md` file to configure authentication, permissions, and deploy the service.

## Contributing

Please read our [coding style guide](coding_style.md) for details on our code standards and contribution process.

![Google Cloud Platform](https://img.shields.io/badge/GCP-Cloud_Functions-4285F4?logo=google-cloud)
![Vertex AI](https://img.shields.io/badge/Vertex_AI-Gemini-0F9D58?logo=google-cloud)
![CI/CD](https://img.shields.io/badge/CI_CD-GitLab_Flow-FC6D26?logo=gitlab)

Sistem auto-reply email berbasis AI yang secara otomatis membalas email masuk menggunakan Vertex AI Gemini dengan integrasi penuh Google Cloud (Gmail API, Pub/Sub, Cloud Functions). Dirancang untuk meningkatkan kecepatan respon pelanggan tanpa intervensi manual.

## 📌 Fitur Utama

- **Auto-Reply Real-Time** - Balas email dalam <15 detik setelah email masuk
- **Kontekstual & Profesional** - Balasan disesuaikan dengan konten email menggunakan prompt engineering
- **Event-Driven Architecture** - Menggunakan Pub/Sub untuk pemrosesan asinkron
- **Cloud-Native** - Terintegrasi dengan Gmail API, Vertex AI, dan Cloud Functions
- **Monitoring Terpadu** - Dashboard KPI dan alerting untuk error rate >1%

## 🏗️ Arsitektur Sistem

```
+-------------+     +-------------+     +-----------------+     +--------------+
|   Gmail     | --> |   Pub/Sub   | --> | Cloud Function  | --> | Vertex AI    |
|   API (Watch)|     | (new-email) |     | (auto-reply-email)|     | (Gemini)     |
+-------------+     +-------------+     +-----------------+     +--------------+
        ^                                                           |
        |                                                           v
        +------------------- Gmail API (Send) <---------------------+
```

### Komponen Utama
1. **Gmail API** - Memantau email masuk dan mengirim balasan
2. **Pub/Sub** - Mekanisme event-driven untuk trigger Cloud Function
3. **Cloud Function** - Memproses email dan berinteraksi dengan Vertex AI
4. **Vertex AI Gemini** - Menghasilkan konten balasan berbasis konteks email
5. **Nasabah API** - Memverifikasi status pelanggan dan mengambil data untuk personalisasi balasan

## ⚙️ Prerequisites

- Akun GCP dengan akses **Owner/Editor**
- Domain Gmail (Google Workspace atau consumer)
- Google Cloud SDK (`gcloud`) terinstall
- Python 3.11
- Git

## 🚀 Setup & Deployment

### 1. Enable API yang Dibutuhkan
```bash
gcloud services enable \
  gmail.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Konfigurasi Service Account
```bash
gcloud iam service-accounts create autoreply-sa \
    --description="Service Account for Auto Reply AI" \
    --display-name="Auto Reply AI SA"

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

### 3. Setup OAuth & Credentials
1. Buat OAuth 2.0 Client ID di [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Generate token OAuth:
```bash
python scripts/gmail_auth.py
```

### 4. Konfigurasi Pub/Sub
```bash
gcloud pubsub topics create new-email
gcloud pubsub subscriptions create email-subscriber --topic=new-email
```

### 5. Deploy Cloud Function
```bash
gcloud functions deploy auto-reply-email \
  --runtime python311 \
  --trigger-topic new-email \
  --entry-point pubsub_trigger \
  --service-account autoreply-sa@PROJECT_ID.iam.gserviceaccount.com \
  --region us-central1 \
  --memory 256MB \
  --timeout 60s \
  --set-env-vars CUSTOMER_API_ENDPOINT=https://nasabah-api-endpoint.example.com,CUSTOMER_API_KEY=your-api-key
```

## 📊 Monitoring & Alerting

Sistem dilengkapi dengan:
- **Cloud Logging** - Log detail setiap balasan (pengirim, status, timestamp)
- **Dashboard KPI** - Jumlah email dibalas, error rate, waktu respon rata-rata
- **Alerting Otomatis** - Notifikasi jika error >1% atau latency >15 detik

Contoh query log error:
```bash
resource.type="cloud_function" 
resource.labels.function_name="auto-reply-email" 
severity>=ERROR
```

## 🧪 Testing

### Test Case Penting
| ID | Test Case | Target |
|----|-----------|--------|
| TC-001 | Email masuk → Auto reply | <15 detik |
| TC-002 | Balasan sesuai konteks | ≥90% relevansi |
| TC-004 | Load 1000 email/jam | 95% sukses |

Jalankan test end-to-end:
```bash
gcloud functions logs read auto-reply-email
```

## 🔄 CI/CD Pipeline

Menggunakan GitLab CI dengan alur:
1. **Validate** - Lint & validasi Terraform/Python
2. **Plan** - `terraform plan` untuk preview perubahan infra
3. **Apply** - Deploy infra ke GCP (manual approval)
4. **Deploy Function** - Auto-deploy kode setelah infra siap

Konfigurasi variabel GitLab CI:
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCP_SERVICE_ACCOUNT_KEY`
- `TF_STATE_BUCKET`

## 📝 Prompt Engineering

Contoh struktur prompt untuk Vertex AI:
```text
Anda adalah asisten email profesional. 
Tugas Anda adalah membalas email masuk dengan jawaban yang sopan, singkat, dan jelas. 
Gunakan gaya bahasa formal.

Berikut detail email yang masuk:
- Pengirim: client@abc.com
- Subjek: Permintaan Penawaran Harga
- Isi email: 
Mohon kirimkan daftar harga terbaru untuk produk X.

Balas email ini dengan nada formal. Jangan sertakan tanda tangan pribadi.
```

## 📄 Dokumentasi Lengkap

| Dokumen | Deskripsi |
|---------|-----------|
| [BRD](brd.md) | Business Requirements Document |
| [PRD](prd.md) | Product Requirements Document |
| [SDD](sdd.md) | Software Design Document |
| [TDD](tdd.md) | Technical Design Document |
| [Deployment Guide](deployment.md) | Panduan deployment lengkap |
| [CI/CD Guide](cicd.md) | Pipeline infrastruktur sebagai kode |
| [Monitoring Guide](monitoring.md) | Setup monitoring dan alerting |
| [Test Plan](test_plan.md) | Strategi pengujian dan test case |

## 📜 License

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
