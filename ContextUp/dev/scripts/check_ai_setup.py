import sys
import os
import importlib
from pathlib import Path

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_dir = project_root / "ContextUp" / "src"
sys.path.append(str(src_dir))

def check_import(package_name, display_name=None):
    if not display_name:
        display_name = package_name
    try:
        importlib.import_module(package_name)
        print(f"✅ {display_name:<25} : Installed")
        return True
    except ImportError:
        print(f"❌ {display_name:<25} : NOT FOUND")
        return False
    except Exception as e:
        print(f"⚠️ {display_name:<25} : Error - {e}")
        return False

def check_binary(path, name):
    if path.exists():
        print(f"✅ {name:<25} : Found at {path}")
        return True
    else:
        print(f"❌ {name:<25} : MISSING at {path}")
        return False

print("=== ContextUp AI & Dependency Verification ===\n")

# 1. Python Libraries
print("[ Python Libraries ]")
checks = [
    ("torch", "PyTorch"),
    ("rembg", "Rembg (BG Removal)"),
    ("google.genai", "Google GenAI"),
    ("diffusers", "Diffusers (Marigold)"),
    ("demucs", "Demucs (Audio Split)"),
    ("faster_whisper", "Faster Whisper"),
    ("rapidocr_onnxruntime", "RapidOCR"),
    ("onnxruntime", "ONNX Runtime"),
    ("yt_dlp", "YT-DLP"),
    ("deep_translator", "Deep Translator"),
    ("ctranslate2", "CTranslate2"),
    ("cv2", "OpenCV")
]

success_count = 0
for pkg, name in checks:
    if check_import(pkg, name):
        success_count += 1

# 2. Binaries
print("\n[ Binaries & Resources ]")
resources_dir = project_root / "ContextUp" / "resources"
rife_bin = resources_dir / "bin" / "rife" / "rife-ncnn-vulkan.exe"

bin_checks = [
    (rife_bin, "RIFE Binary"),
]

for path, name in bin_checks:
    if check_binary(path, name):
        success_count += 1

total_checks = len(checks) + len(bin_checks)
print(f"\nSummary: {success_count}/{total_checks} Checks Passed.")

if success_count == total_checks:
    print("\n🎉 ALL SYSTEMS GO! AI features are correctly connected.")
    sys.exit(0)
else:
    print("\n⚠️ SOME FEATURES MAY FAIL. Check logs above.")
    sys.exit(1)
