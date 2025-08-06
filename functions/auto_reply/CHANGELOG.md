# Catatan Perubahan

Semua perubahan penting pada proyek ini akan didokumentasikan di file ini.

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
- **Penyaringan Alamat Email**: Hanya merespons email yang dikirim ke `addhe.warman+cs@gmail.com`
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
- OAuth 2.0 with secure token storage
- Input validation and sanitization
- Rate limiting considerations
- Secure environment variable handling

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
