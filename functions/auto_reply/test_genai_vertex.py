#!/usr/bin/env python3
"""
Test script using GenAI SDK with Vertex AI backend
"""

from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "awanmasterpiece"
VERTEX_MODEL = "gemini-2.5-flash-lite"

def test_genai_vertex():
    """Test GenAI SDK with Vertex AI backend."""
    try:
        print("Initializing GenAI client with Vertex AI backend...")
        
        # Create GenAI client with Vertex AI backend
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="us-central1",
        )
        
        print(f"Using model: {VERTEX_MODEL}")
        
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
        
        # Create content
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt)
                ]
            )
        ]
        
        # Generate content config
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.8,
            max_output_tokens=256,
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
        )
        
        print("Generating response...")
        response_text = ""
        
        for chunk in client.models.generate_content_stream(
            model=VERTEX_MODEL,
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
    test_genai_vertex()
