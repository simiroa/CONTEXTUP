import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent / "src"))

from features.finder.ui import FinderApp

if __name__ == "__main__":
    app = FinderApp()
    
    # Save a screenshot before mainloop
    app.update()
    app.after(1000, lambda: app.destroy()) # Close after 1s
    
    # Capture screenshot
    from PIL import ImageGrab
    import time
    
    time.sleep(0.5)
    screenshot_path = "finder_gui_check.png"
    # Note: On some systems ImageGrab might need coordinates or might fail in headless.
    # But since I'm in an agent environment with GUI support, I'll try.
    # Actually, I should use the browser tool if it's a web app, but this is a desktop app.
    # I'll just run it and see if it crashes.
    
    print("Launching Finder GUI...")
    app.mainloop()
    print("GUI closed.")
