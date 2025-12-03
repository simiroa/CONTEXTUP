import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_CONFIG_DIR = PROJECT_ROOT / "config" / "tools"
OUTPUT_CONFIG_PATH = PROJECT_ROOT / "config" / "menu_config.json"

def build_config():
    if not TOOLS_CONFIG_DIR.exists():
        print(f"Tools config directory not found: {TOOLS_CONFIG_DIR}")
        return

    combined_config = []
    
    # List all json files
    files = [f for f in os.listdir(TOOLS_CONFIG_DIR) if f.endswith('.json')]
    
    print(f"Found {len(files)} tool configurations.")
    
    for filename in files:
        file_path = TOOLS_CONFIG_DIR / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tool_config = json.load(f)
                combined_config.append(tool_config)
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    # Sort by Category then Name for tidiness
    combined_config.sort(key=lambda x: (x.get('category', 'ZZZ'), x.get('name', '')))

    # Write to menu_config.json
    with open(OUTPUT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(combined_config, f, indent=4)
        
    print(f"Successfully rebuilt menu_config.json with {len(combined_config)} entries.")

if __name__ == "__main__":
    build_config()
