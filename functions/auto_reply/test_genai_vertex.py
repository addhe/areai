#!/usr/bin/env python3
"""
Test script using GenAI SDK with Vertex AI backend
"""

import os
from main import generate_ai_response

# Set environment variable for Project ID if not already set
os.environ.setdefault('PROJECT_ID', 'awanmasterpiece')

# Mock function to simulate Nasabah API responses
def mock_check_is_nasabah(email):
    """Mock function to simulate Nasabah API responses."""
    print(f"Checking customer status for: {email}")
    
    # Simulate API response based on email domain
    # Hanya email dengan domain tertentu yang dianggap sebagai nasabah
    if '@outlook.co.id' in email:
        print(f"Customer found for email: {email}")
        return True
    else:
        print(f"Customer not found for email: {email}")
        return False

def run_test(email_from, subject, body):
    """Simulates the auto-reply flow for a single email."""
    print(f"\n--- Testing for: {email_from} ---")
    
    email_data = {
        'from': email_from,
        'subject': subject,
        'body': body
    }
    
    # 1. Check if the sender is a customer using our mock function
    is_nasabah = mock_check_is_nasabah(email_from)
    print(f"Customer check result: {'Nasabah' if is_nasabah else 'Bukan Nasabah'}")
     
    # 2. Generate AI response with the context
    print("Generating AI response...")
    response = generate_ai_response(email_data, is_nasabah)
    
    if response:
        print("✅ Success! Generated response:")
        print("-" * 20)
        print(response)
        print("-" * 20)
    else:
        print("❌ Error: Failed to generate AI response.")

if __name__ == "__main__":
    # Test case 1: Email dari nasabah terdaftar
    run_test(
        email_from='addhe.warman@outlook.co.id',
        subject='Pertanyaan tentang produk',
        body='Halo, saya ingin bertanya tentang detail produk terbaru Anda.'
    )

    # Test case 2: Email dari bukan nasabah
    run_test(
        email_from='random.person@example.com',
        subject='Kerjasama',
        body='Selamat siang, kami ingin mengajukan proposal kerjasama.'
    )
    
    # Test case 3: Email dari bukan nasabah dengan pertanyaan saldo
    run_test(
        email_from='potential.customer@example.com',
        subject='Pertanyaan Saldo',
        body='Hi cs team, Apakah saya boleh tahu saldo saya saat ini ada berapa? Thank you'
    )
