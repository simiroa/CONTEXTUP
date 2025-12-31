import sys
import os
from pathlib import Path
import customtkinter as ctk

def main():
    # Setup Paths
    current_file = Path(__file__).resolve()
    # If executed as src/manager/main.py, parent is src/manager, parent.parent is src
    src_dir = current_file.parent.parent 
    root_dir = src_dir.parent
    
    # Ensure src is in sys.path for absolute imports of other packages (core, features, etc.)
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    # Remove own directory from path to avoid shadowing the package name 'manager'
    if str(current_file.parent) in sys.path:
        sys.path.remove(str(current_file.parent))
        
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
    from core.logger import setup_logger
    setup_logger(file_prefix="app")
    
    # Use absolute import from 'src' root, which is now in sys.path
    from manager.ui.app import ContextUpManager
    
    app = ContextUpManager(root_dir)
    app.mainloop()

if __name__ == "__main__":
    main()
