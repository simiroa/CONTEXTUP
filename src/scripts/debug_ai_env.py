import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.ai_runner import run_ai_script

success, output = run_ai_script("install_rife.py")
print(f"Success: {success}")
print("Output:")
print(output)
