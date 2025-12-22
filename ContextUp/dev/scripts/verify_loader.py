import sys
from pathlib import Path

# Add src to path
# Script: ContextUp/dev/scripts/verify_loader.py
# Root: HG_context_v2
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "ContextUp" / "src"
sys.path.append(str(src_path))

from core.config import MenuConfig

def verify_loader():
    print("Testing MenuConfig loader...")
    try:
        config = MenuConfig()
        print(f"Loaded {len(config.items)} items.")
        
        # Verify specific items exist
        clean_empty = config.get_item_by_id("dir_clean_empty")
        clean_empty = config.get_item_by_id("clean_empty_folders")
        manager = config.get_item_by_id("manager")
        
        if not clean_empty:
            print("FAIL: clean_empty_folders not found.")
            return False
            
        expected_ids = ["image_convert", "clean_empty_folders", "manager"]
        print(f"clean_empty_folders icon: {clean_empty.get('icon')}")
        if "icon_sys_clean_empty_dir.ico" not in clean_empty.get('icon', ''):
             print("FAIL: clean_empty_folders has wrong icon.")
             return False

        if not manager:
            print("FAIL: manager not found.")
            return False
            
        print(f"manager icon: {manager.get('icon')}")
        if "icon_sys_manager_gui.ico" not in manager.get('icon', ''):
             print("FAIL: manager has wrong icon.")
             return False
             
        print("PASS: Loader verification successful.")
        return True
        
    except Exception as e:
        print(f"Loader failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_loader():
        sys.exit(0)
    else:
        sys.exit(1)
