"""
Master Setup Script
Downloads all necessary binaries and models.
"""
import sys
import subprocess
from pathlib import Path

def run_script(script_name):
    script_path = Path(__file__).parent / "src" / "scripts" / script_name
    if not script_path.exists():
        print(f"Script not found: {script_name}")
        return
        
    print(f"Running {script_name}...")
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"Finished {script_name}.\n")
    except Exception as e:
        print(f"Failed to run {script_name}: {e}\n")

def main():
    print("=== ContextUp Setup ===\n")
    
    # 1. RIFE Binary
    run_script("download_rife.py")
    
    # 2. Add other setup scripts here if needed
    # e.g. setup_nllb.py (if we were using offline translator, but we switched to online)
    
    print("=== Setup Complete ===")
    print("You can now run 'ContextUpManager.bat' to register the menu.")

if __name__ == "__main__":
    main()
