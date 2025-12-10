import sys
import os
import shutil
import logging
from pathlib import Path

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("uninstall")

ROOT_DIR = Path(__file__).parent.parent.parent
TOOLS_DIR = ROOT_DIR / "tools"
CLEANUP_SCRIPT = TOOLS_DIR / "cleanup_registry.py"

def run_registry_cleanup():
    print("--- Removing Registry Entries ---")
    if CLEANUP_SCRIPT.exists():
        try:
            # We can import it or run it. Running is safer to avoid path issues.
            import subprocess
            subprocess.run([sys.executable, str(CLEANUP_SCRIPT)], check=True)
        except Exception as e:
            logger.error(f"Failed to run registry cleanup: {e}")
    else:
        logger.warning(f"Registry cleanup script not found at {CLEANUP_SCRIPT}")

def remove_temp_files():
    print("--- Removing Temporary Files ---")
    patterns = ["*.log", "*.pyc", "__pycache__"]
    
    count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        # Remove __pycache__ dirs
        if "__pycache__" in dirs:
            p = Path(root) / "__pycache__"
            try:
                shutil.rmtree(p)
                dirs.remove("__pycache__")
                count += 1
            except Exception as e:
                logger.warning(f"Failed to remove {p}: {e}")
                
        # Remove log files in root/logs
        # (Implementation optional based on strictness, user might want logs?)
        # Let's clean root level logs as requested previously
    
    print(f"Cleaned {count} cache directories.")

def main():
    print("=== ContextUp Uninstaller ===")
    print("This will remove:")
    print("1. Context Menu Registry Entries")
    print("2. Temporary Cache Files")
    print("3. (In next step) Virtual Environments")
    
    confirm = input("Are you sure? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Uninstall cancelled.")
        sys.exit(1) # Signal BAT to stop
        
    run_registry_cleanup()
    remove_temp_files()
    
    print("\nRegistry and Cache cleanup complete.")
    print("Proceeding to remove environments...")

if __name__ == "__main__":
    main()
