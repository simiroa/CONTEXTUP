
import sys
import os
from pathlib import Path

# Setup paths
sys.path.append(str(Path.cwd() / "src"))

from core.config import MenuConfig
from manager.mgr_core.packages import PackageManager

def test_registry_filtering():
    print("--- Simulating Registry Registration Checks ---")
    try:
        # 1. Config
        config = MenuConfig()
        print(f"Loaded {len(config.items)} items from config.")

        # 2. Package Manager
        root_dir = Path.cwd()
        pm = PackageManager(root_dir)
        
        print("\nChecking Installed Packages...")
        installed = pm.get_installed_packages()
        print(f"Found {len(installed)} packages.")
        if len(installed) < 5:
            print(f"WARNING: Very few packages found: {installed}")
        else:
            print(f"Sample: {list(installed.keys())[:5]}")

        # 3. Simulate Check
        enabled_count = 0
        valid_dep_count = 0
        
        print("\nChecking Item Dependencies:")
        for item in config.items:
            if not item.get('enabled', True):
                continue
            enabled_count += 1
            
            valid, missing = pm.check_dependencies(item, installed)
            if valid:
                valid_dep_count += 1
            else:
                print(f" [SKIP] {item.get('id')}: Missing {missing}")

        print("\n--- Summary ---")
        print(f"Total Items: {len(config.items)}")
        print(f"Enabled: {enabled_count}")
        print(f"Passing Dependency Check: {valid_dep_count}")
        
        if valid_dep_count == 0:
            print("CRITICAL: ALL ITEMS FAILED DEPENDENCY CHECK. This causes empty menu.")
        
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registry_filtering()
