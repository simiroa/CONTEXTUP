import sys
import json
import pyperclip
from pathlib import Path
from tkinter import messagebox

# Path to config
CONFIG_PATH = Path(__file__).parent.parent.parent / "userdata" / "copy_my_info.json"

def copy_content(label):
    try:
        if not CONFIG_PATH.exists():
            messagebox.showerror("Error", "Config file not found.")
            return

        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items = data.get('items', [])
            
        content = None
        for item in items:
            if item.get('label') == label:
                content = item.get('content')
                break
        
        if content is not None:
            pyperclip.copy(content)
            # Optional: Toast notification (using tiny script or just silence)
            # Using ctypes for a simple beep or just fail silently if OK.
            print(f"Copied: {content}")
        else:
            messagebox.showwarning("Warning", f"Label '{label}' not found.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy content: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        copy_content(sys.argv[1])
    else:
        print("Usage: sys_copy_content.py <Label>")
