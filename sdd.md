# **Software Design Document (SDD)**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Introduction**

### **1.1 Purpose**

Dokumen ini menjelaskan desain perangkat lunak untuk sistem auto-reply email berbasis AI menggunakan Vertex AI Gemini. SDD mencakup arsitektur perangkat lunak, desain modul, antarmuka, dan pertimbangan performa serta keamanan.

---

### **1.2 Scope**

Sistem ini mendeteksi email baru di Gmail dan secara otomatis membalas menggunakan AI. Semua komponen berjalan di Google Cloud (Gmail API, Pub/Sub, Cloud Functions, Vertex AI).

---

## **2. System Overview**

### **2.1 High-Level Workflow**

1. Gmail API `watch` memantau email masuk.  
2. Notifikasi `historyId` dikirim ke Pub/Sub.  
3. Cloud Function menerima event, mengambil detail email.  
4. Cloud Function memanggil Vertex AI Gemini untuk membuat balasan.  
5. Balasan dikirim ke pengirim email via Gmail API.  

---

### **2.2 Technology Stack**

* **Backend Processing**: Python 3.11 (Cloud Functions)  
* **AI Generation**: Vertex AI Gemini (`gemini-1.5-pro`)  
* **Event Messaging**: Google Pub/Sub  
* **Email API**: Gmail API  
* **UI Monitoring**: React.js + Tailwind (opsional fase berikutnya)  

---

## **3. Architecture Design**

### **3.1 Component Diagram**

```
+----------------+     +----------------+     +----------------+
| Gmail API      | --> | Pub/Sub Topic  | --> | Cloud Function |
+----------------+     +----------------+     +----------------+
                                                  |
                                                  v
                                          +----------------+
                                          | Vertex AI Gemini|
                                          +----------------+
                                                  |
                                                  v
                                           +--------------+
                                           | Gmail API Send|
                                           +--------------+
```

---

## **4. Module Design**

### **4.1 Modules**

1. **Gmail Watcher**  
   * Menetapkan watch pada inbox Gmail.  
   * Mengirim event ke Pub/Sub.  

2. **Pub/Sub Subscriber**  
   * Trigger Cloud Function untuk memproses email.  

3. **Email Processor**  
   * Mengambil detail email via Gmail API (`users.messages.get`).  
   * Parsing `subject`, `body`, `from`.  

4. **AI Generator**  
   * Mengirim prompt ke Vertex AI Gemini.  
   * Mendapatkan teks balasan AI.  

5. **Reply Sender**  
   * Mengirim balasan ke pengirim email via Gmail API (`users.messages.send`).  

6. **Logging & Monitoring**  
   * Menyimpan log proses ke Cloud Logging.  

---

## **5. Data Model**

### **5.1 Pub/Sub Message**

```json
{
  "emailAddress": "user@example.com",
  "historyId": "987654321"
}
```

### **5.2 Email Detail**

```json
{
  "subject": "Order Status Inquiry",
  "body": "Could you provide the latest status for order #123?",
  "from": "customer@example.com"
}
```

### **5.3 AI Reply Output**

```json
{
  "reply_text": "Thank you for your inquiry. We are processing your order and will update you shortly."
}
```

---

## **6. API Design**

### **6.1 Gmail API**

* **Watch Endpoint**: `POST /gmail/v1/users/me/watch`  
* **Messages List**: `GET /gmail/v1/users/me/messages`  
* **Message Detail**: `GET /gmail/v1/users/me/messages/{id}`  
* **Send Message**: `POST /gmail/v1/users/me/messages/send`  

---

### **6.2 Vertex AI**

* **Model**: `gemini-1.5-pro`  
* **Method**: `generate_content(prompt)`  

---

## **7. Error Handling**

* **Pub/Sub Failure**: Gunakan dead-letter topic untuk pesan gagal.  
* **Gmail API Limit**: Implement exponential backoff untuk retry.  
* **AI Failure**: Fallback ke template balasan default.  
* **Parsing Error**: Jika body kosong, gunakan template “Terima kasih, email Anda telah kami terima.”  

---

## **8. Security Design**

* Gunakan **OAuth 2.0** untuk akses Gmail API.  
* Gunakan **Service Account** dengan role minimal:  
  * `roles/pubsub.subscriber`  
  * `roles/aiplatform.user`  
  * `roles/gmail.modify`  
* Enkripsi data sensitif (API Key, token) di Secret Manager.  
* Hindari penyimpanan konten email penuh (hanya metadata yang dilogging).  

---

## **9. Performance Considerations**

* Cloud Function bersifat stateless dan auto-scale.  
* Batasi panjang prompt ke AI (maks 2000 karakter) untuk efisiensi biaya.  
* Rata-rata waktu balasan ditargetkan <15 detik per email.  

---

## **10. Deployment Plan**

1. Enable API: Gmail, Pub/Sub, Cloud Functions, Vertex AI.  
2. Buat Pub/Sub topic & subscription.  
3. Setup Gmail API watch.  
4. Deploy Cloud Function menggunakan Python 3.11.  
5. Test end-to-end dengan email simulasi.  
6. Monitoring via Cloud Logging & Alerting.  

---

## **11. Future Enhancements**

* **Moderation Layer**: Review balasan sebelum terkirim.  
* **Multi-language Reply**: Deteksi bahasa otomatis.  
* **CRM Integration**: Sinkronisasi dengan Zendesk/Freshdesk.  
* **Analytics Dashboard**: Insight balasan AI (relevansi, respon).  

---

## **12. Appendix**

### **12.1 Tools**

* Google Cloud SDK  
* Postman (uji API Gmail)  
* VSCode (development)  
* Terraform (optional untuk infra-as-code)  

---

### **12.2 References**

* [Gmail API Docs](https://developers.google.com/gmail/api)  
* [Pub/Sub Docs](https://cloud.google.com/pubsub/docs)  
* [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)
