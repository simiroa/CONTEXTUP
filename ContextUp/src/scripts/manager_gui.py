"""
Legacy entry point redirecting to new Manager refactor.
"""
import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from manager.main import main

if __name__ == "__main__":
    main()
