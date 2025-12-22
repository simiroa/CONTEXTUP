"""
ContextUp Setup Console
Interactive script to guide the user through installation and explain features/limitations.
"""
import sys
import os
import subprocess
from pathlib import Path
import time

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.logger import setup_logger

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("="*60)
    print("   ContextUp - Windows Context Menu Extension Setup")
    print("="*60)
    print()

def main():
    clear_screen()
    print_header()
    
    print("Welcome to ContextUp!")
    print("This tool enhances your Windows Context Menu with powerful utilities for:")
    print("  - 3D Model Conversion (CAD to OBJ, etc.)")
    print("  - AI Image Tools (Generation, Analysis, PBR Maps)")
    print("  - Video/Audio Processing")
    print("  - System Utilities (File Management)")
    print()
    
    print("-" * 60)
    print("IMPORTANT: PORTABILITY & REGISTRY")
    print("-" * 60)
    print("1. This application works as a 'Portable' app, BUT it relies on the")
    print("   Windows Registry to display the context menu items.")
    print()
    print("2. The Registry entries use ABSOLUTE PATHS to this specific folder.")
    print(f"   Current Location: {os.getcwd()}")
    print()
    print("3. If you MOVE or RENAME this folder, the context menu will STOP working.")
    print("   You must run this setup (or the Manager) again to update the paths.")
    print("-" * 60)
    print()
    
    while True:
        choice = input("Do you want to register the Context Menu now? (Y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            break
        elif choice in ['n', 'no']:
            print("\nSetup cancelled. You can run this script later or use 'ContextUpManager.bat'.")
            return
    
    print("\nRegistering Context Menu...")
    try:
        # Run manage.py register
        manage_script = src_dir.parent / "manage.py"
        python_exe = sys.executable
        
        subprocess.run([python_exe, str(manage_script), "register"], check=True)
        
        print("\n" + "="*60)
        print("SUCCESS! Context Menu has been registered.")
        print("="*60)
        print("Right-click on any file or folder to see the 'ContextUp' menu.")
        print("You can customize the menu anytime using 'ContextUpManager.bat'.")
        
    except Exception as e:
        print(f"\nERROR: Registration failed: {e}")
        print("Please check the logs or try running as Administrator.")

if __name__ == "__main__":
    main()
