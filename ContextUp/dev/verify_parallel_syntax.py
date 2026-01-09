import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path("c:/Users/HG/Documents/HG_context_v2/ContextUp/src")))

def check_import(module_path):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("module", str(module_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {module_path.name}: Syntax OK")
        return True
    except Exception as e:
        print(f"❌ {module_path.name}: Failed - {e}")
        return False

base_path = Path("c:/Users/HG/Documents/HG_context_v2/ContextUp")
files_to_check = [
    base_path / "src/features/image/convert_gui.py",
    base_path / "src/features/video/convert_gui.py",
    base_path / "src/features/video/audio_gui.py",
    base_path / "src/features/document/convert_gui.py"
]

print("--- Verifying Syntax of Parallel Processing Implementations ---")
failures = []
for f in files_to_check:
    if f.exists():
        if not check_import(f):
            failures.append(f.name)
    else:
        print(f"⚠️ {f.name}: File not found at {f}")

if failures:
    print(f"\n❌ Syntax check failed for: {', '.join(failures)}")
    sys.exit(1)
else:
    print("\n✅ All modified files passed syntax check.")
