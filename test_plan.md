# **Test Plan & Test Cases (QA TDD)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Purpose**

Dokumen ini bertujuan untuk mendefinisikan strategi pengujian dan daftar test case untuk memastikan kualitas, akurasi, serta stabilitas fitur **Auto Reply Email dengan AI** sebelum implementasi production.

---

## **2. Objectives**

* Memastikan sistem mampu membalas email masuk secara otomatis.  
* Memvalidasi kualitas balasan AI (relevansi, tone, panjang balasan).  
* Menguji integrasi antar komponen (Gmail API, Pub/Sub, Cloud Function, Vertex AI).  
* Menguji performa (waktu balasan, skalabilitas).  
* Menjamin keamanan data dan kepatuhan pada scope fungsional.  

---

## **3. Scope of Testing**

### **In Scope**

* Functional Testing: Email detection, AI reply, auto send.  
* Integration Testing: Gmail API ↔ Pub/Sub ↔ Cloud Function ↔ Vertex AI.  
* Performance Testing: Waktu balasan <15 detik untuk 1000 email/hari.  
* Security Testing: OAuth, IAM permissions, data privacy.  
* UAT (User Acceptance Testing): Validasi kualitas balasan AI oleh tim user.  

### **Out of Scope**

* Multi-language auto reply (fase berikutnya).  
* Analitik dashboard & laporan KPI (fase berikutnya).  
* Integrasi CRM eksternal.  

---

## **4. Test Strategy**

* **Functional Testing** → Validasi semua requirement fungsional.  
* **Integration Testing** → Pastikan end-to-end flow berjalan tanpa error.  
* **Negative Testing** → Uji sistem dengan input abnormal (body kosong, lampiran besar).  
* **Performance Testing** → Simulasi load besar via script.  
* **Security Testing** → Cek role IAM & token OAuth.  
* **UAT** → User menilai relevansi balasan AI (≥90% relevansi target).  

---

## **5. Test Environment**

* **Cloud Platform**: Google Cloud Platform (GCP)  
* **Components**: Gmail API, Pub/Sub, Cloud Functions, Vertex AI Gemini  
* **Test Gmail Account**: `test.autoreply@domain.com`  
* **Tools**: Postman, Python scripts (load test), Cloud Logging for verification  

---

## **6. Entry & Exit Criteria**

### **Entry Criteria**

* Semua komponen ter-deploy (API enabled, Pub/Sub, Function, Vertex AI).  
* Kredensial OAuth & Service Account tersedia.  
* Data test email disiapkan (dummy customer emails).  

### **Exit Criteria**

* 95% test cases PASS.  
* Error rate <1%.  
* Semua defect kritikal ditutup.  

---

## **7. Test Cases**

### **TC-001: Email Masuk → Auto Reply**

* **Description**: Sistem membalas email baru secara otomatis.  
* **Precondition**: Gmail API watch aktif, Pub/Sub terhubung.  
* **Steps**:  
  1. Kirim email ke inbox test.  
  2. Verifikasi Pub/Sub menerima event.  
  3. Verifikasi balasan terkirim via Gmail API.  
* **Expected Result**: Balasan AI diterima oleh pengirim dalam <15 detik.  

---

### **TC-002: Balasan AI Sesuai Konteks**

* **Description**: Balasan AI relevan dengan isi email.  
* **Steps**:  
  1. Kirim email berisi permintaan harga produk X.  
  2. Verifikasi balasan menyebutkan “harga produk X”.  
* **Expected Result**: Balasan menyertakan referensi ke produk X, menggunakan bahasa formal.  

---

### **TC-003: Negative Test – Body Kosong**

* **Description**: Email tanpa body tetap dibalas template default.  
* **Steps**:  
  1. Kirim email tanpa isi (hanya subjek).  
* **Expected Result**: Balasan default: “Terima kasih, email Anda telah kami terima.”  

---

### **TC-004: Performance Test – Load 1000 Emails**

* **Description**: Uji sistem dengan 1000 email dalam 1 jam.  
* **Steps**:  
  1. Simulasi 1000 email masuk menggunakan script.  
  2. Monitor waktu balasan rata-rata.  
* **Expected Result**: 95% balasan terkirim <15 detik.  

---

### **TC-005: Security Test – Unauthorized Access**

* **Description**: Pastikan endpoint tidak bisa diakses tanpa OAuth.  
* **Steps**:  
  1. Coba akses Gmail API tanpa token.  
* **Expected Result**: Request ditolak (401 Unauthorized).  

---

### **TC-006: Retry Mechanism – Pub/Sub Failure**

* **Description**: Verifikasi retry jika Cloud Function gagal proses.  
* **Steps**:  
  1. Simulasikan error Cloud Function.  
  2. Lihat apakah Pub/Sub mengirim ulang pesan.  
* **Expected Result**: Pesan diproses ulang hingga sukses atau masuk dead-letter topic.  

---

### **TC-007: UAT – User Review Balasan**

* **Description**: Validasi kualitas balasan oleh tim user.  
* **Steps**:  
  1. Kirim 20 email sample ke sistem.  
  2. Tim user memberi rating relevansi (1-5).  
* **Expected Result**: ≥90% balasan mendapat rating ≥4.  

---

## **8. Defect Management**

* **Severity**: Critical / Major / Minor  
* **Tool**: Google Sheets / Jira (tergantung tim)  
* **SLA Fix**:  
  * Critical: 24 jam  
  * Major: 48 jam  
  * Minor: 5 hari kerja  

---

## **9. Reporting**

* Laporan harian jumlah test pass/fail.  
* Laporan akhir UAT dengan metrik:  
  * Total email diuji  
  * Waktu balasan rata-rata  
  * Tingkat relevansi balasan  
  * Error rate  

---

## **10. Sign-Off**

* **QA Lead**: \[Nama]  
* **Product Owner**: \[Nama]  
* **Approval Date**: \[TBD]
