"""
Find menu items defined in menu.py but missing from menu_categories.
Also find scripts that might be missing menu entries.
"""
import json
from pathlib import Path
import sys

# Ensure output is UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Load menu.py handlers
menu_py = Path("src/core/menu.py")
handlers_in_code = set()

with open(menu_py, 'r', encoding='utf-8') as f:
    content = f.read()
    # Find all entries like "item_id": something
    import re
    pattern = r'"([a-z_0-9]+)":\s*(?:_lazy|lambda|")'
    matches = re.findall(pattern, content)
    handlers_in_code = set(matches)

# Load all IDs from menu_categories
cat_dir = Path("config/menu_categories")
ids_in_categories = set()

for json_file in cat_dir.glob("*.json"):
    try:
        data = json.load(open(json_file, encoding='utf-8'))
        for item in data:
            ids_in_categories.add(item.get('id'))
    except Exception as e:
        print(f"Error loading {json_file.name}: {e}")

print()
print("=" * 70)
print("MENU ITEMS IN menu.py BUT MISSING FROM CATEGORIES")
print("=" * 70)
missing_from_categories = sorted(handlers_in_code - ids_in_categories)
if missing_from_categories:
    for item_id in missing_from_categories:
        print(f"  - {item_id}")
    print(f"\nTotal: {len(missing_from_categories)} items")
else:
    print("  (None - all items are in categories!)")

print()
print("=" * 70)
print("IDS IN CATEGORIES")
print("=" * 70)
print(f"Total: {len(ids_in_categories)} items")

print()
print("=" * 70) 
print("IDS IN menu.py")
print("=" * 70)
print(f"Total: {len(handlers_in_code)} items")
