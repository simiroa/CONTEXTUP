import json
import os
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MENU_CONFIG_PATH = PROJECT_ROOT / "config" / "menu_config.json"
OUTPUT_DIR = PROJECT_ROOT / "config" / "menu_categories"

def migrate():
    if not MENU_CONFIG_PATH.exists():
        print(f"Error: {MENU_CONFIG_PATH} not found.")
        return

    try:
        with open(MENU_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading menu_config.json: {e}")
        return

    if not isinstance(data, list):
        print("Error: menu_config.json must be a list of objects.")
        return

    categories = defaultdict(list)
    
    for item in data:
        cat = item.get("category", "Uncategorized")
        # Normalize category name for filename (lowercase, no spaces)
        filename = cat.lower().replace(" ", "_") + ".json"
        categories[filename].append(item)

    if not OUTPUT_DIR.exists():
        os.makedirs(OUTPUT_DIR)

    for filename, items in categories.items():
        output_path = OUTPUT_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
        print(f"Created {filename} with {len(items)} items.")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
