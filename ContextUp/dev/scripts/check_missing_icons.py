
import json
import os
from pathlib import Path

def check_icons():
    # Setup paths
    root_dir = Path(__file__).resolve().parent.parent.parent
    config_dir = root_dir / "config" / "categories"
    
    print(f"Checking icons in {config_dir}...")
    
    missing_icons = []
    
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
                icon_path_str = item.get('icon', '')
                
                if not icon_path_str:
                    missing_icons.append(f"[{json_file.name}] {name}: No icon defined")
                    continue
                    
                # Check path
                if os.path.isabs(icon_path_str):
                    icon_path = Path(icon_path_str)
                else:
                    icon_path = root_dir / icon_path_str
                    
                if not icon_path.exists():
                    missing_icons.append(f"[{json_file.name}] {name}: Missing file '{icon_path_str}'")
                    
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")

    print("\n--- Missing Icons Report ---")
    if missing_icons:
        for msg in missing_icons:
            print(msg)
    else:
        print("All icons exist!")

if __name__ == "__main__":
    check_icons()
