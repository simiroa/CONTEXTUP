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
RIFE_URL = "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-windows.zip"

def download_file(url, dest):
    print(f"다운로드 중: {url}...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print("다운로드 완료.")
        return True
    except Exception as e:
        print(f"다운로드 실패: {e}")
        return False

def extract_zip(zip_path, extract_to):
    print(f"압축 해제 중: {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("압축 해제 완료.")
        return True
    except Exception as e:
        print(f"압축 해제 실패: {e}")
        return False

def setup_ffmpeg():
    # Install to tools/ffmpeg (external_tools.py looks for tools/ffmpeg/bin/ffmpeg.exe)
    target_dir = TOOLS_DIR / "ffmpeg"
    if (target_dir / "bin" / "ffmpeg.exe").exists():
        print("[OK] FFmpeg가 이미 존재합니다.")
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
                print(f"[OK] FFmpeg 설치 완료: {target_dir}")
                
    if zip_path.exists(): 
        os.remove(zip_path)
    return (target_dir / "bin" / "ffmpeg.exe").exists()



def setup_realesrgan():
    # Install to resources/bin/realesrgan (AI binary)
    target_dir = AI_BIN_DIR / "realesrgan"
    if (target_dir / "realesrgan-ncnn-vulkan.exe").exists():
        print("[OK] Real-ESRGAN이 이미 존재합니다.")
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
                print(f"[OK] Real-ESRGAN 설치 완료: {target_dir}")
            else:
                 print("[FAIL] 추출된 파일에서 Real-ESRGAN 실행 파일을 찾을 수 없습니다.")

    if zip_path.exists(): 
        os.remove(zip_path)
    return (target_dir / "realesrgan-ncnn-vulkan.exe").exists()

def setup_rife():
    # Install to resources/bin/rife
    target_dir = AI_BIN_DIR / "rife"
    if (target_dir / "rife-ncnn-vulkan.exe").exists():
        print("[OK] RIFE가 이미 존재합니다.")
        return True

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_DIR / "rife.zip"
    
    if download_file(RIFE_URL, zip_path):
        if extract_zip(zip_path, TEMP_DIR):
            # Robust search
            found_exe = None
            found_dir = None
            for root, _, files in os.walk(TEMP_DIR):
                if "rife-ncnn-vulkan.exe" in files:
                    found_exe = Path(root) / "rife-ncnn-vulkan.exe"
                    found_dir = Path(root)
                    break
            
            if found_dir:
                if target_dir.exists(): 
                    shutil.rmtree(target_dir)
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                # Ensure we copy the whole folder content or just the executable and models?
                # RIFE usually needs the model folders alongside the exe.
                shutil.move(str(found_dir), str(target_dir))
                print(f"[OK] RIFE 설치 완료: {target_dir}")
            else:
                 print("[FAIL] 추출된 파일에서 RIFE 실행 파일을 찾을 수 없습니다.")

    if zip_path.exists(): 
        os.remove(zip_path)
    return (target_dir / "rife-ncnn-vulkan.exe").exists()

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
            requested = {"ffmpeg", "realesrgan", "rife"}
            break
    if not requested:
        requested = {"ffmpeg", "realesrgan", "rife"}
    return requested

def main():
    print("=== 외부 도구 설정 ===\n")

    requested = parse_requested_tools(sys.argv[1:])
    results = {}
    if "ffmpeg" in requested:
        results["FFmpeg"] = setup_ffmpeg()
    if "realesrgan" in requested:
        results["Real-ESRGAN"] = setup_realesrgan()
    if "rife" in requested:
        results["RIFE"] = setup_rife()
    
    cleanup_temp()
    
    print("\n=== 외부 도구 설치 요약 ===")
    for tool, success in results.items():
        status = "OK" if success else "FAIL"
        print(f"  {tool}: {status}")
    
    all_ok = all(results.values())
    if all_ok:
        print("\n모든 도구가 성공적으로 설치되었습니다!")
    else:
        print("\n일부 도구 설치에 실패했습니다. 위 출력을 확인하세요.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

