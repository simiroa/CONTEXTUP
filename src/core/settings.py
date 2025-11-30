import json
import os
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent.parent / "config" / "settings.json"

DEFAULT_SETTINGS = {
    "GEMINI_API_KEY": "",
    "OLLAMA_URL": "http://localhost:11434",
    "PYTHON_PATH": "",
    "THEME": "light",
    "FFMPEG_PATH": "",
    "BLENDER_PATH": "",
    "MAYO_PATH": ""
}

def load_settings():
    """Load settings from JSON and set environment variables."""
    settings = DEFAULT_SETTINGS.copy()
    
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                settings.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    # Set environment variables
    if settings.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = settings["GEMINI_API_KEY"]
        
    if settings.get("OLLAMA_URL"):
        os.environ["OLLAMA_HOST"] = settings["OLLAMA_URL"]
        
    return settings

def save_settings(new_settings):
    """Save settings to JSON."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(new_settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False
