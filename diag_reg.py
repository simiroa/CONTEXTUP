import sys
from pathlib import Path

src_dir = Path(r'ContextUp\src')
sys.path.insert(0, str(src_dir))

from core.config import MenuConfig
from manager.mgr_core.packages import PackageManager

cfg = MenuConfig()
pm = PackageManager(cfg.root_dir)
installed = pm.get_installed_packages()

print(f"Total items: {len(cfg.items)}")
print(f"Installed pkgs: {len(installed)}")

skipped_counts = {}

for it in cfg.items:
    valid, missing = pm.check_dependencies(it, installed)
    if not valid:
        reason = ", ".join(missing)
        skipped_counts[reason] = skipped_counts.get(reason, 0) + 1
        print(f"Skipped {it['id']}: Missing {reason}")

print("\nSummary of skipped items:")
for reason, count in skipped_counts.items():
    print(f"  - {count} items skipped due to missing: {reason}")

# Check if ANY item remains
enabled_items = [it for it in cfg.items if it.get('enabled', True)]
print(f"\nEnabled items: {len(enabled_items)}")

registered_items = []
for it in enabled_items:
    valid, _ = pm.check_dependencies(it, installed)
    if valid:
        registered_items.append(it)

print(f"Items that SHOULD be registered: {len(registered_items)}")
