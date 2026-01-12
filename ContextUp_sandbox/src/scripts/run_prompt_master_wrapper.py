import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent # scripts
src_dir = current_dir.parent # src
sys.path.append(str(src_dir))

from features.prompt_master.main import PromptMasterApp

if __name__ == "__main__":
    app = PromptMasterApp()
    app.mainloop()
