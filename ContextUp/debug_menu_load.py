
import sys
from pathlib import Path
import json

# Setup paths
sys.path.append(str(Path.cwd() / "src"))

from core.config import MenuConfig
from core.registry import RegistryManager

def test_load():
    print("Testing MenuConfig...")
    try:
        config = MenuConfig()
        print(f"Config Dir: {config.config_dir} (Exists: {config.config_dir.exists()})")
        print(f"Items loaded: {len(config.items)}")
        
        for item in config.items[:3]:
            print(f" - {item.get('id')} ({item.get('name')})")
            
        if not config.items:
            print("ERROR: No items loaded!")
            
        # Test Registry Map logic
        print("\nTesting Registry Logic...")
        mgr = RegistryManager(config)
        # Mimic register_all logic partially
        registry_map = {}
        for item in config.items:
            if not item.get('enabled', True): continue
            
            submenu = item.get('submenu', 'ContextUp')
            if not submenu: submenu = 'ContextUp'
            
            # Just count
            if submenu not in registry_map: registry_map[submenu] = 0
            registry_map[submenu] += 1
            
        print("Registry Map Counts:")
        for k,v in registry_map.items():
            print(f" - {k}: {v}")
            
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_load()
