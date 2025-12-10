"""
Extract missing items from backup and restore to category files.
"""
import json
from pathlib import Path
from collections import defaultdict

# Load backup
backup_path = Path("config/menu_config_backup.json")
backup_data = json.load(open(backup_path, encoding='utf-8'))

# Group by category
by_category = defaultdict(list)
for item in backup_data:
    category = item.get('category', 'Uncategorized')
    by_category[category].append(item)

print("=== Backup Analysis ===")
for cat, items in sorted(by_category.items()):
    print(f"{cat}: {len(items)} items")
    for item in items[:3]:  # Show first 3
        print(f"  - {item.get('name')}")
    if len(items) > 3:
        print(f"  ... and {len(items) - 3} more")

# Focus on missing categories
print("\n=== Missing Categories ===")
missing = ['Video', 'Audio', 'AI']
for cat in missing:
    items = by_category.get(cat, [])
    print(f"\n{cat}: {len(items)} items")
    for item in items:
        print(f"  - {item.get('name'):40} [id: {item.get('id')}]")
