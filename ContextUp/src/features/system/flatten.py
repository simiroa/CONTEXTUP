"""
Flatten Directory Tool (Headless).
Moves all files from subdirectories to the root folder and deletes empty subdirectories.
"""
import sys
import os
import shutil
from pathlib import Path
from tkinter import messagebox, Tk

def run_flatten_headless(target_path):
    target_path = Path(target_path)
    
    if not target_path.exists() or not target_path.is_dir():
        # Minimal root window for error dialog
        root = Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Invalid directory: {target_path}")
        root.destroy()
        return

    # Scan for files
    files_to_move = []
    subdirs = []
    
    for root, dirs, files in os.walk(target_path):
        if Path(root) == target_path:
            # Don't move files already in root
            subdirs.extend([Path(root) / d for d in dirs])
            continue
            
        for f in files:
            files_to_move.append(Path(root) / f)
        
        subdirs.append(Path(root))
    
    if not files_to_move:
        root = Tk()
        root.withdraw()
        messagebox.showinfo("Info", "No files found in subdirectories to flatten.")
        root.destroy()
        return

    # Safety Confirmation
    root = Tk()
    root.withdraw()
    confirm = messagebox.askyesno(
        "Flatten Directory", 
        f"Flattening '{target_path.name}'\n\n"
        f"Found {len(files_to_move)} files in {len(subdirs)} subdirectories.\n\n"
        "This will move ALL files to the root folder and delete empty subdirectories.\n"
        "This action cannot be undone.\n\n"
        "Proceed?",
        icon='warning'
    )
    
    if not confirm:
        root.destroy()
        return

    # Execute
    moved_count = 0
    errors = 0
    
    for src in files_to_move:
        dst = target_path / src.name
        
        # Handle collision (Rename strategy: file.txt -> file_1.txt)
        if dst.exists():
            base = dst.stem
            ext = dst.suffix
            counter = 1
            while dst.exists():
                dst = target_path / f"{base}_{counter}{ext}"
                counter += 1
        
        try:
            shutil.move(str(src), str(dst))
            moved_count += 1
        except Exception as e:
            print(f"Error moving {src}: {e}")
            errors += 1
            
    # Clean empty dirs
    deleted_dirs = 0
    for root_dir, dirs, files in os.walk(target_path, topdown=False):
        if Path(root_dir) == target_path: continue
        try:
            os.rmdir(root_dir)
            deleted_dirs += 1
        except:
            pass

    # Final Report
    msg = f"Flatten Complete.\n\nMoved: {moved_count} files\nDeleted: {deleted_dirs} folders"
    if errors > 0:
        msg += f"\nErrors: {errors}"
        
    messagebox.showinfo("Success", msg)
    root.destroy()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path_arg = sys.argv[1]
        run_flatten_headless(path_arg)
    else:
        # If run without args, ask for dir (fallback)
        root = Tk()
        root.withdraw()
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Directory to Flatten")
        root.destroy()
        if path:
            run_flatten_headless(path)
