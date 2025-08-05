# **UX/UI Design Flow Documentation (UDFD)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)
**Document Version**: 1.0
**Date**: 2025-08-04
**Author**: addhe warman

---

## **1. Overview**

Dokumen ini menjelaskan alur desain pengalaman pengguna (UX) dan antarmuka pengguna (UI) untuk sistem auto-reply email berbasis AI. Fokus utama adalah tampilan dashboard monitoring dan konfigurasi, serta alur interaksi pengguna dengan sistem.

---

## **2. User Personas**

### **2.1 Tim Customer Support**

* **Tujuan**: Memastikan semua email pelanggan dibalas otomatis dan relevan.
* **Kebutuhan**:
  * Melihat status balasan otomatis.
  * Memastikan AI membalas sesuai konteks.

---

### **2.2 Tim Operasional / Admin**

* **Tujuan**: Mengelola konfigurasi, memantau performa, dan troubleshooting.
* **Kebutuhan**:
  * Mengatur filter email yang akan dibalas otomatis.
  * Memantau log, error, dan statistik balasan.

---

### **2.3 Manajemen**

* **Tujuan**: Melihat ringkasan performa sistem auto-reply.
* **Kebutuhan**:
  * Dashboard KPI: jumlah email dibalas, waktu respon, tingkat error.

---

## **3. UX Goals**

* **Sederhana**: Dashboard mudah dipahami oleh non-teknis.
* **Real-time**: Status balasan dan log tampil hampir real-time.
* **Kontrol**: Admin dapat mengatur filter (label Gmail, domain pengirim).
* **Keterlacakan**: Log detail email (ID, status balasan, waktu).

---

## **4. UI Components**

### **4.1 Dashboard Overview**

* **Elemen Utama**:
  * **Total Email Dibalas Hari Ini**
  * **Rata-rata Waktu Balas**
  * **Jumlah Error (Hari Ini & Mingguan)**
  * **Grafik Tren Balasan (Harian/Mingguan)**

---

### **4.2 Email Logs**

* Tabel berisi:
  * ID Email
  * Pengirim
  * Status Nasabah (Verified/Non-Customer)
  * Subject
  * Status Balasan (Sukses/Gagal)
  * Timestamp Balasan

---

### **4.3 Settings Page**

* Konfigurasi:
  * Filter Label Gmail (contoh: hanya balas email dengan label `INBOX`)
  * Pilihan Balasan (Formal / Santai)
  * API Key & Model Gemini yang digunakan

---

### **4.4 Error & Alert Panel**

* Menampilkan error Pub/Sub, Gmail API, atau Vertex AI.
* Link ke Cloud Logging untuk detail debugging.

---

## **5. User Flow**

### **5.1 Flow Diagram**

```
[Login Dashboard]
      |
      v
[Dashboard Overview] ----> [View Logs Detail]
      |
      v
 [Settings Page] ----> [Configure Filters & AI Tone]
      |
      v
[Save Settings] ----> [System Auto-Apply Changes]
```

---

## **6. Interaction Flow (Scenario)**

### **Scenario 1: Monitoring Auto-Reply**

1. User membuka dashboard.
2. Melihat statistik balasan hari ini (jumlah email dibalas, waktu rata-rata).
3. Jika ada error, klik panel error untuk detail.

---

### **Scenario 2: Konfigurasi Filter Balasan**

1. User masuk ke halaman Settings.
2. Pilih label email mana yang akan di-auto-reply (contoh: hanya `INBOX`).
3. Pilih gaya balasan AI (formal atau santai).
4. Simpan konfigurasi → sistem langsung update setting Gmail API watch.

---

## **7. Wireframe (Textual)**

### **7.1 Dashboard Overview**

```
-----------------------------------------------------
|  Auto Reply AI Dashboard                          |
-----------------------------------------------------
| Total Replied Today: 120  | Avg Response: 8 sec   |
-----------------------------------------------------
| Graph: Replies per Day (line chart)               |
-----------------------------------------------------
| Error Panel (Today: 2) | [View Logs] [Settings]   |
-----------------------------------------------------
```

---

### **7.2 Email Log Page**

```
-----------------------------------------------------
| ID Email  | Sender        | Subject  | Status     |
-----------------------------------------------------
| 123456    | client@abc.com | RFQ Prod X | Success  |
| 123457    | partner@xyz.com| Support   | Failed    |
-----------------------------------------------------
```

---

### **7.3 Settings Page**

```
-----------------------------------------------------
| Settings                                           |
-----------------------------------------------------
| [ ] Reply to INBOX only                            |
| [x] Reply to label: "Customer"                     |
| Tone: [Formal v]                                   |
| Vertex AI Model: gemini-1.5-pro                    |
-----------------------------------------------------
| Save Changes                                       |
-----------------------------------------------------
```

---

## **8. Design Principles**

* **Clarity**: Informasi ringkas, fokus pada KPI utama.
* **Consistency**: Warna dan icon standar GCP (material design).
* **Feedback**: Setiap perubahan konfigurasi menampilkan notifikasi sukses.
* **Accessibility**: Gunakan warna kontras tinggi dan support screen reader.

---

## **9. Future Enhancements**

* Dark mode untuk dashboard.
* Mobile-responsive design.
* Custom prompt editor untuk tuning gaya balasan AI.
* Integrasi analitik sentiment email.

---

## **10. Tools & Tech for UI**

* **Frontend**: React.js + Tailwind CSS
* **Charts**: Recharts (untuk grafik tren)
* **Backend API**: Cloud Functions (REST endpoint untuk log & setting)
* **Auth**: Google OAuth 2.0 (SSO)
* **Deployment**: Firebase Hosting / Cloud Run (untuk frontend)
