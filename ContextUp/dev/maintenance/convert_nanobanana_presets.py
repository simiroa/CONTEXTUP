import json
import os
import re
from pathlib import Path

# Load the list.json file
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
list_file = project_root / "config" / "prompt_master" / "presets" / "nanobanana" / "list.json"
output_dir = list_file.parent

with open(list_file, 'r', encoding='utf-8') as f:
    presets = json.load(f)

def sanitize_filename(name):
    """Convert preset name to safe filename"""
    # Remove special characters and replace spaces with underscores
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name.lower()

def convert_prompt_variables(raw_prompt):
    """Convert [variable] format to {variable} format"""
    return re.sub(r'\[(\w+)\]', r'{\1}', raw_prompt)

def convert_preset(preset):
    """Convert external format to our service format"""
    # Extract variables and convert to inputs
    inputs = []
    if preset.get("variables"):
        for var_id, var_data in preset["variables"].items():
            inputs.append({
                "id": var_id,
                "label": var_data.get("label", var_id),
                "default": var_data.get("default", "")
            })
    
    # Create description from tags
    tags = preset.get("default_tags", [])
    description = f"Tags: {', '.join(tags)}" if tags else ""
    
    # Convert prompt format
    template = convert_prompt_variables(preset.get("raw_prompt", ""))
    
    # Build new preset object
    new_preset = {
        "engine": preset.get("engine", "nanobanana"),
        "name": preset.get("preset_name", "Untitled"),
        "description": description,
        "inputs": inputs,
        "options": [],  # No options in original format
        "template": template
    }
    
    return new_preset

# Convert and save each preset
count = 0
for preset in presets:
    preset_name = preset.get("preset_name", f"preset_{count}")
    filename = sanitize_filename(preset_name) + ".json"
    output_path = output_dir / filename
    
    # Convert to our format
    converted = convert_preset(preset)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted, f, indent=4, ensure_ascii=False)
    
    count += 1
    print(f"Created: {filename}")

print(f"\n✅ Successfully converted {count} presets!")
