"""
Standardize all category JSON files with consistent fields.
"""
import json
from pathlib import Path

cat_dir = Path("config/menu_categories")

# Standard defaults for missing required fields
DEFAULTS = {
    "enabled": True,
    "submenu": "ContextUp",
    "environment": "system",
    "show_in_tray": False,  # Optional, default false
}

# Required fields (must be present)
REQUIRED_FIELDS = [
    "category", "id", "name", "icon", "types", "scope", 
    "status", "enabled", "submenu", "environment"
]

# Optional fields (can be present)
OPTIONAL_FIELDS = ["show_in_tray", "dependencies", "command", "hotkey"]

# Field order for consistent formatting
FIELD_ORDER = [
    "category", "id", "name", "icon", "types", "scope", "status",
    "enabled", "submenu", "show_in_tray", "environment", 
    "dependencies", "command", "hotkey"
]

changes_made = []

for json_file in sorted(cat_dir.glob("*.json")):
    print(f"\nProcessing {json_file.name}...")
    
    data = json.load(open(json_file, encoding='utf-8'))
    if not data:
        print(f"  Skipping empty file")
        continue
    
    file_changes = []
    
    for item in data:
        item_changes = []
        
        # Add missing required fields
        for field in REQUIRED_FIELDS:
            if field not in item:
                if field in DEFAULTS:
                    item[field] = DEFAULTS[field]
                    item_changes.append(f"+{field}")
        
        # Reorder fields for consistency
        ordered_item = {}
        for field in FIELD_ORDER:
            if field in item:
                ordered_item[field] = item[field]
        
        # Add any remaining fields not in FIELD_ORDER
        for key, value in item.items():
            if key not in ordered_item:
                ordered_item[key] = value
        
        # Replace item with ordered version
        item.clear()
        item.update(ordered_item)
        
        if item_changes:
            file_changes.append(f"  {item['id']}: {', '.join(item_changes)}")
    
    if file_changes:
        # Write back standardized data
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        changes_made.append(f"\n{json_file.name}:")
        changes_made.extend(file_changes)
        print(f"  ✓ Standardized {len(file_changes)} items")
    else:
        print(f"  ✓ Already standardized")

if changes_made:
    print("\n" + "=" * 60)
    print("CHANGES SUMMARY:")
    print("=" * 60)
    for line in changes_made:
        print(line)
else:
    print("\n✓ All files already standardized!")

print("\n✓ Standardization complete!")
