import sys
import os
import json
import winreg
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "ContextUp" / "src"
sys.path.append(str(src_dir))

def check_copy_my_info_config():
    print("Checking tools.json...")
    config_path = current_dir / "ContextUp" / "config" / "categories" / "tools.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item['id'] == 'copy_my_info':
                if item.get('scope') == 'tray_only':
                    print("PASS: copy_my_info scope is 'tray_only'")
                    return True
                else:
                    print(f"FAIL: copy_my_info scope is {item.get('scope')}")
                    return False
    print("FAIL: copy_my_info not found in tools.json")
    return False

def check_module_import():
    print("\nChecking CopyMyInfoModule import...")
    try:
        from tray.modules.copy_my_info import CopyMyInfoModule
        print("PASS: Successfully imported CopyMyInfoModule")
        return True
    except Exception as e:
        print(f"FAIL: Failed to import CopyMyInfoModule: {e}")
        return False

def check_registry_key():
    print("\nChecking Registry for ContextUp.CopyInfoMenu...")
    try:
        key_path = "Software\\Classes\\ContextUp.CopyInfoMenu"
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        print("WARNING: ContextUp.CopyInfoMenu key still exists (Wait for Tray Reload or run unregister)")
        return False
    except FileNotFoundError:
        print("PASS: ContextUp.CopyInfoMenu key is gone (or never existed)")
        return True
    except Exception as e:
        print(f"Registry check error: {e}")
        return False

if __name__ == "__main__":
    p1 = check_copy_my_info_config()
    p2 = check_module_import()
    p3 = check_registry_key()
    
    if p1 and p2:
        print("\nAll code checks passed. Setup looks correct.")
        print("Please RELOAD the Tray Agent to apply changes.")
    else:
        print("\nSome checks failed.")
