# **Technical Design Document (TDD)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Overview**

Dokumen ini menjelaskan desain teknis implementasi sistem auto-reply email berbasis AI yang memanfaatkan Gmail API, Pub/Sub, Cloud Functions, dan Vertex AI Gemini. Fokus TDD adalah detail arsitektur, flow, integrasi API, serta pertimbangan keamanan dan skalabilitas.

---

## **2. High-Level Architecture**

### **Komponen Utama**

1. **Gmail API (Watch & Send)**  
   * Memantau email masuk di inbox Gmail.  
   * Mengirim balasan otomatis ke pengirim.  

2. **Pub/Sub**  
   * Menjadi message broker yang menerima event `historyId` dari Gmail API dan meneruskannya ke Cloud Function.  

3. **Cloud Function**  
   * Triggered oleh Pub/Sub.  
   * Ambil detail email berdasarkan `historyId`.  
   * Panggil Vertex AI Gemini untuk generate balasan.  
   * Kirim balasan ke pengirim email via Gmail API.  

4. **Vertex AI Gemini**  
   * Model generatif yang membuat balasan profesional dan kontekstual berdasarkan isi email.  

5. **Cloud Logging**  
   * Menyimpan log proses balasan email (ID email, pengirim, status).  

---

## **3. Detailed Flow**

### **Step-by-Step Flow**

1. Email baru masuk ke akun Gmail.  
2. Gmail API `watch` mengirim notifikasi ke Pub/Sub topic dengan `historyId`.  
3. Pub/Sub trigger Cloud Function.  
4. Cloud Function:  
   * Decode event dari Pub/Sub.  
   * Ambil detail email terbaru (`users.messages.get`).  
   * Extract `subject`, `body`, dan `from`.  
   * Generate balasan dengan Vertex AI Gemini (`generate_content`).  
   * Kirim balasan ke pengirim (`users.messages.send`).  
   * Catat log status ke Cloud Logging.  

---

## **4. System Components & Interfaces**

### **4.1 Gmail API**

* **Endpoint Watch**:  
  `POST https://gmail.googleapis.com/gmail/v1/users/me/watch`  
* **Endpoint Get Message**:  
  `GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{messageId}`  
* **Endpoint Send Message**:  
  `POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send`  

### **4.2 Pub/Sub**

* **Topic**: `projects/<PROJECT_ID>/topics/new-email`  
* **Subscription**: `projects/<PROJECT_ID>/subscriptions/email-subscriber`  

### **4.3 Vertex AI Gemini**

* **Model**: `gemini-1.5-pro`  
* **API Method**: `generate_content(prompt)`  

---

## **5. Data Flow Diagram**

```
+---------+      +---------+       +-------------+       +-------------+
|  Gmail  | ---> | Pub/Sub | --->  | Cloud Func  | --->  | Vertex AI   |
|  API    |      | Topic   |       | Subscriber  |       | Gemini      |
+---------+      +---------+       +-------------+       +-------------+
       \_____________________________________________________________/
                                 |
                           Auto Reply via
                           Gmail API Send
```

---

## **6. Data Structures**

### **6.1 Pub/Sub Message**

```json
{
  "emailAddress": "user@example.com",
  "historyId": "123456789"
}
```

### **6.2 Parsed Email Object**

```json
{
  "subject": "Request for quotation",
  "body": "Please provide your price list for product X.",
  "from": "client@example.com"
}
```

### **6.3 AI Reply**

```json
{
  "reply_text": "Terima kasih atas email Anda. Kami akan segera mengirimkan daftar harga produk X sesuai permintaan Anda."
}
```

---

## **7. Security Considerations**

* Gunakan **OAuth 2.0** untuk akses Gmail API.  
* Service account dengan role minimal:  
  * `roles/pubsub.subscriber`  
  * `roles/cloudfunctions.invoker`  
  * `roles/aiplatform.user`  
  * `roles/gmail.modify`  
* Pastikan **data email tidak disimpan permanen**, hanya metadata log.  

---

## **8. Error Handling**

### **8.1 Gmail API Errors**

* Retry jika API rate limit tercapai (exponential backoff).  
* Tangani email yang tidak memiliki `subject` atau `body` (balas template default).  

### **8.2 Pub/Sub Failures**

* Gunakan **dead-letter topic** untuk pesan gagal.  
* Set retry policy (max retries & backoff).  

### **8.3 AI Generation Failures**

* Fallback ke balasan template default jika AI gagal merespon.  

---

## **9. Performance & Scalability**

* **Cloud Functions** auto-scale berdasarkan jumlah event Pub/Sub.  
* Gmail API rate limit: 250 requests/user/second (cukup untuk 10k email/hari).  
* Batasi panjang prompt ke Gemini untuk menghemat biaya dan waktu inferensi.  

---

## **10. Deployment Plan**

### **Langkah-langkah:**

1. Enable API: Gmail, Pub/Sub, Cloud Functions, Vertex AI.  
2. Buat Pub/Sub topic & subscription.  
3. Setup Gmail API watch ke topic.  
4. Deploy Cloud Function:  

   ```bash
   gcloud functions deploy auto-reply-email \
       --runtime python311 \
       --trigger-topic new-email \
       --entry-point pubsub_trigger \
       --region us-central1
   ```  
5. Test: Kirim email ke inbox dan pastikan balasan otomatis terkirim.  

---

## **11. Monitoring & Logging**

* Gunakan **Cloud Logging** untuk mencatat status balasan.  
* Setup **alerting** jika error >1% (Cloud Monitoring).  
* Simpan metrik jumlah balasan harian untuk analisis performa.  

---

## **12. Future Enhancements**

* Tambahkan **moderation layer** untuk review balasan sebelum kirim.  
* Dukungan **multi-language reply** (deteksi bahasa otomatis).  
* Integrasi ke CRM atau tiket sistem (Zendesk, Freshdesk, dsb).  
* Analitik kepuasan balasan AI (feedback loop).