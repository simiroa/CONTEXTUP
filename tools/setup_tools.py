import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).parent.parent
TOOLS_DIR = ROOT_DIR / "tools"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def download_file(url, dest):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print("Download complete.")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Extraction complete.")
        return True
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False

def setup_ffmpeg():
    ffmpeg_dir = TOOLS_DIR / "ffmpeg"
    if (ffmpeg_dir / "bin" / "ffmpeg.exe").exists():
        print("FFmpeg already exists.")
        return

    TOOLS_DIR.mkdir(exist_ok=True)
    zip_path = TOOLS_DIR / "ffmpeg.zip"
    
    if download_file(FFMPEG_URL, zip_path):
        if extract_zip(zip_path, TOOLS_DIR):
            # The zip usually contains a subfolder like "ffmpeg-master-latest-win64-gpl"
            # We want to move its contents to tools/ffmpeg or rename it
            extracted_dirs = [d for d in TOOLS_DIR.iterdir() if d.is_dir() and "ffmpeg" in d.name and d.name != "ffmpeg"]
            if extracted_dirs:
                src_dir = extracted_dirs[0]
                # Rename to 'ffmpeg'
                if ffmpeg_dir.exists():
                    shutil.rmtree(ffmpeg_dir)
                src_dir.rename(ffmpeg_dir)
                print(f"FFmpeg installed to {ffmpeg_dir}")
            
            # Cleanup
            os.remove(zip_path)

EXIFTOOL_URL = "https://exiftool.org/exiftool-13.06_64.zip" # Fallback or specific version

def setup_exiftool():
    exif_dir = TOOLS_DIR / "exiftool"
    if (exif_dir / "exiftool.exe").exists():
        print("ExifTool already exists.")
        return

    TOOLS_DIR.mkdir(exist_ok=True)
    zip_path = TOOLS_DIR / "exiftool.zip"
    
    # Try 13.06 first (known good)
    if download_file(EXIFTOOL_URL, zip_path):
        if extract_zip(zip_path, TOOLS_DIR):
            # Usually extracts to a folder or just the exe
            # ExifTool zip usually contains "exiftool(-k).exe"
            
            # Find the extracted exe
            found_exe = None
            for root, _, files in os.walk(TOOLS_DIR):
                for file in files:
                    if file.startswith("exiftool") and file.endswith(".exe"):
                        found_exe = Path(root) / file
                        break
                if found_exe: break
            
            if found_exe:
                if exif_dir.exists():
                    shutil.rmtree(exif_dir)
                exif_dir.mkdir()
                
                target_exe = exif_dir / "exiftool.exe"
                shutil.move(str(found_exe), str(target_exe))
                print(f"ExifTool installed to {target_exe}")
                
                # Cleanup if it was in a subfolder
                if found_exe.parent != TOOLS_DIR and found_exe.parent != exif_dir:
                     try:
                         shutil.rmtree(found_exe.parent)
                     except: pass
            else:
                print("Could not find exiftool.exe in the downloaded zip.")
            
            # Cleanup zip
            if zip_path.exists():
                os.remove(zip_path)

REALESRGAN_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"

def setup_realesrgan():
    esrgan_dir = TOOLS_DIR / "realesrgan"
    if (esrgan_dir / "realesrgan-ncnn-vulkan.exe").exists():
        print("Real-ESRGAN already exists.")
        return

    TOOLS_DIR.mkdir(exist_ok=True)
    zip_path = TOOLS_DIR / "realesrgan.zip"
    
    if download_file(REALESRGAN_URL, zip_path):
        if extract_zip(zip_path, TOOLS_DIR):
            # It extracts to a folder like "realesrgan-ncnn-vulkan-20220424-windows"
            extracted_dirs = [d for d in TOOLS_DIR.iterdir() if d.is_dir() and "realesrgan" in d.name and d.name != "realesrgan"]
            if extracted_dirs:
                src_dir = extracted_dirs[0]
                if esrgan_dir.exists():
                    shutil.rmtree(esrgan_dir)
                src_dir.rename(esrgan_dir)
                print(f"Real-ESRGAN installed to {esrgan_dir}")
            
            if zip_path.exists():
                os.remove(zip_path)

def main():
    print("Setting up tools...")
    setup_ffmpeg()
    setup_exiftool()
    setup_realesrgan()
    print("Done.")

if __name__ == "__main__":
    main()
