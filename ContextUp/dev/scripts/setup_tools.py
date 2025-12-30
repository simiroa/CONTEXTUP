import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

# Configuration
# Script is in: ContextUp/dev/scripts
# Tools dir:    ContextUp/tools (FFmpeg, ExifTool, etc.)
# AI Bin dir:   ContextUp/resources/bin (AI models/binaries)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # ContextUp
TOOLS_DIR = ROOT_DIR / "tools"
AI_BIN_DIR = ROOT_DIR / "resources" / "bin"
TEMP_DIR = TOOLS_DIR / "temp"

FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
REALESRGAN_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"

def download_file(url, dest):
    print(f"?ㅼ슫濡쒕뱶 以? {url}...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print("?ㅼ슫濡쒕뱶 ?꾨즺.")
        return True
    except Exception as e:
        print(f"?ㅼ슫濡쒕뱶 ?ㅽ뙣: {e}")
        return False

def extract_zip(zip_path, extract_to):
    print(f"?뺤텞 ?댁젣 以? {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("?뺤텞 ?댁젣 ?꾨즺.")
        return True
    except Exception as e:
        print(f"?뺤텞 ?댁젣 ?ㅽ뙣: {e}")
        return False

def setup_ffmpeg():
    # Install to tools/ffmpeg (external_tools.py looks for tools/ffmpeg/bin/ffmpeg.exe)
    target_dir = TOOLS_DIR / "ffmpeg"
    if (target_dir / "bin" / "ffmpeg.exe").exists():
        print("[OK] FFmpeg媛 ?대? 議댁옱?⑸땲??")
        return True

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_DIR / "ffmpeg.zip"
    
    if download_file(FFMPEG_URL, zip_path):
        if extract_zip(zip_path, TEMP_DIR):
            # Find extracted folder
            extracted_dirs = [d for d in TEMP_DIR.iterdir() if d.is_dir() and "ffmpeg" in d.name.lower() and d.name != "ffmpeg"]
            if extracted_dirs:
                src_dir = extracted_dirs[0]
                if target_dir.exists(): 
                    shutil.rmtree(target_dir)
                shutil.move(str(src_dir), str(target_dir))
                print(f"[OK] FFmpeg ?ㅼ튂 ?꾨즺: {target_dir}")
                
    if zip_path.exists(): 
        os.remove(zip_path)
    return (target_dir / "bin" / "ffmpeg.exe").exists()



def setup_realesrgan():
    # Install to resources/bin/realesrgan (AI binary)
    target_dir = AI_BIN_DIR / "realesrgan"
    if (target_dir / "realesrgan-ncnn-vulkan.exe").exists():
        print("[OK] Real-ESRGAN???대? 議댁옱?⑸땲??")
        return True

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_DIR / "realesrgan.zip"
    
    if download_file(REALESRGAN_URL, zip_path):
        if extract_zip(zip_path, TEMP_DIR):
            # Robust search for executable
            found_exe = None
            for root, _, files in os.walk(TEMP_DIR):
                if "realesrgan-ncnn-vulkan.exe" in files:
                    found_exe = Path(root)
                    break
            
            if found_exe:
                if target_dir.exists(): 
                    shutil.rmtree(target_dir)
                # If the found dir is just the bin itself inside a folder, copy logic might vary
                # But typically we want the folder containing the exe.
                # If we just move found_exe (dir) to target_dir:
                # e.g. temp/realesrgan-windows/realesrgan.exe -> resources/bin/realesrgan/realesrgan.exe
                
                # Check if target_dir parent exists
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the *content* of the folder or the folder itself? 
                # The goal is AI_BIN_DIR / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
                shutil.move(str(found_exe), str(target_dir))
                print(f"[OK] Real-ESRGAN ?ㅼ튂 ?꾨즺: {target_dir}")
            else:
                 print("[FAIL] 異붿텧???뚯씪?먯꽌 Real-ESRGAN ?ㅽ뻾 ?뚯씪??李얠쓣 ???놁뒿?덈떎.")

    if zip_path.exists(): 
        os.remove(zip_path)
    return (target_dir / "realesrgan-ncnn-vulkan.exe").exists()


def cleanup_temp():
    if TEMP_DIR.exists():
        try:
            shutil.rmtree(TEMP_DIR)
        except: 
            pass

def parse_requested_tools(argv):
    requested = set()
    for arg in argv:
        if arg == "--ffmpeg":
            requested.add("ffmpeg")
        elif arg == "--realesrgan":
            requested.add("realesrgan")
        elif arg == "--rife":
            requested.add("rife")
        elif arg in ("--all", "-a"):
            requested = {"ffmpeg", "realesrgan"}
            break
    if not requested:
        requested = {"ffmpeg", "realesrgan"}
    return requested

def main():
    print("=== ?몃? ?꾧뎄 ?ㅼ젙 ===\n")

    requested = parse_requested_tools(sys.argv[1:])
    results = {}
    if "ffmpeg" in requested:
        results["FFmpeg"] = setup_ffmpeg()
    if "realesrgan" in requested:
        results["Real-ESRGAN"] = setup_realesrgan()
    
    cleanup_temp()
    
    print("\n=== ?몃? ?꾧뎄 ?ㅼ튂 ?붿빟 ===")
    for tool, success in results.items():
        status = "OK" if success else "FAIL"
        print(f"  {tool}: {status}")
    
    all_ok = all(results.values())
    if all_ok:
        print("\n紐⑤뱺 ?꾧뎄媛 ?깃났?곸쑝濡??ㅼ튂?섏뿀?듬땲??")
    else:
        print("\n?쇰? ?꾧뎄 ?ㅼ튂???ㅽ뙣?덉뒿?덈떎. ??異쒕젰???뺤씤?섏꽭??")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

