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

def debug_gemini_image():
    settings = load_settings()
    api_key = settings.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = "A simple red cube"
    
    models_to_test = [
        "gemini-2.5-flash-image",
        "models/gemini-2.5-flash-image",
        "gemini-2.5-flash-image-preview"
    ]
    
    for model_name in models_to_test:
        print(f"\nTesting generate_images with model: '{model_name}'")
        try:
            response = client.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    # aspect_ratio not supported by all models
                )
            )
            if response.generated_images:
                print(f"✅ SUCCESS with {model_name}!")
                return model_name
            else:
                print(f"❌ Returned no images")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            
    return None

if __name__ == "__main__":
    debug_gemini_image()
