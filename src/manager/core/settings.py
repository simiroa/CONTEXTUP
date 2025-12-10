import json
import logging
from pathlib import Path

logger = logging.getLogger("manager.core.settings")

SETTINGS_FILE = Path("config/settings.json")
SECRETS_FILE = Path("config/secrets.json")

SENSITIVE_KEYS = ["GEMINI_API_KEY"]

def load_settings() -> dict:
    """Load application settings from JSON."""
    defaults = {
        "PYTHON_PATH": "",
        "CATEGORY_COLORS": {
            "Audio": "#ff9999",
            "Video": "#99ff99",
            "Images": "#9999ff",
            "Tools": "#ffff99",
            "System": "#ffcc99",
            "3D": "#cc99ff",
            "Text": "#99ccff"
        },
        "BACKUP_EXCLUDE": [],
        "GEMINI_API_KEY": "",
        "OLLAMA_URL": "http://localhost:11434",
        "TRAY_ENABLED": False
    }
    
    try:
        # Load main settings
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                defaults.update(data)
                
        # Load secrets
        if SECRETS_FILE.exists():
            with open(SECRETS_FILE, "r") as f:
                secrets = json.load(f)
                for key in SENSITIVE_KEYS:
                    if key in secrets:
                        defaults[key] = secrets[key]
                        
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        
    return defaults

def save_settings(settings: dict) -> bool:
    """Save application settings to JSON, separating secrets."""
    try:
        if not SETTINGS_FILE.parent.exists():
            SETTINGS_FILE.parent.mkdir(parents=True)
            
        # Prepare content
        settings_to_save = settings.copy()
        secrets_to_save = {}
        
        for key in SENSITIVE_KEYS:
            if key in settings_to_save:
                secrets_to_save[key] = settings_to_save.pop(key)
        
        # Save main settings
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_to_save, f, indent=4)
            
        # Save secrets
        if secrets_to_save:
            existing_secrets = {}
            if SECRETS_FILE.exists():
                try:
                    with open(SECRETS_FILE, "r") as f:
                        existing_secrets = json.load(f)
                except:
                    pass
            
            existing_secrets.update(secrets_to_save)
            
            with open(SECRETS_FILE, "w") as f:
                json.dump(existing_secrets, f, indent=4)
                
        logger.info("Settings saved successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return False
