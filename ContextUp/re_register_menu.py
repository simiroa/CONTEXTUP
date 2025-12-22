import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from core.registry import RegistryManager
from core.config import MenuConfig

def main():
    print("Loading config...")
    config = MenuConfig()
    
    print("Initializing RegistryManager...")
    reg_mgr = RegistryManager(config)
    
    print("Unregistering old items...")
    reg_mgr.unregister_all()
    
    print("Registering new items (with Position='Top')...")
    reg_mgr.register_all()
    
    print("Done! Check your context menu.")

if __name__ == "__main__":
    main()
