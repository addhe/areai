#!/usr/bin/env python3
"""
List available Vertex AI models
"""

import vertexai
from vertexai.language_models import TextGenerationModel

PROJECT_ID = "awanmasterpiece"

def list_available_models():
    """List available text generation models."""
    try:
        print("Initializing Vertex AI...")
        vertexai.init(project=PROJECT_ID, location="us-central1")
        
        # Common model names to try
        models_to_try = [
            "text-bison",
            "text-bison@002", 
            "text-bison@latest",
            "text-unicorn",
            "text-unicorn@001",
            "gemini-pro",
            "gemini-1.0-pro",
            "gemini-1.5-pro"
        ]
        
        print("Testing available models:")
        available_models = []
        
        for model_name in models_to_try:
            try:
                print(f"  Testing {model_name}...", end="")
                model = TextGenerationModel.from_pretrained(model_name)
                
                # Try a simple prediction to verify access
                response = model.predict("Hello", max_output_tokens=10)
                print(f" ✅ Available")
                available_models.append(model_name)
                
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    print(f" ❌ Not found")
                elif "permission" in str(e).lower() or "access" in str(e).lower():
                    print(f" ❌ No access")
                else:
                    print(f" ❌ Error: {str(e)[:50]}...")
        
        print(f"\n✅ Available models: {available_models}")
        
        if available_models:
            print(f"\n🎯 Recommended model to use: {available_models[0]}")
        else:
            print("\n❌ No models available. Check project permissions and API enablement.")
            
    except Exception as e:
        print(f"❌ Error initializing Vertex AI: {e}")

if __name__ == "__main__":
    list_available_models()
