import json
from pathlib import Path
from collections import defaultdict

# Path to category files
cat_dir = Path("config/menu_categories")

# Track statistics
stats = {}

for cat_file in cat_dir.glob("*.json"):
    with open(cat_file, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    # Find duplicates by ID
    seen_ids = defaultdict(int)
    for item in items:
        item_id = item.get('id', 'NO_ID')
        seen_ids[item_id] += 1
    
    duplicates = {k: v for k, v in seen_ids.items() if v > 1}
    
    if duplicates:
        print(f"\n{cat_file.name}:")
        print(f"  Total items: {len(items)}")
        print(f"  Duplicates: {duplicates}")
        
        # Remove duplicates, keep first occurrence
        seen = set()
        unique_items = []
        for item in items:
            item_id = item.get('id', f"NO_ID_{len(unique_items)}")
            if item_id not in seen:
                seen.add(item_id)
                unique_items.append(item)
        
        # Save cleaned file
        with open(cat_file, 'w', encoding='utf-8') as f:
            json.dump(unique_items, f, indent=4)
        
        print(f"  Cleaned: {len(items)} -> {len(unique_items)} items")
        stats[cat_file.name] = {'before': len(items), 'after': len(unique_items)}
    else:
        stats[cat_file.name] = {'before': len(items), 'after': len(items), 'status': 'OK'}

print("\n\nSummary:")
for filename, stat in stats.items():
    status = stat.get('status', f"Cleaned: {stat['before']} -> {stat['after']}")
    print(f"  {filename}: {status}")
