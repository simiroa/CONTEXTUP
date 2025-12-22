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

def test_gemini_vision():
    settings = load_settings()
    api_key = settings.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    model_name = "gemini-2.5-flash-image"
    prompt = "A simple red cube"
    
    print(f"Testing model: {model_name}")
    
    # 1. Try generate_images
    print("\n--- Method 1: client.models.generate_images ---")
    try:
        response = client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
            )
        )
        if response.generated_images:
            print("✅ generate_images SUCCESS!")
            return "generate_images"
        else:
            print("❌ generate_images returned no images")
    except Exception as e:
        print(f"❌ generate_images FAILED: {custom_str(e)}")

    # 2. Try generate_content
    print("\n--- Method 2: client.models.generate_content ---")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(
                 response_mime_type="image/png" # Try asking for image mime type?
            )
        )
        # Check parts
        if response.parts:
            print(f"Parts count: {len(response.parts)}")
            for part in response.parts:
                if part.inline_data:
                    print("✅ generate_content returned INLINE DATA (Image likely)")
                    return "generate_content"
                elif part.text:
                    print(f"ℹ️ generate_content returned TEXT: {part.text[:50]}...")
            print("❌ generate_content returned neither inline_data nor text??")
        else:
             print("❌ generate_content returned no parts")

    except Exception as e:
         print(f"❌ generate_content FAILED: {custom_str(e)}")
    
    return None

def custom_str(e):
    # Helper to shorten error message
    s = str(e)
    return s[:200] + "..." if len(s) > 200 else s

if __name__ == "__main__":
    method = test_gemini_vision()
    print(f"\nRecommended Method: {method}")
