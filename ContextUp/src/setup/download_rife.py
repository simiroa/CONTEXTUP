import os
import zipfile
import urllib.request
import shutil
from pathlib import Path

def download_rife():
    url = "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-windows.zip"
    dest_dir = Path(__file__).parent.parent.parent / "resources" / "bin" / "rife"
    zip_path = dest_dir / "rife.zip"
    
    # Create dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading RIFE binary from {url}...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("Download complete.")
        
        print("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
            
        # Cleanup
        os.remove(zip_path)
        
        # Move files up if needed (usually inside a folder)
        # The zip contains "rife-ncnn-vulkan-20221029-windows" folder
        extracted_folder = dest_dir / "rife-ncnn-vulkan-20221029-windows"
        if extracted_folder.exists():
            for item in extracted_folder.iterdir():
                shutil.move(str(item), str(dest_dir))
            extracted_folder.rmdir()
            
        print(f"Success! RIFE binary installed at {dest_dir}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    download_rife()

