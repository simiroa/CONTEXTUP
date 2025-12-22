
from google import genai
import os

import sys

API_KEY = os.getenv("GEMINI_API_KEY")

def check_models():
    if not API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
        
    print(f"Using Key: {API_KEY[:5]}...")
    try:
        client = genai.Client(api_key=API_KEY)
        # Using the new SDK pattern if possible, or try catch
        # The new SDK might not expose list_models directly on 'models' property same way as old SDK
        # But let's try broadly.
        
        # Based on documentation for google-genai package:
        pager = client.models.list()
        print("Available Models:")
        found = False
        for model in pager:
            print(f" - {model.name}")
            if "gemini-2.5" in model.name:
                found = True
        
        if found:
            print("\n✅ 'gemini-2.5' variant found.")
        else:
            print("\n❌ 'gemini-2.5' NOT found.")
            
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    check_models()
