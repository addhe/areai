# **Prompt Engineering Document**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-04  
**Author**: addhe warman  

---

## **1. Purpose**

Dokumen ini mendefinisikan strategi prompt engineering untuk menghasilkan balasan email otomatis yang **profesional**, **relevan**, dan **kontekstual** menggunakan model **Vertex AI Gemini**.

---

## **2. Goals**

* Memastikan balasan AI sesuai konteks email masuk.  
* Menjaga tone balasan tetap profesional (atau formal/santai sesuai konfigurasi).  
* Menghindari kesalahan faktual atau balasan yang tidak pantas.  
* Mendukung fleksibilitas untuk multi-bahasa di fase selanjutnya.  

---

## **3. Prompt Structure**

### **3.1 Format Prompt Dasar**

```text
Anda adalah asisten email profesional. 
Tugas Anda adalah membalas email masuk dengan jawaban yang sopan, singkat, dan jelas. 
Gunakan gaya bahasa {TONE}.

Berikut detail email yang masuk:
- Pengirim: {SENDER}
- Subjek: {SUBJECT}
- Isi email: 
{BODY}

Balas email ini dengan nada {TONE}. Jangan sertakan tanda tangan pribadi.
```

### **3.2 Variabel yang Digunakan**

* `{TONE}`: Formal / Santai (diset dari konfigurasi user).  
* `{SENDER}`: Alamat pengirim email.  
* `{SUBJECT}`: Subjek email masuk.  
* `{BODY}`: Konten email masuk.  

---

## **4. Prompt Example**

### **Input Prompt**

```text
Anda adalah asisten email profesional. 
Tugas Anda adalah membalas email masuk dengan jawaban yang sopan, singkat, dan jelas. 
Gunakan gaya bahasa formal.

Berikut detail email yang masuk:
- Pengirim: client@abc.com
- Subjek: Permintaan Penawaran Harga
- Isi email: 
Mohon kirimkan daftar harga terbaru untuk produk X.

Balas email ini dengan nada formal. Jangan sertakan tanda tangan pribadi.
```

### **Output yang Diharapkan**

```
Terima kasih atas permintaan Anda. Kami akan segera mengirimkan daftar harga terbaru untuk produk X melalui email ini. Jika ada spesifikasi tambahan yang dibutuhkan, mohon informasikan kepada kami.
```

---

## **5. Prompt Variations (Untuk Tuning)**

### **5.1 Tone Variations**

* **Formal**: Gunakan bahasa baku, tanpa emotikon, fokus pada profesionalitas.  
* **Santai**: Gunakan bahasa ramah, sedikit personal, tetapi tetap sopan.  

---

### **5.2 Context Awareness**

Tambahkan instruksi untuk memperhatikan:  
* Bahasa email masuk (jika non-Indonesia, balas dalam bahasa yang sama).  
* Jika email bersifat negatif/complaint, balas dengan empati.  
* Jika email meminta informasi teknis, berikan jawaban jelas tapi ringkas.  

---

## **6. Guardrails / Kontrol Output**

* **Jangan sertakan informasi sensitif** (misal: internal pricing, password).  
* **Tidak menjawab di luar konteks email** (hindari improvisasi).  
* **Balasan ≤ 150 kata** agar tidak terlalu panjang.  
* **Selalu ucapkan terima kasih di awal balasan**.  

---

## **7. Strategy for Prompt Tuning**

1. **Iterative Testing**  
   Uji 10-20 contoh email real untuk melihat konsistensi tone & konteks.  

2. **Prompt Refinement**  
   * Jika AI terlalu panjang → Tambahkan instruksi "balasan maksimal 3 kalimat".  
   * Jika AI terlalu kaku → Tambahkan instruksi "gunakan bahasa natural".  

3. **Context Injection**  
   * Tambahkan metadata (role user, jenis pelanggan, label Gmail) ke prompt jika diperlukan.  

4. **Multi-Language Support (Future)**  
   * Tambahkan deteksi bahasa otomatis (`detectLanguage`) sebelum prompt.  
   * Sisipkan instruksi: “Balas dengan bahasa yang sama seperti email masuk.”  

---

## **8. Prompt for Fallback Reply**

Jika AI gagal merespon (timeout atau error):  

```
Terima kasih atas email Anda. Kami sudah menerimanya dan akan segera menindaklanjuti.
```

---

## **9. Example API Call (Python)**

```python
from google.cloud import aiplatform

aiplatform.init(project="PROJECT_ID", location="us-central1")
model = aiplatform.GenerativeModel("gemini-1.5-pro")

prompt = f"""
Anda adalah asisten email profesional. 
Tugas Anda adalah membalas email masuk dengan jawaban yang sopan, singkat, dan jelas.
Gunakan gaya bahasa formal.

Berikut detail email yang masuk:
- Pengirim: {sender}
- Subjek: {subject}
- Isi email: 
{body}

Balas email ini dengan nada formal. Jangan sertakan tanda tangan pribadi.
"""

response = model.generate_content(prompt)
reply_text = response.text
```

---

## **10. Future Prompt Enhancements**

* **Custom Prompt per Department**: Sales, Support, Finance.  
* **Dynamic Persona**: AI bisa berbicara seolah-olah dari tim tertentu.  
* **Sentiment-aware Replies**: Balasan menyesuaikan nada email masuk (positif/negatif).  
* **Integration with Knowledge Base**: AI menarik jawaban dari FAQ internal.
