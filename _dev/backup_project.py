import os
import zipfile
import datetime
from pathlib import Path

# Configuration
IGNORE_FOLDERS = {
    ".venv", ".git", ".pytest_cache", "__pycache__", 
    "logs", "backups", "data", "tmp", "example",
    "models", "bin", # Large binaries/models
    # Tools to exclude (restorable)
    "ffmpeg", "exiftool", "realesrgan", "ImageMagick", "Mayo", "blender",
    "tcl", "share", "test", "tests", "idlelib", "doc", "docs", "include", "Tools", "libs" # Python bloat
}
IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", "*.pyc", "*.spec"
}
INCLUDE_TOOLS_FOLDERS = {
    "quadwild" # Include small/custom tools
}

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def should_exclude(path, root_dir):
    """
    Check if path should be excluded based on whitelist/blacklist logic.
    """
    rel_path = path.relative_to(root_dir)
    parts = rel_path.parts
    
    # 1. Top-level folder exclusions
    if len(parts) > 0 and parts[0] in IGNORE_FOLDERS:
        return True
        
    # 2. Tools folder specific logic
    if len(parts) > 1 and parts[0] == "tools":
        tool_name = parts[1]
        # files in tools root are fine (setup scripts)
        if len(parts) == 2 and path.is_file(): 
            return False
            
        if tool_name not in INCLUDE_TOOLS_FOLDERS and tool_name not in IGNORE_FOLDERS:
             # Check if it was explicitly ignored in our set
             # If exact match in IGNORE_FOLDERS set above (e.g. "python")
             if tool_name in IGNORE_FOLDERS:
                 return True
             # If it's a directory in tools and NOT in include list, assume we want to keep it?
             # Wait, strategy: Exclude known large ones. Keep unknown small ones.
             pass

    # 3. Recurse check for ignored names anywhere
    for part in parts:
        if part in IGNORE_FOLDERS: # Safety catch
            return True
            
    return False

def backup_project():
    # Helper script is now in _dev/, so root is one level up
    root_dir = Path(__file__).parent.parent
    os.chdir(root_dir) # Ensure cwd is root for relative paths
    
    timestamp = get_timestamp()
    backup_file_name = f"ContextUp_Backup_{timestamp}.zip"
    backup_dir = root_dir / "backups"
    backup_path = backup_dir / backup_file_name
    
    # Create backups folder if needed
    backup_dir.mkdir(exist_ok=True)
    
    print(f"Creating backup: {backup_path}")
    print("Scanning directories...")
    
    files_to_zip = []
    
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored directories during traversal
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        
        # Special handling for 'tools' directory to strip specific subfolders
        if Path(root).name == "tools":
            # Remove excluded tools from traversal
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

        for file in files:
            file_path = Path(root) / file
            
            # Skip backup zip itself if it's being written
            if file_path == backup_path:
                continue
                
            # Skip existing backups
            if "backups" in file_path.parts:
                continue

            files_to_zip.append(file_path)

    print(f"Found {len(files_to_zip)} files to backup.")
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            arcname = file.relative_to(root_dir)
            zipf.write(file, arcname)
            
    print("-" * 50)
    print(f"✅ Backup Complete!")
    print(f"📁 Local Path: {backup_path}")
    
    # Get file size
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    print(f"📦 Size: {size_mb:.2f} MB")
    print("-" * 50)

if __name__ == "__main__":
    backup_project()
