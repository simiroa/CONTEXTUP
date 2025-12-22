import os
import sys
from pathlib import Path

# Add src path
project_root = Path(__file__).resolve().parents[3] # HG_context_v2
src_path = project_root / "ContextUp" / "src"
sys.path.append(str(src_path))

try:
    from google import genai
    from core.settings import load_settings
    
    settings = load_settings()
    api_key = settings.get("GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    
    print("Direct attributes of client.models:")
    print(dir(client.models))
    
    print("\nAttempting to find 'generate_images' or similar...")
    if hasattr(client.models, 'generate_images'):
        print("✅ client.models.generate_images exists!")
    
    print("\nListing available models:")
    try:
        for model in client.models.list():
            print(f"- {model.name}")
            # Some SDK versions might expose supported methods
            if hasattr(model, 'supported_generation_methods'):
                print(f"  Methods: {model.supported_generation_methods}")
    except Exception as e:
        print(f"Failed to list models: {e}")
        
except Exception as e:
    print(f"Error: {e}")
