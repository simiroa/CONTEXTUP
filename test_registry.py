import sys
from pathlib import Path
import winreg

src_dir = Path(r'ContextUp\src')
sys.path.insert(0, str(src_dir))

from core.config import MenuConfig
from core.registry import RegistryManager

cfg = MenuConfig()
reg = RegistryManager(cfg)

print(f"Total items: {len(cfg.items)}")

# Mock winreg.CreateKey to see what's being done
original_create_key = winreg.CreateKey
def mocked_create_key(root, path):
    print(f"DEBUG: CreateKey called for {path}")
    return original_create_key(root, path)

# winreg.CreateKey = mocked_create_key # Can't mock built-in like this easily sometimes, but let's try or just use proxy

print("Attempting registration...")
try:
    reg.register_all()
    print("Registration call finished.")
except Exception as e:
    print(f"Registration failed with error: {e}")
    import traceback
    traceback.print_exc()
