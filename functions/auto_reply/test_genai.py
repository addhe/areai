#!/usr/bin/env python3
"""
Test script using Google GenAI SDK instead of Vertex AI
"""

import os
from google import genai
from google.genai import types

def test_genai():
    """Test Google GenAI SDK."""
    try:
        print("Testing Google GenAI SDK...")
        
        # Check if API key is available
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY environment variable not set")
            print("You need to:")
            print("1. Get API key from https://aistudio.google.com/app/apikey")
            print("2. Set environment variable: export GEMINI_API_KEY=your_key_here")
            return
        
        print(f"✅ API key found: {api_key[:10]}...")
        
        client = genai.Client(api_key=api_key)
        
        model = "gemini-2.5-flash-lite"
        
        # Test prompt
        test_prompt = """You are a helpful AI email assistant. Generate a polite and professional response to this email:

From: test@example.com
Subject: Testing auto-reply
Message: Hello, this is a test email to check if the auto-reply system is working.

Your response should:
- Acknowledge their email
- Be helpful and professional
- Be concise (2-3 sentences)
- End politely

Response:"""
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=test_prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
        )
        
        print("Generating response...")
        response_text = ""
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
            print(chunk.text, end="")
        
        print(f"\n\n✅ Success! Generated response:")
        print(f"'{response_text.strip()}'")
        
        return response_text.strip()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_genai()
