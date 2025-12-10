import json
import os
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent.parent / "config" / "settings.json"
SECRETS_FILE = Path(__file__).parent.parent.parent / "config" / "secrets.json"

DEFAULT_SETTINGS = {
    "GEMINI_API_KEY": "",
    "OLLAMA_URL": "http://localhost:11434",
    "PYTHON_PATH": "",
    "THEME": "light",
    "FFMPEG_PATH": "",
    "BLENDER_PATH": "",
    "MAYO_PATH": "",
    "CATEGORY_COLORS": {
        "Image": "#2ecc71",
        "Video": "#3498db",
        "Audio": "#e67e22",
        "3D": "#9b59b6",
        "Sys": "#95a5a6",
        "Document": "#f1c40f",
        "Custom": "#ecf0f1"
    }
}

SENSITIVE_KEYS = ["GEMINI_API_KEY"]

def load_settings():
    """Load settings from JSON and set environment variables."""
    settings = DEFAULT_SETTINGS.copy()
    
    # Load main settings
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                settings.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    # Load secrets (overrides main settings if present)
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, 'r') as f:
                secrets = json.load(f)
                for key in SENSITIVE_KEYS:
                    if key in secrets:
                        settings[key] = secrets[key]
        except Exception as e:
            print(f"Error loading secrets: {e}")
            
    # Set environment variables
    if settings.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = settings["GEMINI_API_KEY"]
        
    if settings.get("OLLAMA_URL"):
        os.environ["OLLAMA_HOST"] = settings["OLLAMA_URL"]
        
    return settings

def save_settings(new_settings):
    """Save settings to JSON, separating secrets."""
    try:
        # Prepare content for settings.json (exclude secrets)
        settings_to_save = new_settings.copy()
        secrets_to_save = {}
        
        for key in SENSITIVE_KEYS:
            if key in settings_to_save:
                secrets_to_save[key] = settings_to_save.pop(key)
                
        # Save main settings
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_to_save, f, indent=4)
            
        # Save secrets if there are any to update
        if secrets_to_save:
            existing_secrets = {}
            if SECRETS_FILE.exists():
                try:
                    with open(SECRETS_FILE, 'r') as f:
                        existing_secrets = json.load(f)
                except:
                    pass
            
            existing_secrets.update(secrets_to_save)
            
            with open(SECRETS_FILE, 'w') as f:
                json.dump(existing_secrets, f, indent=4)
                
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False
