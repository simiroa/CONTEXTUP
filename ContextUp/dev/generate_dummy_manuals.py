import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

def generate_manuals():
    root_dir = Path.cwd()
    config_dir = root_dir / "config" / "categories"
    manuals_dir = root_dir / "docs" / "manuals"
    images_dir = manuals_dir / "images"
    
    manuals_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Template for Markdown
    template = """# {name}

## Introduction
{name} is a powerful feature in ContextUp that helps you streamline your workflow.
This tool is part of the **{category}** category.

## Usage
1. Right-click on the target file or folder.
2. Navigate to **{category} -> {name}**.
3. Follow the instructions in the tool's interface to complete the task.
"""

    for config_file in config_dir.glob("*.json"):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                
            for item in items:
                item_id = item.get("id")
                item_name = item.get("name")
                item_cat = item.get("category", "Tools")
                
                if not item_id: continue
                
                # 1. Create Markdown
                md_path = manuals_dir / f"{item_id}.md"
                # Only create if it doesn't exist to avoid overwriting user edits
                if not md_path.exists():
                    content = template.format(name=item_name, category=item_cat)
                    with open(md_path, "w", encoding="utf-8") as f_md:
                        f_md.write(content)
                    print(f"Created manual: {item_id}.md")
                
                # 2. Create Placeholder Image
                img_path = images_dir / f"{item_id}.png"
                if not img_path.exists():
                    # Create a colored placeholder with text
                    img = Image.new('RGB', (640, 360), color=(40, 44, 52))
                    d = ImageDraw.Draw(img)
                    d.text((320, 180), f"{item_name}\n[Screenshot Placeholder]", fill=(171, 178, 191), anchor="mm")
                    img.save(img_path)
                    print(f"Created image: {item_id}.png")
                    
        except Exception as e:
            print(f"Error processing {config_file}: {e}")

if __name__ == "__main__":
    generate_manuals()
