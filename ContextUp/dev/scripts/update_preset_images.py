import os
import json
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PRESETS_DIR = os.path.join(BASE_DIR, "config", "prompt_master", "presets")

PLACEHOLDERS = {
    "abstract.png": ["abstract", "art", "style", "color", "pattern"],
    "portrait.png": ["character", "portrait", "person", "face", "girl", "boy", "man", "woman"],
    "landscape.png": ["landscape", "scenery", "nature", "mountain", "sky", "view", "background"],
    "scifi.png": ["scifi", "tech", "future", "space", "cyber", "robot", "mech"]
}

DEFAULT_PLACEHOLDER = "abstract.png"

def get_placeholder_for_preset(name, description):
    text = (name + " " + description).lower()
    
    for image, keywords in PLACEHOLDERS.items():
        for keyword in keywords:
            if keyword in text:
                return image
    
    return random.choice(list(PLACEHOLDERS.keys()))

def update_presets():
    count = 0
    for root, dirs, files in os.walk(PRESETS_DIR):
        if "_placeholders" in root:
            continue
            
        for file in files:
            if file.endswith(".json") and file != "list.json":
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if "example_image" not in data or not data["example_image"]:
                        placeholder = get_placeholder_for_preset(data.get("name", ""), data.get("description", ""))
                        data["example_image"] = placeholder
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        
                        print(f"Updated {file} with {placeholder}")
                        count += 1
                except Exception as e:
                    print(f"Error updating {file}: {e}")
    
    print(f"Total presets updated: {count}")

if __name__ == "__main__":
    update_presets()
