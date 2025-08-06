#!/usr/bin/env python3
"""
Test script to debug Vertex AI integration
"""

import os
import vertexai
from vertexai.generative_models import GenerativeModel

# Configuration
PROJECT_ID = "awanmasterpiece"
VERTEX_MODEL = "gemini-1.5-flash"  # More commonly available

def test_vertex_ai():
    """Test Vertex AI text generation."""
    try:
        print("Initializing Vertex AI...")
        vertexai.init(project=PROJECT_ID, location="us-central1")
        
        print(f"Loading model: {VERTEX_MODEL}")
        model = GenerativeModel(VERTEX_MODEL)
        
        # Test prompt
        prompt = """You are a helpful AI email assistant. Generate a polite and professional response to this email:

From: test@example.com
Subject: Testing auto-reply
Message: Hello, this is a test email to check if the auto-reply system is working.

Your response should:
- Acknowledge their email
- Be helpful and professional
- Be concise (2-3 sentences)
- End politely

Response:"""
        
        print("Generating response...")
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40
            }
        )
        
        print(f"✅ Success! Generated response:")
        print(f"'{response.text.strip()}'")
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vertex_ai()
