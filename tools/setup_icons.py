import os
import requests
import zipfile
import io
from pathlib import Path

def setup_icons():
    # URL for Windows 11 Icons (HaydenReeve/WindowsIcons)
    # Using the archive link for main branch
    url = "https://github.com/HaydenReeve/WindowsIcons/archive/refs/heads/main.zip"
    
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets" / "icons"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading icons from {url}...")
    try:
        r = requests.get(url)
        r.raise_for_status()
        
        print("Extracting...")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            # We want to extract specific icons or just dump them?
            # The repo structure is likely WindowsIcons-main/...
            # Let's extract all to a temp dir first or just iterate
            
            # We need to find suitable icons for our categories:
            # Image, Video, Audio, Sys (Folder, File)
            
            # Mapping heuristic (filename keywords)
            # We will try to find files matching these keywords and copy them to assets/icons
            
            targets = {
                "image.ico": ["Photos", "Image", "Picture", "Gallery"],
                "video.ico": ["Movies", "Video", "Film", "Cinema"],
                "audio.ico": ["Music", "Audio", "Sound"],
                "folder.ico": ["Folder", "Explorer"],
                "file.ico": ["Document", "File"],
                "settings.ico": ["Settings", "Gear"],
                "pdf.ico": ["PDF", "Acrobat"],
                "link.ico": ["Link", "Shortcut"]
            }
            
            found = {}
            
            for file_info in z.infolist():
                if not file_info.filename.endswith(".ico"):
                    continue
                    
                # Check if this file matches any target
                filename = Path(file_info.filename).name
                
                for target_name, keywords in targets.items():
                    if target_name in found:
                        continue
                        
                    for kw in keywords:
                        if kw.lower() in filename.lower():
                            # Found a match!
                            print(f"Found {target_name}: {filename}")
                            source = z.read(file_info)
                            with open(assets_dir / target_name, "wb") as f:
                                f.write(source)
                            found[target_name] = True
                            break
                            
            print(f"Extracted {len(found)} icons to {assets_dir}")
            
    except Exception as e:
        print(f"Failed to download/extract icons: {e}")

if __name__ == "__main__":
    setup_icons()
