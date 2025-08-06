#!/usr/bin/env python3
"""
Alternative AI response generation using Google GenAI SDK
"""

import os
from google import genai
from google.genai import types

def generate_ai_response_genai(email_data):
    """Generate an AI response using Google GenAI SDK."""
    try:
        print("Initializing Google GenAI client")
        
        # Get API key from environment or Secret Manager
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("No GEMINI_API_KEY found, falling back to Vertex AI")
            return None
        
        client = genai.Client(api_key=api_key)
        
        # Create prompt
        prompt = f"""You are a helpful AI email assistant. Generate a polite and professional response to this email:

From: {email_data['from']}
Subject: {email_data['subject']}
Message: {email_data['body']}

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
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
        )
        
        print("Generating AI response with GenAI SDK...")
        response_text = ""
        
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        response_text = response_text.strip()
        print(f"Successfully generated AI response: {response_text[:100]}...")
        return response_text
        
    except Exception as e:
        print(f"Error generating AI response with GenAI SDK: {e}")
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
