import customtkinter as ctk
import sys
import os
import time
from pathlib import Path
import threading
import pygetwindow as gw

# Setup path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from src.features.system.unwrap_folder_gui import UnwrapFolderGUI
from utils.gui_lib import setup_theme

# Mock Settings or ensure settings.json is read
# We assume settings.json is already set to Light by previous test step
# But we can force it here for testing if we want using ctk
ctk.set_appearance_mode("Light")

def check_window_visibility():
    time.sleep(2)
    titles = gw.getAllTitles()
    print("Visible Windows:")
    for t in titles:
        if t: print(f"- {t}")
    
    target_titles = ["Unwrap Folder", "폴더 풀기", "Debug Host"]
    found = [t for t in titles if any(k in t for k in target_titles)]
    print(f"\nFound Targets: {found}")
    
    # Close app
    if root:
        try:
            root.destroy()
        except: pass
    sys.exit(0)

if __name__ == "__main__":
    t = threading.Thread(target=check_window_visibility, daemon=True)
    t.start()
    
    root = ctk.CTk()
    root.title("Debug Host Root")
    root.geometry("200x200")
    
    # We want to mimic __main__ of unwrap_folder_gui.py exactly? 
    # Actually, let's just RUN unwrap_folder_gui.py as a subprocess with LIGHT settings using the same logic as the test runner.
    pass
