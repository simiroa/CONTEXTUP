import sys
from pathlib import Path
import logging

# Add src to path so we can import modules
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from core.config import MenuConfig
from core.registry import RegistryManager

def apply_changes():
    print("Applying registry changes...")
    try:
        config = MenuConfig()
        manager = RegistryManager(config)
        
        print("Unregistering old keys...")
        manager.unregister_all()
        
        print("Registering new keys...")
        manager.register_all()
        
        print("Success! Registry updated.")
    except Exception as e: # Catching general exception to report error
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_changes()
