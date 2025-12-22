import sys
import os
from pathlib import Path
import customtkinter as ctk

def main():
    # Setup Paths
    current_file = Path(__file__).resolve()
    src_dir = current_file.parent.parent # src/manager -> src
    root_dir = src_dir.parent
    
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
        
    # High DPI Fix (Windows)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
             ctypes.windll.user32.SetProcessDPIAware()
        except: pass
        
    # Import App
    # We import here to ensure sys.path is set first
    from manager.ui.app import ContextUpManager
    
    app = ContextUpManager(root_dir)
    app.mainloop()

if __name__ == "__main__":
    main()
