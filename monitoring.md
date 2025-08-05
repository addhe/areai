# **Monitoring & Alerting Guide**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)
**Document Version**: 1.0
**Date**: 2025-08-04
**Author**: addhe warman

---

## **1. Overview**

Panduan ini menjelaskan cara memantau kesehatan sistem auto-reply email AI di Google Cloud, termasuk penggunaan **Cloud Logging**, **Cloud Monitoring (Metrics & Dashboard)**, serta konfigurasi **alerting** untuk mendeteksi masalah operasional secara proaktif.

---

## **2. Goals**

* Memastikan balasan AI dikirim tepat waktu (<15 detik).
* Mendeteksi error Gmail API, Pub/Sub, atau Vertex AI secara real-time.
* Menyediakan dashboard KPI (jumlah email dibalas, error rate, waktu balasan rata-rata).
* Memberikan notifikasi otomatis ke tim jika terjadi gangguan.

---

## **3. Components to Monitor**

1. **Cloud Functions (auto-reply-email)**
   * Execution count (success/fail)
   * Latency (average & p95)
   * Memory usage

2. **Pub/Sub**
   * Subscription backlog
   * Delivery latency

3. **Vertex AI**
   * Request count
   * Error rate (model generate failure)

4. **Gmail API**
   * Rate limit errors (429)
   * Authorization failures (401)

5. **Overall KPIs**
   * Total auto-replied emails per day
   * Verified customer replies count
   * Non-customer replies count
   * Average response time
   * Error percentage

---

## **4. Cloud Logging Setup**

### **4.1 Enable Logging**

* Cloud Functions otomatis menulis log ke **Cloud Logging**.
* Tambahkan log custom (status balasan, subject email, waktu proses).

### **4.2 Log Query Contoh**

* Semua error function:
```bash
resource.type="cloud_function"
resource.labels.function_name="auto-reply-email"
severity>=ERROR
```

* Waktu proses >10 detik:
```bash
jsonPayload.latency>10
```

* Email dari nasabah terverifikasi:
```bash
jsonPayload.customer_status="verified"
```

* Email dari non-nasabah:
```bash
jsonPayload.customer_status="non-customer"
```

---

## **5. Cloud Monitoring Metrics**

### **5.1 Function Metrics**

* **Metric**: `cloudfunctions.googleapis.com/function/execution_count`
* **Filter**: label `status="error"` vs `status="ok"`

### **5.2 Pub/Sub Metrics**

* **Metric**: `pubsub.googleapis.com/subscription/num_undelivered_messages`

### **5.3 Vertex AI Metrics**

* Buat custom metric:
  * `vertex_ai_auto_reply_success_count`
  * `vertex_ai_auto_reply_failure_count`

---

## **6. Dashboard Setup**

### **6.1 Langkah Buat Dashboard**

1. Buka [Cloud Monitoring → Dashboards](https://console.cloud.google.com/monitoring/dashboards).
2. Klik **Create Dashboard** → nama: `Auto Reply AI Dashboard`.
3. Tambahkan widget:
   * **Time Series**: Jumlah email dibalas per hari.
   * **Pie Chart**: Success vs Error.
   * **Line Chart**: Response time p95.

### **6.2 Contoh Layout**

```
-----------------------------------------------------
|   Auto Reply AI Dashboard                         |
-----------------------------------------------------
| Total Replies Today | Error Rate | Avg Latency     |
-----------------------------------------------------
| Graph: Replies/Day (line) | Graph: Errors (bar)   |
-----------------------------------------------------
```

---

## **7. Alerting Policy**

### **7.1 Error Rate Alert**

* **Condition**: Error > 1% dari total execution selama 5 menit.
* **Metric**: `cloudfunctions.googleapis.com/function/execution_count`
* **Notification**: Email ke tim support.

### **7.2 Pub/Sub Backlog Alert**

* **Condition**: `num_undelivered_messages` > 100 selama 10 menit.
* **Impact**: Indikasi fungsi lambat atau mati.

### **7.3 Latency Alert**

* **Condition**: Execution latency > 15 detik (p95) selama 5 menit.

---

## **8. Incident Response Playbook**

1. **Deteksi**: Alert masuk via email/Slack.
2. **Identifikasi**: Cek Cloud Logging → lihat error detail.
3. **Aksi Cepat**:
   * Error Gmail API → cek quota & OAuth token.
   * Pub/Sub backlog → scale function / cek retry.
   * Vertex AI error → cek quota model / region availability.
4. **Recovery**: Redeploy function jika perlu.
5. **Postmortem**: Catat penyebab & perbaikan permanen.

---

## **9. Reporting**

* **Laporan Harian**:
  * Jumlah email dibalas
  * Error count
  * Waktu balasan rata-rata

* **Laporan Mingguan**:
  * Tren error
  * Evaluasi relevansi balasan AI (UAT feedback)

---

## **10. Continuous Improvement**

* Tambah anomaly detection (BigQuery ML / Looker).
* Integrasi alert ke Slack / PagerDuty.
* Tambah metric “AI relevansi score” (feedback user).
