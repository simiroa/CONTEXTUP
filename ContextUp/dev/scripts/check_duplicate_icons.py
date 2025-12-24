
import json
import os
from pathlib import Path
from collections import defaultdict

def check_duplicate_icons():
    # Setup paths
    root_dir = Path(__file__).resolve().parent.parent.parent
    config_dir = root_dir / "config" / "categories"
    
    print(f"Checking duplicate icons in {config_dir}...")
    
    icon_usage = defaultdict(list)
    
    if not config_dir.exists():
        print(f"Error: {config_dir} does not exist")
        return

    for json_file in config_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "features" in data:
                items = data["features"]

            for item in items:
                name = item.get('name', 'Unknown')
                icon_path = item.get('icon', '')
                
                if icon_path:
                    # Normalize path separation
                    normalized_path = icon_path.replace("\\", "/")
                    icon_usage[normalized_path].append(f"[{json_file.name}] {name}")
                    
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")

    print("\n--- Duplicate Icons Report ---")
    duplicates_found = False
    for icon, usages in icon_usage.items():
        if len(usages) > 1:
            duplicates_found = True
            print(f"Icon: {icon}")
            for u in usages:
                print(f"  - {u}")
            print("")
            
    if not duplicates_found:
        print("No duplicate icon usage found!")

if __name__ == "__main__":
    check_duplicate_icons()
