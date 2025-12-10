import sys
import os
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

print("Verifying Hotkey Dependencies...")

try:
    import pynput
    print(f"pynput imported.")
    import pystray
    print(f"pystray imported.")
    
    from scripts.tray_agent import ContextUpTray
    print("ContextUpTray class imported successfully.")
    
    print("VERIFICATION SUCCESS")
except ImportError as e:
    print(f"VERIFICATION FAILED: {e}")
except Exception as e:
    print(f"VERIFICATION FAILED (Other): {e}")
