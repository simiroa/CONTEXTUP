"""
Restore missing items from backup to category files.
"""
import json
from pathlib import Path

backup_path = Path("config/menu_config_backup.json")
categories_dir = Path("config/menu_categories")

# Load backup
print("Loading backup...")
backup_data = json.load(open(backup_path, encoding='utf-8'))

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for item in backup_data:
    category = item.get('category', 'Uncategorized')
    by_category[category].append(item)

# Restore specific categories
restore_categories = ['Video', 'Audio', 'AI']

for category in restore_categories:
    items = by_category.get(category, [])
    if not items:
        print(f"\n{category}: No items found in backup, skipping")
        continue
    
    # Prepare filename
    filename = f"{category.lower()}.json"
    filepath = categories_dir / filename
    
    print(f"\n{category}: {len(items)} items")
    for item in items:
        print(f"  - {item.get('name')}")
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=4, ensure_ascii=False)
    
    print(f"  ✓ Saved to {filepath}")

print("\n✓ Restoration complete!")
print("\nNext step: Run config_builder.py to rebuild menu_config.json")
