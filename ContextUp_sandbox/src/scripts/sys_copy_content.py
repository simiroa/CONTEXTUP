import sys
import json
import pyperclip
from pathlib import Path
from tkinter import messagebox

# Path: ContextUp/userdata/copy_my_info.json
CONFIG_PATH = Path(__file__).parent.parent.parent / "userdata" / "copy_my_info.json"

def copy_content(label):
    try:
        content = None
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get('items', [])
                for item in items:
                    if item.get('label') == label:
                        content = item.get('content')
                        break
        
        if content is not None:
            pyperclip.copy(content)
        else:
            # Fallback or error
            messagebox.showwarning("Copy My Info", f"Item '{label}' not found.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy: {e}")

def open_manager():
    try:
        import subprocess
        script = Path(__file__).parent / "sys_info_manager.py"
        subprocess.Popen([sys.executable, str(script)], creationflags=0x08000000)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open manager: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--manage" or arg == "No items - Click Manage":
            open_manager()
        else:
            copy_content(arg)
    else:
        # Test mode or usage
        pass
