import webbrowser
import sys
import time
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from manager.helpers.comfyui_client import ComfyUIManager

def main():
    print("Checking ComfyUI Server status...")
    client = ComfyUIManager()
    
    if not client.is_running():
        print("Server not running. Starting...")
        if client.start():
            print("Server started.")
            # Give it a moment to initialize
            time.sleep(2)
        else:
            print("Failed to start server.")
            # Try opening anyway, maybe external instance
            
    url = "http://127.0.0.1:8190"
    print(f"Opening {url}...")
    webbrowser.open(url)

if __name__ == "__main__":
    main()
