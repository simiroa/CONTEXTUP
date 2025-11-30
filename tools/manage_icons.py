import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

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
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config" / "menu_config.json"
    icons_dir = root_dir / "assets" / "icons"
    
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    used_icons = set()
    
    # 1. Identify used icons
    for item in config:
        icon_rel_path = item.get('icon')
        if icon_rel_path:
            # Normalize path separators
            icon_rel_path = icon_rel_path.replace('\\', '/')
            # Assuming icon_rel_path starts with "assets/icons/"
            if icon_rel_path.startswith("assets/icons/"):
                name = icon_rel_path.split("/")[-1]
                used_icons.add(name)
                
                # Check if exists
                full_path = root_dir / icon_rel_path
                if not full_path.exists():
                    print(f"Missing icon: {name}")
                    generate_dummy_icon(full_path, color=(50, 150, 250)) # Blue-ish dummy
            else:
                print(f"Warning: Icon path not in assets/icons: {icon_rel_path}")

    # 2. Identify unused icons
    if icons_dir.exists():
        for file in icons_dir.glob("*.ico"):
            if file.name not in used_icons:
                print(f"Deleting unused icon: {file.name}")
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"Failed to delete {file.name}: {e}")

if __name__ == "__main__":
    main()
