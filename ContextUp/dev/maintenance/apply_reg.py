import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent / "src"
sys.path.append(str(src_dir))

from core.config import MenuConfig
from core.registry import RegistryManager

def apply_registry():
    print("Loading config...")
    config = MenuConfig()
    
    print("Initializing Registry Manager...")
    reg_mgr = RegistryManager(config)
    
    print("Unregistering old keys...")
    reg_mgr.unregister_all()
    
    print("Registering new keys...")
    reg_mgr.register_all()
    print("Done!")

if __name__ == "__main__":
    apply_registry()
