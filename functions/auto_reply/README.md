# Sistem Balas Otomatis Email dengan Gmail API dan Vertex AI

Direktori ini berisi sistem balas email otomatis canggih yang didukung AI, dirancang untuk berjalan di Google Cloud. Sistem ini memanfaatkan Gmail API, Pub/Sub untuk notifikasi real-time, dan Vertex AI (khususnya model Gemini) untuk menghasilkan respons yang cerdas dan sesuai konteks terhadap email yang masuk.

## Arsitektur

Sistem ini dirancang sebagai aplikasi serverless yang ditujukan untuk deployment di Google Cloud Run. Alur kerjanya adalah sebagai berikut:

1.  **Gmail Watch**: Gmail API dikonfigurasi untuk memantau akun email tertentu untuk pesan baru.
2.  **Notifikasi Pub/Sub**: Ketika email baru tiba, Gmail mengirimkan notifikasi ke topik Pub/Sub yang telah ditentukan.
3.  **Pemicu Cloud Run**: Langganan Pub/Sub memicu layanan Cloud Run, yang menjadi host aplikasi Flask (`main.py`).
4.  **Pemrosesan Email**: Aplikasi menerima notifikasi, mengambil konten email baru menggunakan Gmail API, dan melakukan beberapa pemeriksaan keamanan (misalnya, validasi pengirim, penyaringan spam, usia email).
5.  **Pembuatan Respons AI**: Jika email lolos pemeriksaan, kontennya dikirim ke model Gemini Vertex AI (`generate_ai_genai.py`) untuk menghasilkan balasan yang relevan.
6.  **Kirim Balasan**: Respons yang dihasilkan dikirim kembali ke pengirim asli melalui Gmail API.

## Fitur Utama

-   **Balasan Berbasis AI**: Menggunakan Vertex AI Gemini untuk menghasilkan respons email yang mirip manusia.
-   **Pemrosesan Real-time**: Memanfaatkan notifikasi push Gmail API melalui Pub/Sub untuk respons segera.
-   **Aman & Terfilter**: Termasuk mekanisme keamanan untuk hanya memproses email tertentu (misalnya, berdasarkan alamat penerima seperti `+cs`), menyaring spam, dan menghindari loop balasan.
-   **Serverless**: Dibuat untuk berjalan di Google Cloud Run untuk skalabilitas dan efisiensi biaya.
-   **Peralatan Komprehensif**: Termasuk skrip untuk penyiapan, pengujian, dan deployment.

## Struktur Direktori

Berikut adalah gambaran umum file-file kunci di direktori ini:

-   `main.py`: Aplikasi Flask inti yang menangani pesan Pub/Sub yang masuk, memproses email, dan mengatur logika balasan.
-   `generate_ai_genai.py`: Berisi fungsi untuk berinteraksi dengan model Gemini Vertex AI untuk pembuatan respons.
-   `requirements.txt`: Mendaftar semua dependensi Python yang diperlukan untuk proyek.
-   `deploy.sh`: Skrip shell untuk mengotomatiskan proses deployment ke Google Cloud Run.
-   `setup_gmail_watch.py`: Skrip untuk mengonfigurasi notifikasi Gmail API watch pada akun email target.
-   `activate_gmail_watch.py` & `check_gmail_watch.py`: Skrip pembantu untuk mengelola siklus hidup Gmail watch.
-   `*test*.py`: Serangkaian skrip pengujian untuk memverifikasi berbagai komponen sistem, dari pengujian unit sederhana hingga pengujian integrasi komprehensif.

## Penyiapan dan Deployment

1.  **Prasyarat**: Pastikan Anda memiliki Proyek Google Cloud dengan API Gmail, API Pub/Sub, API Vertex AI, dan API Secret Manager diaktifkan.
2.  **Izin**: Jalankan `setup_permissions.py` untuk mengonfigurasi peran IAM yang diperlukan untuk akun layanan.
3.  **Autentikasi**: Jalankan `gmail_auth.py` (dari direktori `scripts` induk) untuk menghasilkan kredensial OAuth2 yang diperlukan dan menyimpannya di Secret Manager.
4.  **Gmail Watch**: Jalankan `setup_gmail_watch.py` untuk menautkan akun Gmail Anda ke topik Pub/Sub.
5.  **Deployment**: Jalankan skrip `deploy.sh` untuk membangun image container dan mendeploy layanan ke Google Cloud Run.

## Pengujian

Sistem ini mencakup berbagai skrip pengujian:
-   `simple_test.py`: Tes dasar untuk memeriksa apakah endpoint layanan yang di-deploy responsif.
-   `comprehensive_test.py`: Mensimulasikan pesan Pub/Sub untuk menguji seluruh alur pemrosesan.
-   `test_genai.py`: Secara khusus menguji modul pembuatan respons AI.

Jalankan skrip ini untuk memastikan semua bagian sistem berfungsi dengan benar sebelum dan sesudah deployment.

Sistem balas otomatis email Gmail yang aman dan didukung AI, di-deploy di Google Cloud Run. Sistem ini secara otomatis menghasilkan dan mengirimkan respons yang dipersonalisasi ke email menggunakan model AI Gemini dari Google.

## 🚀 Fitur

### Fungsionalitas Inti
- **Respons Berbasis AI**: Menggunakan Google GenAI SDK dengan backend Vertex AI (Gemini 2.5 Flash Lite)
- **Pemrosesan Real-time**: API Gmail watch dengan notifikasi push Pub/Sub untuk deteksi email instan
- **Autentikasi Aman**: Kredensial Gmail OAuth disimpan di Google Cloud Secret Manager
- **Cloud Native**: Di-deploy di Google Cloud Run dengan penskalaan otomatis

### Keamanan & Penyaringan
- **Penyaringan Alamat Email**: Hanya merespons email yang dikirim ke `addhe.warman+cs@gmail.com`
- **Penyaringan Berbasis Waktu**: Hanya memproses email dari 24 jam terakhir
- **Perlindungan Spam**: Penyaringan kata kunci spam bawaan
- **Pencegahan Duplikat**: Menambahkan label Gmail untuk mencegah balasan ganda ke email yang sama
- **Daftar Putih Domain**: Validasi domain pengirim opsional

### Pemantauan & Debugging
- **Logging Komprehensif**: Log terperinci untuk semua operasi dan kesalahan
- **Endpoint Pemeriksaan Kesehatan**: Endpoint `/` untuk pemantauan layanan
- **Alat Debug**: Beberapa skrip pengujian untuk validasi dan pemecahan masalah

## 📁 Struktur Proyek

### File Inti
- `main.py` - Aplikasi Flask utama dengan pemrosesan Pub/Sub dan pembuatan respons AI
- `deploy.sh` - Skrip deployment Cloud Run
- `requirements.txt` - Dependensi Python
- `runtime.txt` - Spesifikasi runtime Python
- `Procfile` - Konfigurasi Gunicorn
- `gunicorn_config.py` - Konfigurasi server

### Skrip Penyiapan & Manajemen
- `setup_gmail_watch.py` - Menyiapkan topik Pub/Sub, langganan, dan Gmail watch
- `setup_permissions.py` - Mengonfigurasi izin IAM untuk Gmail API dan Pub/Sub
- `activate_gmail_watch.py` - Mengaktifkan notifikasi Gmail watch
- `debug_email.py` - Debug pesan email tertentu berdasarkan ID

### Skrip Pengujian
- `test_genai_vertex.py` - Uji GenAI SDK dengan backend Vertex AI
- `test_vertex_ai_v2.py` - Uji integrasi Vertex AI
- `test_direct.py` - Pengujian API langsung
- `simple_test.py` - Pengujian endpoint dasar
- `comprehensive_test.py` - Simulasi sistem penuh

## 🔧 Konfigurasi

### Variabel Lingkungan
- `PROJECT_ID` - Google Cloud project ID (`awanmasterpiece`)
- `SECRET_NAME` - Gmail OAuth token secret name (default: `gmail-oauth-token`)
- `VERTEX_MODEL` - AI model name (default: `gemini-2.5-flash-lite`)

### Security Settings (Internal)
- `ALLOWED_EMAIL_ADDRESS` - Target email address (`addhe.warman+cs@gmail.com`)
- `MAX_EMAIL_AGE_HOURS` - Email age limit (24 hours)
- `AUTO_REPLY_LABEL` - Gmail label for processed emails (`Auto-Replied`)

## 🚀 Deployment

### Prerequisites
1. Google Cloud project with billing enabled
2. Gmail API enabled
3. Vertex AI API enabled
4. Pub/Sub API enabled
5. Secret Manager API enabled
6. Cloud Run API enabled

### Setup Process
1. **Deploy the application**:
   ```bash
   ./deploy.sh
   ```

2. **Set up Pub/Sub and Gmail watch**:
   ```bash
   python3 setup_gmail_watch.py
   ```

3. **Configure permissions**:
   ```bash
   python3 setup_permissions.py
   ```

4. **Activate Gmail watch**:
   ```bash
   python3 activate_gmail_watch.py
   ```

## 🔐 Security & Permissions

### Service Account Roles
- `roles/secretmanager.secretAccessor` - Access Gmail OAuth credentials
- `roles/aiplatform.user` - Use Vertex AI models
- `roles/pubsub.subscriber` - Receive Pub/Sub messages

### Gmail API Service Account
- `roles/pubsub.publisher` - Publish Gmail notifications to Pub/Sub topic

### Security Features
- OAuth 2.0 authentication with Gmail API
- Secure credential storage in Secret Manager
- Email address validation and filtering
- Spam detection and prevention
- Rate limiting and error handling

## 🧪 Testing

### Manual Testing
Send an email to `addhe.warman+cs@gmail.com` with:
- **Subject**: "Test AI Auto-Reply"
- **Body**: "Hello, I need help with your services."

### Automated Testing
```bash
# Test GenAI integration
python3 test_genai_vertex.py

# Test specific email
python3 debug_email.py <message_id>

# Test endpoints
python3 simple_test.py
```

## 📊 Monitoring

### Logs
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email" --limit=20 --project=awanmasterpiece

# View error logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email AND severity>=ERROR" --limit=10 --project=awanmasterpiece
```

### Health Check
```bash
curl https://auto-reply-email-361046956504.us-central1.run.app/
```

## 🔄 System Flow

1. **Email Received** → Gmail detects new email
2. **Notification Sent** → Gmail watch sends Pub/Sub notification
3. **Processing Triggered** → Cloud Run receives Pub/Sub push
4. **Security Check** → Validates email meets criteria (address, age, spam)
5. **AI Generation** → GenAI SDK generates personalized response
6. **Reply Sent** → Gmail API sends auto-reply
7. **Label Added** → Marks email as processed to prevent duplicates

## 🛠️ Troubleshooting

### Common Issues
- **No auto-replies**: Check Gmail watch status and Pub/Sub permissions
- **Fallback responses**: Verify Vertex AI API access and model availability
- **Missing emails**: Ensure emails are sent to `+cs` address and within 24 hours
- **Permission errors**: Run `setup_permissions.py` to fix IAM bindings

### Debug Commands
```bash
# Check Gmail watch status
python3 activate_gmail_watch.py

# Debug specific email
python3 debug_email.py <message_id>

# Test AI generation
python3 test_genai_vertex.py
```

## 📈 Production Considerations

- **Rate Limiting**: Gmail API has quotas and rate limits
- **Cost Management**: Vertex AI charges per token generated
- **Monitoring**: Set up alerts for errors and unusual activity
- **Backup**: Consider fallback mechanisms for AI service outages
- **Scaling**: Cloud Run auto-scales based on traffic

## 🔗 Dependencies

- `google-api-python-client` - Gmail API client
- `google-cloud-pubsub` - Pub/Sub messaging
- `google-cloud-secret-manager` - Secure credential storage
- `google-cloud-aiplatform` - Vertex AI integration
- `google-genai` - GenAI SDK for AI generation
- `flask` - Web framework
- `gunicorn` - WSGI server

---

**Status**: ✅ Production Ready  
**Last Updated**: August 2025  
**Version**: 2.0 (GenAI SDK Integration)

## Setup

1. Create a Google Cloud project
2. Enable the Gmail API, Pub/Sub API, Secret Manager API, and Vertex AI API
3. Create OAuth credentials for the Gmail API
4. Store the credentials in Secret Manager
5. Create a Pub/Sub topic and subscription for Gmail notifications
6. Deploy the application to Cloud Run using the deployment script

## 🔒 Pembaruan Privasi & Isolasi (v2.1.0)

- **Isolasi Chat per Email**: `generate_ai_response()` kini menggunakan `GenerativeModel(...).start_chat(history=[])` per email sehingga tidak ada memori silang antar pelanggan/thread.
- **Guardrail Privasi**:
  - Menghapus kutipan/riwayat dari body email sebelum diproses AI.
  - Menyaring keluaran AI untuk meredaksi alamat email selain `addhe.warman+cs@gmail.com` dan deretan digit panjang (PII seperti nomor identitas/akun).
- **Routing Header Balasan**:
  - `send_reply()` menyetel `From` dan `Reply-To` ke `addhe.warman+cs@gmail.com` agar balasan pelanggan selalu menuju alias +cs yang terlindungi.
- **Endpoint Operasional**:
  - `GET /check-watch-status` — memeriksa status Gmail watch.
  - `POST /renew-watch` — memperbarui Gmail watch sebelum kedaluwarsa.
  - `POST /test-pubsub` — uji integrasi Pub/Sub dengan simulasi pesan.

Catatan: Sistem hanya merespons email yang ditujukan ke `addhe.warman+cs@gmail.com` dan menerapkan label untuk mencegah balasan ganda serta menghindari reply loop.
