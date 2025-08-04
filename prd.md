# **Product Requirements Document (PRD)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Overview**

### **1.1 Purpose**

Menyediakan fitur auto-reply email berbasis AI yang secara otomatis membalas email masuk dengan balasan profesional dan relevan menggunakan Vertex AI Gemini, untuk meningkatkan kecepatan respon dan efisiensi operasional.

---

### **1.2 Background**

Proses manual membalas email memakan waktu dan dapat menimbulkan keterlambatan komunikasi. Dengan sistem auto-reply berbasis AI:

* Respon dapat dilakukan real-time (<15 detik).
* Balasan lebih konsisten dan kontekstual.
* Mengurangi beban kerja tim support.

---

## **2. Goals & Objectives**

* Memberikan balasan otomatis pada email masuk menggunakan AI.
* Memastikan balasan tetap profesional dan sesuai konteks email.
* Mengintegrasikan solusi ini sepenuhnya dengan ekosistem Google Cloud (Gmail API, Pub/Sub, Cloud Functions, Vertex AI).
* Memungkinkan skalabilitas untuk ribuan email per hari.

---

## **3. User Stories**

### **3.1 Primary User: Tim Customer Support**

* **Sebagai** anggota tim support  
  **Saya ingin** setiap email masuk mendapatkan balasan otomatis  
  **Sehingga** pelanggan merasa email mereka diterima tanpa menunggu lama.

---

### **3.2 Secondary User: Tim Operasional**

* **Sebagai** tim operasional  
  **Saya ingin** sistem bekerja tanpa perlu monitoring manual setiap saat  
  **Sehingga** saya bisa fokus ke eskalasi yang benar-benar penting.

---

### **3.3 Tertiary User: Admin / DevOps**

* **Sebagai** admin  
  **Saya ingin** bisa melihat log email yang dibalas otomatis  
  **Sehingga** saya bisa troubleshooting jika ada masalah.

---

## **4. Functional Requirements**

### **4.1 Email Detection**

* Sistem mendeteksi email baru secara real-time menggunakan Gmail API `watch`.
* Notifikasi dikirim ke Pub/Sub dengan `historyId`.

---

### **4.2 AI Reply Generation**

* Konten email (subject & body) dikirim ke Vertex AI Gemini.
* AI menghasilkan balasan profesional berdasarkan prompt standar.

---

### **4.3 Auto Reply**

* Sistem mengirim balasan otomatis ke pengirim email menggunakan Gmail API `users.messages.send`.
* Subjek balasan menggunakan format `Re: <original subject>`.

---

### **4.4 Event Processing**

* Pub/Sub mengirim event ke Cloud Function untuk diproses.
* Cloud Function menangani error dan retry jika gagal kirim balasan.

---

### **4.5 Logging & Monitoring**

* Setiap balasan tercatat dengan detail:

  * ID email  
  * Pengirim  
  * Timestamp  
  * Status balasan (sukses/gagal)  

---

## **5. Non-Functional Requirements**

* **Performance**: Balasan terkirim maksimal 15 detik setelah email diterima.
* **Scalability**: Mampu menangani 10.000 email/hari.
* **Security**: OAuth 2.0 dan IAM digunakan untuk akses API.
* **Reliability**: SLA minimal 99,5%.
* **Cost Efficiency**: Optimasi penggunaan Pub/Sub & Cloud Functions.

---

## **6. Product Features**

1. **Auto-Reply AI**  
   * Balas email masuk otomatis dengan konten kontekstual.  
2. **Event-Driven Architecture**  
   * Gunakan Pub/Sub untuk memproses email secara asinkron.  
3. **Cloud Native**  
   * Semua komponen berjalan di Google Cloud (Gmail API, Pub/Sub, Cloud Functions, Vertex AI).  
4. **Real-Time Response**  
   * Balasan dikirim <15 detik dari waktu email masuk.  
5. **Basic Logging**  
   * Log status balasan untuk audit dan debugging.  

---

## **7. UX / Interaction Flow**

### **7.1 Flow Diagram (High-Level)**

1. Email masuk ke Gmail.  
2. Gmail API `watch` trigger → kirim event ke Pub/Sub.  
3. Pub/Sub trigger Cloud Function.  
4. Cloud Function ambil detail email.  
5. Cloud Function kirim prompt ke Vertex AI Gemini → dapat balasan.  
6. Cloud Function kirim balasan via Gmail API.  
7. Log status ke Cloud Logging.  

---

## **8. Success Metrics**

* **Kecepatan**: 95% balasan terkirim <15 detik.  
* **Relevansi**: 90% balasan dinilai relevan oleh tim QA.  
* **Stabilitas**: Error rate <1% selama 30 hari pertama.  

---

## **9. Dependencies**

* Gmail API (untuk monitoring dan kirim balasan)  
* Google Pub/Sub (untuk event)  
* Google Cloud Functions (untuk pemrosesan event)  
* Vertex AI Gemini (untuk AI generatif)  
* IAM & OAuth (untuk keamanan akses)  

---

## **10. Risks & Mitigations**

* **Risiko AI salah konteks** → tuning prompt, validasi contoh email.  
* **API rate limit Gmail** → gunakan label/filters untuk batasi scope.  
* **Keterlambatan Pub/Sub** → aktifkan retry policy.  
* **Biaya Vertex AI tinggi** → batasi panjang prompt & optimalkan request.  

---

## **11. Open Questions**

* Apakah perlu mendukung **multi-language auto reply** di fase awal?  
* Apakah akan ada **moderation layer** sebelum balasan terkirim (fase berikutnya)?  
* Apakah log balasan perlu disimpan ke **BigQuery** untuk analitik jangka panjang?  

---

## **12. Acceptance Criteria**

* Sistem dapat mengirim balasan otomatis pada 95% email masuk.  
* Balasan dihasilkan oleh Vertex AI Gemini tanpa campur tangan manual.  
* Waktu balasan rata-rata <15 detik dari email masuk.  
* Tidak ada kebocoran data sensitif dalam balasan AI.  
* Semua event & balasan tercatat di log sistem.
