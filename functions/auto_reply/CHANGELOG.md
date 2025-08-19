# Catatan Perubahan

Semua perubahan penting pada proyek ini akan didokumentasikan di file ini.

## [2.2.0] - 2025-08-13

### 🏗️ Refactoring & Modularization
- **Customer Service Module**: Refactored customer verification logic into separate `customer_service.py` module for better modularity and easier debugging.
- **Import Path Fixes**: Fixed import paths for Cloud Run environment using absolute imports (`functions.auto_reply.module`).
- **Session Management**: Implemented session isolation using MD5 hash of email subject for privacy protection.

### 🔒 Security & Configuration
- **Environment Variables**: Migrated from hardcoded config to secure environment variable configuration.
- **Deploy Script Security**: Updated `deploy.sh` to validate required environment variables and prevent hardcoded API keys.
- **Config File Protection**: Ensured `config.py` remains in `.gitignore` for security while providing fallback to environment variables.

### 🔧 Bug Fixes & Improvements
- **Logger Configuration**: Fixed logger initialization order to prevent `NameError` during startup.
- **Reply Loop Detection**: Adjusted threshold from 2 to 3 reply indicators to allow normal email chains.
- **API Integration**: Fixed customer API integration with proper error handling and fallback responses.

### 🧪 Testing & Debugging
- **Debug Tools**: Added `debug_customer_service.py` for local testing of customer service integration.
- **Comprehensive Logging**: Enhanced logging for customer verification, API calls, and error tracking.

### 📚 Documentation
- **README Updates**: Updated documentation with customer service integration details and environment variable setup.
- **Deployment Guide**: Added secure deployment instructions with environment variable validation.

## [2.1.0] - 2025-08-12

### 🔒 Keamanan & Privasi
- Isolasi sesi AI per email menggunakan Vertex AI `GenerativeModel.start_chat(history=[])` agar tidak ada memori silang antar pelanggan/thread.
- Guardrail privasi ketat: strip teks kutipan/riwayat dari body email sebelum diproses dan sanitasi keluaran AI (redaksi alamat email non-+cs dan deretan digit panjang/PII).
- Pengaturan header balasan: set `From` dan `Reply-To` ke `squidgamecs2025@gmail.com` untuk memastikan jalur balasan aman via alias +cs.

### ✉️ Perilaku Balasan
- Hanya membalas email yang ditujukan ke alias `squidgamecs2025@gmail.com` dan bukan dari sistem sendiri (anti-reply loop).
- Penambahan label Gmail untuk mencegah balasan ganda pada pesan yang sama.

### 🔧 Operasional & Ketahanan
- Backfill scan: jika history kosong, sistem memindai pesan UNREAD terbaru agar tidak ada email baru yang terlewat selama reset watch.
- Endpoint operasional baru:
  - `GET /check-watch-status` — cek status Gmail watch.
  - `POST /renew-watch` — perbarui watch Gmail.
  - `POST /test-pubsub` — simulasi pemrosesan pesan Pub/Sub.

### 🧰 Lainnya
- Peningkatan logging dan instruksi prompt untuk mencegah penggunaan data di luar konteks email saat ini dan data pelanggan yang terverifikasi.

## [1.0.0] - 2025-08-06

### Penambahan
-   Pengaturan awal sistem Balas Otomatis Gmail sebagai aplikasi Flask.
-   Integrasi dengan Google Cloud Run untuk deployment serverless (`deploy.sh`).
-   Logika inti di `main.py` untuk menangani notifikasi Pub/Sub dari Gmail API.
-   Pembuatan respons berbasis AI menggunakan Vertex AI Gemini (`generate_ai_genai.py`).
-   Filter keamanan komprehensif untuk mencegah spam dan loop balasan.
-   Serangkaian skrip pengujian lengkap (`simple_test.py`, `comprehensive_test.py`, `test_genai.py`) untuk memastikan keandalan.
-   Skrip untuk mengotomatiskan penyiapan, termasuk izin (`setup_permissions.py`) dan konfigurasi Gmail watch (`setup_gmail_watch.py`).
-   Alur autentikasi OAuth2 (`scripts/gmail_auth.py`) untuk menangani kredensial pengguna secara aman dengan Google Secret Manager.

### Perubahan
-   Refactor basis kode untuk modularitas dan keterbacaan yang lebih baik.
-   Beralih dari model AI dasar ke Gemini untuk respons berkualitas lebih tinggi.

### Perbaikan
-   Menyelesaikan berbagai kesalahan linting dan meningkatkan kualitas kode.
-   Mengatasi masalah autentikasi awal dengan Gmail API (`redirect_uri_mismatch`).

Semua perubahan penting pada Sistem Balas Otomatis Email Gmail didokumentasikan dalam file ini.

## [2.0.0] - 2025-08-06

### 🚀 Penambahan Fitur Utama
- **Integrasi GenAI SDK**: Migrasi dari panggilan Vertex AI langsung ke Google GenAI SDK dengan backend Vertex AI
- **Penyaringan Keamanan yang Ditingkatkan**: Menambahkan sistem penyaringan email yang komprehensif
- **Pemrosesan Real-time**: Menerapkan API Gmail watch dengan notifikasi push Pub/Sub
- **Logging Komprehensif**: Menambahkan logging terperinci di seluruh sistem

### 🔒 Peningkatan Keamanan
- **Penyaringan Alamat Email**: Hanya merespons email yang dikirim ke `squidgamecs2025@gmail.com`
- **Penyaringan Berbasis Waktu**: Hanya memproses email dari 24 jam terakhir
- **Perlindungan Spam**: Penyaringan kata kunci spam bawaan
- **Pencegahan Duplikat**: Menambahkan label Gmail untuk mencegah balasan ganda
- **Daftar Putih Domain**: Validasi domain pengirim opsional

### 🛠️ Peningkatan Teknis
- **Peningkatan Model AI**: Diperbarui untuk menggunakan model `gemini-2.5-flash-lite`
- **Penanganan Kesalahan**: Penanganan kesalahan yang ditingkatkan dengan respons fallback
- **Autentikasi**: Penyimpanan kredensial OAuth yang aman di Secret Manager
- **Cloud Native**: Dioptimalkan untuk deployment Google Cloud Run

### 📁 Penambahan File Baru
- `setup_gmail_watch.py` - Penyiapan Pub/Sub dan Gmail watch
- `setup_permissions.py` - Konfigurasi izin IAM
- `activate_gmail_watch.py` - Gmail watch activation
- `debug_email.py` - Email debugging utility
- `test_genai_vertex.py` - GenAI SDK testing
- `test_vertex_ai_v2.py` - Vertex AI integration testing
- `test_direct.py` - Direct API testing
- `generate_ai_genai.py` - GenAI SDK implementation
- `list_models.py` - Available models checker

### 🔧 Configuration Changes
- **Environment Variables**: 
  - `VERTEX_MODEL` default changed to `gemini-2.5-flash-lite`
  - Added internal security configuration variables
- **Dependencies**: Added `google-genai>=1.28.0` to requirements.txt
- **Model Configuration**: Updated AI generation parameters for better responses

### 🐛 Bug Fixes
- Fixed Vertex AI model access issues
- Resolved authentication problems with service accounts
- Fixed Pub/Sub message processing
- Corrected Gmail API permission issues
- Fixed email processing filters

### 📚 Documentation Updates
- **README.md**: Complete rewrite with comprehensive documentation
- **CHANGELOG.md**: Added this changelog file
- **Code Comments**: Enhanced inline documentation
- **Setup Instructions**: Detailed deployment and configuration guides

### 🧪 Testing Improvements
- Multiple test scripts for different scenarios
- Debug utilities for troubleshooting
- Health check endpoints
- Comprehensive error logging

### 🔄 System Architecture Changes
- **Processing Flow**: 
  1. Gmail watch → Pub/Sub notification → Cloud Run processing
  2. Security validation → AI generation → Email reply → Label marking
- **Fallback Mechanism**: Graceful degradation when AI services are unavailable
- **Monitoring**: Enhanced logging and health checks

### ⚡ Performance Optimizations
- Streaming responses from GenAI SDK
- Optimized Pub/Sub message processing
- Reduced cold start times
- Efficient error handling

### 🔐 Security Hardening
- OAuth 2.0 dengan penyimpanan token aman
- Validasi input dan sanitasi
- Pertimbangan rate limiting
- Penanganan variabel lingkungan yang aman

---

## [1.0.0] - Initial Release

### Initial Features
- Basic Gmail API integration
- Simple auto-reply functionality
- Google Cloud Run deployment
- Basic Vertex AI integration

### Components
- `main.py` - Core Flask application
- `deploy.sh` - Deployment script
- `requirements.txt` - Dependencies
- Basic testing scripts

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.
