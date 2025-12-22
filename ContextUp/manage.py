import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config import MenuConfig
from core.registry import RegistryManager
from core.logger import setup_logger

logger = setup_logger("manage")

def main():
    parser = argparse.ArgumentParser(description="Manage Context Menu")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    subparsers.add_parser("register", help="Register context menu in Registry")
    subparsers.add_parser("unregister", help="Remove context menu from Registry")
    subparsers.add_parser("test", help="Run tests")
    
    args = parser.parse_args()
    
    config = MenuConfig()
    manager = RegistryManager(config)
    
    if args.command == "register":
        print("Registering context menu...")
        # Always clean up first to avoid stale keys
        try:
            manager.unregister_all()
        except Exception as e:
            logger.warning(f"Unregister failed during cleanup: {e}")
            
        manager.register_all()
        print("Done.")
        
    elif args.command == "unregister":
        print("Unregistering context menu...")
        manager.unregister_all()
        print("Done.")
        
    elif args.command == "test":
        print("Running tests...")
        import pytest
        sys.exit(pytest.main(["tests"]))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
