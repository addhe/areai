#!/usr/bin/env python3
"""
Alternative AI response generation using Google GenAI SDK
"""

import os
from google import genai
from google.genai import types

def generate_ai_response_genai(email_data):
    """Menghasilkan respons AI menggunakan Google GenAI SDK."""
    try:
        print("Menginisialisasi klien Google GenAI")
        
        # Dapatkan kunci API dari environment atau Secret Manager
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Kunci GEMINI_API_KEY tidak ditemukan, kembali ke Vertex AI")
            return None
        
        client = genai.Client(api_key=api_key)
        
        # Buat prompt dalam Bahasa Indonesia
        prompt = f"""Anda adalah asisten email AI yang membantu. Buat balasan yang sopan dan profesional untuk email ini.

PENTING:
- Balas dalam Bahasa Indonesia.
- JANGAN menambahkan frasa pengantar seperti "Tentu, ini balasannya:" atau sejenisnya.
- Langsung mulai dengan "Kepada [nama]" atau sapaan yang sesuai.
- Jika ada pertanyaan tentang saldo, berikan informasi saldo yang sebenarnya, bukan placeholder "[Jumlah Saldo Anda]".

Dari: {email_data['from']}
Subjek: {email_data['subject']}
Pesan: {email_data['body']}

Balasan Anda harus:
- Mengakui email mereka
- Membantu dan profesional
- Ringkas (2-3 kalimat)
- Diakhiri dengan sopan

Balasan:"""
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
        )
        
        print("Membuat respons AI dengan GenAI SDK...")
        response_text = ""
        
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        response_text = response_text.strip()
        print(f"Berhasil membuat respons AI: {response_text[:100]}...")
        return response_text
        
    except Exception as e:
        print(f"Gagal membuat respons AI dengan GenAI SDK: {e}")
        return None

if __name__ == "__main__":
    # Test the function
    test_email = {
        'from': 'test@example.com',
        'subject': 'Testing auto-reply',
        'body': 'Hello, this is a test email to check if the auto-reply system is working.'
    }
    
    response = generate_ai_response_genai(test_email)
    if response:
        print(f"Generated response: {response}")
    else:
        print("Failed to generate response")
