import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

import argparse

def generate_dummy_icon(path, color=(100, 100, 100)):
    """Generates a simple dummy .ico file."""
    img = Image.new('RGB', (256, 256), color)
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 236, 236], outline=(255, 255, 255), width=10)
    
    # Save as ICO
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='ICO', sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])
    print(f"Generated dummy icon: {path}")

def main():
    parser = argparse.ArgumentParser(description="Manage ContextUp Icons")
    parser.add_argument("--delete", action="store_true", help="Delete unused icons from assets/icons")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[2] # ContextUp
    config_dir = root_dir / "config" / "menu" / "categories"
    legacy_config = root_dir / "config" / "menu_config.json"
    icons_dir = root_dir / "assets" / "icons"
    
    config_files = []
    if config_dir.exists():
        config_files.extend(list(config_dir.glob("*.json")))
    if legacy_config.exists():
        config_files.append(legacy_config)

    if not config_files:
        print(f"No config files found in {config_dir} or {legacy_config}")
        return

    used_icons = set()
    
    # 1. Identify used icons from all config files
    for config_path in config_files:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                items = []
                if isinstance(config, list):
                    items = config
                elif isinstance(config, dict):
                    if "features" in config and isinstance(config["features"], list):
                        items = config["features"]
                    else:
                        items = [config] # Single object or other structure
                
                for item in items:
                    icon_rel_path = item.get('icon')
                    if icon_rel_path:
                        icon_rel_path = icon_rel_path.replace('\\', '/')
                        if "assets/icons/" in icon_rel_path:
                            name = icon_rel_path.split("/")[-1]
                            used_icons.add(name)
                            
                            full_path = root_dir / icon_rel_path
                            if not full_path.exists():
                                print(f"Missing icon: {name} (referenced in {config_path.name})")
                                # generate_dummy_icon(full_path, color=(50, 150, 250))
        except Exception as e:
            print(f"Error parsing {config_path}: {e}")

    # 2. Identify unused icons
    unused_count = 0
    if icons_dir.exists():
        for file in icons_dir.glob("*.ico"):
            if file.name not in used_icons:
                unused_count += 1
                if args.delete:
                    print(f"Deleting unused icon: {file.name}")
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f"Failed to delete {file.name}: {e}")
                else:
                    print(f"Unused icon (not deleted): {file.name}")

    print(f"\nSummary: {len(used_icons)} icons in use, {unused_count} unused icons found.")
    if unused_count > 0 and not args.delete:
        print("Tip: Run with --delete to remove unused icons.")

if __name__ == "__main__":
    main()
