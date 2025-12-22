import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from features.comfyui.icon_gen_gui import IconGenGUI

if __name__ == "__main__":
    print("Launching AI Icon Generator GUI for Verification...")
    app = IconGenGUI()
    app.mainloop()
