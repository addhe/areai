# **Business Requirements Document (BRD)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Purpose**

Membuat sistem auto-reply email berbasis AI yang mampu membalas email masuk secara otomatis menggunakan model generatif Vertex AI Gemini. Sistem ini bertujuan untuk meningkatkan respon cepat ke pelanggan atau stakeholder tanpa intervensi manual, sekaligus menjaga kualitas balasan yang profesional dan relevan.

---

## **2. Background**

Proses membalas email secara manual membutuhkan waktu dan sumber daya besar, terutama untuk email yang sifatnya repetitif atau membutuhkan respon cepat. Dengan menggunakan integrasi Gmail API, Pub/Sub, dan Vertex AI Gemini, sistem ini memungkinkan:

* Pemantauan email real-time.
* Pembuatan balasan otomatis dengan AI.
* Pengiriman balasan langsung ke pengirim email.

---

## **3. Objectives**

* Mengimplementasikan auto-reply berbasis AI untuk Gmail.
* Menjamin balasan bersifat **profesional**, **kontekstual**, dan **relevan**.
* Meningkatkan efisiensi tim dalam menangani email masuk.
* Memberikan arsitektur yang **scalable** dan **cloud-native**.

---

## **4. Scope**

### **In-Scope**

* Integrasi Gmail API untuk menerima email masuk.
* Menggunakan Pub/Sub sebagai mekanisme event-driven.
* Cloud Function untuk memproses event dan memanggil Vertex AI Gemini.
* Vertex AI Gemini untuk menghasilkan konten balasan email.
* Pengiriman balasan otomatis ke pengirim email.
* Basic logging untuk setiap email yang dibalas.
* Inquiry ke API endpoint pelanggan untuk personalisasi balasan.

### **Out-of-Scope**

* Moderasi manual sebelum balasan terkirim (fase berikutnya).
* Penanganan email dengan lampiran besar (di luar pilot project).
* Integrasi ke CRM / sistem tiket (fase selanjutnya).

---

## **5. Stakeholders**

* **Project Owner**: Tim IT / DevOps  
* **Users**: Tim Customer Support, Tim Operasional  
* **AI Model Owner**: Vertex AI Team  
* **Infra Owner**: Google Cloud Platform Admin  

---

## **6. Functional Requirements**

### **FR1** – Email Monitoring

* Sistem harus dapat memantau inbox Gmail secara real-time menggunakan Gmail API `watch`.
* Sistem harus mampu mendeteksi email baru berdasarkan `historyId`.

### **FR2** – Customer Verification

* Sistem harus melakukan inquiry ke API endpoint pelanggan untuk memverifikasi status keanggotaan pengirim email
* Data yang diverifikasi: alamat email pengirim dan status keanggotaan

### **FR3** – AI Reply Generation

* Sistem harus memanggil Vertex AI Gemini untuk menghasilkan balasan email dengan personalisasi berbasis data nasabah
* Balasan harus menyesuaikan konteks email (subject & body) + informasi nasabah (jika terverifikasi)

### **FR3** – Auto Reply Sending

* Sistem harus mengirim balasan otomatis ke pengirim email menggunakan Gmail API `users.messages.send`.
* Subjek balasan harus menggunakan format `Re: <original subject>`.

### **FR4** – Event Handling

* Event email masuk harus dipublikasikan ke Pub/Sub topic.
* Cloud Function harus membaca event Pub/Sub dan memproses email tersebut.

### **FR5** – Logging

* Sistem harus menyimpan log minimal berupa:

  * ID email  
  * Alamat pengirim  
  * Status balasan (berhasil/gagal)  

---

## **7. Non-Functional Requirements**

### **NFR1 – Performance**

* Respon balasan maksimal 15 detik setelah email masuk.

### **NFR2 – Scalability**

* Harus dapat menangani minimal 10.000 email per hari tanpa penurunan performa.

### **NFR3 – Security**

* Menggunakan OAuth 2.0 dan IAM untuk akses Gmail API.
* Data email tidak disimpan secara permanen kecuali untuk logging minimal.

### **NFR4 – Reliability**

* Sistem harus memiliki SLA minimal 99,5%.

### **NFR5 – Cost Efficiency**

* Mengoptimalkan penggunaan Pub/Sub dan Cloud Functions agar biaya minimal.

---

## **8. Assumptions**

* Akses Gmail API telah diberikan melalui akun Google Workspace.
* Model Vertex AI Gemini sudah tersedia di project GCP yang sama.
* Tidak ada kebutuhan balasan multi-bahasa pada fase awal.

---

## **9. Risks**

* **Risk 1**: AI menghasilkan balasan yang tidak sesuai konteks → mitigasi dengan tuning prompt.
* **Risk 2**: Gmail API rate limit → mitigasi dengan caching dan pengaturan polling minimal.
* **Risk 3**: Keterlambatan Pub/Sub event → mitigasi dengan retry logic di Cloud Function.

---

## **10. Deliverables**

* Arsitektur desain dokumen  
* Source code Cloud Function  
* Konfigurasi Pub/Sub dan Gmail API  
* Dokumen deployment (step-by-step)  
* UAT (User Acceptance Testing) plan  

---

## **11. Timeline (High-Level)**

| Milestone            | Target Date |
| -------------------- | ----------- |
| BRD Approval         | 2025-08-06  |
| Design Finalization  | 2025-08-08  |
| Development Complete | 2025-08-15  |
| Testing (UAT)        | 2025-08-18  |
| Go-Live              | 2025-08-20  |

---

## **12. Success Metrics**

* 95% email masuk terbalas otomatis dalam <15 detik.
* Minimal 90% balasan dinilai relevan oleh tim QA.
* Tidak ada error API >1% dalam 1 bulan pertama operasi.
