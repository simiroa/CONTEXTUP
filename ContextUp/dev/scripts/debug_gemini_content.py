import os
import sys
from pathlib import Path
from google import genai
from google.genai import types

# Add src path
project_root = Path(__file__).resolve().parents[3]
src_path = project_root / "ContextUp" / "src"
sys.path.append(str(src_path))

from core.settings import load_settings

def debug_gemini_content():
    settings = load_settings()
    api_key = settings.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = "Describe a red cube"
    model_name = "gemini-2.5-flash-image"
    
    print(f"\nTesting generate_content with model: '{model_name}'")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt]
        )
        if response.text:
            print(f"✅ SUCCESS! Output text: {response.text}")
            print("Conclusion: This is likely a Text/Vision model, NOT an Image Generation model.")
        else:
            print(f"❌ No text returned.")
            
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    debug_gemini_content()
