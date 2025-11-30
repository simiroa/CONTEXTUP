import os
import sys
from pathlib import Path
from PIL import Image
from tkinter import messagebox, ttk
import tkinter as tk
import subprocess
import threading
import math

# Add src to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.gui import ask_selection
from utils.explorer import get_selection_from_explorer
from utils.external_tools import get_ffmpeg

def _get_root():
    root = tk.Tk()
    root.withdraw()
    return root

def _get_target_files(target_path: str):
    selection = get_selection_from_explorer(target_path)
    if not selection:
        selection = [target_path]
    return [Path(p) for p in selection]



def convert_format(target_path: str):
    try:
        files = _get_target_files(target_path)
        # Filter images
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tga', '.tif', '.tiff', '.ico', '.exr'}
        files = [f for f in files if f.suffix.lower() in img_exts]
        
        if not files: 
            messagebox.showinfo("Info", "No image files selected.")
            return

        formats = ["PNG", "JPG", "WEBP", "BMP", "TGA", "TIFF", "ICO"]
        target_format = ask_selection("Convert Image", f"Select target format for {len(files)} files:", formats)
        
        if not target_format: return

        if target_format == "JPG": target_format = "JPEG"
        
        if target_format == "JPG": target_format = "JPEG"
        
        from utils.progress_gui import run_batch_gui
        
        def process_convert(path, update_msg):
            try:
                update_msg(f"Converting {path.name}...")
                
                # Special handling for EXR
                if path.suffix.lower() == '.exr':
                    ffmpeg = get_ffmpeg()
                    new_path = path.with_suffix(f".{target_format.lower()}")
                    cmd = [ffmpeg, "-i", str(path), "-y", str(new_path)]
                    subprocess.run(cmd, check=True, capture_output=True)
                    return True, ""

                img = Image.open(path)
                new_path = path.with_suffix(f".{target_format.lower()}")
                
                # Handle transparency for JPEG
                if target_format == "JPEG" and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif target_format == "JPEG" and img.mode == 'P':
                     img = img.convert("RGB")
                    
                img.save(new_path)
                return True, ""
            except Exception as e:
                return False, str(e)
        
        run_batch_gui("Converting Images", files, process_convert)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert: {e}")

def remove_exif(target_path: str):
    try:
        files = _get_target_files(target_path)
        
        from utils.progress_gui import run_batch_gui
        
        def process_exif(path, update_msg):
            try:
                update_msg(f"Processing {path.name}...")
                img = Image.open(path)
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                image_without_exif.save(path)
                return True, ""
            except Exception as e:
                return False, str(e)
                
        run_batch_gui("Removing EXIF", files, process_exif)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove EXIF: {e}")

def resize_pot(target_path: str):
    try:
        files = _get_target_files(target_path)
        
        # Ask for mode: Canvas (Pad) or Stretch
        root = _get_root()
        mode = ask_selection("Resize POT", "Select resize mode:", ["Canvas (Pad with Transparency/Black)", "Stretch (Distort)"])
        if not mode: return
        
        is_stretch = "Stretch" in mode
        
        from utils.progress_gui import run_batch_gui
        
        def nearest_power_of_2(x):
            if x == 0: return 1
            return 2**math.ceil(math.log2(x))

        def process_resize(path, update_msg):
            try:
                update_msg(f"Resizing {path.name}...")
                img = Image.open(path)
                width, height = img.size
                
                new_w = nearest_power_of_2(width)
                new_h = nearest_power_of_2(height)
                
                if new_w == width and new_h == height:
                    return True, "Already POT"

                if is_stretch:
                    new_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                else:
                    color = (0, 0, 0, 0) if 'A' in img.mode else (0, 0, 0)
                    new_img = Image.new(img.mode, (new_w, new_h), color)
                    
                    x = (new_w - width) // 2
                    y = (new_h - height) // 2
                    new_img.paste(img, (x, y))
                
                new_img.save(path)
                return True, ""
            except Exception as e:
                return False, str(e)

        run_batch_gui("Resizing to Power of 2", files, process_resize)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to resize: {e}")

def exr_split(target_path: str):
    try:
        files = _get_target_files(target_path)
        files = [f for f in files if f.suffix.lower() == '.exr']
        if not files: return

        ffmpeg = get_ffmpeg()
        
        from utils.progress_gui import run_batch_gui
        
        def process_split(path, update_msg):
            try:
                update_msg(f"Splitting {path.name}...")
                output_pattern = path.parent / f"{path.stem}_layer_%02d.exr"
                cmd = [
                    ffmpeg, "-i", str(path),
                    "-map", "0",
                    "-c", "copy",
                    "-f", "image2",
                    str(output_pattern)
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return True, ""
            except Exception as e:
                return False, str(e)
                
        run_batch_gui("Splitting EXR Layers", files, process_split)
        
    except Exception as e:
        messagebox.showerror("Error", f"EXR Split failed: {e}")

def exr_merge(target_path: str):
    try:
        selection = _get_target_files(target_path)
        
        if not selection or len(selection) < 2:
            messagebox.showinfo("Info", "Select multiple EXR files to merge.")
            return
            
        selection = sorted([p for p in selection if p.suffix.lower() == '.exr'])
        if len(selection) < 2:
             messagebox.showinfo("Info", "Not enough EXR files selected.")
             return

        output_path = selection[0].with_name(f"{selection[0].stem}_merged.exr")
        ffmpeg = get_ffmpeg()
        
        root = _get_root()
        progress = ProgressWindow("Merging EXR Files", 1)
        progress.update_progress(0, "Merging...")
            
        cmd = [ffmpeg]
        for f in selection:
            cmd.extend(["-i", str(f)])
            
        # Map all inputs
        for i in range(len(selection)):
            cmd.extend(["-map", f"{i}"])
            
        cmd.extend(["-c", "copy", "-y", str(output_path)])
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        progress.destroy()
        messagebox.showinfo("Success", f"Merged {len(selection)} files to {output_path.name}")
        
    except Exception as e:
        messagebox.showerror("Error", f"EXR Merge failed: {e}")
