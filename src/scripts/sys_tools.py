import os
import shutil
from pathlib import Path
from tkinter import simpledialog, messagebox, filedialog
import tkinter as tk

from core.logger import setup_logger

logger = setup_logger("sys_tools")

def _get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    root.focus_force()
    return root

def move_to_new_folder(target_path: str, selection=None):
    try:
        logger.info(f"Moving to new folder: {target_path}")
        
        if not selection:
            # Fallback if not passed (e.g. direct call)
            from utils.explorer import get_selection_from_explorer
            selection = get_selection_from_explorer(target_path)
            if not selection:
                # If still no selection, check if target_path itself is a file
                p = Path(target_path)
                if p.is_file():
                    selection = [p]
                else:
                    return
        
        # Ensure selection is list of Path
        selection = [Path(p) for p in selection]
            
        if not selection: return

        # Use parent of the first item as base
        base_dir = selection[0].parent
        
        # Auto-generate name: "New Folder", "New Folder (2)", etc.
        folder_name = "New Folder"
        new_folder = base_dir / folder_name
        
        if new_folder.exists():
            idx = 2
            while True:
                new_folder = base_dir / f"New Folder ({idx})"
                if not new_folder.exists():
                    break
                idx += 1
            
        new_folder.mkdir()
        
        count = 0
        errors = []
        for item in selection:
            try:
                if item.exists():
                    # Check if we are trying to move the new folder into itself (unlikely but possible if selection included parent?)
                    # Also check if destination exists
                    dest = new_folder / item.name
                    if dest.exists():
                        # Rename if collision? Or skip?
                        # Windows usually renames to "Name - Copy" or similar, or asks.
                        # For "Immediate" mode, let's try to rename automatically or skip.
                        # Let's skip and report error for now to be safe.
                        errors.append(f"{item.name} (Destination exists)")
                        continue
                        
                    shutil.move(str(item), str(dest))
                    count += 1
            except Exception as e:
                errors.append(f"{item.name}: {e}")
                
        if errors:
            msg = f"Moved {count} items.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5: msg += "\n..."
            messagebox.showwarning("Move Result", msg)
        
        # Trigger Rename on the new folder
        from utils.explorer import select_and_rename
        select_and_rename(new_folder)
        
    except Exception as e:
        logger.error(f"Move failed: {e}")
        messagebox.showerror("Error", f"Move failed: {e}")

def save_clipboard_image(target_path: str):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img is None:
            messagebox.showinfo("Info", "No image in clipboard.")
            return
            
        dest_dir = Path(target_path)
        if dest_dir.is_file(): dest_dir = dest_dir.parent
        
        # Find next available name
        idx = 1
        while True:
            save_path = dest_dir / f"clipboard_{idx:03d}.png"
            if not save_path.exists():
                break
            idx += 1
            
        img.save(save_path, "PNG")
        
    except Exception as e:
        messagebox.showerror("Error", f"Save failed: {e}")

def pdf_merge(target_path: str, selection=None):
    try:
        from pypdf import PdfWriter
        
        if not selection:
            from utils.explorer import get_selection_from_explorer
            selection = get_selection_from_explorer(target_path)
            if not selection:
                selection = [Path(target_path)]
            else:
                selection = [Path(p) for p in selection]
        
        selection = [Path(p) for p in selection]
            
        pdfs = [p for p in selection if p.suffix.lower() == '.pdf']
        
        if len(pdfs) < 2:
            # If folder selected, merge all inside?
            p = Path(target_path)
            if p.is_dir():
                pdfs = sorted([f for f in p.glob("*.pdf")])
            
        if len(pdfs) < 2:
            messagebox.showinfo("Info", "Select at least 2 PDF files.")
            return
            
        pdfs.sort()
        
        merger = PdfWriter()
        for pdf in pdfs:
            merger.append(str(pdf))
            
        dest = pdfs[0].parent / "merged.pdf"
        merger.write(str(dest))
        merger.close()
        
        messagebox.showinfo("Success", f"Merged {len(pdfs)} PDFs to {dest.name}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Merge failed: {e}")

def pdf_split(target_path: str):
    try:
        from pypdf import PdfReader, PdfWriter
        from pdf2image import convert_from_path
        
        path = Path(target_path)
        if path.suffix.lower() != '.pdf': return
        
        root = _get_root()
        
        # Ask for mode
        mode = simpledialog.askstring("Split PDF", "Enter mode: 'pdf' (split pages) or 'png' (convert to images):", parent=root)
        if not mode: return
        mode = mode.lower()
        
        output_dir = path.parent / path.stem
        output_dir.mkdir(exist_ok=True)
        
        if 'pdf' in mode:
            reader = PdfReader(str(path))
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                out_path = output_dir / f"{path.stem}_page_{i+1:03d}.pdf"
                with open(out_path, "wb") as f:
                    writer.write(f)
            messagebox.showinfo("Success", f"Split into {len(reader.pages)} PDFs in {output_dir.name}")
            
        elif 'png' in mode:
            # Requires poppler installed and in PATH
            try:
                images = convert_from_path(str(path))
                for i, img in enumerate(images):
                    out_path = output_dir / f"{path.stem}_page_{i+1:03d}.png"
                    img.save(out_path, "PNG")
                messagebox.showinfo("Success", f"Converted to {len(images)} PNGs in {output_dir.name}")
            except Exception as e:
                messagebox.showerror("Error", f"PNG conversion failed (Poppler installed?): {e}")
        else:
            messagebox.showwarning("Warning", "Unknown mode. Use 'pdf' or 'png'.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Split failed: {e}")

def copy_unc_path(target_path: str):
    try:
        import pyperclip
        p = Path(target_path).resolve()
        pyperclip.copy(str(p))
    except Exception as e:
        messagebox.showerror("Error", f"Copy failed: {e}")


def _get_target_files(target_path: str, allow_folder_content=False):
    from utils.explorer import get_selection_from_explorer
    selection = get_selection_from_explorer(target_path)
    if selection:
        return [Path(p) for p in selection]
    
    p = Path(target_path)
    if p.is_file():
        return [p]
    
    if allow_folder_content and p.is_dir():
        return [f for f in p.iterdir() if f.is_file()]
        
    return []


def clean_empty_dirs(target_path: str):
    path = Path(target_path)
    if not path.is_dir():
        messagebox.showwarning("Warning", "Please select a folder.")
        return
 
    if not messagebox.askyesno("Confirm", f"Remove all empty subdirectories in {path.name}?"):
        return
 
    removed_count = 0
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                d = Path(root) / name
                try:
                    if not any(d.iterdir()):
                        d.rmdir()
                        removed_count += 1
                except OSError:
                    pass
        
        messagebox.showinfo("Success", f"Removed {removed_count} empty directories.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to clean: {e}")
 
def create_symlink(target_path: str, selection=None):
    try:
        if selection:
            files = [Path(p) for p in selection]
        else:
            files = _get_target_files(target_path)
            
        if not files: return
        
        # If single file, create link immediately and trigger rename
        if len(files) == 1:
            src_path = files[0]
            
            # Auto-generate name
            link_name = f"{src_path.stem} - Link{src_path.suffix}"
            link_path = src_path.parent / link_name
            
            # Collision check
            if link_path.exists():
                idx = 2
                while True:
                    link_name = f"{src_path.stem} - Link ({idx}){src_path.suffix}"
                    link_path = src_path.parent / link_name
                    if not link_path.exists(): break
                    idx += 1
            
            try:
                os.symlink(src_path, link_path)
                
                # Trigger Rename
                from utils.explorer import select_and_rename
                select_and_rename(link_path)
                
            except OSError as e:
                if hasattr(e, 'winerror') and e.winerror == 1314:
                    messagebox.showerror("Error", "Privilege not held. Enable Developer Mode or run as Admin.")
                else:
                    messagebox.showerror("Error", str(e))
        else:
            # Batch mode: Create links with default suffix (No rename trigger for batch)
            count = 0
            errors = []
            for src_path in files:
                link_name = f"{src_path.stem} - Link{src_path.suffix}"
                link_path = src_path.parent / link_name
                
                if link_path.exists():
                    errors.append(f"{src_path.name}: Link exists")
                    continue
                    
                try:
                    os.symlink(src_path, link_path)
                    count += 1
                except OSError as e:
                    if hasattr(e, 'winerror') and e.winerror == 1314:
                        # Fail fast for privilege error
                        messagebox.showerror("Error", "Privilege not held. Enable Developer Mode or run as Admin.")
                        return
                    errors.append(f"{src_path.name}: {e}")
            
            if errors:
                msg = f"Created {count}/{len(files)} links.\n\nErrors:\n" + "\n".join(errors[:5])
                messagebox.showwarning("Completed with Errors", msg)
            else:
                messagebox.showinfo("Success", f"Created {count} symlinks.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to create symlink: {e}")

def find_missing_frames(target_path: str, selection=None):
    try:
        # Allow folder content if background clicked
        if selection:
            files = [Path(p) for p in selection]
        else:
            files = _get_target_files(target_path, allow_folder_content=True)
            
        if not files: return
        
        # Logic expects a list of files to check sequences from
        # If we selected a folder, we want to check inside it.
        # _get_target_files handles this if allow_folder_content=True
        
        # But wait, if we selected specific files, we only check those?
        # Usually "Find Missing Frames" checks the sequence the file belongs to.
        # So if I select "shot.0100.jpg", I want to check the whole folder?
        # Or just the selection?
        # User said "No need for single file selection".
        # If multiple files selected, check gaps in selection.
        # If folder selected, check all sequences in folder.
        
        if len(files) == 1 and files[0].is_file():
            # If single file, maybe check parent folder?
            # But user said "No need for single file".
            return
            
        # ... (Rest of logic is similar but needs adaptation to 'files' list)
        # The original logic iterated 'folder.iterdir()'.
        # We should adapt to use 'files'.
        
        import re
        sequences = {}
        pattern = re.compile(r"^(.*?)(\d+)(\.[a-zA-Z0-9]+)$")
        
        for f in files:
            match = pattern.match(f.name)
            if match:
                prefix, num_str, ext = match.groups()
                key = (prefix, ext)
                if key not in sequences:
                    sequences[key] = []
                sequences[key].append(int(num_str))
                
        if not sequences:
            messagebox.showinfo("Result", "No sequences found in selection.")
            return
            
        report = []
        for (prefix, ext), nums in sequences.items():
            nums.sort()
            missing = []
            if len(nums) > 1:
                full_range = set(range(nums[0], nums[-1] + 1))
                existing = set(nums)
                missing = sorted(list(full_range - existing))
                
            if missing:
                missing_str = ", ".join(map(str, missing[:20]))
                if len(missing) > 20: missing_str += "..."
                report.append(f"{prefix}*{ext}: Missing {len(missing)} frames ({missing_str})")
            else:
                report.append(f"{prefix}*{ext}: OK ({len(nums)} frames)")
                
        messagebox.showinfo("Missing Frames Report", "\n".join(report))
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
 
def arrange_sequences(target_path: str, selection=None):
    try:
        if selection:
            files = [Path(p) for p in selection]
        else:
            files = _get_target_files(target_path, allow_folder_content=True)
            
        if not files: return
        
        import re
        pattern = re.compile(r"^(.*?)(\d+)(\.[a-zA-Z0-9]+)$")
        
        moves = {} 
        
        for f in files:
            match = pattern.match(f.name)
            if match:
                prefix, _, _ = match.groups()
                if not prefix: continue
                # Use parent of file as base
                dest = f.parent / prefix.strip(" _-.")
                if dest not in moves:
                    moves[dest] = []
                moves[dest].append(f)
                
        if not moves:
            messagebox.showinfo("Result", "No sequences detected.")
            return
            
        count = 0
        for dest, flist in moves.items():
            if len(flist) < 2: continue 
            
            dest.mkdir(exist_ok=True)
            for f in flist:
                shutil.move(str(f), str(dest / f.name))
                count += 1
                
        messagebox.showinfo("Success", f"Moved {count} files into {len(moves)} folders.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
