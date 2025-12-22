import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "ContextUp" / "src"
sys.path.append(str(src_dir))

from core.registry import RegistryManager
from core.config import MenuConfig
from core.logger import setup_logger

if __name__ == "__main__":
    logger = setup_logger("apply_changes")
    print("Loading configuration...")
    config = MenuConfig()
    
    print("Initializing Registry Manager...")
    reg_mgr = RegistryManager(config)
    
    # 1. Unregister everything first to be clean (especially the old Copy My Info key)
    print("Unregistering old keys...")
    reg_mgr.unregister_all()
    
    # 2. Register everything again (Copy My Info will be skipped due to new scope)
    print("Registering new configuration...")
    reg_mgr.register_all()
    
    print("Done! Context Menu should be updated.")
